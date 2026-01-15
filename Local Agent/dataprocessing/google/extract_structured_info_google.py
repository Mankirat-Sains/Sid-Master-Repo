#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Structured Information Extraction for Engineering Drawings using Google Gemini

This script processes region images from engineering drawings and extracts structured
information optimized for Supabase storage and semantic search using Google Gemini API.

For each image, it extracts:
- Classification: Plan, elevation, section, detail, notes, schedule
- Location: North, east, level 1, level 2, etc.
- Section callouts: Section cuts like "A/S01" that link to details
- Element type: Retaining wall, floating slab, main floor plan, etc.
- Text verbatim: Exact text word-for-word from the image (from OCR)
- Summary: Rich summary explaining how text relates to linework (for embeddings)
"""

import os
import json
import base64
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from google.oauth2 import service_account
from google.cloud import vision
import vertexai
from vertexai.generative_models import GenerativeModel, Part
from PIL import Image
from tqdm import tqdm
import io

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, will use environment variables directly

# ================= CONFIGURATION =================
# Google Service Account Key Path
OCR_KEY_PATH = r"C:\Users\shine\Testing-2025-01-07\Local Agent\dataprocessing\google\ocr-key.json"
# Also check environment variable as fallback
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
BASE_DIR = r"C:\Users\shine\Testing-2025-01-07\Local Agent\dataprocessing"
# Allow override via environment variable for batch processing
TEST_EMBEDDINGS_DIR = os.getenv("PROJECT_INPUT_DIR", os.path.join(BASE_DIR, "google", "input_images"))
OUTPUT_DIR = os.path.join(BASE_DIR, "google", "structured_json")
BATCH_SIZE = 10  # Process multiple images per API call
# Path to OCR results for verbatim text
OCR_RESULTS_PATH = os.path.join(BASE_DIR, "google", "ocr_results.json")
# Vertex AI Configuration
VERTEX_AI_LOCATION = "us-east4"  # Change if your Vertex AI is in a different region
GEMINI_MODEL = "gemini-2.5-flash-lite"  # Vertex AI model name
# =================================================

# System prompt for Gemini Vision (same as GPT-4o prompt)
EXTRACTION_PROMPT = r"""
You are a senior structural engineer analyzing technical drawing images.

Your task is to extract structured information from each image for database storage and semantic search.

**STRUCTURAL DRAWING CONTEXT (HOW TO READ THE DRAWINGS):**
- Treat every image as part of a coordinated structural drawing set (plans, sections, elevations, details, schedules)
- **Key / Site / General Arrangement plans**: show the building in context (site, roads, existing structures) and overall footprint
- **Plans**: top‑down cuts at a level (foundation plan, ground floor plan, roof/framing plan). X/Y axes show length and width; use these views to understand overall geometry, grids, and layout of foundations, columns, beams, slabs, doors, and openings
- **Sections**: vertical cuts (X/Z or Y/Z). Use these to understand heights, levels, vertical relationships, wall/footing depths, and how roof/floor systems bear on supports
- **Details**: enlarged portions of plans or sections that clarify reinforcement, connections, member build‑ups, etc. A single typical detail (e.g., column C1, beam B1) often applies wherever that tag appears on the plans
- **Schedules / tables**: tabular data listing members, reinforcement, spacings, bar sizes, etc. Use these to decode tags and symbols in the plans/sections (e.g., beam schedule, rebar schedule)
- Section/elevation callout symbols (e.g., bubbles with numbers and sheet references) define how drawings connect; use them to relate plan regions to their corresponding sections and details
- When interpreting ANY image, always reason like a structural engineer: identify load paths (roof → floors → beams/joists → columns/walls → foundations → soil), system types (steel, concrete, wood), and how typical details and schedules control repeated elements

**CRITICAL REQUIREMENTS:**
1. **DO NOT extract verbatim text** - verbatim text will be provided separately from Google Vision OCR. Focus on visual analysis and structured information extraction.
2. **MANDATORY: Extract ALL section/elevation callouts** (e.g., "1/S1.0", "2/S2.0", "3/S1.0", "A-A", "B-B"). These are ESSENTIAL for understanding how drawings connect. Look for circular/diamond callout bubbles with numbers/letters above and sheet references below, or text like "SECTION 1 / S1.0". In plan views especially, scan the ENTIRE image for ALL section callout symbols - plans often have multiple callouts that MUST all be captured.
3. The "summary" field MUST incorporate verbatim text values that will be provided from OCR but explain their meaning and relationships. You should still analyze the image visually to understand what the text means and how it relates to linework.
4. Example: If verbatim text contains "5'-0\"" and "15M @10\" o/c", the summary should say:
   "This detail shows a retaining wall with a height of 5'-0\" (five feet zero inches) as indicated by the dimension line. The reinforcement consists of 15M rebar bars spaced at 10 inches on center, as specified in the notation '15M @10\" o/c'. The wall thickness is 8 inches with a 4-inch concrete foundation below."
