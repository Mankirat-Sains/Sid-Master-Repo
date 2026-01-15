"""
Text-to-Cypher Assistant
Created: 2026-01-15
Purpose: Convert natural language queries to Cypher queries for KuzuDB graph database

This module provides the TextToCypherAssistant class which:
1. Generates Cypher queries from natural language using LLM
2. Verifies generated queries using the Cypher verification agent
3. Executes verified queries against KuzuDB
4. Formats results as LangChain Documents for RAG pipeline integration

Architecture:
- Mirrors TextToSQLAssistant pattern from sid_text2sql
- Uses agent-based verification before execution
- Logs all queries in DEBUG_MODE for developer inspection
"""

import json
import time
import logging
from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.documents import Document

# Import LLM instances and prompts
from config.llm_instances import llm_fast
from prompts.cypher_generator_prompts import CYPHER_SYSTEM_PROMPT
from nodes.DBRetrieval.KGdb.kuzu_client import KuzuManager, get_kuzu_manager
from nodes.DBRetrieval.KGdb.cypher_verifier import CypherVerifier
from config.settings import DEBUG_MODE

# Setup logging
log_assistant = logging.getLogger("TEXT_TO_CYPHER")
if DEBUG_MODE:
    log_assistant.setLevel(logging.INFO)
else:
    log_assistant.setLevel(logging.WARNING)


