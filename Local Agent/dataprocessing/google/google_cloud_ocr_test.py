"""
Google Cloud OCR Script
Extracts verbatim text from images and PDFs using Google Vision API and Document AI API
"""

import os
import json
from pathlib import Path
from google.cloud import vision
from google.cloud import documentai
from google.oauth2 import service_account
import io


def setup_clients(credentials_path):
    """Initialize Google Vision and Document AI clients"""
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path
    )
    
    vision_client = vision.ImageAnnotatorClient(credentials=credentials)
    documentai_client = documentai.DocumentProcessorServiceClient(credentials=credentials)
    
    return vision_client, documentai_client


def extract_text_vision(vision_client, file_path):
    """Extract text using Google Vision API (supports images and PDFs)"""
    try:
        file_path_obj = Path(file_path)
        file_extension = file_path_obj.suffix.lower()
        
        # Handle PDFs
        if file_extension == '.pdf':
            return extract_text_vision_pdf(vision_client, file_path)
        
        # Handle images
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


def extract_text_vision_pdf(vision_client, pdf_path):
    """Extract text from PDF using Google Vision API batch processing, returns pages separately"""
    try:
        with open(pdf_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
        
        # Create a file input config for PDF
        input_config = vision.InputConfig(
            content=pdf_content,
            mime_type='application/pdf'
        )
        
        # Configure the feature to extract text
        feature = vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)
        
        # Create the request
        request = vision.AnnotateFileRequest(
            input_config=input_config,
            features=[feature]
        )
        
        # Process the PDF
        response = vision_client.batch_annotate_files(requests=[request])
        
        if not response.responses:
            return None, "No response from Vision API"
        
        # Extract text from each page separately
        pages = []
        for file_response in response.responses:
            if file_response.error.message:
                return None, f"Error: {file_response.error.message}"
            
            for page_num, page_response in enumerate(file_response.responses, start=1):
                if hasattr(page_response, 'full_text_annotation') and page_response.full_text_annotation:
                    page_text = page_response.full_text_annotation.text
                    pages.append({
                        'page_number': page_num,
                        'text': page_text
                    })
        
        if pages:
            return pages, None
        else:
            return None, "No text detected in PDF"
    
    except Exception as e:
        return None, f"Exception: {str(e)}"


