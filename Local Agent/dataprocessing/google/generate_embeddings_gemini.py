#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Text Embeddings using Gemini Embedding Model (Vertex AI)

This script generates embeddings for text_verbatim and summary fields using
Google's gemini-embedding-001 model via Vertex AI, capped at 1536 dimensions
for Supabase compatibility.

All authentication uses service account credentials from ocr-key.json.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from google.oauth2 import service_account
import vertexai
from vertexai.language_models import TextEmbeddingModel

# ================= CONFIGURATION =================
# Google Service Account Key Path (for Vertex AI)
OCR_KEY_PATH = r"C:\Users\shine\Testing-2025-01-07\Local Agent\dataprocessing\google\ocr-key.json"

# Input/Output directories
STRUCTURED_JSON_DIR = r"C:\Users\shine\Testing-2025-01-07\Local Agent\dataprocessing\google\structured_json"

# Vertex AI Configuration
VERTEX_AI_LOCATION = "us-central1"  # Change if your Vertex AI is in a different region
EMBEDDING_MODEL = "text-embedding-004"  # Try text-embedding-004 first, fallback to textembedding-gecko@003

# Embedding Configuration
MAX_EMBEDDING_DIM = 1536  # Cap dimensions to avoid Supabase issues (MUST be exactly 1536)

# Rate Limiting Configuration
DELAY_BETWEEN_BATCHES = 1.0  # Seconds to wait between batches
BATCH_SIZE = 100  # Process embeddings in batches
# =================================================

# Global variables
_project_id = None
_credentials = None
_embedding_model = None


def setup_vertex_ai():
    """Initialize Vertex AI with service account credentials"""
    global _project_id, _credentials, _embedding_model
    
    if _embedding_model is not None:
        return _embedding_model
    
    if not os.path.exists(OCR_KEY_PATH):
        raise FileNotFoundError(f"OCR Key file not found at: {OCR_KEY_PATH}")
    
    # Load project_id and credentials
    with open(OCR_KEY_PATH, 'r', encoding='utf-8') as f:
        key_data = json.load(f)
        _project_id = key_data.get('project_id')
        if not _project_id:
            raise ValueError("project_id not found in ocr-key.json. Required for Vertex AI.")
    
    _credentials = service_account.Credentials.from_service_account_file(OCR_KEY_PATH)
    
    # Initialize Vertex AI
    vertexai.init(project=_project_id, location=VERTEX_AI_LOCATION, credentials=_credentials)
    
    # Load embedding model
    # Try multiple model names as Vertex AI model names may vary
    model_names = [
        "text-embedding-004",
        "textembedding-gecko@003",
        "textembedding-gecko@002",
        "text-embedding-001"
    ]
    
    last_error = None
    for model_name in model_names:
        try:
            _embedding_model = TextEmbeddingModel.from_pretrained(model_name)
            print(f"✅ Vertex AI embedding model initialized: {model_name} (Location: {VERTEX_AI_LOCATION})")
            break
        except Exception as e:
            last_error = e
            continue
    
    if _embedding_model is None:
        raise RuntimeError(f"Failed to initialize embedding model. Tried: {', '.join(model_names)}. Last error: {last_error}")
    
    return _embedding_model


