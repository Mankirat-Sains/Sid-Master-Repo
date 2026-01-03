"""
Image Processing Nodes
Handle image embedding generation and similarity search
"""
import time
from typing import Optional, Dict, Any
from models.rag_state import RAGState
from config.logging_config import log_query, log_vlm
from config.settings import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client


def generate_vit_h14_embedding(image_base64: str):
    """Generate Vit-H14 embedding for an image"""
    from transformers import CLIPProcessor, CLIPModel
    import torch
    import base64
    from io import BytesIO
    from PIL import Image
    
    # Load model (cache on first call)
    if not hasattr(generate_vit_h14_embedding, '_model'):
        log_vlm.info("🖼️ Loading CLIP model for image embeddings...")
        generate_vit_h14_embedding._model = CLIPModel.from_pretrained("laion/CLIP-ViT-H-14-laion2B-s32B-b79K")
        generate_vit_h14_embedding._processor = CLIPProcessor.from_pretrained("laion/CLIP-ViT-H-14-laion2B-s32B-b79K")
        log_vlm.info("🖼️ CLIP model loaded")
    
    model = generate_vit_h14_embedding._model
    processor = generate_vit_h14_embedding._processor
    
    # Decode base64 image
    image_data = base64.b64decode(image_base64)
    image = Image.open(BytesIO(image_data))
    
    # Process and generate embedding
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        image_features = model.get_image_features(**inputs)
        embedding = image_features[0].numpy().tolist()
    
    return embedding


def node_generate_image_embeddings(state: RAGState) -> dict:
    """Generate Vit-H14 embeddings for uploaded images"""
    t_start = time.time()
    log_query.info(">>> GENERATE IMAGE EMBEDDINGS START")
    
    if not state.images_base64 or not state.use_image_similarity:
        log_query.info("⏭️  Skipping image embedding generation - no images or similarity disabled")
        return {}
    
    try:
        embeddings = []
        for i, image_base64 in enumerate(state.images_base64):
            try:
                embedding = generate_vit_h14_embedding(image_base64)
                embeddings.append(embedding)
                log_vlm.info(f"🖼️ Generated embedding {i+1}/{len(state.images_base64)}: {len(embedding)} dimensions")
            except Exception as e:
                log_vlm.error(f"🖼️ Failed to generate embedding for image {i+1}: {e}")
                continue
        
        if not embeddings:
            log_vlm.warning("🖼️ No embeddings generated, falling back to text-only search")
            return {"use_image_similarity": False}
        
        t_elapsed = time.time() - t_start
        log_vlm.info(f"<<< GENERATE IMAGE EMBEDDINGS DONE in {t_elapsed:.2f}s")
        
        return {"image_embeddings": embeddings}
        
    except Exception as e:
        log_vlm.error(f"🖼️ Image embedding generation failed: {e}")
        return {"use_image_similarity": False}


