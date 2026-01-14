"""
Answer Synthesis
Main synthesis function that generates answers from documents
"""
from collections import defaultdict
from typing import List, Dict, Optional, Any
from langchain_core.documents import Document
from config.settings import MAX_SYNTHESIS_DOCS, PROJECT_CATEGORIES
from config.logging_config import log_query
from config.llm_instances import llm_synthesis
from prompts.synthesis_prompts import ANSWER_PROMPT, CODE_ANSWER_PROMPT, COOP_ANSWER_PROMPT
from models.memory import get_conversation_context
from nodes.DBRetrieval.KGdb.project_metadata import fetch_project_metadata
from utils.project_utils import date_from_project_id


def extract_text_from_content(content) -> str:
    """
    Extract text content from AIMessageChunk.content.
    Handles both string format (OpenAI, Anthropic) and list format (Gemini 3.0).
    
    Gemini 3.0 returns: [{'type': 'text', 'text': "..."}]
    Other models return: "text content"
    """
    if not content:
        return ""
    
    # Handle list format (Gemini 3.0)
    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                # Extract text from dict items (e.g., {'type': 'text', 'text': "..."})
                if item.get('type') == 'text' and 'text' in item:
                    text_parts.append(str(item['text']))
                elif 'text' in item:
                    # Fallback: just try 'text' key
                    text_parts.append(str(item['text']))
            elif isinstance(item, str):
                # If list contains strings directly
                text_parts.append(item)
        return ''.join(text_parts)
    
    # Handle string format (OpenAI, Anthropic, etc.)
    if isinstance(content, str):
        return content
    
    # Fallback: try to convert to string
    return str(content)