def generate_embedding(text: str) -> Optional[List[float]]:
    """
    Generate embedding for text using Gemini embedding model via Vertex AI
    
    Args:
        text: Text to embed
        
    Returns:
        Embedding vector (capped at MAX_EMBEDDING_DIM) or None if error
    """
    if not text or not text.strip():
        return None
    
    try:
        model = setup_vertex_ai()
        
        # Generate embedding
        embeddings = model.get_embeddings([text.strip()])
        
        if not embeddings or len(embeddings) == 0:
            return None
        
        embedding = embeddings[0].values
        
        # Cap/truncate to MAX_EMBEDDING_DIM dimensions
        if len(embedding) > MAX_EMBEDDING_DIM:
            embedding = embedding[:MAX_EMBEDDING_DIM]
        elif len(embedding) < MAX_EMBEDDING_DIM:
            # Pad with zeros if shorter (shouldn't happen, but be safe)
            padding = [0.0] * (MAX_EMBEDDING_DIM - len(embedding))
            embedding = embedding + padding
        
        # Verify dimension
        if len(embedding) != MAX_EMBEDDING_DIM:
            raise ValueError(f"Embedding dimension mismatch: expected {MAX_EMBEDDING_DIM}, got {len(embedding)}")
        
        return embedding
    
    except Exception as e:
        print(f"      ⚠️ Error generating embedding: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_embeddings_batch(texts: List[str]) -> List[Optional[List[float]]]:
    """
    Generate embeddings for a batch of texts
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List of embedding vectors (capped at MAX_EMBEDDING_DIM) or None for errors
    """
    if not texts:
        return []
    
    try:
        model = setup_vertex_ai()
        
        # Filter out empty texts
        non_empty_texts = [t.strip() for t in texts if t and t.strip()]
        if not non_empty_texts:
            return [None] * len(texts)
        
        # Generate embeddings
        embeddings = model.get_embeddings(non_empty_texts)
        
        results = []
        text_idx = 0
        
        for i, original_text in enumerate(texts):
            if not original_text or not original_text.strip():
                results.append(None)
            else:
                if text_idx < len(embeddings):
                    embedding = embeddings[text_idx].values
                    
                    # Cap/truncate to MAX_EMBEDDING_DIM dimensions
                    if len(embedding) > MAX_EMBEDDING_DIM:
                        embedding = embedding[:MAX_EMBEDDING_DIM]
                    elif len(embedding) < MAX_EMBEDDING_DIM:
                        # Pad with zeros if shorter
                        padding = [0.0] * (MAX_EMBEDDING_DIM - len(embedding))
                        embedding = embedding + padding
                    
                    # Verify dimension
                    if len(embedding) != MAX_EMBEDDING_DIM:
                        print(f"      ⚠️ Embedding dimension mismatch: expected {MAX_EMBEDDING_DIM}, got {len(embedding)}")
                        results.append(None)
                    else:
                        results.append(embedding)
                    text_idx += 1
                else:
                    results.append(None)
        
        return results
    
    except Exception as e:
        print(f"      ⚠️ Error generating batch embeddings: {e}")
        import traceback
        traceback.print_exc()
        return [None] * len(texts)


def process_project(project_id: str, skip_existing: bool = True):
    """Process a single project and add embeddings to JSON file"""
    json_file = Path(STRUCTURED_JSON_DIR) / project_id / f"structured_{project_id}.json"
    
    if not json_file.exists():
        print(f"  ❌ JSON file not found: {json_file}")
        return -1
    
    print(f"\n  Processing: {project_id}")
    print(f"    File: {json_file}")
    
    # Load JSON
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"    ❌ Error loading JSON: {e}")
        return -1
    
    images = data.get("images", [])
    if not images:
        print(f"    ⚠️ No images found in JSON")
        return 0
    
    print(f"    📸 Found {len(images)} images")
    
    # Check how many already have embeddings
    already_embedded = 0
    needs_embedding = []
    
    for i, img in enumerate(images):
        has_verbatim_emb = "text_verbatim_embedding" in img and img["text_verbatim_embedding"] is not None
        has_summary_emb = "summary_embedding" in img and img["summary_embedding"] is not None
        
        if skip_existing and has_verbatim_emb and has_summary_emb:
            already_embedded += 1
        else:
            needs_embedding.append((i, img))
    
    if skip_existing:
        print(f"    📊 Already embedded: {already_embedded}/{len(images)}")
        print(f"    ⚙️  Need embedding: {len(needs_embedding)}/{len(images)}")
    else:
        print(f"    ⚙️  Processing all: {len(images)} images")
        needs_embedding = [(i, img) for i, img in enumerate(images)]
    
    if not needs_embedding:
        print(f"    ✅ All images already have embeddings!")
        return 0
    
    # Process in batches
    setup_vertex_ai()  # Initialize before processing
    
    embedded_count = 0
    error_count = 0
    
    for batch_start in range(0, len(needs_embedding), BATCH_SIZE):
        batch = needs_embedding[batch_start:batch_start + BATCH_SIZE]
        batch_num = batch_start // BATCH_SIZE + 1
        total_batches = (len(needs_embedding) + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"    ⚙️  Processing batch {batch_num}/{total_batches} ({len(batch)} images)...")
        
        # Collect texts for batch
        verbatim_texts = []
        summary_texts = []
        batch_indices = []
        
        for idx, img in batch:
            verbatim = img.get("text_verbatim", "") or ""
            summary = img.get("summary", "") or ""
            
            verbatim_texts.append(verbatim)
            summary_texts.append(summary)
            batch_indices.append(idx)
        
        # Generate embeddings for verbatim texts
        print(f"      🔍 Generating verbatim embeddings...")
        verbatim_embeddings = generate_embeddings_batch(verbatim_texts)
        
        # Generate embeddings for summary texts
        print(f"      🔍 Generating summary embeddings...")
        time.sleep(DELAY_BETWEEN_BATCHES)  # Rate limiting
        summary_embeddings = generate_embeddings_batch(summary_texts)
        
        # Update images with embeddings
        for i, (idx, img) in enumerate(batch):
            verbatim_emb = verbatim_embeddings[i] if i < len(verbatim_embeddings) else None
            summary_emb = summary_embeddings[i] if i < len(summary_embeddings) else None
            
            # Only update if embedding was generated or if not skipping existing
            if verbatim_emb is not None:
                images[idx]["text_verbatim_embedding"] = verbatim_emb
                embedded_count += 1
            elif not skip_existing:
                images[idx]["text_verbatim_embedding"] = None
                error_count += 1
            
            if summary_emb is not None:
                images[idx]["summary_embedding"] = summary_emb
            elif not skip_existing:
                images[idx]["summary_embedding"] = None
        
        # Save incrementally after each batch
        data["images"] = images
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"      ✅ Batch {batch_num} saved")
        
        # Rate limiting delay
        if batch_start + BATCH_SIZE < len(needs_embedding):
            time.sleep(DELAY_BETWEEN_BATCHES)
    
    print(f"    ✅ Complete! Embedded: {embedded_count}, Errors: {error_count}")
    return embedded_count