def describe_image_for_search(image_base64: str, user_question: str = "") -> str:
    """
    Use VLM to convert an image into a searchable text description.
    Works for any type of image - drawings, code documents, photos, etc.
    """
    from openai import OpenAI
    from config.settings import OPENAI_API_KEY
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Build context-aware prompt with maximum detail extraction
    if user_question:
        prompt = f"""You are an expert technical document analyzer. Examine this image exhaustively and provide a comprehensive description.

The user is asking: "{user_question}"

Provide an extremely detailed description covering ALL of the following:

**1. DOCUMENT IDENTIFICATION:**
- What type of document is this? (structural drawing, architectural detail, building code section, calculation sheet, specification, photo, sketch, table, diagram, etc.)
- Any title, heading, or document name visible
- Project number, drawing number, revision number, date
- Company name, engineer/architect stamps, or signatures

**2. ALL VISIBLE TEXT - Transcribe everything you can read:**
- Headers, titles, labels
- Notes, annotations, callouts
- Dimensions, measurements, scales
- Specifications, codes, standards referenced
- Any text in tables, lists, or bullet points

**3. VISUAL ELEMENTS:**
- Drawings: What is shown? (plans, sections, elevations, details, diagrams)
- Symbols, annotations, callouts, reference markers
- Lines, shapes, patterns, hatching
- Colors (if relevant)
- Photos: What objects, structures, or scenes are visible?

**4. TECHNICAL CONTENT:**
- Structural elements (beams, columns, walls, foundations, etc.)
- Materials mentioned or shown
- Construction methods or details
- Code references or standards
- Calculations or formulas visible
- Any technical specifications

**5. CONTEXT & RELATIONSHIPS:**
- How elements relate to each other
- Spatial relationships
- Sequence or process if shown
- Any relationships to the user's question

Format your response as a single, comprehensive paragraph that would be perfect for semantic search. Include ALL relevant keywords and technical terms."""
    else:
        prompt = """You are an expert technical document analyzer. Examine this image exhaustively and provide a comprehensive description.

Provide an extremely detailed description covering:
- Document type, titles, project numbers, dates
- ALL visible text (transcribe everything)
- Visual elements (drawings, symbols, annotations)
- Technical content (structural elements, materials, codes, specifications)
- Context and relationships

Format as a single, comprehensive paragraph perfect for semantic search. Include ALL relevant keywords and technical terms."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000
        )
        
        description = response.choices[0].message.content.strip()
        log_vlm.info(f"🖼️ VLM Description generated: {len(description)} chars")
        return description
        
    except Exception as e:
        log_vlm.error(f"🖼️ VLM description failed: {e}")
        return f"Image description unavailable: {str(e)}"


def classify_image_query_intent(user_query: str, image_base64: Optional[str] = None) -> Dict[str, Any]:
    """
    Classify user intent to determine if image similarity search is needed.
    
    TEMPORARY: Always does image similarity search when image is present.
    """
    from typing import Optional, Dict, Any
    
    query_lower = user_query.lower().strip()
    
    # TEMPORARY: If image is present, ALWAYS do image similarity search
    if image_base64:
        log_vlm.info(f"🖼️ IMAGE INTENT CLASSIFICATION: Image present - FORCING similarity search (temporary mode)")
        return {
            "intent": "image_similarity",
            "use_image_similarity": True,
            "confidence": 1.0
        }
    
    # Keywords that suggest image similarity search
    similarity_keywords = [
        "similar", "simillar", "like this", "same type", "look like", "match", 
        "find similar", "show similar", "other images", "other drawings",
        "same drawing", "similar screenshot", "find images like",
        "find me similar", "show me similar", "get similar", "find similar images",
        "similar images", "similar drawings", "similar screenshots",
    ]
    
    has_keyword = any(kw in query_lower for kw in similarity_keywords)
    
    if has_keyword:
        return {
            "intent": "image_similarity",
            "use_image_similarity": True,
            "confidence": 0.8
        }
    
    return {
        "intent": "text_only",
        "use_image_similarity": False,
        "confidence": 0.5
    }


def node_image_similarity_search(state: RAGState) -> dict:
    """Search for similar images using vector similarity"""
    t_start = time.time()
    log_vlm.info(">>> IMAGE SIMILARITY SEARCH START")
    
    if not state.image_embeddings or not state.use_image_similarity:
        log_vlm.info("⏭️  Skipping image similarity search - no embeddings available")
        return {"image_similarity_results": []}
    
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            log_vlm.warning("🖼️ Supabase not configured, skipping image similarity search")
            return {"image_similarity_results": []}
        
        _supa = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        query_embedding = state.image_embeddings[0]
        match_count = 10
        
        log_vlm.info(f"🖼️ Searching for similar images with match_count={match_count}")
        
        try:
            result = _supa.rpc("match_image_embeddings", {
                'query_embedding': query_embedding,
                'match_count': match_count
            }).execute()
            
            similar_images = result.data or []
            log_vlm.info(f"🖼️ Found {len(similar_images)} similar images")
            
            project_keys = []
            for img in similar_images:
                project_key = img.get("project_key")
                if project_key and project_key not in project_keys:
                    project_keys.append(project_key)
            
            log_vlm.info(f"🖼️ Images from {len(project_keys)} projects: {project_keys[:5]}")
            
            t_elapsed = time.time() - t_start
            log_vlm.info(f"<<< IMAGE SIMILARITY SEARCH DONE in {t_elapsed:.2f}s")
            
            return {
                "image_similarity_results": similar_images,
                "selected_projects": list(set(project_keys + state.selected_projects)) if project_keys else state.selected_projects
            }
            
        except Exception as rpc_error:
            log_vlm.error(f"🖼️ Supabase RPC function failed: {rpc_error}")
            return {"image_similarity_results": []}
            
    except Exception as e:
        log_vlm.error(f"🖼️ Image similarity search failed: {e}")
        return {"image_similarity_results": []}

