"""
Image Processing Nodes
Handle image description and text-based semantic search on image_descriptions table
"""
import time
from typing import Optional, Dict, Any, List
from models.db_retrieval_state import DBRetrievalState
from config.logging_config import log_query, log_vlm
from config.settings import SUPABASE_URL, SUPABASE_KEY
from config.llm_instances import emb  # Text embedding model (text-embedding-3-small)
from supabase import create_client


def describe_image_for_search(image_base64: str, user_question: str = "") -> str:
    """
    Use VLM to convert an image into a searchable text description.
    Works for any type of image - drawings, code documents, photos, etc.
    Uses a structured prompt similar to EXTRACTION_PROMPT for comprehensive analysis.
    """
    import time
    from openai import OpenAI
    from config.settings import OPENAI_API_KEY
    
    t_start = time.time()
    log_vlm.info("=" * 60)
    log_vlm.info("🖼️ VLM IMAGE DESCRIPTION - START")
    log_vlm.info(f"📋 User question: {user_question[:100] if user_question else 'None (general description)'}")
    log_vlm.info(f"📏 Image base64 length: {len(image_base64)} chars")
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Structured prompt based on EXTRACTION_PROMPT structure
    base_prompt = """You are a senior structural engineer analyzing technical drawing images.

Your task is to provide a comprehensive text description of this image for semantic search and database queries.

**STRUCTURAL DRAWING CONTEXT (HOW TO READ THE DRAWINGS):**
- Treat every image as part of a coordinated structural drawing set (plans, sections, elevations, details, schedules)
- **Key / Site / General Arrangement plans**: show the building in context (site, roads, existing structures) and overall footprint
- **Plans**: top‑down cuts at a level (foundation plan, ground floor plan, roof/framing plan). X/Y axes show length and width; use these views to understand overall geometry, grids, and layout of foundations, columns, beams, slabs, doors, and openings
- **Sections**: vertical cuts (X/Z or Y/Z). Use these to understand heights, levels, vertical relationships, wall/footing depths, and how roof/floor systems bear on supports
- **Details**: enlarged portions of plans or sections that clarify reinforcement, connections, member build‑ups, etc. A single typical detail (e.g., column C1, beam B1) often applies wherever that tag appears on the plans
- **Schedules / tables**: tabular data listing members, reinforcement, spacings, bar sizes, etc. Use these to decode tags and symbols in the plans/sections (e.g., beam schedule, rebar schedule)
- When interpreting ANY image, always reason like a structural engineer: identify load paths (roof → floors → beams/joists → columns/walls → foundations → soil), system types (steel, concrete, wood), and how typical details and schedules control repeated elements

**CRITICAL REQUIREMENTS:**
1. Extract ALL visible text VERBATIM (word-for-word, exactly as shown) and incorporate it into your description
2. Your description MUST incorporate ALL verbatim text values but explain their meaning and relationships
3. Example: If verbatim text contains "5'-0\"" and "15M @10\" o/c", describe it as: "This detail shows a retaining wall with a height of 5'-0\" (five feet zero inches) as indicated by the dimension line. The reinforcement consists of 15M rebar bars spaced at 10 inches on center, as specified in the notation '15M @10\" o/c'. The wall thickness is 8 inches with a 4-inch concrete foundation below."
4. The description should be rich and detailed for semantic search - explain HOW the text relates to the visual elements
5. Be precise with classifications, locations, and element types

**CLASSIFICATION GUIDELINES:**
- "Plan": Floor plans, site plans, roof plans (top-down views showing layout)
- "Elevation": Building elevations, exterior views (side views of building)
- "Section": Section cuts through the building (cut-away views)
- "Detail": Close-up details of specific connections or assemblies (zoomed-in views)
- "Notes": General notes, specifications, legends (text-heavy, no major linework)
- "Schedule": Tables, schedules (beam schedules, lintel schedules, rebar schedules, etc.)

**LOCATION & LEVEL GUIDELINES:**
- Always try to describe BOTH vertical level and horizontal position/orientation so the element can be tied into a global building model
- Use normalized vertical categories (e.g., "Foundation", "Basement", "Ground Floor", "Second Floor", "Roof"). This should come from plan titles, section notes, or titles like "FOUNDATION PLAN", "GROUND FLOOR PLAN", "ROOF FRAMING PLAN", "SECTION @ GRID 3", etc.
- Combine level + orientation + any zone information into a concise phrase (e.g., "Ground Floor – south bay at grid 7", "Roof – east end over manure storage area", "Foundation – F1 footings under east wall")
- For sections/elevations, describe primary orientation and cut direction (e.g., "Transverse section looking North", "Longitudinal section looking East", "North elevation", "West wall elevation")
- Extract grid lines or bay references (e.g., "Grid 1-5", "Grids A-C", "Between Grid 3 and Grid 7")
- Extract this information from view titles, key notes, grid bubbles, section titles, and nearby annotations

**ELEMENT CALLOUTS (FOUNDATION / WALL / BEAM / TRUSS / SLAB TAGS):**
- Extract tags that label specific elements or typical details, e.g., "F1", "F2", "F3" (footing types), "W1", "W2" (wall types), "B1", "B2" (beam marks), "T1", "T2" (truss types), "WE1" (wall elevation), etc.
- These are often shown in diamonds, squares, or other symbols adjacent to foundations, walls, beams, or trusses and are cross‑referenced to schedules or typical details

**TEXT VERBATIM:**
- Extract EVERY piece of text visible in the image
- Include: dimensions, notes, labels, schedules, material specifications, etc.
- **CRITICAL FOR PLAN VIEWS: Extract ALL dimension lines and their values, especially overall building dimensions that span from one exterior edge to the opposite exterior edge. Include dimension values like "256'-0\"", "295'-0\"", "295'-4\"", "137'-0\"", "124'-0\"", etc. - even if they appear to be partial dimensions, extract them all as they may be needed for synthesis.**
- If text is partially obscured, indicate with [unclear] or [partially visible]
- Preserve special characters, units, and formatting exactly as shown

**DESCRIPTION FORMAT (MOST IMPORTANT):**
- Must be rich and detailed for semantic search and embeddings
- MUST incorporate verbatim values from the text but explain their meaning
- MUST explain relationships between text and visual elements (e.g., "the dimension '12'-0\"' indicates the width of the room")
- MAXIMUM 500 WORDS - The description cannot exceed 500 words. It can be less if all information is contained, but it cannot be more than 500 words.
- Should read naturally for semantic search queries
- Structure: "This [classification] shows [what is visible]. [Specific verbatim values] indicate [what they mean]. [How text relates to linework]. [Additional context and relationships]."
- Before writing the final description, internally identify all distinct structural systems present in the image (e.g., truss bracing system, slab system, foundation system). The description MUST describe each system explicitly and explain how the extracted text applies to that system.

STRUCTURAL DRAWING INTERPRETATION RULES:

1. Identify the drawing type first (Plan, Section, Detail, Elevation).
2. Read ALL general notes before interpreting geometry.
3. Notes marked "TYP." apply unless explicitly overridden.
4. Dimensions govern over scale; drawings may be N.T.S.
5. Structural members are identified by function first, size second.
6. Fastener schedules and spacing notes are critical and must not be summarized away.
7. If multiple systems are present, identify and describe each system separately.
8. Assume industry-standard conventions unless explicitly contradicted by notes.
9. Always explain how text annotations relate to physical members shown in linework.

Provide a comprehensive, single-paragraph description that incorporates all of the above information. Focus on verbatim text extraction, element callouts, dimensions, and how all elements relate to each other."""
    
    if user_question:
        prompt = f"""{base_prompt}

The user is asking: "{user_question}"

Make sure your description addresses the user's question while still providing comprehensive detail."""
    else:
        prompt = base_prompt
    
    log_vlm.info(f"📝 Prompt length: {len(prompt)} chars")
    log_vlm.info("⏳ Calling OpenAI GPT-4o vision model...")
    
    try:
        api_start = time.time()
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
        api_elapsed = time.time() - api_start
        
        description = response.choices[0].message.content.strip()
        t_elapsed = time.time() - t_start
        
        # Log detailed information
        log_vlm.info(f"✅ VLM API call completed in {api_elapsed:.2f}s")
        log_vlm.info(f"📊 Description generated: {len(description)} characters, {len(description.split())} words")
        log_vlm.info(f"⏱️  Total processing time: {t_elapsed:.2f}s")
        
        # Log preview of description (first 300 chars)
        preview = description[:300] + "..." if len(description) > 300 else description
        log_vlm.info(f"📄 Description preview (first 300 chars):")
        log_vlm.info(f"   {preview}")
        
        log_vlm.info("🖼️ VLM IMAGE DESCRIPTION - COMPLETE")
        log_vlm.info("=" * 60)
        
        return description
        
    except Exception as e:
        t_elapsed = time.time() - t_start
        log_vlm.error(f"❌ VLM description failed after {t_elapsed:.2f}s: {e}")
        log_vlm.error(f"❌ Error type: {type(e).__name__}")
        import traceback
        log_vlm.error(f"❌ Traceback: {traceback.format_exc()}")
        log_vlm.info("=" * 60)
        return f"Image description unavailable: {str(e)}"


