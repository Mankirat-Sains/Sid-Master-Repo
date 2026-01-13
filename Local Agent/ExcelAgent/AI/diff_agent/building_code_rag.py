#!/usr/bin/env python3
"""
Building Code RAG System for Excel Agent

This creates a semantic search system over building codes to enhance
spreadsheet understanding. The system can query:
- CSA A23.3 (Concrete Design)
- CSA S16 (Steel Design)
- CSA O86 (Wood/Timber Design)
- OBC (Ontario Building Code)

Based on SheetMind's approach of using domain knowledge to understand spreadsheets.
"""

import pickle
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ============================================================================
# Building Code RAG System
# ============================================================================

class BuildingCodeRAG:
    """
    RAG system for querying building codes to enhance spreadsheet understanding
    """
    
    def __init__(self):
        # Path: Excel_Agent/ -> agents/ -> Backend/ -> Building codes/
        self.base_path = Path(__file__).parent.parent.parent / "Building codes"
        self.codes = {}
        self.loaded = False
        
        print("🔧 Initializing Building Code RAG System...")
        print(f"   📂 Looking for codes in: {self.base_path.resolve()}")
        print(f"   📂 Path exists: {self.base_path.exists()}")
        self._load_all_codes()
    
    def _load_code_embeddings(self, code_name: str, folder_path: Path) -> Dict[str, Any]:
        """Load embeddings and metadata for a specific building code"""
        try:
            # Find embedding and metadata files (look for simple_embeddings pattern)
            npy_files = list(folder_path.glob("*.npy"))
            pkl_files = list(folder_path.glob("*.pkl"))
            
            if not npy_files or not pkl_files:
                print(f"   ⚠️ {code_name}: No embeddings found in {folder_path}")
                print(f"      Files: {list(folder_path.glob('*'))}")
                return None
            
            print(f"   🔍 {code_name}: Found {len(npy_files)} .npy and {len(pkl_files)} .pkl files")
            
            # Use the first embeddings file found
            embeddings = np.load(npy_files[0])
            
            with open(pkl_files[0], 'rb') as f:
                metadata = pickle.load(f)
            
            print(f"   ✅ {code_name}: Loaded {len(embeddings)} chunks from {npy_files[0].name}")
            
            return {
                "embeddings": embeddings,
                "metadata": metadata,
                "code_name": code_name,
                "folder": str(folder_path)
            }
            
        except Exception as e:
            print(f"   ❌ {code_name}: Failed to load - {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _load_all_codes(self):
        """Load all available building codes"""
        
        code_folders = {
            "CSA_A23.3_Concrete": self.base_path / "concrete",
            "CSA_S16_Steel": self.base_path / "steel",
            "CSA_O86_Timber": self.base_path / "timber",
            "OBC": self.base_path / "obc"
        }
        
        for code_name, folder in code_folders.items():
            if folder.exists():
                code_data = self._load_code_embeddings(code_name, folder)
                if code_data:
                    self.codes[code_name] = code_data
        
        if self.codes:
            self.loaded = True
            print(f"✅ Building Code RAG ready with {len(self.codes)} codes\n")
        else:
            print("⚠️ No building codes loaded\n")
    
    def _embed_query(self, query: str) -> np.ndarray:
        """Create embedding for a query"""
        try:
            response = client.embeddings.create(
                model="text-embedding-3-large",  # Match the building code embeddings
                input=query
            )
            return np.array(response.data[0].embedding)
        except Exception as e:
            print(f"❌ Embedding failed: {e}")
            return None
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        return dot_product / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0
    
    def query_code(self, code_name: str, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Query a specific building code
        
        Args:
            code_name: Which code to query (e.g., 'CSA_S16_Steel')
            query: Natural language query
            top_k: Number of top results to return
            
        Returns:
            List of relevant code chunks with metadata
        """
        if not self.loaded:
            return []
        
        if code_name not in self.codes:
            print(f"⚠️ Code '{code_name}' not available")
            return []
        
        code_data = self.codes[code_name]
        
        # Embed query
        query_embedding = self._embed_query(query)
        if query_embedding is None:
            return []
        
        # Calculate similarities
        embeddings = code_data["embeddings"]
        similarities = []
        
        for idx, chunk_embedding in enumerate(embeddings):
            sim = self._cosine_similarity(query_embedding, chunk_embedding)
            similarities.append((idx, sim))
        
        # Get top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_results = similarities[:top_k]
        
        # Format results
        results = []
        metadata = code_data["metadata"]
        
        for idx, score in top_results:
            if idx < len(metadata):
                result = {
                    "code": code_name,
                    "score": float(score),
                    "text": metadata[idx].get("text", ""),
                    "page": metadata[idx].get("page", "N/A"),
                    "chunk_id": idx
                }
                results.append(result)
        
        return results
    
    def query_all_codes(self, query: str, top_k_per_code: int = 2) -> Dict[str, List[Dict[str, Any]]]:
        """
        Query ALL building codes and return results from each
        
        Useful when you don't know which code is relevant
        """
        if not self.loaded:
            return {}
        
        results = {}
        
        for code_name in self.codes.keys():
            code_results = self.query_code(code_name, query, top_k=top_k_per_code)
            if code_results:
                results[code_name] = code_results
        
        return results
    
    def understand_parameter(self, parameter_name: str, context: str = "") -> Dict[str, Any]:
        """
        Understand what a parameter means by querying building codes
        
        Args:
            parameter_name: Parameter to understand (e.g., "f'c", "M_r", "K_D")
            context: Additional context (e.g., "concrete beam design")
            
        Returns:
            Dict with code references, description, typical ranges, etc.
        """
        query = f"What is {parameter_name} in structural engineering? {context}"
        
        # Query all codes
        all_results = self.query_all_codes(query, top_k_per_code=2)
        
        if not all_results:
            return {
                "parameter": parameter_name,
                "found": False,
                "description": "No code references found"
            }
        
        # Find most relevant code
        best_code = None
        best_score = 0.0
        
        for code_name, results in all_results.items():
            if results and results[0]["score"] > best_score:
                best_score = results[0]["score"]
                best_code = code_name
        
        # Use AI to synthesize understanding
        if best_code and all_results[best_code]:
            code_context = "\n\n".join([
                f"[{r['code']} - Page {r['page']}]\n{r['text'][:500]}"
                for r in all_results[best_code]
            ])
            
            return self._synthesize_parameter_understanding(
                parameter_name, 
                best_code, 
                code_context
            )
        
        return {
            "parameter": parameter_name,
            "found": False,
            "description": "Parameter found in codes but understanding failed"
        }
    
    def _synthesize_parameter_understanding(self, param_name: str, 
                                           code_name: str, 
                                           code_context: str) -> Dict[str, Any]:
        """Use AI to synthesize parameter understanding from code context"""
        
        prompt = f"""You are a structural engineering code expert.

Parameter: {param_name}
Most Relevant Code: {code_name}

Code Context:
{code_context}

Analyze this parameter and provide:
1. What it represents in engineering
2. Which code section defines it
3. Typical values or ranges
4. How it's used in calculations
5. Any code requirements or limits

Return as JSON:
{{
  "parameter": "{param_name}",
  "code": "code name",
  "section": "section number",
  "description": "what it means",
  "typical_range": [min, max],
  "unit": "unit of measurement",
  "formula": "if applicable",
  "code_requirement": "any mandatory requirements",
  "usage": "how it's used in design"
}}
"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert in structural engineering codes. Provide detailed, accurate analysis in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.2
            )
            
            raw_content = response.choices[0].message.content
            
            # Strip markdown
            if raw_content.startswith("```json"):
                raw_content = raw_content[7:]
            if raw_content.startswith("```"):
                raw_content = raw_content[3:]
            if raw_content.endswith("```"):
                raw_content = raw_content[:-3]
            raw_content = raw_content.strip()
            
            result = json.loads(raw_content)
            result["found"] = True
            return result
            
        except Exception as e:
            print(f"⚠️ AI synthesis failed: {e}")
            return {
                "parameter": param_name,
                "code": code_name,
                "found": True,
                "description": f"Parameter found in {code_name}",
                "raw_context": code_context[:300]
            }
    
    def validate_calculation(self, calculation_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate if a calculation follows building code requirements
        
        Example:
            validate_calculation("beam_moment_resistance", {
                "M_r": 150, "M_f": 120, "material": "steel"
            })
        """
        query = f"Code requirements for {calculation_type} with parameters: {parameters}"
        
        all_results = self.query_all_codes(query, top_k_per_code=2)
        
        if not all_results:
            return {"valid": "unknown", "reason": "No code references found"}
        
        # Get relevant code sections
        code_context = []
        for code_name, results in all_results.items():
            for result in results[:1]:  # Top result per code
                code_context.append(f"[{result['code']}]: {result['text'][:300]}")
        
        # Use AI to validate
        return self._validate_with_ai(calculation_type, parameters, "\n\n".join(code_context))
    
    def _validate_with_ai(self, calc_type: str, params: Dict, code_context: str) -> Dict[str, Any]:
        """Use AI to validate calculation against codes"""
        
        prompt = f"""You are a structural engineering code compliance expert.

Calculation Type: {calc_type}
Parameters: {json.dumps(params, indent=2)}

Relevant Code Context:
{code_context}

Validate if this calculation meets code requirements. Return as JSON:
{{
  "valid": true/false,
  "code_reference": "applicable code section",
  "compliance_check": "what needs to be checked",
  "issues": ["any issues found"],
  "recommendations": ["suggestions for compliance"]
}}
"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert in building code compliance validation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.2
            )
            
            raw_content = response.choices[0].message.content
            
            # Strip markdown
            if raw_content.startswith("```json"):
                raw_content = raw_content[7:]
            if raw_content.startswith("```"):
                raw_content = raw_content[3:]
            if raw_content.endswith("```"):
                raw_content = raw_content[:-3]
            
            return json.loads(raw_content.strip())
            
        except Exception as e:
            return {"valid": "unknown", "error": str(e)}


# ============================================================================
# Singleton Instance
# ============================================================================

_code_rag_instance = None

def get_building_code_rag() -> BuildingCodeRAG:
    """Get or create singleton instance of Building Code RAG"""
    global _code_rag_instance
    if _code_rag_instance is None:
        _code_rag_instance = BuildingCodeRAG()
    return _code_rag_instance


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Building Code RAG System Test")
    print("=" * 60 + "\n")
    
    # Initialize
    rag = BuildingCodeRAG()
    
    if not rag.loaded:
        print("❌ No building codes loaded!")
        exit(1)
    
    # Test 1: Understand a concrete parameter
    print("\n" + "=" * 60)
    print("TEST 1: Understanding f'c (concrete strength)")
    print("=" * 60)
    
    fc_understanding = rag.understand_parameter("f'c", "concrete design")
    print(json.dumps(fc_understanding, indent=2))
    
    # Test 2: Understand a steel parameter
    print("\n" + "=" * 60)
    print("TEST 2: Understanding M_r (moment resistance)")
    print("=" * 60)
    
    mr_understanding = rag.understand_parameter("M_r", "steel beam design")
    print(json.dumps(mr_understanding, indent=2))
    
    # Test 3: Understand a wood parameter
    print("\n" + "=" * 60)
    print("TEST 3: Understanding K_D (load duration factor)")
    print("=" * 60)
    
    kd_understanding = rag.understand_parameter("K_D", "wood beam design")
    print(json.dumps(kd_understanding, indent=2))
    
    # Test 4: Query specific code
    print("\n" + "=" * 60)
    print("TEST 4: Query steel code for beam design")
    print("=" * 60)
    
    steel_results = rag.query_code("CSA_S16_Steel", "beam moment resistance calculation", top_k=2)
    for result in steel_results:
        print(f"\nScore: {result['score']:.3f}")
        print(f"Text: {result['text'][:200]}...")