5. The summary should be rich and detailed for semantic search - explain HOW the text relates to the visual elements
6. Be precise with classifications, locations, and element types
7. **CRITICAL: All JSON strings must be properly escaped. Use \\" for quotes within strings, \\n for newlines, and ensure all strings are properly closed.**

**OUTPUT FORMAT:**
Output a JSON object with a single key "images" containing an array. Each image object must have these exact keys:

{
  "images": [
    {
      "image_id": "<filename>",
      "classification": "<One of: Plan, Elevation, Section, Detail, Notes, Schedule>",
      "location": "<Concise human-readable description of where this view/element sits in the building, combining level + orientation + zone where possible. Examples: 'Foundation – F1 footing along North wall', 'Ground Floor – main barn bay between grid 3-7', 'Roof – typical truss at mid-span', 'East wall elevation', or null if not determinable.>",
      "level": "<Normalized vertical level for this view/element: one of ['Site', 'Foundation', 'Basement', 'Ground Floor', 'Mezzanine', 'Second Floor', 'Third Floor', 'Roof', 'Parapet', 'Unknown']>",
      "orientation": "<For elevations/sections: primary orientation and cut direction, e.g., 'Transverse section looking North at mid-span', 'Longitudinal section looking East along grid 1', 'North elevation', 'South wall interior elevation', or null if not obvious>",
      "grid_references": [
        "<Any grid lines or bay references explicitly visible, e.g., 'Grid 1-5', 'Grids A-C', 'Between Grid 3 and Grid 7'. Return [] if none visible.>"
      ],
      "section_callouts": [
        "<e.g., 'A/S01', '3/D1', '1/S2.1', 'Section A-A', 'A-A'> - only SECTION or ELEVATION callout markers that reference other views/sheets"
      ],
      "element_type": "<e.g., 'Retaining Wall', 'Floating Slab', 'Main Floor Plan', 'Foundation Detail', 'Roof Framing', 'Wall Assembly', etc.>",
      "element_callouts": [
        "<Element / member / type tags such as 'F1', 'F2', 'W1', 'B1', 'T1', 'WE1', 'C1', 'BEAM 1', etc. that identify specific foundations, wall types, beam marks, truss types, slab types or other repeated elements. DO NOT put section or elevation references with a slash (e.g., '1/S2.1', 'A/A2.1') here.>"
      ],
      "key_components": [
        "<List of key structural components, materials, or systems visible in the image. For plans: e.g., 'Slab-on-Grade', 'Foundation Walls', 'Manure Storage Pad', 'Dropped Pen Floor Areas'. For details: e.g., 'Rebar', 'Concrete', 'Welded Wire Fabric', 'Footing'. Each distinct element type should be listed as a separate component.>"
      ],
      "summary": "<A comprehensive summary that: (1) Describes what the image shows visually (linework, structural elements), (2) Incorporates verbatim text values that will be provided from OCR but explains their meaning and relationships, (3) Explains how text annotations relate to the linework and structural elements, (4) Is rich in detail for semantic search and embeddings. The summary should reference specific values from the OCR text when available, explaining what they mean in the context of the visual elements shown. MAXIMUM 500 WORDS - ensure the summary does not exceed 500 words. Example: 'This section view shows a retaining wall detail with foundation. The wall has a height of 5'-0\" as indicated by the vertical dimension line. Reinforcement consists of 15M rebar bars spaced at 10 inches on center (15M @10\" o/c) as shown in the rebar notation. The wall is 8 inches thick and includes a 4-inch concrete foundation below. The detail shows the connection between the wall and foundation, with angle fasteners specified as 8-5/16\" x 3\" wood lags fastened to studs.'>"
    }
  ]
}

**CLASSIFICATION GUIDELINES:**
- "Plan": Floor plans, site plans, roof plans (top-down views showing layout)
- "Elevation": Building elevations, exterior views (side views of building)
- "Section": Section cuts through the building (cut-away views)
- "Detail": Close-up details of specific connections or assemblies (zoomed-in views)
- "Notes": General notes, specifications, legends (text-heavy, no major linework)
- "Schedule": Tables, schedules (beam schedules, lintel schedules, rebar schedules, etc.)