class TextToCypherAssistant:
    """
    Assistant for converting natural language to Cypher queries.

    Workflow:
    1. User Query → Generate Cypher (LLM)
    2. Verify Cypher (Agent-based verification)
    3. Execute Cypher (KuzuDB)
    4. Format Results (LangChain Documents)
    """

    def __init__(
        self,
        kuzu_manager: Optional[KuzuManager] = None,
        llm: Optional[BaseChatModel] = None,
        verifier: Optional[CypherVerifier] = None
    ):
        """
        Initialize the Text-to-Cypher Assistant.

        Args:
            kuzu_manager: KuzuDB manager instance (if None, uses global singleton)
            llm: LLM instance for query generation (if None, uses llm_fast from config)
            verifier: Cypher verifier instance (if None, creates new one)
        """
        self.kuzu_manager = kuzu_manager or get_kuzu_manager()
        self.llm: BaseChatModel = llm or llm_fast
        self.verifier = verifier or CypherVerifier(llm=self.llm)
        self.schema_cache = None  # Cache schema for 5 minutes (to be implemented)

        # Create prompt template
        self.generation_prompt = ChatPromptTemplate.from_messages([
            ("system", CYPHER_SYSTEM_PROMPT),
            ("human", "Convert this natural language query to Cypher:\n\n{user_query}")
        ])

        log_assistant.info("✅ Text-to-Cypher Assistant initialized")

    def generate_cypher(self, user_query: str) -> Dict[str, Any]:
        """
        Generate Cypher query from natural language.

        Args:
            user_query: Natural language question from user

        Returns:
            Dict with keys: cypher, reasoning, confidence, requires_clarification
        """
        try:
            log_assistant.info(f"🤖 Generating Cypher for: '{user_query}'")

            # Build prompt
            prompt = self.generation_prompt.format_messages(user_query=user_query)

            # Call LLM
            log_assistant.info(f"📞 Calling LLM: {type(self.llm).__name__}")
            response = self.llm.invoke(prompt)

            # Handle different response types
            if hasattr(response, 'content'):
                content = response.content.strip()
            elif isinstance(response, dict):
                content = response.get('content', str(response))
            else:
                content = str(response)

            log_assistant.info(f"📥 LLM response received ({len(content)} chars)")

            # Strip markdown code fences if present
            if content.startswith("```"):
                # Extract content between ```json and ```
                lines = content.split("\n")
                json_lines = []
                in_code_block = False
                for line in lines:
                    if line.strip().startswith("```"):
                        if not in_code_block:
                            in_code_block = True
                            continue
                        else:
                            break
                    if in_code_block:
                        json_lines.append(line)
                content = "\n".join(json_lines).strip()
                log_assistant.info("📋 Stripped markdown code fences from response")

            # Parse JSON response
            try:
                result = json.loads(content)

                # Validate response structure
                if "cypher_query" not in result:
                    log_assistant.error("❌ LLM response missing 'cypher_query' field")
                    return {
                        "cypher": None,
                        "reasoning": "LLM response was malformed",
                        "confidence": 0.0,
                        "requires_clarification": False,
                        "error": "Invalid LLM response format"
                    }

                log_assistant.info(f"✅ Cypher generated (confidence: {result.get('confidence', 0.0)})")

                return {
                    "cypher": result.get("cypher_query"),
                    "reasoning": result.get("reasoning", ""),
                    "confidence": result.get("confidence", 0.0),
                    "requires_clarification": result.get("requires_clarification", False),
                    "clarification_question": result.get("clarification_question", None)
                }

            except json.JSONDecodeError as e:
                log_assistant.error(f"❌ Failed to parse LLM JSON response: {e}")
                log_assistant.error(f"Raw response: {content[:500]}")

                # Try to extract Cypher query from markdown code blocks
                if "```cypher" in content.lower():
                    lines = content.split("\n")
                    cypher_lines = []
                    in_code_block = False
                    for line in lines:
                        if "```cypher" in line.lower():
                            in_code_block = True
                            continue
                        if "```" in line and in_code_block:
                            break
                        if in_code_block:
                            cypher_lines.append(line)

                    if cypher_lines:
                        cypher_query = "\n".join(cypher_lines).strip()
                        log_assistant.warning(f"⚠️ Extracted Cypher from markdown: {cypher_query[:100]}")
                        return {
                            "cypher": cypher_query,
                            "reasoning": "Extracted from markdown code block",
                            "confidence": 0.7,
                            "requires_clarification": False
                        }

                return {
                    "cypher": None,
                    "reasoning": f"Failed to parse JSON: {str(e)}",
                    "confidence": 0.0,
                    "requires_clarification": False,
                    "error": str(e)
                }

        except Exception as e:
            log_assistant.error(f"❌ Cypher generation failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "cypher": None,
                "reasoning": f"Exception during generation: {str(e)}",
                "confidence": 0.0,
                "requires_clarification": False,
                "error": str(e)
            }

    def verify_cypher(self, cypher_query: str) -> Dict[str, Any]:
        """
        Verify Cypher query is safe and valid using agent-based verification.

        Args:
            cypher_query: The Cypher query to verify

        Returns:
            Verification result dict from CypherVerifier
        """
        log_assistant.info("🛡️ Verifying Cypher query with agent...")
        return self.verifier.verify(cypher_query)

    def execute_cypher(self, cypher_query: str) -> Dict[str, Any]:
        """
        Execute verified Cypher query against Kuzu.

        Args:
            cypher_query: The verified Cypher query to execute

        Returns:
            Dict with keys: success, documents, row_count, error (if failed)
        """
        try:
            log_assistant.info("⚡ Executing Cypher query...")

            # Execute via KuzuManager
            result = self.kuzu_manager.execute(cypher_query)

            if not result.get("success", False):
                log_assistant.error(f"❌ Cypher execution failed: {result.get('error')}")
                return {
                    "success": False,
                    "error": result.get("error"),
                    "documents": [],
                    "row_count": 0
                }

            # Format results as Documents for RAG pipeline
            documents = self._format_results_as_documents(result, cypher_query)

            log_assistant.info(f"✅ Cypher executed successfully, {len(documents)} documents created")

            return {
                "success": True,
                "documents": documents,
                "row_count": result.get("row_count", 0),
                "columns": result.get("columns", [])
            }

        except Exception as e:
            log_assistant.error(f"❌ Cypher execution exception: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "documents": [],
                "row_count": 0
            }

    def _format_results_as_documents(
        self,
        execution_result: Dict[str, Any],
        cypher_query: str
    ) -> List[Document]:
        """
        Format Cypher query results as LangChain Documents for RAG pipeline.

        Args:
            execution_result: Result dict from KuzuManager.execute()
            cypher_query: The Cypher query that produced these results

        Returns:
            List of Document objects
        """
        documents = []

        try:
            columns = execution_result.get("columns", [])
            rows = execution_result.get("rows", [])

            if not rows:
                # Create a single document indicating no results
                doc = Document(
                    page_content="No results found for the graph database query.",
                    metadata={
                        "source": "kuzu_graph_db",
                        "source_type": "graph",
                        "cypher_query": cypher_query,
                        "row_count": 0,
                        "result_type": "empty"
                    }
                )
                documents.append(doc)
                return documents

            # Create one document per row (for small result sets)
            # Or aggregate into fewer documents (for large result sets)
            if len(rows) <= 20:
                # Small result set: one document per row
                for idx, row in enumerate(rows):
                    # Format row as key-value pairs
                    content_parts = []
                    for col_name, value in zip(columns, row):
                        content_parts.append(f"{col_name}: {value}")

                    page_content = "\n".join(content_parts)

                    doc = Document(
                        page_content=page_content,
                        metadata={
                            "source": "kuzu_graph_db",
                            "source_type": "graph",
                            "cypher_query": cypher_query,
                            "row_index": idx,
                            "row_count": len(rows),
                            "result_type": "row"
                        }
                    )
                    documents.append(doc)
            else:
                # Large result set: aggregate into summary document
                summary_parts = [f"Graph database query returned {len(rows)} results:"]

                # Include first 10 rows
                for idx, row in enumerate(rows[:10]):
                    row_str = ", ".join([f"{col}: {val}" for col, val in zip(columns, row)])
                    summary_parts.append(f"{idx + 1}. {row_str}")

                if len(rows) > 10:
                    summary_parts.append(f"... and {len(rows) - 10} more rows")

                page_content = "\n".join(summary_parts)

                doc = Document(
                    page_content=page_content,
                    metadata={
                        "source": "kuzu_graph_db",
                        "source_type": "graph",
                        "cypher_query": cypher_query,
                        "row_count": len(rows),
                        "result_type": "aggregated_summary"
                    }
                )
                documents.append(doc)

        except Exception as e:
            log_assistant.error(f"❌ Failed to format results as documents: {e}")
            # Return a fallback error document
            doc = Document(
                page_content=f"Error formatting graph database results: {str(e)}",
                metadata={
                    "source": "kuzu_graph_db",
                    "source_type": "graph",
                    "cypher_query": cypher_query,
                    "error": str(e)
                }
            )
            documents.append(doc)

        return documents

    def query(self, user_query: str) -> Dict[str, Any]:
        """
        End-to-end: generate, verify, and execute Cypher query.

        This is the main entry point for the assistant.

        Args:
            user_query: Natural language question from user

        Returns:
            Dict with keys:
                - success: bool
                - cypher_query: str (generated query)
                - verification_result: dict
                - documents: List[Document]
                - row_count: int
                - error: str (if failed)
                - reasoning: str
                - confidence: float
        """
        t_start = time.time()
        log_assistant.info("=" * 80)
        log_assistant.info(">>> TEXT-TO-CYPHER QUERY START")
        log_assistant.info(f"User Query: {user_query}")

        try:
            # Step 1: Generate Cypher
            generation_result = self.generate_cypher(user_query)
            cypher_query = generation_result.get("cypher")

            if not cypher_query:
                log_assistant.warning("⚠️ No Cypher query generated")
                t_elapsed = time.time() - t_start
                return {
                    "success": False,
                    "cypher_query": None,
                    "verification_result": None,
                    "documents": [],
                    "row_count": 0,
                    "error": "Failed to generate Cypher query",
                    "reasoning": generation_result.get("reasoning", "Unknown"),
                    "confidence": 0.0,
                    "latency_ms": t_elapsed * 1000,
                    "requires_clarification": generation_result.get("requires_clarification", False),
                    "clarification_question": generation_result.get("clarification_question")
                }

            # DEBUG MODE: Log generated Cypher
            if DEBUG_MODE:
                log_assistant.info("=" * 80)
                log_assistant.info("🔍 GENERATED CYPHER QUERY:")
                log_assistant.info(cypher_query)
                log_assistant.info(f"💭 Reasoning: {generation_result.get('reasoning', 'N/A')}")
                log_assistant.info(f"📊 Confidence: {generation_result.get('confidence', 0.0)}")
                log_assistant.info("=" * 80)

            # Step 2: Verify Cypher (agent-based)
            verification_result = self.verify_cypher(cypher_query)

            if not verification_result.get("approved", False):
                log_assistant.warning(f"❌ Cypher verification failed: {verification_result.get('issues', [])}")

                # Try corrected query if available
                corrected_query = verification_result.get("corrected_query")
                if corrected_query:
                    log_assistant.info("🔧 Using corrected query from verifier...")
                    cypher_query = corrected_query

                    # Re-verify the corrected query
                    verification_result = self.verify_cypher(cypher_query)
                    if not verification_result.get("approved", False):
                        log_assistant.error("❌ Corrected query still failed verification")
                        t_elapsed = time.time() - t_start
                        return {
                            "success": False,
                            "cypher_query": cypher_query,
                            "verification_result": verification_result,
                            "documents": [],
                            "row_count": 0,
                            "error": "Query verification failed after correction attempt",
                            "reasoning": generation_result.get("reasoning", ""),
                            "confidence": generation_result.get("confidence", 0.0),
                            "latency_ms": t_elapsed * 1000
                        }
                else:
                    # No corrected query available, fail gracefully
                    t_elapsed = time.time() - t_start
                    return {
                        "success": False,
                        "cypher_query": cypher_query,
                        "verification_result": verification_result,
                        "documents": [],
                        "row_count": 0,
                        "error": "Query verification failed, no correction available",
                        "reasoning": generation_result.get("reasoning", ""),
                        "confidence": generation_result.get("confidence", 0.0),
                        "latency_ms": t_elapsed * 1000
                    }

            log_assistant.info("✅ Cypher query approved by verification agent")

            # Step 3: Execute if approved
            execution_result = self.execute_cypher(cypher_query)

            if not execution_result.get("success", False):
                log_assistant.error(f"❌ Cypher execution failed: {execution_result.get('error')}")
                t_elapsed = time.time() - t_start
                return {
                    "success": False,
                    "cypher_query": cypher_query,
                    "verification_result": verification_result,
                    "documents": [],
                    "row_count": 0,
                    "error": f"Query execution failed: {execution_result.get('error')}",
                    "reasoning": generation_result.get("reasoning", ""),
                    "confidence": generation_result.get("confidence", 0.0),
                    "latency_ms": t_elapsed * 1000
                }

            # Success! Return formatted results
            documents = execution_result.get("documents", [])
            row_count = execution_result.get("row_count", 0)

            t_elapsed = time.time() - t_start
            log_assistant.info(f"✅ Query completed successfully: {row_count} rows, {len(documents)} documents")
            log_assistant.info(f"<<< TEXT-TO-CYPHER QUERY DONE in {t_elapsed:.2f}s")
            log_assistant.info("=" * 80)

            return {
                "success": True,
                "cypher_query": cypher_query,
                "verification_result": verification_result,
                "documents": documents,
                "row_count": row_count,
                "reasoning": generation_result.get("reasoning", ""),
                "confidence": generation_result.get("confidence", 0.0),
                "latency_ms": t_elapsed * 1000
            }

        except Exception as e:
            t_elapsed = time.time() - t_start
            log_assistant.error(f"❌ Text-to-Cypher query failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "cypher_query": None,
                "verification_result": None,
                "documents": [],
                "row_count": 0,
                "error": str(e),
                "reasoning": "",
                "confidence": 0.0,
                "latency_ms": t_elapsed * 1000
            }


# =====================================================================
# CONVENIENCE FUNCTION
# =====================================================================

def query_graph_with_natural_language(user_query: str) -> Dict[str, Any]:
    """
    Convenience function to query the graph database with natural language.

    Args:
        user_query: Natural language question from user

    Returns:
        Query result dict from TextToCypherAssistant.query()
    """
    assistant = TextToCypherAssistant()
    return assistant.query(user_query)