def should_output_images(user_query: str) -> bool:
    """
    Determine if images should be output/displayed in the response.
    This is separate from image similarity search - we may search for context
    but only output images when explicitly requested.
    """
    query_lower = user_query.lower().strip()
    
    # Keywords that explicitly request image output
    # These are more specific - user must explicitly ask for images to be shown
    output_keywords = [
        "output images", "output the images", "output image", "output the image",
        "show images", "show the images", "show image", "show the image",
        "display images", "display the images", "display image", "display the image",
        "render images", "render the images", "render image", "render the image",
        "output detail images", "output the detail images", "output detail image", "output the detail image",
        "show detail images", "show the detail images", "show detail image", "show the detail image",
        "display detail images", "display the detail images", "display detail image",
        "output similar images", "show similar images", "display similar images",
        "include images", "include the images", "include image",
        "with images", "with the images", "with image",
        "detail images", "the detail images", "detail image", "the detail image",
        "images like", "images similar", "similar images",
        "output detail", "show detail", "display detail",  # When combined with image context
        "output the detail", "show the detail", "display the detail",
        # Similar detail queries - when user asks for similar details, show the images
        "similar detail", "similar details", "simillar detail", "simillar details",
        "find similar", "find me similar", "get similar", "show similar",
        # Similar image queries (singular and with typos)
        "similar image", "simillar image", "simillar images",
    ]
    
    has_output_keyword = any(kw in query_lower for kw in output_keywords)
    
    log_vlm.info(f"🖼️ IMAGE OUTPUT CHECK: Query='{query_lower[:80]}...'")
    log_vlm.info(f"🖼️ IMAGE OUTPUT CHECK: Checking against {len(output_keywords)} keywords")
    
    if has_output_keyword:
        matched = [kw for kw in output_keywords if kw in query_lower]
        log_vlm.info(f"🖼️ IMAGE OUTPUT CHECK: ✅ MATCHED keywords: {matched}")
        log_vlm.info(f"🖼️ IMAGE OUTPUT CHECK: Will INCLUDE images in response")
        return True
    
    log_vlm.info(f"🖼️ IMAGE OUTPUT CHECK: ❌ NO keyword match - will EXCLUDE images from response")
    return False


