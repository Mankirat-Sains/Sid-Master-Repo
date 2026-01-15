"""
Cypher Query Verification Agent

This module provides an agent-based verification system for Cypher queries
before they are executed against the KuzuDB graph database. It ensures that
all queries are safe, valid, and properly scoped.

Verification Checks:
1. Safety Validation: Reject WRITE operations (CREATE, MERGE, SET, DELETE, DROP)
2. Schema Validation: Verify node labels and relationship types exist in schema
3. Syntax Validation: Basic Cypher syntax checks (MATCH...RETURN structure)
4. KuzuDB Compatibility: Reject Neo4j-specific syntax not supported by KuzuDB
5. Complexity Validation: Limit query depth and ensure result limits
"""

import re
from typing import Dict, List, Optional, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel
from config.llm_instances import llm_fast
from prompts.cypher_verifier_prompts import (
    CYPHER_VERIFICATION_PROMPT,
    KUZU_INCOMPATIBLE_PATTERNS,
    KUZU_COMPATIBILITY_NOTES
)
import logging

# Setup logging
log_verifier = logging.getLogger("CYPHER_VERIFIER")


# =====================================================================
# SCHEMA CONSTANTS (from BimDB.cypher)
# =====================================================================

VALID_NODE_LABELS = {
    "User", "Project", "Model", "Version",
    "Wall", "Floor", "Roof", "Beam", "Column",
    "Ceiling", "Door", "Window", "Pipe", "Duct"
}

VALID_RELATIONSHIP_TYPES = {
    "OWNS", "CONTAINS_MODEL", "HAS_VERSION",
    "CREATED_MODEL", "CREATED_VERSION",
    "REFERENCES_WALL", "REFERENCES_FLOOR", "REFERENCES_ROOF",
    "REFERENCES_BEAM", "REFERENCES_COLUMN", "REFERENCES_CEILING",
    "REFERENCES_DOOR", "REFERENCES_WINDOW", "REFERENCES_PIPE", "REFERENCES_DUCT"
}

# Reserved keywords that need backticks
RESERVED_KEYWORDS = {"Column"}


# =====================================================================
# CYPHER VERIFIER CLASS
# =====================================================================