def synthesize(
    q: str,
    docs: List[Document],
    session_id: str = "default",
    stream: bool = False,
    project_metadata: Optional[Dict[str, Dict[str, str]]] = None,
    code_docs: Optional[List[Document]] = None,
    use_code_prompt: bool = False,
    coop_docs: Optional[List[Document]] = None,
    use_coop_prompt: bool = False,
    active_filters: Optional[Dict[str, Any]] = None,
    image_results: Optional[List[Dict]] = None
):
    """
    Group docs by project, use pre-fetched metadata (or fetch if not provided), synthesize answer.
    """
    log_query.info(f"🔍 SYNTHESIS DEBUG: synthesize() called - use_code_prompt={use_code_prompt}, use_coop_prompt={use_coop_prompt}, code_docs={len(code_docs) if code_docs else 0}, coop_docs={len(coop_docs) if coop_docs else 0}, docs={len(docs)}")

    grouped = defaultdict(list)
    cites = []
    unique_projects = set()

    print(f"🔍 SYNTHESIS: Processing {len(docs)} docs")  # Diagnostic

    for i, d in enumerate(docs[:MAX_SYNTHESIS_DOCS], 1):
        md = d.metadata or {}
        proj = md.get("drawing_number") or md.get("project_key") or "?"
        page = md.get("page_id") or md.get("page") or "?"
        title = md.get("title") or ""

        if proj and proj != "?":
            unique_projects.add(proj)

        derived_date = date_from_project_id(proj)
        date_str = (
            md.get("date")
            or md.get("issue_date")
            or md.get("signed_date")
            or (derived_date.isoformat() if derived_date else "")
        )

        cites.append({
            "project": proj,
            "page": page,
            "title": title,
            "date": date_str,
            "bundle": md.get("bundle_file"),
            "chunk_index": md.get("chunk_index"),
        })

        grouped[proj].append(
            f"[{i}] (proj {proj}, page {page}, date {date_str}) {title}\n{d.page_content}"
        )
    
    print(f"📋 SYNTHESIS: Extracted project IDs from docs: {sorted(list(unique_projects))[:20]}{'...' if len(unique_projects) > 20 else ''}")  # Diagnostic
    
    # Log any suspicious project IDs (very short or non-standard format)
    suspicious_projects = [p for p in unique_projects if len(p) < 5 or not any(c.isdigit() for c in p)]
    if suspicious_projects:
        log_query.warning(f"⚠️ Found suspicious project IDs: {suspicious_projects}")

    # Fetch metadata from Supabase for ALL unique projects (if not pre-fetched)
    print(f"🔍 SYNTHESIS: About to fetch metadata for {len(unique_projects)} unique projects")  # Diagnostic
    
    # Ensure project_metadata is always a dict
    if project_metadata is None:
        project_metadata = fetch_project_metadata(list(unique_projects))
    elif not isinstance(project_metadata, dict):
        log_query.warning(f"⚠️ project_metadata is not a dict (type: {type(project_metadata)}), resetting to empty dict")
        project_metadata = {}
    
    # Final safety check - ensure it's a dict
    if not isinstance(project_metadata, dict):
        log_query.error(f"❌ project_metadata is not a dict after fetch (type: {type(project_metadata)}), using empty dict")
        project_metadata = {}
    
    # Find missing projects and fetch their metadata
    missing_projects = [p for p in unique_projects if p not in project_metadata]
    if missing_projects:
        log_query.info(f"🔍 Fetching metadata for {len(missing_projects)} missing projects: {missing_projects[:5]}{'...' if len(missing_projects) > 5 else ''}")
        additional_metadata = fetch_project_metadata(missing_projects)
        if isinstance(additional_metadata, dict):
            project_metadata.update(additional_metadata)
        else:
            log_query.warning(f"⚠️ fetch_project_metadata returned non-dict: {type(additional_metadata)}, skipping update")

    # Build grouped context with enriched project information
    lines = []
    for proj, chunks in grouped.items():
        meta = project_metadata.get(proj, {})
        proj_name = meta.get("name", "")
        proj_addr = meta.get("address", "")
        proj_city = meta.get("city", "")

        if proj_name and proj_addr and proj_city:
            proj_header = f"### Project {proj} - Project Name: {proj_name}, Project Address: {proj_addr}, City: {proj_city}"
        elif proj_name and proj_addr:
            proj_header = f"### Project {proj} - Project Name: {proj_name}, Project Address: {proj_addr}"
        elif proj_name:
            proj_header = f"### Project {proj} - Project Name: {proj_name}"
        else:
            proj_header = f"### Project {proj}"

        lines.append(proj_header + "\n" + "\n\n".join(chunks))

    ctx = "\n\n".join(lines)

    # Format code docs (if any)
    if code_docs:
        code_lines = []
        code_lines.append("\n\n### Code References")
        
        for i, cd in enumerate(code_docs[:MAX_SYNTHESIS_DOCS], 1):
            md = cd.metadata or {}
            filename = md.get("filename", "")
            source = md.get("source", "unknown")
            section = md.get("section", "")
            title = md.get("title", "")
            page = md.get("page", "")
            page_number = md.get("page_number", "")
            
            final_page = page_number or page
            
            code_header_parts = [f"[{i}]"]
            if filename:
                code_header_parts.append(f"Document: {filename}")
            else:
                if source:
                    code_header_parts.append(f"Document: {source}")
            
            if source and source != filename:
                code_header_parts.append(f"Source: {source}")
            if section:
                code_header_parts.append(f"Section: {section}")
            if title:
                code_header_parts.append(f"Title: {title}")
            if final_page:
                code_header_parts.append(f"Page: {final_page}")
            
            code_header = " | ".join(code_header_parts)
            code_lines.append(f"{code_header}\n{cd.page_content}")
            
            cites.append({
                "project": None,
                "filename": filename or source,
                "page": final_page,
                "page_number": final_page,
                "file_path": md.get("file_path", ""),
                "title": title or section or source,
                "date": None,
                "source": source,
                "section": section,
                "chunk_index": md.get("chunk_index"),
            })
        
        ctx = ctx + "\n\n" + "\n\n".join(code_lines)

    # Format coop docs (if any)
    if coop_docs:
        coop_lines = []
        coop_lines.append("\n\n### Training Manual References")
        
        for i, cd in enumerate(coop_docs[:MAX_SYNTHESIS_DOCS], 1):
            md = cd.metadata or {}
            filename = md.get("filename", "")
            page = md.get("page", "")
            page_number = md.get("page_number", "")
            file_path = md.get("file_path", "")
            
            final_page = page_number or page
            
            coop_header_parts = [f"[{i}]"]
            if filename:
                coop_header_parts.append(f"Document: {filename}")
            if final_page:
                coop_header_parts.append(f"Page: {final_page}")
            
            coop_header = " | ".join(coop_header_parts)
            coop_lines.append(f"{coop_header}\n{cd.page_content}")
            
            cites.append({
                "project": None,
                "filename": filename,
                "page": final_page,
                "page_number": final_page,
                "file_path": file_path,
                "title": filename,
                "date": None,
                "source": None,
                "section": None,
                "chunk_index": md.get("chunk_index"),
            })
        
        ctx = ctx + "\n\n" + "\n\n".join(coop_lines)

    # Get conversation context for synthesis
    conversation_context = get_conversation_context(session_id, max_exchanges=3)
    
    # Build image context if image results are provided
    image_context = ""
    if image_results and len(image_results) > 0:
        log_query.info(f"🖼️ [SYNTHESIS] Building image context with {len(image_results)} images")
        image_lines = [
            "SIMILAR IMAGES FOUND (if user asked for images, describe these in PLAIN TEXT only):",
            "CRITICAL: Describe each image with project key, page number, and what it shows.",
            "DO NOT include URLs, DO NOT use markdown syntax (![]()), DO NOT format as links.",
            "Just describe them as plain text - the system will display images automatically.",
            ""
        ]
        for i, img in enumerate(image_results[:10], 1):  # Limit to top 10
            proj = img.get('project_key', 'Unknown')
            page_num = img.get('page_number', '?')
            content = img.get('content', '')  # text_verbatim description
            similarity = img.get('similarity', 0)
            # Include project, page, similarity, and description - but NOT the URL
            desc = content[:200] + "..." if len(content) > 200 else content if content else "No description available"
            image_lines.append(f"  [{i}] Project {proj}, Page {page_num} (similarity: {similarity:.2%}): {desc}")
            log_query.info(f"🖼️ [SYNTHESIS]   Image {i}: Project {proj}, Page {page_num}, similarity={similarity:.2%}")
        image_context = "\n".join(image_lines) + "\n\n"
    
    # Build filter context message if filters are active
    filter_context = ""
    if active_filters:
        filter_messages = []
        if active_filters.get('has_revit'):
            filter_messages.append(
                "CRITICAL FILTER INFORMATION: "
                "All projects in the retrieved context have Revit files available (has_revit=true). "
                "The user's query specifically requested projects with Revit files. "
                "You MUST acknowledge this filter and list all projects from the context, "
                "explicitly stating that they all have Revit files available. "
                "Do NOT say that the context doesn't mention Revit - the filter ensures all retrieved projects have Revit files."
            )
        
        if filter_messages:
            filter_context = "\n\n" + "\n\n".join(filter_messages) + "\n\n"

    # Select appropriate prompt based on content type
    if use_coop_prompt:
        prompt_template = COOP_ANSWER_PROMPT
    elif use_code_prompt:
        prompt_template = CODE_ANSWER_PROMPT
    else:
        prompt_template = ANSWER_PROMPT
    
    # Format prompt with categories for project prompts (not code or coop)
    if not use_coop_prompt and not use_code_prompt:
        prompt_kwargs = {
            "q": q,
            "ctx": ctx,
            "conversation_context": (conversation_context or "(No prior conversation)") + filter_context,
            "project_categories": PROJECT_CATEGORIES,
            "image_context": image_context
        }
    else:
        prompt_kwargs = {
            "q": q,
            "ctx": ctx,
            "conversation_context": (conversation_context or "(No prior conversation)") + filter_context,
            "image_context": image_context
        }
    
    total_chunks = len(docs) + (len(code_docs) if code_docs else 0) + (len(coop_docs) if coop_docs else 0)
    prompt_type = "COOP" if use_coop_prompt else ("CODE" if use_code_prompt else "PROJECT")
    print(f"📤 SENDING TO LLM: {total_chunks} chunks | Type: {prompt_type} | Context: {len(ctx)} chars")
    
    if stream:
        def stream_generator():
            first_chunk = True
            for chunk in llm_synthesis.stream(prompt_template.format(**prompt_kwargs)):
                if chunk.content:
                    # Extract text - handles both string and list formats (Gemini 3.0)
                    text_content = extract_text_from_content(chunk.content)
                    if first_chunk:
                        yield (text_content, cites)
                        first_chunk = False
                    else:
                        yield text_content
        return stream_generator()
    else:
        formatted_prompt = prompt_template.format(**prompt_kwargs)
        response = llm_synthesis.invoke(formatted_prompt)
        # Extract text - handles both string and list formats (Gemini 3.0)
        ans = extract_text_from_content(response.content).strip()
        return ans, cites