def extract_text_documentai(documentai_client, file_path, project_id, location='us', processor_id=None):
    """
    Extract text using Google Document AI API (supports images and PDFs)
    For PDFs, returns pages separately
    
    Note: For Document AI, you typically need a processor. If processor_id is None,
    this will attempt to use the OCR processor. You may need to create a processor
    in the Google Cloud Console first.
    """
    try:
        # If no processor_id is provided, we'll use the general OCR processor
        # You may need to create a processor in Google Cloud Console and provide its ID
        if processor_id is None:
            # Try to use the default OCR processor
            # Note: You'll need to create a processor in Document AI and provide its full name
            return None, "Document AI requires a processor_id. Please create a processor in Google Cloud Console."
        
        # Read the file
        with open(file_path, 'rb') as file:
            file_content = file.read()
        
        # Determine MIME type based on file extension
        file_path_obj = Path(file_path)
        file_extension = file_path_obj.suffix.lower()
        is_pdf = file_extension == '.pdf'
        
        mime_type = "image/png"  # default
        if is_pdf:
            mime_type = "application/pdf"
        elif file_extension in ['.jpg', '.jpeg']:
            mime_type = "image/jpeg"
        elif file_extension == '.gif':
            mime_type = "image/gif"
        elif file_extension == '.bmp':
            mime_type = "image/bmp"
        elif file_extension == '.tiff':
            mime_type = "image/tiff"
        elif file_extension == '.webp':
            mime_type = "image/webp"
        
        # Prepare the request
        name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"
        
        raw_document = documentai.RawDocument(
            content=file_content,
            mime_type=mime_type
        )
        
        # Enable imageless mode for OCR-only / verbatim text extraction
        # This allows processing up to 30 pages without returning page images
        process_options = documentai.ProcessOptions(
            ocr_config=documentai.OcrConfig(
                enable_image_quality_scores=False  # Disable image quality scores (required for imageless mode)
            )
        )
        
        request = documentai.ProcessRequest(
            name=name,
            raw_document=raw_document,
            process_options=process_options,
            imageless_mode=True  # Enable imageless mode - allows up to 30 pages
        )
        
        # Process the document
        result = documentai_client.process_document(request=request)
        document = result.document
        
        # For PDFs, extract text per page
        if is_pdf and hasattr(document, 'pages') and document.pages:
            pages = []
            full_text = document.text if hasattr(document, 'text') else ""
            
            for page_num, page in enumerate(document.pages, start=1):
                page_text = ""
                
                # Try to extract text using text anchors from page elements
                if hasattr(page, 'paragraphs') and page.paragraphs:
                    text_segments = []
                    for paragraph in page.paragraphs:
                        if hasattr(paragraph, 'layout') and hasattr(paragraph.layout, 'text_anchor'):
                            text_anchor = paragraph.layout.text_anchor
                            if text_anchor and hasattr(text_anchor, 'text_segments'):
                                for segment in text_anchor.text_segments:
                                    if hasattr(segment, 'start_index') and hasattr(segment, 'end_index'):
                                        start_idx = int(segment.start_index)
                                        end_idx = int(segment.end_index)
                                        if start_idx < len(full_text) and end_idx <= len(full_text):
                                            text_segments.append(full_text[start_idx:end_idx])
                    
                    if text_segments:
                        page_text = " ".join(text_segments)
                
                # If we couldn't extract page-specific text, try using blocks
                if not page_text and hasattr(page, 'blocks') and page.blocks:
                    text_segments = []
                    for block in page.blocks:
                        if hasattr(block, 'layout') and hasattr(block.layout, 'text_anchor'):
                            text_anchor = block.layout.text_anchor
                            if text_anchor and hasattr(text_anchor, 'text_segments'):
                                for segment in text_anchor.text_segments:
                                    if hasattr(segment, 'start_index') and hasattr(segment, 'end_index'):
                                        start_idx = int(segment.start_index)
                                        end_idx = int(segment.end_index)
                                        if start_idx < len(full_text) and end_idx <= len(full_text):
                                            text_segments.append(full_text[start_idx:end_idx])
                    
                    if text_segments:
                        page_text = " ".join(text_segments)
                
                # If still no page-specific text, split full text evenly across pages
                if not page_text and full_text:
                    num_pages = len(document.pages)
                    chars_per_page = len(full_text) // num_pages if num_pages > 0 else len(full_text)
                    start_idx = (page_num - 1) * chars_per_page
                    end_idx = page_num * chars_per_page if page_num < num_pages else len(full_text)
                    page_text = full_text[start_idx:end_idx].strip()
                
                pages.append({
                    'page_number': page_num,
                    'text': page_text if page_text else ""
                })
            
            if pages and any(p.get('text', '') for p in pages):
                return pages, None
            else:
                # Fallback to full text if page extraction fails
                return full_text if full_text else None, None
        else:
            # For images or if page extraction fails, return full text
            text = document.text if hasattr(document, 'text') else None
            return text, None
    
    except Exception as e:
        return None, f"Exception: {str(e)}"


def process_images_in_directory(vision_client, documentai_client, directory_path, project_id, processor_id=None):
    """Process all images and PDFs in the directory and extract text using both APIs"""
    
    results = []
    supported_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.pdf'}
    
    # Walk through all subdirectories
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = Path(root) / file
            
            # Check if it's a supported file (image or PDF)
            if file_path.suffix.lower() in supported_extensions:
                file_type = "PDF" if file_path.suffix.lower() == '.pdf' else "Image"
                print(f"\nProcessing {file_type}: {file_path}")
                
                # Extract text using Vision API
                vision_result, vision_error = extract_text_vision(vision_client, str(file_path))
                
                # Extract text using Document AI API
                docai_result, docai_error = extract_text_documentai(
                    documentai_client, str(file_path), project_id, processor_id=processor_id
                )
                
                # Structure result based on file type
                if file_type == 'PDF':
                    # For PDFs, results are page-by-page
                    result = {
                        'file_path': str(file_path),
                        'file_type': file_type,
                        'vision_api': {
                            'pages': vision_result if vision_result and isinstance(vision_result, list) else None,
                            'error': vision_error
                        },
                        'documentai_api': {
                            'pages': docai_result if docai_result and isinstance(docai_result, list) else None,
                            'error': docai_error
                        }
                    }
                    
                    # Print results for PDFs
                    if vision_result and isinstance(vision_result, list):
                        print(f"  Vision API: ✓ Text extracted from {len(vision_result)} pages")
                        for page in vision_result[:3]:  # Show first 3 pages preview
                            page_text = page.get('text', '')[:100] if isinstance(page, dict) else str(page)[:100]
                            print(f"    Page {page.get('page_number', '?')} preview: {page_text}...")
                    else:
                        print(f"  Vision API: ✗ {vision_error}")
                    
                    if docai_result and isinstance(docai_result, list):
                        print(f"  Document AI: ✓ Text extracted from {len(docai_result)} pages")
                        for page in docai_result[:3]:  # Show first 3 pages preview
                            page_text = page.get('text', '')[:100] if isinstance(page, dict) else str(page)[:100]
                            print(f"    Page {page.get('page_number', '?')} preview: {page_text}...")
                    else:
                        print(f"  Document AI: ✗ {docai_error}")
                else:
                    # For images, results are single text
                    result = {
                        'file_path': str(file_path),
                        'file_type': file_type,
                        'vision_api': {
                            'text': vision_result,
                            'error': vision_error
                        },
                        'documentai_api': {
                            'text': docai_result,
                            'error': docai_error
                        }
                    }
                    
                    # Print results for images
                    print(f"  Vision API: {'✓ Text extracted' if vision_result else f'✗ {vision_error}'}")
                    if vision_result:
                        text_preview = vision_result[:200] if len(vision_result) > 200 else vision_result
                        print(f"    Text preview: {text_preview}...")
                    
                    print(f"  Document AI: {'✓ Text extracted' if docai_result else f'✗ {docai_error}'}")
                    if docai_result:
                        text_preview = docai_result[:200] if len(docai_result) > 200 else docai_result
                        print(f"    Text preview: {text_preview}...")
                
                results.append(result)
    
    return results