def classify_image_query_intent(user_query: str, image_base64: Optional[str] = None) -> Dict[str, Any]:
    """
    Classify user intent to determine if image similarity search is needed.
    
    When image is present, always enable similarity search (using text semantic search).
    """
    query_lower = user_query.lower().strip()
    
    # If image is present, ALWAYS do image similarity search
    if image_base64:
        log_vlm.info(f"🖼️ IMAGE INTENT CLASSIFICATION: Image present - enabling text-based similarity search")
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
        "similar detail", "similar details", "output the detail", "output detail",
        "show detail", "show details", "find detail", "find details"
    ]
    
    has_keyword = any(kw in query_lower for kw in similarity_keywords)
    
    if has_keyword:
        log_vlm.info(f"🖼️ IMAGE INTENT CLASSIFICATION: Keyword match found - enabling similarity search")
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


def node_generate_image_description(state: DBRetrievalState) -> dict:
    """
    Generate text description of uploaded image using VLM.
    This description will be used for text-based semantic search.
    """
    t_start = time.time()
    log_query.info(">>> GENERATE IMAGE DESCRIPTION START")
    
    if not state.images_base64 or not state.use_image_similarity:
        log_query.info("⏭️  Skipping image description - no images or similarity disabled")
        return {}
    
    try:
        # Get the first image and generate description
        image_base64 = state.images_base64[0]
        description = describe_image_for_search(image_base64, state.user_query)
        
        if not description or description.startswith("Image description unavailable"):
            log_vlm.warning("🖼️ Failed to generate description, disabling image search")
            return {"use_image_similarity": False}
        
        t_elapsed = time.time() - t_start
        log_vlm.info(f"<<< GENERATE IMAGE DESCRIPTION DONE in {t_elapsed:.2f}s")
        
        # Store the description for use in similarity search
        return {"image_description": description}
        
    except Exception as e:
        log_vlm.error(f"🖼️ Image description generation failed: {e}")
        return {"use_image_similarity": False}