def main():
    """Main entry point"""
    print("="*80)
    print("Generate Text Embeddings using Gemini (Vertex AI)")
    print("="*80)
    print(f"Structured JSON directory: {STRUCTURED_JSON_DIR}")
    print(f"Embedding model: {EMBEDDING_MODEL}")
    print(f"Max embedding dimensions: {MAX_EMBEDDING_DIM}")
    print()
    
    # Find all projects
    structured_path = Path(STRUCTURED_JSON_DIR)
    if not structured_path.exists():
        print(f"❌ Structured JSON directory not found: {structured_path}")
        return
    
    projects = []
    for project_dir in structured_path.iterdir():
        if project_dir.is_dir():
            json_file = project_dir / f"structured_{project_dir.name}.json"
            if json_file.exists():
                projects.append(project_dir.name)
    
    if not projects:
        print(f"❌ No projects found in {structured_path}")
        return
    
    projects = sorted(projects)
    print(f"📁 Found {len(projects)} project(s): {', '.join(projects)}")
    print()
    
    # Check if project ID provided as argument
    import sys
    if len(sys.argv) > 1:
        project_id = sys.argv[1]
        if project_id not in projects:
            print(f"❌ Project {project_id} not found!")
            return
        projects = [project_id]
    
    # Process each project
    total_embedded = 0
    successful = 0
    failed = 0
    
    for project_id in projects:
        try:
            count = process_project(project_id, skip_existing=True)
            if count >= 0:
                successful += 1
                total_embedded += count
            else:
                failed += 1
        except Exception as e:
            print(f"  ❌ Error processing {project_id}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*80)
    print("✨ Embedding Generation Complete!")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    print(f"   Total embeddings generated: {total_embedded}")
    print("="*80)


if __name__ == "__main__":
    main()