**LOCATION & LEVEL GUIDELINES:**
- Always try to describe BOTH vertical level and horizontal position/orientation so the element can be tied into a global building model
- Use the "level" field for a **normalized vertical category** (e.g., "Foundation", "Basement", "Ground Floor", "Second Floor", "Roof"). This should come from plan titles, section notes, or callouts like "FOUNDATION PLAN", "GROUND FLOOR PLAN", "ROOF FRAMING PLAN", "SECTION @ GRID 3", etc.
- Use the "location" string to combine level + orientation + any zone information into a concise phrase a structural engineer would say on a coordination call (e.g., "Ground Floor – south bay at grid 7", "Roof – east end over manure storage area", "Foundation – F1 footings under east wall").
- Use the "orientation" field primarily for sections/elevations (e.g., "Transverse section looking North", "Longitudinal section looking East", "North elevation", "West wall elevation"). For plan views, orientation can often be null unless explicitly noted.
- Use "grid_references" to capture any grid lines or bay tags that appear (e.g., ["Grid 1-5", "Grids A-C"]). If only single grids appear (e.g., "3", "A"), include them as simple strings in the array.
- Extract this information from view titles, key notes, grid bubbles, section titles (e.g., "SECTION 1/S2.1 – BUILDING SECTION – BARN"), and nearby annotations.
- Return null for "location", "level", or "orientation" only when you truly cannot infer them from the image. For "grid_references", return [] if no grids are visible.

**SECTION CALLOUTS (CRITICAL - MUST CAPTURE ALL):**
- **MANDATORY**: You MUST extract EVERY section/elevation callout marker visible in the image. These are ESSENTIAL for understanding how drawings connect together.
- Look for section/elevation call markers that reference another view or sheet. Common formats include:
  - **Number/Sheet format**: "1/S1.0", "2/S2.0", "3/S1.0", "1/S2.1", "3/S3", "A/S01", "3/D1" (section number / sheet number)
  - **Letter-letter format**: "A-A", "B-B", "C-C", "Section A-A"
  - **Text references**: "SEE SECTION 1/S2.1", "SEE SECTION A-A", "SECTION 1", "SECTION 3"
  - **With spaces**: "1 / S1.0", "3 / S1.0" (extract as "1/S1.0", "3/S1.0" - normalize by removing spaces)
- **Where to find them:**
  - **In PLAN views**: Section callouts appear as circular or diamond-shaped bubbles with numbers/letters above and sheet references below (e.g., "1" above, "S1.0" below = "1/S1.0"). These indicate where section cuts are made through the plan. **CRITICAL: Plans often have MULTIPLE section callouts - you MUST capture ALL of them.**
  - **In SECTION/ELEVATION views**: The section title itself (e.g., "SECTION 1 / S1.0") is a section callout - extract it!
  - **In DETAIL views**: Section callouts may reference other details or sections
- **Visual patterns to recognize:**
  - Circular bubbles bisected by a cutting plane line, with section number on top and sheet number on bottom
  - Diamond-shaped symbols with section number and sheet reference
  - Triangular arrows pointing along a cutting plane with callout bubbles
  - Text labels like "SECTION 1 / S1.0" or "SECTION 3 WIND COLUMN"
- **Normalization**: If you see "1 / S1.0" or "1/S1.0" or "1-S1.0", normalize to "1/S1.0" format (number/sheet). If you see "SECTION 1 / S1.0", extract as "1/S1.0".
- **CRITICAL DISTINCTION**: 
  - **Section callouts** have a "/" or "-" separating section number from sheet number (e.g., "1/S1.0", "2/S2.0", "3/S1.0") OR are letter-letter format (e.g., "A-A", "B-B")
  - **Element callouts** are single tags without "/" or "-" (e.g., "F1", "W1", "B1", "T1") - these go in "element_callouts"
- **Do NOT include element or type designations such as 'F1', 'F2', 'W1', 'B1', 'T1', 'WE1', etc. in section_callouts** – those belong in "element_callouts"
- **If you see ANY callout symbol with a number/letter above and a sheet reference below, or any text containing "SECTION" followed by a number and sheet reference, it MUST be captured in section_callouts**
- Return empty array [] ONLY if you are absolutely certain no section/elevation callouts are present

**ELEMENT CALLOUTS (FOUNDATION / WALL / BEAM / TRUSS / SLAB TAGS):**
- Collect tags that label specific elements or typical details, e.g., "F1", "F2", "F3" (footing types), "W1", "W2" (wall types), "B1", "B2" (beam marks), "T1", "T2" (truss types), "WE1" (wall elevation), etc.
- These are often shown in diamonds, squares, or other symbols adjacent to foundations, walls, beams, or trusses and are cross‑referenced to schedules or typical details
- Do NOT include view references with a slash "/" (e.g., "1/S2.1", "3/A3.0") – those are section_callouts
- Return empty array [] if none are present

**ELEMENT TYPE:**
- Be specific and descriptive: "Retaining Wall Detail", "Main Floor Framing Plan", "Foundation Wall Section", "Roof Truss Connection", "Beam Schedule", etc.
- Combine the structural element with the view type when appropriate
- Use engineering terminology