def node_image_similarity_search(state: DBRetrievalState) -> dict:
    """
    Search for similar images using TEXT semantic search on image_descriptions table.
    
    Uses the SAME RPC function as document retrieval: match_image_descriptions_summary
    
    Flow:
    1. Use the VLM-generated description from state.image_description
    2. Embed the description using text-embedding-3-small (1536 dims)
    3. Call match_image_descriptions_summary RPC (same as retriever uses)
    4. Return results for answer node to decide whether to display
    """
    t_start = time.time()
    log_vlm.info(">>> IMAGE SIMILARITY SEARCH (TEXT-BASED) START")
    
    # Check if we have an image description to search with
    image_description = getattr(state, 'image_description', None)
    if not image_description or not state.use_image_similarity:
        log_vlm.info("⏭️  Skipping image similarity search - no description available")
        return {"image_similarity_results": []}
    
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            log_vlm.warning("🖼️ Supabase not configured, skipping image similarity search")
            return {"image_similarity_results": []}
        
        _supa = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Generate text embedding from the image description
        log_vlm.info(f"🖼️ Generating text embedding for image description ({len(image_description)} chars)")
        query_embedding = emb.embed_query(image_description)
        log_vlm.info(f"🖼️ Generated {len(query_embedding)}-dim text embedding")
        
        # Use the SAME RPC function as document retrieval
        match_count = 100
        projects_limit = 10
        chunks_per_project = 3
        
        log_vlm.info(f"🖼️ Calling match_image_descriptions_summary (match_count={match_count}, projects_limit={projects_limit})")
        
        result = _supa.rpc("match_image_descriptions_summary", {
            'query_embedding': query_embedding,
            'match_count': match_count,
            'projects_limit': projects_limit,
            'chunks_per_project': chunks_per_project,
            'project_keys': None  # Search all projects
        }).execute()
        
        raw_results = result.data or []
        log_vlm.info(f"🖼️ RPC returned {len(raw_results)} results")
        
        # Transform results - relative_path IS the full image URL
        similar_images = []
        for row in raw_results:
            metadata = row.get('metadata', {})
            project_key = metadata.get('project_key')
            image_id = metadata.get('image_id')
            image_url = metadata.get('relative_path')  # relative_path is already the full Supabase URL
            page_number = metadata.get('page_number')
            
            similar_images.append({
                'id': row.get('id'),
                'content': row.get('content'),  # text_verbatim
                'similarity': row.get('similarity'),
                'project_key': project_key,
                'page_number': page_number,
                'image_id': image_id,
                'image_url': image_url
            })
        
        # Log ALL retrieved image URLs explicitly
        log_vlm.info(f"🖼️ ========== RETRIEVED IMAGE URLS ==========")
        for i, img in enumerate(similar_images):
            url = img.get('image_url', 'NONE')
            proj = img.get('project_key', 'UNKNOWN')
            sim = img.get('similarity', 0)
            log_vlm.info(f"🖼️   [{i+1}] project={proj}, similarity={sim:.3f}")
            log_vlm.info(f"🖼️       URL: {url}")
        log_vlm.info(f"🖼️ ==========================================")
        
        # Extract project keys from results
        project_keys = []
        for img in similar_images:
            project_key = img.get("project_key")
            if project_key and project_key not in project_keys:
                project_keys.append(project_key)
        
        log_vlm.info(f"🖼️ Images from {len(project_keys)} projects: {project_keys[:5]}")
        log_vlm.info(f"🖼️ TOTAL IMAGES TO PASS TO ANSWER NODE: {len(similar_images)}")
        
        t_elapsed = time.time() - t_start
        log_vlm.info(f"<<< IMAGE SIMILARITY SEARCH DONE in {t_elapsed:.2f}s")
        
        return {
            "image_similarity_results": similar_images,
            "selected_projects": list(set(project_keys + (state.selected_projects or []))) if project_keys else state.selected_projects
        }
        
    except Exception as e:
        log_vlm.error(f"🖼️ Image similarity search failed: {e}")
        import traceback
        log_vlm.error(f"🖼️ Traceback: {traceback.format_exc()}")
        return {"image_similarity_results": []}


# For backward compatibility - alias the old node name
node_generate_image_embeddings = node_generate_image_description