def save_results(results, output_path):
    """Save extraction results to a JSON file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {output_path}")


def main():
    # Configuration
    credentials_path = r"C:\Users\shine\Testing-2025-01-07\Local Agent\dataprocessing\google\ocr-key.json"
    input_directory = r"C:\Users\shine\Testing-2025-01-07\Local Agent\dataprocessing\google\input_images"
    output_file = r"C:\Users\shine\Testing-2025-01-07\Local Agent\dataprocessing\google\ocr_results.json"
    
    # Load project ID from credentials
    with open(credentials_path, 'r') as f:
        creds_data = json.load(f)
        project_id = creds_data.get('project_id', 'vlm-text-parsing')
    
    # Document AI processor ID
    # Processor: general-purpose-ocr (ID: b308d9a5abe2196, Region: us)
    processor_id = "b308d9a5abe2196"
    
    print("Initializing Google Cloud clients...")
    vision_client, documentai_client = setup_clients(credentials_path)
    
    print(f"Processing images and PDFs in: {input_directory}")
    print("=" * 80)
    
    results = process_images_in_directory(
        vision_client, 
        documentai_client, 
        input_directory, 
        project_id,
        processor_id=processor_id
    )
    
    print("\n" + "=" * 80)
    print(f"Processing complete! Processed {len(results)} files.")
    
    # Save results
    save_results(results, output_file)
    
    # Print summary
    vision_success = sum(1 for r in results if (
        (r['file_type'] == 'Image' and r['vision_api'].get('text')) or
        (r['file_type'] == 'PDF' and r['vision_api'].get('pages'))
    ))
    docai_success = sum(1 for r in results if (
        (r['file_type'] == 'Image' and r['documentai_api'].get('text')) or
        (r['file_type'] == 'PDF' and r['documentai_api'].get('pages'))
    ))
    
    # Count by file type
    pdf_count = sum(1 for r in results if r['file_type'] == 'PDF')
    image_count = sum(1 for r in results if r['file_type'] == 'Image')
    vision_pdf_success = sum(1 for r in results if r['file_type'] == 'PDF' and r['vision_api'].get('pages'))
    vision_image_success = sum(1 for r in results if r['file_type'] == 'Image' and r['vision_api'].get('text'))
    
    # Count total pages extracted
    total_vision_pages = sum(
        len(r['vision_api'].get('pages', [])) 
        for r in results 
        if r['file_type'] == 'PDF' and r['vision_api'].get('pages')
    )
    total_docai_pages = sum(
        len(r['documentai_api'].get('pages', [])) 
        for r in results 
        if r['file_type'] == 'PDF' and r['documentai_api'].get('pages')
    )
    
    print(f"\nSummary:")
    print(f"  Total files processed: {len(results)} ({image_count} images, {pdf_count} PDFs)")
    print(f"  Vision API: {vision_success}/{len(results)} successful ({vision_image_success}/{image_count} images, {vision_pdf_success}/{pdf_count} PDFs)")
    if total_vision_pages > 0:
        print(f"    Total pages extracted (Vision): {total_vision_pages}")
    print(f"  Document AI: {docai_success}/{len(results)} successful")
    if total_docai_pages > 0:
        print(f"    Total pages extracted (Document AI): {total_docai_pages}")


if __name__ == "__main__":
    main()