**KEY COMPONENTS:**
- List all key structural components, materials, or systems visible in the image
- For floor plans: Each distinct element type should be listed separately (e.g., "Slab-on-Grade", "Foundation Walls", "Manure Storage Pad", "Dropped Pen Floor Areas", "Thickened Slab Edge")
- For details: List specific materials and components (e.g., "Rebar", "Concrete", "Welded Wire Fabric", "Footing", "Curb")
- Be specific and use engineering terminology
- Return empty array [] if no distinct components are identifiable

**SUMMARY (MOST IMPORTANT):**
- Must be rich and detailed for semantic search and embeddings
- MUST incorporate verbatim text values from OCR (which will be provided) but explain their meaning
- MUST explain relationships between text and visual elements (e.g., "the dimension '12'-0\"' indicates the width of the room")
- Analyze the image visually to understand what dimensions, labels, and annotations mean in context
- MAXIMUM 500 WORDS - The summary cannot exceed 500 words. It can be less if all information is contained, but it cannot be more than 500 words.
- Should read naturally for semantic search queries
- Example structure: "This [classification] shows [what is visible]. [Specific verbatim values from OCR] indicate [what they mean based on visual analysis]. [How text relates to linework]. [Additional context and relationships]."
- Before writing the final summary, internally identify all distinct structural systems present in the image (e.g., truss bracing system, slab system, foundation system). The summary MUST describe each system explicitly and explain how the OCR-extracted text applies to that system.

STRUCTURAL DRAWING INTERPRETATION RULES:

1. Identify the drawing type first (Plan, Section, Detail, Elevation).
2. Read ALL general notes before interpreting geometry.
3. Notes marked "TYP." apply unless explicitly overridden.
4. Dimensions govern over scale; drawings may be N.T.S.
5. Structural members are identified by function first, size second.
6. Section and detail callouts reference other drawings and must be captured verbatim.
7. Fastener schedules and spacing notes are critical and must not be summarized away.
8. If multiple systems are present, identify and describe each system separately.
9. Assume industry-standard conventions unless explicitly contradicted by notes.
10. Always explain how text annotations relate to physical members shown in linework.
"""


# Initialize Gemini client (Vertex AI)
model = None
_project_id = None


def setup_gemini_client():
    """Initialize Vertex AI Gemini client using service account credentials from ocr-key.json"""
    global model, _project_id
    
    if model is not None:
        return model
    
    if not os.path.exists(OCR_KEY_PATH):
        raise FileNotFoundError(f"OCR Key file not found at: {OCR_KEY_PATH}")
    
    # Load project_id and credentials
    with open(OCR_KEY_PATH, 'r', encoding='utf-8') as f:
        key_data = json.load(f)
        _project_id = key_data.get('project_id')
        if not _project_id:
            raise ValueError("project_id not found in ocr-key.json. Required for Vertex AI.")
    
    credentials = service_account.Credentials.from_service_account_file(OCR_KEY_PATH)
    
    # Initialize Vertex AI
    vertexai.init(project=_project_id, location=VERTEX_AI_LOCATION, credentials=credentials)
    
    # Try multiple model names
    model_names = [GEMINI_MODEL, "gemini-2.0-flash-exp", "gemini-1.5-pro"]
    model = None
    last_error = None
    
    for model_name in model_names:
        try:
            model = GenerativeModel(model_name)
            print(f"   ✅ Vertex AI Gemini model initialized: {model_name} (Location: {VERTEX_AI_LOCATION})")
            break
        except Exception as e:
            last_error = e
            continue
    
    if model is None:
        raise RuntimeError(f"Failed to initialize Gemini model via Vertex AI. Tried: {', '.join(model_names)}. Last error: {last_error}")
    
    return model


def extract_text_vision(vision_client, file_path):
    """Extract text using Google Vision API"""
    try:
        with open(file_path, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        response = vision_client.document_text_detection(image=image)
        
        if response.error.message:
            return None, f"Error: {response.error.message}"
        
        texts = response.text_annotations
        if texts:
            # The first annotation contains the full text
            full_text = texts[0].description
            return full_text, None
        else:
            return None, "No text detected"
    
    except Exception as e:
        return None, f"Exception: {str(e)}"


def run_ocr_on_project(project_dir: Path, project_id: str) -> Dict[str, Dict[str, Any]]:
    """Run OCR on all region images in a project and return OCR data"""
    print(f"   🔍 Running OCR on project images...")
    
    # Setup Vision API client
    credentials = service_account.Credentials.from_service_account_file(OCR_KEY_PATH)
    vision_client = vision.ImageAnnotatorClient(credentials=credentials)
    
    # Find all region images
    region_images = find_all_region_images(project_dir)
    
    ocr_data = {}
    ocr_results = []
    
    for img_data in tqdm(region_images, desc="   OCR Progress"):
        img_path = img_data["path"]
        filename = img_data["filename"]
        page_number = img_data.get("page_number")  # Extract from img_data
        region_number = img_data.get("region_number")  # Extract from img_data
        
        # Extract text using Vision API
        text, error = extract_text_vision(vision_client, str(img_path))
        
        ocr_results.append({
            "file_path": str(img_path),
            "filename": filename,
            "vision_api": {
                "text": text,
                "error": error
            }
        })
        
        if text:
            # Use full path as key to avoid conflicts when same filename appears on different pages
            full_path = str(img_path).replace('\\', '/')
            ocr_data[full_path] = {
                'text': text,
                'file_path': str(img_path),
                'filename': filename,
                'page_number': page_number,
                'region_number': region_number
            }
            # Also store by filename for backward compatibility, but prefer full path
            if filename not in ocr_data:
                ocr_data[filename] = {
                    'text': text,
                    'file_path': str(img_path)
                }
    
    # Save OCR results (append to existing file if it exists, or create new)
    ocr_output_path = Path(OCR_RESULTS_PATH)
    ocr_output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing results if file exists
    existing_results = []
    if ocr_output_path.exists():
        try:
            with open(ocr_output_path, 'r', encoding='utf-8') as f:
                existing_results = json.load(f)
            # Remove any existing results for this project to avoid duplicates
            project_dir_str = str(project_dir).replace('\\', '/')
            existing_results = [r for r in existing_results if project_dir_str not in r.get('file_path', '').replace('\\', '/')]
        except:
            existing_results = []
    
    # Append new results
    existing_results.extend(ocr_results)
    
    # Save combined results
    with open(ocr_output_path, 'w', encoding='utf-8') as f:
        json.dump(existing_results, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ OCR complete! Extracted text from {len(ocr_data)} images for project {project_id}")
    print(f"   💾 OCR results saved to: {OCR_RESULTS_PATH}")
    
    return ocr_data


def load_ocr_results(project_dir: Path, project_id: str) -> Dict[str, Dict[str, Any]]:
    """Load OCR results from file filtered by project, or run OCR if needed"""
    ocr_data = {}
    
    # Normalize project directory path for matching
    project_dir_str = str(project_dir).replace('\\', '/')
    
    # Check if we need to run OCR for this project
    need_ocr = False
    
    if not os.path.exists(OCR_RESULTS_PATH):
        need_ocr = True
    else:
        # Check if OCR results exist for this project
        try:
            with open(OCR_RESULTS_PATH, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            # Check if any results match this project
            project_results = [r for r in results if project_dir_str in r.get('file_path', '').replace('\\', '/')]
            if not project_results:
                need_ocr = True
        except:
            need_ocr = True
    
    if need_ocr:
        print(f"   ⚠️ OCR results not found for project {project_id}")
        print(f"   🔄 Running OCR on project images...")
        # Run OCR on the project
        ocr_data = run_ocr_on_project(project_dir, project_id)
        return ocr_data
    
    # Load and filter OCR results by project
    try:
        with open(OCR_RESULTS_PATH, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Build a mapping from file path to OCR text - ONLY for this project
        for result in results:
            file_path = result.get('file_path', '')
            # Normalize path separators
            file_path_normalized = file_path.replace('\\', '/')
            
            # Only include results from this project directory
            if project_dir_str not in file_path_normalized:
                continue
            
            # Get text from Vision API (preferred) or Document AI
            vision_data = result.get('vision_api', {})
            docai_data = result.get('documentai_api', {})
            
            # Prefer Vision API text, fall back to Document AI
            text = None
            if vision_data.get('text'):
                text = vision_data['text']
            elif vision_data.get('pages'):
                # For PDFs, combine all pages
                pages = vision_data['pages']
                text_parts = [p.get('text', '') for p in pages if isinstance(p, dict) and p.get('text')]
                text = '\n\n'.join(text_parts)
            elif docai_data.get('text'):
                text = docai_data['text']
            elif docai_data.get('pages'):
                # For PDFs, combine all pages
                pages = docai_data['pages']
                text_parts = [p.get('text', '') for p in pages if isinstance(p, dict) and p.get('text')]
                text = '\n\n'.join(text_parts)
            
            if text:
                # Store by full path to avoid conflicts when same filename appears on different pages
                filename = os.path.basename(file_path)
                full_path = file_path_normalized
                ocr_data[full_path] = {
                    'text': text,
                    'file_path': file_path,
                    'filename': filename
                }
                # Also store by filename for backward compatibility, but prefer full path
                if filename not in ocr_data:
                    ocr_data[filename] = {
                        'text': text,
                        'file_path': file_path
                    }
        
        print(f"   📄 Loaded OCR results for {len(ocr_data)} files from project {project_id}")
        return ocr_data
    
    except Exception as e:
        print(f"   ⚠️ Error loading OCR results: {e}")
        print(f"   🔄 Running OCR on project images...")
        # Fallback: run OCR if loading fails
        ocr_data = run_ocr_on_project(project_dir, project_id)
        return ocr_data


def truncate_summary(text: str, max_words: int = 500) -> str:
    """Truncate summary to maximum word count"""
    if not text:
        return text
    
    words = text.split()
    if len(words) <= max_words:
        return text
    
    # Truncate to max_words and add ellipsis
    truncated = ' '.join(words[:max_words])
    # Try to end at a sentence boundary
    last_period = truncated.rfind('.')
    if last_period > len(truncated) * 0.8:  # If period is in last 20%, use it
        return truncated[:last_period + 1]
    return truncated + '...'


def parse_json_with_retry(json_str: str, max_retries: int = 5) -> Dict[str, Any]:
    """Parse JSON with retry and repair attempts"""
    import json as json_lib
    import re
    
    # Clean up markdown code blocks first
    json_str_clean = json_str.strip()
    if json_str_clean.startswith("```json"):
        json_str_clean = json_str_clean[7:]
    if json_str_clean.startswith("```"):
        json_str_clean = json_str_clean[3:]
    if json_str_clean.endswith("```"):
        json_str_clean = json_str_clean[:-3]
    json_str_clean = json_str_clean.strip()
    
    for attempt in range(max_retries + 1):
        try:
            return json_lib.loads(json_str_clean)
        except json_lib.JSONDecodeError as e:
            if attempt < max_retries:
                error_msg = str(e)
                print(f"      ⚠️ JSON parsing attempt {attempt + 1} failed: {error_msg[:100]}")
                
                # Fix 1: Remove trailing commas before } or ] and fix invalid escape sequences
                if attempt == 0:
                    json_str_clean = re.sub(r',(\s*[}\]])', r'\1', json_str_clean)
                    # Fix invalid escape sequences - JSON only allows: \" \\ \/ \b \f \n \r \t \uXXXX
                    # Replace invalid escapes like \' with just the character
                    json_str_clean = re.sub(r'\\(?![\\"/bfnrt]|u[0-9a-fA-F]{4})', r'', json_str_clean)
                
                # Fix 2: Fix incorrectly escaped quotes in property names and string delimiters
                # Pattern: \"property_name" should be "property_name"
                elif attempt == 1:
                    # Fix escaped quotes that are property names (before colon)
                    json_str_clean = re.sub(r'\\"([a-zA-Z_][a-zA-Z0-9_]*)"\s*:', r'"\1":', json_str_clean)
                    # Fix escaped quotes at start of strings (after colon, comma, or opening brace/bracket)
                    json_str_clean = re.sub(r'([:,\[\{]\s*)\\"', r'\1"', json_str_clean)
                    # Fix escaped quotes at end of strings (before comma, closing brace/bracket)
                    json_str_clean = re.sub(r'\\"(\s*[,}\]])', r'"\1', json_str_clean)
                    # Fix invalid escape sequences again (in case they were introduced)
                    json_str_clean = re.sub(r'\\(?![\\"/bfnrt]|u[0-9a-fA-F]{4})', r'', json_str_clean)
                
                # Fix 3: Try to find and extract just the JSON object
                elif attempt == 2:
                    start_idx = json_str_clean.find('{')
                    if start_idx >= 0:
                        brace_count = 0
                        end_idx = start_idx
                        for i in range(start_idx, len(json_str_clean)):
                            if json_str_clean[i] == '{':
                                brace_count += 1
                            elif json_str_clean[i] == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end_idx = i + 1
                                    break
                        if end_idx > start_idx:
                            json_str_clean = json_str_clean[start_idx:end_idx]
                
                # Fix 4: Fix invalid escape sequences (like double-escaped quotes and invalid escapes)
                elif attempt == 3:
                    # Fix invalid escape sequences first - remove backslashes before invalid characters
                    # JSON only allows: \" \\ \/ \b \f \n \r \t \uXXXX
                    json_str_clean = re.sub(r'\\(?![\\"/bfnrt]|u[0-9a-fA-F]{4})', r'', json_str_clean)
                    # Fix double-escaped quotes: \\" -> \"
                    json_str_clean = json_str_clean.replace('\\\\"', '\\"')
                    # Fix triple-escaped quotes: \\\" -> \"
                    json_str_clean = json_str_clean.replace('\\\\\\"', '\\"')
                    # Fix escaped quotes in property names more aggressively
                    json_str_clean = re.sub(r'\\"([a-zA-Z_][a-zA-Z0-9_]*)"\s*:', r'"\1":', json_str_clean)
                
                # Fix 5: More aggressive - fix all escaped quotes that shouldn't be escaped
                elif attempt == 4:
                    # Unescape quotes that are clearly property names or string delimiters
                    # Look for pattern: \"word": and replace with "word":
                    json_str_clean = re.sub(r'\\"([a-zA-Z_][a-zA-Z0-9_]*)"\s*:', r'"\1":', json_str_clean)
                    # Also fix array/object boundaries
                    json_str_clean = re.sub(r'\\"(\s*[\[\{])', r'"\1', json_str_clean)
                    json_str_clean = re.sub(r'([\]\}])\s*\\"', r'\1"', json_str_clean)
                    # Fix escaped quotes around array brackets
                    json_str_clean = re.sub(r'\\"(\s*\[)', r'"\1', json_str_clean)
                    json_str_clean = re.sub(r'(\]\s*)\\"', r'\1"', json_str_clean)
                
                continue
            else:
                # Last attempt failed - print the problematic section for debugging
                error_pos = getattr(e, 'pos', None)
                if error_pos:
                    start = max(0, error_pos - 200)
                    end = min(len(json_str_clean), error_pos + 200)
                    print(f"      ❌ JSON error at position {error_pos}")
                    print(f"      Problematic section: {json_str_clean[start:end]}")
                    # Also try to save the full response for debugging
                    try:
                        debug_file = Path("debug_json_response.txt")
                        with open(debug_file, 'w', encoding='utf-8') as f:
                            f.write(json_str_clean)
                        print(f"      💾 Full response saved to: {debug_file}")
                    except:
                        pass
                raise


def find_all_region_images(project_dir: Path) -> List[Dict[str, Any]]:
    """Find all region images in a project directory"""
    images = []
    
    # Look for page_XXX subdirectories
    for page_dir in sorted(project_dir.glob("page_*")):
        if not page_dir.is_dir():
            continue
        
        # Extract page number
        page_match = re.search(r'page_(\d+)', page_dir.name)
        page_number = int(page_match.group(1)) if page_match else None
        
        # Find all region images in this page directory
        for img_path in sorted(page_dir.glob("region_*_red_box.png")):
            # Extract region number
            region_match = re.search(r'region_(\d+)_red_box', img_path.name)
            region_number = int(region_match.group(1)) if region_match else None
            
            images.append({
                "path": img_path,
                "filename": img_path.name,  # Full filename like "region_01_red_box.png"
                "page_number": page_number,  # Integer from page_001 -> 1
                "region_number": region_number,  # Integer from region_01 -> 1
                "relative_path": None  # Can be empty as per user requirement
            })
    
    return images


def process_image_batch(
    image_data_list: List[Dict[str, Any]],
    project_id: str,
    ocr_data: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Process a batch of region images with Gemini Vision"""
    global model
    
    results = []
    
    # Process images one at a time (Gemini works better this way)
    for img_data in image_data_list:
        try:
            img_path = img_data["path"]
            filename = img_data["filename"]
            
            # Read image as bytes directly (since they're already PNG files)
            with open(str(img_path), 'rb') as f:
                image_bytes = f.read()
            
            image_part = Part.from_data(image_bytes, mime_type="image/png")
            
            # Get OCR text if available (for adding to output later, not for prompting)
            # Match by full path first (most accurate), then fall back to filename
            ocr_text = ""
            img_path_str = str(img_path).replace('\\', '/')
            if img_path_str in ocr_data:
                ocr_text = ocr_data[img_path_str].get('text', '')
            elif filename in ocr_data:
                ocr_text = ocr_data[filename].get('text', '')
            
            # Build prompt - DO NOT include verbatim text extraction in the prompt
            # The VLM should focus on visual analysis only
            prompt_parts = [
                "Analyze this engineering drawing image and extract structured information based on visual analysis. Output a JSON object with a single key 'images' containing an array with ONE image analysis object.",
                "",
                "Focus on visual elements: classification, location, section callouts, element type, element callouts, key components, and a summary that explains the visual structure. Verbatim text will be provided separately from OCR."
            ]
            
            # Optionally provide OCR text for context in summary generation (truncated)
            if ocr_text:
                prompt_parts.append(f"\n**OCR Text Available (for summary context only):**\n{ocr_text[:1000]}...")
                prompt_parts.append("\nUse this OCR text to inform your summary - explain what the text values mean in the context of the visual elements shown. DO NOT repeat the full verbatim text in your summary, but DO reference specific values and explain their meaning.")
            
            # Add context
            context_lines = [f"Image ID: {filename}"]
            page_number = img_data.get("page_number")
            if page_number is not None:
                context_lines.append(f"Page Number: {page_number}")
            
            prompt_parts.append("\n".join(context_lines))
            prompt = "\n".join(prompt_parts)
            
            # Build full prompt
            full_prompt = f"{EXTRACTION_PROMPT}\n\n{prompt}"
            
            # Generate response using Vertex AI
            response = model.generate_content(
                [full_prompt, image_part],
                generation_config={
                    "temperature": 0.2,
                    "response_mime_type": "application/json",
                }
            )
            
            result_text = response.text
            result_json = parse_json_with_retry(result_text)
            
            # Extract images array
            images_array = result_json.get("images", [])
            if images_array:
                img_obj = images_array[0]
                img_obj["image_id"] = filename
                img_obj["project_id"] = project_id
                img_obj["page_number"] = page_number
                img_obj["region_number"] = img_data.get("region_number")
                img_obj["relative_path"] = img_data.get("relative_path")
                
                # Add verbatim text from OCR
                if ocr_text:
                    img_obj["text_verbatim"] = ocr_text
                
                # Truncate summary to 500 words if needed
                if "summary" in img_obj and img_obj["summary"]:
                    img_obj["summary"] = truncate_summary(img_obj["summary"], max_words=500)
                
                results.append(img_obj)
            
        except Exception as e:
            print(f"      ❌ Failed to process {img_data.get('filename', 'unknown')}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    return results


def process_project(project_id: str):
    """Process all region images for a single project"""
    global model
    
    project_dir = Path(TEST_EMBEDDINGS_DIR) / project_id
    output_dir = Path(OUTPUT_DIR) / project_id
    
    if not project_dir.exists():
        print(f"❌ Project directory not found: {project_dir}")
        return
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"structured_{project_id}.json"
    
    print(f"\n--- Processing Project: {project_id} ---")
    print(f"   Input: {project_dir}")
    print(f"   Output: {output_file}")
    
    # Load OCR results (or run OCR if needed)
    ocr_data = load_ocr_results(project_dir, project_id)
    
    # Find all region images
    region_images = find_all_region_images(project_dir)
    if not region_images:
        print(f"   ⚠️ No region images found in {project_dir}")
        return
    
    print(f"   📸 Found {len(region_images)} region images")
    
    # Load existing data if resuming
    existing_data = {"images": []}
    existing_ids = set()
    
    if output_file.exists():
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                existing_ids = {img.get("image_id") for img in existing_data.get("images", []) if img.get("image_id")}
            print(f"   📂 Resuming: {len(existing_ids)} images already processed")
            if len(existing_ids) > 0:
                print(f"   📋 Sample existing IDs: {list(existing_ids)[:5]}")
        except Exception as e:
            print(f"   ⚠️ Could not load existing file: {e}")
    
    # Filter out already processed images - match by filename
    images_to_process = []
    for img in region_images:
        filename = img["filename"]
        if filename not in existing_ids:
            images_to_process.append(img)
    
    print(f"   📊 Total images: {len(region_images)}, Already processed: {len(existing_ids)}, To process: {len(images_to_process)}")
    
    if len(images_to_process) == 0:
        print(f"   ✅ All images already processed!")
        return
    
    if len(images_to_process) > 0:
        print(f"   🔄 Will process {len(images_to_process)} new images")
        print(f"   📝 Sample images to process: {[img['filename'] for img in images_to_process[:5]]}")
    
    print(f"   ⚙️ Processing {len(images_to_process)} new images...")
    
    # Process in batches
    for i in range(0, len(images_to_process), BATCH_SIZE):
        batch = images_to_process[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(images_to_process) + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"   ⚙️ Processing Batch {batch_num}/{total_batches} ({len(batch)} images)...")
        
        results = process_image_batch(batch, project_id, ocr_data)
        
        if results:
            existing_data["images"].extend(results)
            
            # Save incrementally
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            print(f"      ✅ Saved {len(results)} images")
        else:
            print(f"      ⚠️ No results for this batch")
    
    print(f"   ✅ Complete! Total images: {len(existing_data['images'])}")
    print(f"   💾 Saved to: {output_file}")


def main():
    """Main entry point"""
    global model
    
    print("="*60)
    print("Structured Information Extraction using Google Gemini")
    print("="*60)
    
    # Setup Gemini client
    try:
        model = setup_gemini_client()
        print("✅ Google Gemini API initialized")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return
    
    # Check if project ID provided as argument
    import sys
    if len(sys.argv) > 1:
        project_id = sys.argv[1]
        process_project(project_id)
    else:
        # Process all projects in input_images directory
        input_images_path = Path(TEST_EMBEDDINGS_DIR)
        
        if not input_images_path.exists():
            print(f"❌ Input images directory not found: {input_images_path}")
            return
        
        # Find all project directories
        projects = sorted([d.name for d in input_images_path.iterdir() if d.is_dir()])
        
        if not projects:
            print(f"❌ No project directories found in {input_images_path}")
            return
        
        print(f"📁 Found {len(projects)} project(s): {', '.join(projects)}")
        print()
        
        for project_id in projects:
            try:
                process_project(project_id)
                print()  # Add blank line between projects
            except Exception as e:
                print(f"❌ Error processing {project_id}: {e}")
                import traceback
                traceback.print_exc()
                print()  # Add blank line even on error
                continue
    
    print("\n" + "="*60)
    print("✨ Processing Complete!")
    print("="*60)


if __name__ == "__main__":
    main()