class CypherVerifier:
    """
    Agent-based verifier for Cypher queries.
    Uses an LLM to perform intelligent validation with fallback to rule-based checks.
    """

    def __init__(self, llm: Optional[BaseChatModel] = None):
        """
        Initialize the Cypher verifier.

        Args:
            llm: LLM instance for agent-based verification (ChatGroq, ChatOpenAI, or ChatAnthropic)
                 If None, will use llm_fast from config (pre-configured fast model)
        """
        self.llm: BaseChatModel = llm or llm_fast  # Fast model for verification
        self.verification_prompt = ChatPromptTemplate.from_template(
            CYPHER_VERIFICATION_PROMPT
        )

    def verify(self, cypher_query: str) -> Dict[str, Any]:
        """
        Verify a Cypher query using agent-based validation.

        Args:
            cypher_query: The Cypher query to verify

        Returns:
            Dict with keys:
                - approved: bool (whether query is safe to execute)
                - safety_passed: bool
                - schema_passed: bool
                - syntax_passed: bool
                - issues: List[str] (blocking issues)
                - warnings: List[str] (non-blocking warnings)
                - corrected_query: Optional[str] (auto-corrected version)
                - reasoning: str (explanation)
        """
        log_verifier.info("🛡️ Starting Cypher query verification...")

        try:
            # First, run quick rule-based safety check
            safety_check = self._rule_based_safety_check(cypher_query)
            if not safety_check["passed"]:
                log_verifier.warning(f"❌ Rule-based safety check failed: {safety_check['reason']}")
                return {
                    "approved": False,
                    "safety_passed": False,
                    "schema_passed": True,
                    "syntax_passed": True,
                    "kuzu_compatibility_passed": True,
                    "issues": [safety_check["reason"]],
                    "warnings": [],
                    "corrected_query": None,
                    "reasoning": "Query contains forbidden write operations"
                }

            # Second, run KuzuDB compatibility check
            kuzu_check = self._kuzu_compatibility_check(cypher_query)
            if not kuzu_check["passed"]:
                log_verifier.warning(f"❌ KuzuDB compatibility check failed: {kuzu_check['reason']}")
                return {
                    "approved": False,
                    "safety_passed": True,
                    "schema_passed": True,
                    "syntax_passed": True,
                    "kuzu_compatibility_passed": False,
                    "issues": [kuzu_check["reason"]],
                    "warnings": [],
                    "corrected_query": None,
                    "reasoning": "Query uses Neo4j-specific syntax not supported by KuzuDB"
                }

            # Run LLM-based verification
            log_verifier.info("🤖 Running LLM-based verification...")
            prompt = self.verification_prompt.format_messages(
                cypher_query=cypher_query,
                valid_node_labels=", ".join(sorted(VALID_NODE_LABELS)),
                valid_relationship_types=", ".join(sorted(VALID_RELATIONSHIP_TYPES))
            )

            response = self.llm.invoke(prompt)
            result_text = response.content.strip()

            # Parse JSON response
            import json
            # Extract JSON from markdown code blocks if present
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            result = json.loads(result_text)

            # Validate response structure
            if not self._validate_response_structure(result):
                log_verifier.error("❌ LLM response has invalid structure")
                # Fallback to rule-based verification
                return self._fallback_verification(cypher_query)

            # Log results
            if result.get("approved", False):
                log_verifier.info("✅ Cypher query APPROVED by verification agent")
                if result.get("warnings"):
                    log_verifier.info(f"⚠️ Warnings: {', '.join(result['warnings'])}")
            else:
                log_verifier.warning(f"❌ Cypher query REJECTED: {', '.join(result.get('issues', []))}")

            return result

        except Exception as e:
            log_verifier.error(f"❌ Verification failed with error: {e}")
            import traceback
            traceback.print_exc()

            # Fallback to rule-based verification
            return self._fallback_verification(cypher_query)

    def _rule_based_safety_check(self, cypher_query: str) -> Dict[str, Any]:
        """
        Quick rule-based safety check for write operations.

        Args:
            cypher_query: The query to check

        Returns:
            Dict with 'passed' (bool) and 'reason' (str)
        """
        # Convert to uppercase for case-insensitive matching
        query_upper = cypher_query.upper()

        # Forbidden write operations
        write_operations = ["CREATE", "MERGE", "SET", "DELETE", "DROP", "DETACH", "REMOVE"]

        for operation in write_operations:
            # Use word boundary to avoid false positives (e.g., "createdAt" property)
            if re.search(r'\b' + operation + r'\b', query_upper):
                return {
                    "passed": False,
                    "reason": f"{operation} operation detected - write operations are forbidden"
                }

        return {"passed": True, "reason": "No write operations detected"}

    def _kuzu_compatibility_check(self, cypher_query: str) -> Dict[str, Any]:
        """
        Check for Neo4j-specific syntax that's incompatible with KuzuDB.

        Args:
            cypher_query: The query to check

        Returns:
            Dict with 'passed' (bool) and 'reason' (str)
        """
        # Check for Neo4j-specific patterns
        for pattern, description in KUZU_INCOMPATIBLE_PATTERNS.items():
            if pattern in cypher_query:
                return {
                    "passed": False,
                    "reason": f"Neo4j-specific syntax '{pattern}' detected - {description}"
                }

        # Check for unbounded variable-length relationships: -[*]-> or -[*]-
        # Must have upper bound in KuzuDB: -[*1..5]->
        unbounded_pattern = re.search(r'-\[\*\](-|>)', cypher_query)
        if unbounded_pattern:
            return {
                "passed": False,
                "reason": "Variable-length relationship '-[*]-' must have upper bound in KuzuDB (e.g., '-[*1..5]->')"
            }

        return {"passed": True, "reason": "No KuzuDB compatibility issues detected"}

    def _validate_response_structure(self, result: Dict) -> bool:
        """Validate that LLM response has required fields."""
        required_fields = ["approved", "safety_passed", "schema_passed", "syntax_passed", "kuzu_compatibility_passed"]
        return all(field in result for field in required_fields)

    def _fallback_verification(self, cypher_query: str) -> Dict[str, Any]:
        """
        Fallback rule-based verification if LLM verification fails.

        Args:
            cypher_query: The query to verify

        Returns:
            Verification result dict
        """
        log_verifier.info("⚙️ Using fallback rule-based verification...")

        issues = []
        warnings = []

        # Safety check
        safety_check = self._rule_based_safety_check(cypher_query)
        if not safety_check["passed"]:
            issues.append(safety_check["reason"])
            return {
                "approved": False,
                "safety_passed": False,
                "schema_passed": True,
                "syntax_passed": True,
                "kuzu_compatibility_passed": True,
                "issues": issues,
                "warnings": warnings,
                "corrected_query": None,
                "reasoning": "Fallback verification: write operations forbidden"
            }

        # KuzuDB compatibility check
        kuzu_check = self._kuzu_compatibility_check(cypher_query)
        if not kuzu_check["passed"]:
            issues.append(kuzu_check["reason"])
            return {
                "approved": False,
                "safety_passed": True,
                "schema_passed": True,
                "syntax_passed": True,
                "kuzu_compatibility_passed": False,
                "issues": issues,
                "warnings": warnings,
                "corrected_query": None,
                "reasoning": "Fallback verification: Neo4j syntax not compatible with KuzuDB"
            }

        # Check for RETURN clause
        if "RETURN" not in cypher_query.upper() and "CALL" not in cypher_query.upper():
            issues.append("Query must have a RETURN clause or CALL statement")

        # Check for LIMIT (warning only)
        if "LIMIT" not in cypher_query.upper():
            warnings.append("Query does not have a LIMIT clause - consider adding one for safety")

        # Check for MATCH (most queries should have it)
        if "MATCH" not in cypher_query.upper():
            warnings.append("Query does not contain MATCH clause - verify this is intentional")

        approved = len(issues) == 0

        return {
            "approved": approved,
            "safety_passed": True,
            "schema_passed": True,  # Can't verify without LLM
            "syntax_passed": len(issues) == 0,
            "kuzu_compatibility_passed": True,
            "issues": issues,
            "warnings": warnings,
            "corrected_query": None,
            "reasoning": "Fallback rule-based verification completed"
        }


# =====================================================================
# CONVENIENCE FUNCTION
# =====================================================================

def verify_cypher_query(cypher_query: str, llm: Optional[BaseChatModel] = None) -> Dict[str, Any]:
    """
    Convenience function to verify a Cypher query.

    Args:
        cypher_query: The Cypher query to verify
        llm: Optional LLM instance (ChatGroq, ChatOpenAI, or ChatAnthropic)
             If None, uses llm_fast from config

    Returns:
        Verification result dict
    """
    verifier = CypherVerifier(llm=llm)
    return verifier.verify(cypher_query)
