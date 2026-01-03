// Backend API Configuration
const AWS_URL = 'https://2x3dnm2tb3.us-east-1.awsapprunner.com';
const RENDER_URL = 'https://rag-waddell.onrender.com'; // Backup
const LOCAL_URL = 'http://localhost:8000';

// Use LOCAL backend for testing, will switch to AWS_URL for production
let BACKEND_URL = AWS_URL;

// Session Management Functions
function getOrCreateSessionId() {
  let sessionId = localStorage.getItem('session_id');
  
  if (!sessionId) {
    // Generate unique session ID
    sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9);
    localStorage.setItem('session_id', sessionId);
    localStorage.setItem('session_created', Date.now().toString());
    console.log(`Created new session: ${sessionId}`);
  }
  
  return sessionId;
}

// Get user identifier from localStorage
function getUserIdentifier() {
  return localStorage.getItem('user_identifier') || null;
}

const bubble = document.getElementById('bubble');
const panel = document.getElementById('panel');
const messages = document.getElementById('messages');
const form = document.getElementById('form');
const input = document.getElementById('input');
const sendBtn = document.getElementById('sendBtn');

let currentMessageId = 0;
let currentUserMessage = '';

// Query history tracking (kept for potential future use)
let queryHistory = [];

// Image attachment state - now supports multiple images
let pendingImageAttachments = [];  // Array of { fileName, base64, preview }

// Image attachment handling
const attachBtn = document.getElementById('attachBtn');
const imageInput = document.getElementById('imageInput');
const attachmentPreview = document.getElementById('attachmentPreview');

/**
 * Smart resize for images - only shrinks large images, never upscales.
 * Uses PNG format to preserve text sharpness (important for engineering drawings).
 * @param {File} file - The image file to process
 * @param {number} maxDimension - Maximum width or height (default 2048px)
 * @returns {Promise<{base64: string, preview: string, wasResized: boolean, originalSize: string, newSize: string}>}
 */
function resizeImageIfNeeded(file, maxDimension = 2048) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    
    img.onload = () => {
      try {
        let width = img.width;
        let height = img.height;
        const originalSize = `${width}×${height}`;
        let wasResized = false;
        
        // Only resize if larger than max dimension (never upscale)
        if (width > maxDimension || height > maxDimension) {
          const ratio = Math.min(maxDimension / width, maxDimension / height);
          width = Math.round(width * ratio);
          height = Math.round(height * ratio);
          wasResized = true;
        }
        
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, width, height);
        
        // Use PNG to preserve text sharpness (not JPEG - would blur text)
        const dataUrl = canvas.toDataURL('image/png');
        const base64Data = dataUrl.split(',')[1];
        
        // Cleanup
        URL.revokeObjectURL(img.src);
        
        resolve({
          base64: base64Data,
          preview: dataUrl,
          wasResized: wasResized,
          originalSize: originalSize,
          newSize: `${width}×${height}`
        });
      } catch (err) {
        reject(err);
      }
    };
    
    img.onerror = (err) => {
      console.error('Failed to load image:', err);
      reject(new Error('Failed to load image'));
    };
    
    img.src = URL.createObjectURL(file);
  });
}

async function handleImageFile(file) {
  console.log('🖼️ handleImageFile called:', file?.name, file?.type, file?.size);
  
  // Validate file exists
  if (!file) {
    console.error('No file provided');
    return;
  }
  
  // Validate file type - accept any image
  if (!file.type.startsWith('image/')) {
    console.error('Invalid file type:', file.type);
    alert('Please select an image file (PNG, JPG, GIF, etc.)');
    return;
  }

  // Validate file size (max 20MB before resize)
  const maxSize = 20 * 1024 * 1024;
  if (file.size > maxSize) {
    alert('Image too large. Maximum size is 20MB.');
    return;
  }
  
  // Limit to 5 images max
  if (pendingImageAttachments.length >= 5) {
    alert('Maximum 5 images allowed. Remove some to add more.');
    return;
  }

  try {
    console.log('🖼️ Processing image...');
    
    // Resize if needed (only shrinks large images, preserves small ones)
    const result = await resizeImageIfNeeded(file, 2048);
    
    console.log('🖼️ Resize complete:', result.wasResized ? 'resized' : 'unchanged');
    
    // Add to array instead of replacing
    pendingImageAttachments.push({
      fileName: file.name || 'image.png',
      base64: result.base64,
      preview: result.preview
    });
    
    console.log('🖼️ Calling updateAttachmentPreview...');
    updateAttachmentPreview();
    console.log('🖼️ Preview updated, attachment count:', pendingImageAttachments.length);
    
    // Log with resize info
    const sizeKB = Math.round((result.base64.length * 3/4) / 1024);
    if (result.wasResized) {
      console.log(`✅ Image attached: ${file.name} (resized ${result.originalSize} → ${result.newSize}, ${sizeKB}KB)`);
    } else {
      console.log(`✅ Image attached: ${file.name} (${result.newSize}, ${sizeKB}KB)`);
    }
  } catch (err) {
    console.error('❌ Error processing image with resize, trying direct method:', err);
    
    // Fallback: read file directly without resize
    try {
      const reader = new FileReader();
      reader.onload = (e) => {
        const dataUrl = e.target.result;
        pendingImageAttachments.push({
          fileName: file.name || 'image.png',
          base64: dataUrl.split(',')[1],
          preview: dataUrl
        });
        updateAttachmentPreview();
        console.log('✅ Image attached (fallback method):', file.name);
      };
      reader.onerror = () => {
        console.error('❌ FileReader also failed');
        alert('Error processing image. Please try again.');
      };
      reader.readAsDataURL(file);
    } catch (fallbackErr) {
      console.error('❌ All image processing failed:', fallbackErr);
      alert('Error processing image. Please try again.');
    }
  }
}

function updateAttachmentPreview() {
  if (!attachmentPreview) {
    console.warn('attachmentPreview element not found');
    return;
  }
  
  if (pendingImageAttachments.length > 0) {
    // Build HTML for all attached images
    const itemsHtml = pendingImageAttachments.map((attachment, index) => `
      <div class="attachment-item">
        <img src="${attachment.preview}" alt="Preview" class="attachment-thumbnail">
        <span class="attachment-name">${attachment.fileName}</span>
        <button type="button" class="attachment-remove" onclick="removeAttachment(${index})">×</button>
      </div>
    `).join('');
    
    attachmentPreview.innerHTML = itemsHtml;
    attachmentPreview.classList.add('has-attachment');
    if (attachBtn) attachBtn.classList.add('has-attachment');
  } else {
    attachmentPreview.innerHTML = '';
    attachmentPreview.classList.remove('has-attachment');
    if (attachBtn) attachBtn.classList.remove('has-attachment');
  }
}

function removeAttachment(index) {
  if (typeof index === 'number' && index >= 0 && index < pendingImageAttachments.length) {
    const removed = pendingImageAttachments.splice(index, 1);
    console.log('Attachment removed:', removed[0]?.fileName);
  } else {
    // Clear all if no index provided (backwards compatibility)
    pendingImageAttachments = [];
    console.log('All attachments removed');
  }
  updateAttachmentPreview();
}

// Make removeAttachment available globally for onclick
window.removeAttachment = removeAttachment;

// Attach button click handler (with null check)
if (attachBtn && imageInput) {
  attachBtn.addEventListener('click', () => {
    imageInput.click();
  });

  // File input change handler - accept multiple images
  imageInput.addEventListener('change', async (e) => {
    if (e.target.files.length > 0) {
      // Process all selected files
      for (const file of e.target.files) {
        await handleImageFile(file);
      }
      imageInput.value = '';  // Reset input for re-selection
    }
  });
} else {
  console.warn('Image attachment elements not found in DOM');
}

// ============================================================
// CLIPBOARD PASTE SUPPORT (Ctrl+V / Cmd+V for screenshots)
// ============================================================
document.addEventListener('paste', (e) => {
  const items = e.clipboardData?.items;
  if (!items) return;
  
  for (let i = 0; i < items.length; i++) {
    if (items[i].type.startsWith('image/')) {
      e.preventDefault();
      const file = items[i].getAsFile();
      if (file) {
        // Give pasted screenshots a meaningful name
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        const namedFile = new File([file], `screenshot-${timestamp}.png`, { type: file.type });
        handleImageFile(namedFile);
        console.log('📋 Image pasted from clipboard');
      }
      break;
    }
  }
});

// ============================================================
// DRAG AND DROP SUPPORT (on entire panel, not just input)
// ============================================================
const dropZone = document.getElementById('panel');
let dragCounter = 0;  // Track nested drag events

if (dropZone) {
  dropZone.addEventListener('dragenter', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter++;
    dropZone.classList.add('drag-over');
  });

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.stopPropagation();
  });

  dropZone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter--;
    if (dragCounter === 0) {
      dropZone.classList.remove('drag-over');
    }
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter = 0;
    dropZone.classList.remove('drag-over');
    
    const files = e.dataTransfer?.files;
    if (files && files.length > 0) {
      // Find first image file
      for (let i = 0; i < files.length; i++) {
        if (files[i].type.startsWith('image/')) {
          handleImageFile(files[i]);
          console.log('📁 Image dropped:', files[i].name);
          break;
        }
      }
    }
  });
}

function generateMessageId() {
  return `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

function formatMessageText(text) {
  // Convert markdown-style formatting to HTML
  let formatted = text;

  // ========== LaTeX MATH BLOCK PROCESSING ==========
  // Extract and process LaTeX math blocks BEFORE HTML escaping
  // This handles \( ... \) for inline math and \[ ... \] for display math
  
  const latexMathPlaceholders = [];
  
  // Function to convert LaTeX notation to HTML (for use inside math blocks)
  function convertLatexToHTML(latexContent) {
    let converted = latexContent;
    
    // Handle fractions: \frac{numerator}{denominator} → HTML fraction
    // Use a more robust pattern that handles nested braces
    converted = converted.replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, function(match, numerator, denominator) {
      // Recursively process numerator and denominator for nested subscripts/superscripts
      const numProcessed = convertLatexToHTML(numerator);
      const denProcessed = convertLatexToHTML(denominator);
      return `<span class="math-fraction"><span class="math-numerator">${numProcessed}</span><span class="math-denominator">${denProcessed}</span></span>`;
    });
    
    // Handle multiplication dots: \cdot → ·
    converted = converted.replace(/\\cdot/g, '·');
    
    // Handle multi-character subscripts with braces: _{xy} → <sub>xy</sub>
    converted = converted.replace(/_\{(.+?)\}/g, '<sub>$1</sub>');
    
    // Handle multi-character superscripts with braces: ^{xy} → <sup>xy</sup>
    converted = converted.replace(/\^\{(.+?)\}/g, '<sup>$1</sup>');
    
    // Handle single-character subscripts: _x → <sub>x</sub>
    // Only process if followed by non-letter or end of string (avoid breaking other patterns)
    converted = converted.replace(/([A-Za-z0-9])_([A-Za-z0-9])(?![A-Za-z0-9_])/g, '$1<sub>$2</sub>');
    
    // Handle single-character superscripts: ^2 → <sup>2</sup>
    converted = converted.replace(/([A-Za-z0-9])\^([0-9A-Za-z])(?![A-Za-z0-9^])/g, '$1<sup>$2</sup>');
    
    return converted;
  }
  
  // Extract inline math: \( ... \)
  // Match literal backslash-paren sequences - use non-greedy match until \)
  formatted = formatted.replace(/\\\(([\s\S]*?)\\\)/g, function(match, mathContent, offset) {
    const placeholder = `__LATEX_INLINE_${latexMathPlaceholders.length}__`;
    const converted = convertLatexToHTML(mathContent);
    latexMathPlaceholders.push({ type: 'inline', content: converted });
    return placeholder;
  });
  
  // Extract display math: \[ ... \]
  // Match literal backslash-bracket sequences - use non-greedy match until \]
  formatted = formatted.replace(/\\\[([\s\S]*?)\\\]/g, function(match, mathContent, offset) {
    const placeholder = `__LATEX_DISPLAY_${latexMathPlaceholders.length}__`;
    const converted = convertLatexToHTML(mathContent);
    latexMathPlaceholders.push({ type: 'display', content: converted });
    return placeholder;
  });

  // Extract and preserve fully-formed HTML links from backend before HTML escaping
  // Backend now sends fully-formed HTML links, so we just need to preserve them
  const linkPlaceholders = [];
  
  // Extract folder-link HTML elements (class="folder-link")
  // Use [\s\S] instead of . to match newlines as well
  formatted = formatted.replace(/<a\s+href="#"\s+class="folder-link"[\s\S]*?<\/a>/g, (match) => {
    const placeholder = `__LINK_${linkPlaceholders.length}__`;
    linkPlaceholders.push(match); // Store the full HTML link
    return placeholder;
  });
  
  // Extract file-link HTML elements (class="file-link")
  // Use [\s\S] instead of . to match newlines as well
  formatted = formatted.replace(/<a\s+href="#"\s+class="file-link"[\s\S]*?<\/a>/g, (match) => {
    const placeholder = `__LINK_${linkPlaceholders.length}__`;
    linkPlaceholders.push(match); // Store the full HTML link
    return placeholder;
  });
  
  // Also handle legacy tag format for backward compatibility (if backend still sends tags)
  const folderLinkPlaceholders = [];
  formatted = formatted.replace(/<folder-link>(.*?)<\/folder-link>/g, (_match, projectNumber) => {
    const placeholder = `__FOLDER_LINK_${folderLinkPlaceholders.length}__`;
    folderLinkPlaceholders.push(projectNumber);
    return placeholder;
  });

  const fileLinkPlaceholders = [];
  formatted = formatted.replace(/<file-link\s+data-path="([^"]+)"(?:\s+data-page="([^"]+)")?>(.*?)<\/file-link>/g, (_match, filePath, pageNumber, fileName) => {
    const placeholder = `__FILE_LINK_${fileLinkPlaceholders.length}__`;
    // Decode HTML entities in file path (backend already escaped them)
    const decodedFilePath = filePath
      .replace(/&amp;/g, '&')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>');
    fileLinkPlaceholders.push({ filePath: decodedFilePath, pageNumber: pageNumber || null, fileName });
    return placeholder;
  });

  // Escape HTML to prevent XSS
  formatted = formatted
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Restore LaTeX math blocks (AFTER HTML escaping, BEFORE other formatting)
  // Note: mathData.content is already converted to HTML (with <sub> and <sup> tags)
  // and stored in the array, so it doesn't get escaped. We can insert it directly.
  latexMathPlaceholders.forEach((mathData, index) => {
    const inlinePlaceholder = `__LATEX_INLINE_${index}__`;
    const displayPlaceholder = `__LATEX_DISPLAY_${index}__`;
    
    if (mathData.type === 'inline') {
      // Content is already HTML, insert directly
      formatted = formatted.replace(inlinePlaceholder, `<span class="math-inline">${mathData.content}</span>`);
    } else if (mathData.type === 'display') {
      // Content is already HTML, insert directly
      formatted = formatted.replace(displayPlaceholder, `<div class="math-display">${mathData.content}</div>`);
    }
  });

  // Restore fully-formed HTML links from backend (already in correct format)
  linkPlaceholders.forEach((htmlLink, index) => {
    const placeholder = `__LINK_${index}__`;
    formatted = formatted.replace(placeholder, htmlLink);
  });

  // Restore legacy folder links (backward compatibility - if backend still sends tags)
  folderLinkPlaceholders.forEach((projectNumber, index) => {
    const placeholder = `__FOLDER_LINK_${index}__`;
    const networkPath = `\\\\WADDELLNAS\\Projects\\${projectNumber}`;
    formatted = formatted.replace(
      placeholder,
      `<a href="#" class="folder-link" data-path="${networkPath}" data-project="${projectNumber}" title="Left-click: Open in Explorer | Right-click: Open in Harmani">${projectNumber}</a>`
    );
  });

  // Restore legacy file links (backward compatibility - if backend still sends tags)
  fileLinkPlaceholders.forEach((linkData, index) => {
    const placeholder = `__FILE_LINK_${index}__`;
    const { filePath, pageNumber, fileName } = linkData;
    const title = pageNumber 
      ? `Click to open file at page ${pageNumber}` 
      : `Click to open file`;
    
    // HTML-escape the file path for the attribute
    const escapedFilePath = filePath
      .replace(/&/g, '&amp;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    
    const dataAttrs = pageNumber 
      ? `data-path="${escapedFilePath}" data-page="${pageNumber}"`
      : `data-path="${escapedFilePath}"`;
    formatted = formatted.replace(
      placeholder,
      `<a href="#" class="file-link" ${dataAttrs} title="${title}">${fileName}</a>`
    );
  });

  // Convert **bold** to <strong>
  formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

  // ========== LaTeX COMMANDS IN REGULAR TEXT ==========
  // Handle LaTeX commands that might appear outside of math blocks
  // This handles cases where formulas appear without \( \) or \[ \] delimiters
  
  // Handle fractions in regular text: \frac{numerator}{denominator}
  formatted = formatted.replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, function(match, numerator, denominator, offset) {
    // Skip if inside HTML tags or citations
    if (isInsideHTMLTag(formatted, offset) || isInsideCitation(formatted, offset)) {
      return match;
    }
    // Process numerator and denominator for subscripts/superscripts
    const numProcessed = convertLatexToHTML(numerator);
    const denProcessed = convertLatexToHTML(denominator);
    return `<span class="math-fraction"><span class="math-numerator">${numProcessed}</span><span class="math-denominator">${denProcessed}</span></span>`;
  });
  
  // Handle multiplication dots in regular text: \cdot → ·
  formatted = formatted.replace(/\\cdot/g, function(match, offset) {
    if (isInsideHTMLTag(formatted, offset) || isInsideCitation(formatted, offset)) {
      return match;
    }
    return '·';
  });

  // ========== MATHEMATICAL NOTATION FORMATTING ==========
  // Process equations with subscripts and superscripts BEFORE other formatting
  // This must be done before italic formatting to avoid underscore conflicts
  
  // Helper function to check if position is inside HTML tag
  function isInsideHTMLTag(text, pos) {
    const before = text.substring(0, pos);
    const lastOpenTag = before.lastIndexOf('<');
    const lastCloseTag = before.lastIndexOf('>');
    return lastOpenTag > lastCloseTag;
  }
  
  // Helper function to check if position is inside citation
  function isInsideCitation(text, pos) {
    const before = text.substring(0, pos);
    const lastOpenBracket = before.lastIndexOf('[');
    const lastCloseBracket = before.lastIndexOf(']');
    // Check if we're inside [Document: ...] or [CIT ...]
    if (lastOpenBracket > lastCloseBracket) {
      const citationText = before.substring(lastOpenBracket);
      return citationText.includes('Document:') || citationText.includes('CIT');
    }
    return false;
  }
  
  // Step 1: Handle explicit LaTeX curly brace notation (safest - highest priority)
  // K_{zt} → K<sub>zt</sub>
  formatted = formatted.replace(/_\{([^}]+)\}/g, '<sub>$1</sub>');
  // x^{2} → x<sup>2</sup>
  formatted = formatted.replace(/\^\{([^}]+)\}/g, '<sup>$1</sup>');
  
  // Step 2: Handle curly brace notation without underscore: K{zt} → K<sub>zt</sub>
  // Pattern: Single letter followed by {alphanumeric} - common engineering notation
  formatted = formatted.replace(/\b([A-Za-z])\{([A-Za-z0-9]{1,6})\}/g, function(match, base, content, offset) {
    if (isInsideHTMLTag(formatted, offset) || isInsideCitation(formatted, offset)) {
      return match;
    }
    return base + '<sub>' + content + '</sub>';
  });
  
  // Step 3: Handle superscripts with caret: V^2 → V<sup>2</sup>, qz^2 → qz<sup>2</sup>
  // Pattern: alphanumeric^digit or alphanumeric^short text
  formatted = formatted.replace(/([A-Za-z0-9])\^([0-9A-Za-z]{1,3})(?![A-Za-z0-9^])/g, function(match, base, exp, offset) {
    if (isInsideHTMLTag(formatted, offset) || isInsideCitation(formatted, offset)) {
      return match;
    }
    return base + '<sup>' + exp + '</sup>';
  });
  
  // Step 4: Handle subscripts with underscore in mathematical contexts
  // F_b → F<sub>b</sub>, q_z → q<sub>z</sub>
  // Only process when clearly in math context to avoid breaking italic formatting
  formatted = formatted.replace(/([A-Za-z0-9])_([a-z0-9]{1,3})(?=\s*[=<>≤≥+\-*/^()\[\]{}:;,]|\s|$|[,\])}])/g, function(match, base, sub, offset) {
    if (isInsideHTMLTag(formatted, offset) || isInsideCitation(formatted, offset)) {
      return match;
    }
    
    // Check context - only process in mathematical contexts
    const contextBefore = formatted.substring(Math.max(0, offset - 40), offset);
    const contextAfter = formatted.substring(offset + match.length, Math.min(formatted.length, offset + match.length + 15));
    
    // Skip if it looks like italic formatting (has spaces around, no math operators)
    const hasSpacesAround = contextBefore.endsWith(' ') || contextAfter.startsWith(' ');
    const hasMathNearby = /[=<>≤≥+\-*/^()\[\]{}:;,]/.test(contextBefore + contextAfter);
    const isInEquation = contextAfter.match(/^\s*[=<>≤≥+\-*/^()\[\]{}:;,]/) || 
                        contextBefore.match(/[=<>≤≥+\-*/^()\[\]{}:;,]\s*$/);
    
    // Process if: has math operators nearby OR is in equation context
    // BUT skip if has spaces and no math (likely italic text)
    if (hasSpacesAround && !hasMathNearby && !isInEquation) {
      return match; // Probably italic text, not math
    }
    
    if (hasMathNearby || isInEquation) {
      return base + '<sub>' + sub + '</sub>';
    }
    
    return match;
  });
  
  // Step 5: Handle common engineering variables in equations: Fb = 0.66 → F<sub>b</sub> = 0.66
  // Pattern: Capital letter + lowercase letter, followed by = and number
  // Common variables: F, q, K, V, E, I, A, P, M, T, S, D, C, R, L, N, W, H, B, G, Y, X, Z
  formatted = formatted.replace(/\b([A-Z])([a-z])(?=\s*=\s*[0-9.])/g, function(match, capital, lower, offset) {
    if (isInsideHTMLTag(formatted, offset) || isInsideCitation(formatted, offset)) {
      return match;
    }
    // Common engineering variable prefixes
    const commonVars = ['F', 'q', 'K', 'V', 'E', 'I', 'A', 'P', 'M', 'T', 'S', 'D', 'C', 'R', 'L', 'N', 'W', 'H', 'B', 'G', 'Y', 'X', 'Z'];
    if (commonVars.includes(capital)) {
      return capital + '<sub>' + lower + '</sub>';
    }
    return match;
  });
  
  // Step 6: Handle multi-character subscripts in equations: Kzt = → K<sub>zt</sub> = (when clearly in equation)
  // Only process when followed immediately by = and number (very safe pattern)
  formatted = formatted.replace(/\b([A-Z])([a-z]{2,3})(?=\s*=\s*[0-9.])/g, function(match, capital, sub, offset) {
    if (isInsideHTMLTag(formatted, offset) || isInsideCitation(formatted, offset)) {
      return match;
    }
    // Only process common engineering variables in equation context
    const commonVars = ['K', 'V', 'E', 'I', 'A', 'P', 'M', 'T', 'S', 'D', 'C', 'R', 'L', 'N', 'W', 'H', 'B', 'G', 'Y', 'X', 'Z'];
    if (commonVars.includes(capital)) {
      return capital + '<sub>' + sub + '</sub>';
    }
    return match;
  });

  // Convert markdown headers to HTML headers (do this BEFORE splitting into lines)
  // Handle ## (h2) headers
  formatted = formatted.replace(/^##\s+(.+)$/gm, '<h2 class="markdown-header">$1</h2>');
  // Handle ### (h3) headers
  formatted = formatted.replace(/^###\s+(.+)$/gm, '<h3 class="markdown-header">$1</h3>');
  // Handle #### (h4) headers
  formatted = formatted.replace(/^####\s+(.+)$/gm, '<h4 class="markdown-header">$1</h4>');

  // Convert [CIT X] citations to styled spans (before lists to avoid breaking them)
  formatted = formatted.replace(/\[CIT\s+(\d+)\]/g, '<span class="citation">[CIT $1]</span>');

  // Split into lines for better list processing
  const lines = formatted.split('\n');
  const processedLines = [];
  let inList = false;
  let currentList = [];
  let listType = null;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    // Skip empty lines and already processed headers
    if (!line || line.startsWith('<h')) {
      if (inList) {
        // Close the list
        processedLines.push(listType === 'ol'
          ? `<ol class="formatted-list">${currentList.join('')}</ol>`
          : `<ul class="formatted-list">${currentList.join('')}</ul>`);
        currentList = [];
        inList = false;
        listType = null;
      }
      if (line) {
        processedLines.push(line);
      }
      continue;
    }

    // Check if this is a numbered list item
    const numberedMatch = line.match(/^(\d+)\.\s+(.*)$/);
    // Check if this is a bullet list item
    const bulletMatch = line.match(/^[\-\*]\s+(.*)$/);

    if (numberedMatch) {
      if (!inList || listType !== 'ol') {
        if (inList) {
          // Close previous list
          processedLines.push(listType === 'ol'
            ? `<ol class="formatted-list">${currentList.join('')}</ol>`
            : `<ul class="formatted-list">${currentList.join('')}</ul>`);
          currentList = [];
        }
        inList = true;
        listType = 'ol';
      }
      // Use the actual number from the markdown with the value attribute
      currentList.push(`<li value="${numberedMatch[1]}">${numberedMatch[2]}</li>`);
    } else if (bulletMatch) {
      if (!inList || listType !== 'ul') {
        if (inList) {
          // Close previous list
          processedLines.push(listType === 'ol'
            ? `<ol class="formatted-list">${currentList.join('')}</ol>`
            : `<ul class="formatted-list">${currentList.join('')}</ul>`);
          currentList = [];
        }
        inList = true;
        listType = 'ul';
      }
      currentList.push(`<li>${bulletMatch[1]}</li>`);
    } else {
      if (inList) {
        // Close the list
        processedLines.push(listType === 'ol'
          ? `<ol class="formatted-list">${currentList.join('')}</ol>`
          : `<ul class="formatted-list">${currentList.join('')}</ul>`);
        currentList = [];
        inList = false;
        listType = null;
      }
      processedLines.push(line);
    }
  }

  // Close any remaining list
  if (inList) {
    processedLines.push(listType === 'ol'
      ? `<ol class="formatted-list">${currentList.join('')}</ol>`
      : `<ul class="formatted-list">${currentList.join('')}</ul>`);
  }

  formatted = processedLines.join('<br>');

  // Convert double breaks to paragraph spacing
  formatted = formatted.replace(/(<br>){2,}/g, '<br><br>');

  // Convert _italic_ text (from route/citations info)
  formatted = formatted.replace(/_(.+?)_/g, '<em>$1</em>');

  return formatted;
}

function addMessage(text, who = 'bot', messageId = null, userQuestion = null) {
  const el = document.createElement('div');
  el.className = 'msg ' + who;

  if (who === 'bot') {
    const msgId = messageId || generateMessageId();
    el.setAttribute('data-message-id', msgId);

    // Create message content wrapper
    const contentDiv = document.createElement('div');
    contentDiv.className = 'msg-content';

    // Format the text with proper HTML rendering
    contentDiv.innerHTML = formatMessageText(text);
    el.appendChild(contentDiv);

    // Create feedback container
    const feedbackDiv = document.createElement('div');
    feedbackDiv.className = 'feedback-container';
    feedbackDiv.innerHTML = `
      <div class="feedback-buttons">
        <button class="feedback-btn thumbs-up" title="Good response" data-rating="positive">👍</button>
        <button class="feedback-btn thumbs-down" title="Poor response" data-rating="negative">👎</button>
      </div>
      <div class="feedback-status" style="display: none;"></div>
    `;
    el.appendChild(feedbackDiv);

    // Add click handlers for feedback buttons
    const thumbsUp = feedbackDiv.querySelector('.thumbs-up');
    const thumbsDown = feedbackDiv.querySelector('.thumbs-down');

    thumbsUp.addEventListener('click', () => handleFeedback(msgId, 'positive', text, userQuestion));
    thumbsDown.addEventListener('click', () => handleFeedback(msgId, 'negative', text, userQuestion));

    // Add click handlers for folder links
    const folderLinks = contentDiv.querySelectorAll('.folder-link');
    console.log(`📎 Found ${folderLinks.length} folder links in message`);

    folderLinks.forEach((link, index) => {
      const projectNumber = link.textContent;
      const folderPath = link.getAttribute('data-path');
      console.log(`  Link ${index + 1}: ${projectNumber} -> ${folderPath}`);

      // Left click - open in Explorer
      link.addEventListener('click', (e) => {
        e.preventDefault();
        console.log('=== FOLDER LINK LEFT CLICKED ===');
        console.log(`Project: ${projectNumber}`);
        console.log(`Path: ${folderPath}`);
        console.log(`window.mantle exists: ${!!window.mantle}`);
        console.log(`window.mantle.openFolder exists: ${!!(window.mantle && window.mantle.openFolder)}`);

        // Call Electron IPC to open the network folder
        if (window.mantle && window.mantle.openFolder) {
          console.log('✅ Calling window.mantle.openFolder()');
          window.mantle.openFolder(folderPath)
            .then(result => {
              console.log('Folder open result:', result);
              if (result && !result.success) {
                console.error('Failed to open folder:', result.error);
              }
            })
            .catch(err => {
              console.error('Error calling openFolder:', err);
            });
        } else {
          console.error('❌ Folder opening not available - mantle.openFolder not found');
          console.error('Available window properties:', Object.keys(window));
        }
      });

      // Right click - open in Harmani directly
      link.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        console.log('=== FOLDER LINK RIGHT CLICKED ===');
        console.log(`Project: ${projectNumber}`);
        console.log(`window.mantle exists: ${!!window.mantle}`);
        console.log(`window.mantle.openHarmani exists: ${!!(window.mantle && window.mantle.openHarmani)}`);

        // Call Electron IPC to open Harmani
        if (window.mantle && window.mantle.openHarmani) {
          console.log('✅ Calling window.mantle.openHarmani()');
          window.mantle.openHarmani(projectNumber)
            .then(result => {
              console.log('Harmani open result:', result);
              if (result && !result.success) {
                console.error('Failed to open Harmani:', result.error);
              }
            })
            .catch(err => {
              console.error('Error calling openHarmani:', err);
            });
        } else {
          console.error('❌ Harmani opening not available - mantle.openHarmani not found');
          console.error('Available window properties:', Object.keys(window));
        }
      });
    });

    // Add click handlers for file links
    try {
      const fileLinks = contentDiv.querySelectorAll('.file-link');
      console.log(`📄 Found ${fileLinks.length} file links in message`);

      fileLinks.forEach((link, index) => {
        try {
          const fileName = link.textContent;
          const filePath = link.getAttribute('data-path');
          const pageNumber = link.getAttribute('data-page');
          console.log(`  File link ${index + 1}: ${fileName} -> ${filePath}${pageNumber ? ` (page ${pageNumber})` : ''}`);
          
          // Log detailed path information for debugging
          console.log(`  📋 File Link ${index + 1} Details:`);
          console.log(`     - File Name: "${fileName}"`);
          console.log(`     - File Path (raw from attribute): "${filePath}"`);
          console.log(`     - File Path (length): ${filePath ? filePath.length : 0} characters`);
          console.log(`     - File Path (starts with): ${filePath ? (filePath.startsWith('\\\\') ? '\\\\ (UNC path)' : filePath.substring(0, 20)) : 'N/A'}`);
          console.log(`     - Page Number: ${pageNumber || 'None'}`);
          if (filePath) {
            // Show path breakdown
            const pathParts = filePath.split('\\');
            console.log(`     - Path parts: ${pathParts.length} segments`);
            console.log(`     - First segment: "${pathParts[0]}"`);
            if (pathParts.length > 1) {
              console.log(`     - Second segment: "${pathParts[1]}"`);
            }
            // Check for special characters
            if (filePath.includes('&')) {
              console.log(`     - ⚠️ Contains '&' character`);
            }
            if (filePath.includes(' ')) {
              console.log(`     - ⚠️ Contains spaces`);
            }
          }

          // Click - open file (with page number if available)
          link.addEventListener('click', (e) => {
            try {
              e.preventDefault();
              console.log('=== FILE LINK CLICKED ===');
              console.log(`📁 File Name: "${fileName}"`);
              console.log(`📍 File Path: "${filePath}"`);
              console.log(`📏 Path Length: ${filePath ? filePath.length : 0} characters`);
              console.log(`📄 Page Number: ${pageNumber || 'None'}`);
              console.log(`🔗 Path that will be sent to Electron:`);
              console.log(`   "${filePath}"`);
              console.log(`   (Type: ${typeof filePath})`);
              console.log(`window.mantle exists: ${!!window.mantle}`);
              console.log(`window.mantle.openFile exists: ${!!(window.mantle && window.mantle.openFile)}`);

              // Call Electron IPC to open the file directly (no confirm dialog)
              if (window.mantle && window.mantle.openFile) {
                console.log('✅ Calling window.mantle.openFile() with path:', filePath, 'page:', pageNumber || 'none');
                window.mantle.openFile(filePath, pageNumber)
                  .then(result => {
                    console.log('📊 File open result:', JSON.stringify(result, null, 2));
                    if (result && !result.success) {
                      console.error('❌ Failed to open file:', result.error);
                      console.error(`   Path: ${filePath}`);
                      console.error(`   Error: ${result.error || 'Unknown error'}`);
                    } else if (result && pageNumber && !result.page_supported) {
                      console.log('⚠️ File opened but page number not supported by default viewer');
                      console.log(`   Path: ${filePath}`);
                      console.log(`   Page: ${pageNumber}`);
                    } else if (result && result.success) {
                      console.log('✅ File opened successfully!');
                      console.log(`   Path: ${filePath}`);
                      console.log(`   Page: ${pageNumber || 'None'}`);
                      console.log(`   Method used: ${result.method || 'unknown'}`);
                      console.log(`   Page supported: ${result.page_supported !== false ? 'Yes' : 'No'}`);
                    }
                  })
                  .catch(err => {
                    console.error('❌ Error calling openFile:', err);
                    console.error(`   Path: ${filePath}`);
                    console.error(`   Page: ${pageNumber || 'None'}`);
                    console.error(`   Error: ${err.message || 'Unknown error'}`);
                  });
              } else {
                console.error('❌ File opening not available - mantle.openFile not found');
                console.error('Available window properties:', Object.keys(window));
              }
            } catch (err) {
              console.error('❌ Error handling file link click:', err);
              // Don't break the page if file link handling fails
            }
          });
        } catch (err) {
          console.error(`❌ Error setting up file link ${index + 1}:`, err);
          // Continue processing other links even if one fails
        }
      });
    } catch (err) {
      console.error('❌ Error processing file links:', err);
      // Don't break message rendering if file link processing fails
    }
  } else {
    el.textContent = text;
  }

  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight;
  
  // Ensure input is enabled and ready for next question after message is added
  if (who === 'bot') {
    // Small delay to ensure DOM is updated before focusing
    setTimeout(() => {
      if (input && !input.disabled) {
        input.focus();
      }
    }, 100);
  }
  
  return el;
}

// Removed bubble toggle functionality - window opens directly now
// function toggleChat() {
//   panel.classList.toggle('collapsed');
// }
// 
// bubble.addEventListener('click', toggleChat);

// Minimize button functionality
const minimizeBtn = document.getElementById('minimizeBtn');
minimizeBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  
  if (window.mantle && window.mantle.minimizeApp) {
    window.mantle.minimizeApp();
  }
});

// Close button functionality - quits the entire application
const closeBtn = document.getElementById('closeBtn');
closeBtn.addEventListener('click', (e) => {
  e.stopPropagation(); // Prevent event bubbling

  // Send quit message to main process to close the application
  if (window.mantle && window.mantle.quitApp) {
    window.mantle.quitApp();
  }
});

// Window dragging functionality for frameless window (Windows support)
const panelHeader = document.querySelector('.panel-header');
let isDragging = false;

panelHeader.addEventListener('mousedown', (e) => {
  // Don't drag if clicking on close button
  if (e.target.closest('.close-btn')) {
    return;
  }

  isDragging = true;
  // Set cursor to move during drag
  document.body.style.cursor = 'move';

  // Initialize drag with current cursor position
  if (window.mantle && window.mantle.startDrag) {
    window.mantle.startDrag();
  }
});

document.addEventListener('mousemove', (e) => {
  if (!isDragging) return;

  // Send drag update to move the window
  if (window.mantle && window.mantle.dragWindow) {
    window.mantle.dragWindow();
  }
});

document.addEventListener('mouseup', () => {
  if (isDragging) {
    isDragging = false;
    // Reset cursor when drag ends
    document.body.style.cursor = '';
    
    // Notify main process that drag ended
    if (window.mantle && window.mantle.endDrag) {
      window.mantle.endDrag();
    }
  }
});

async function handleFeedback(messageId, rating, response, userQuestion) {
  // Show feedback modal
  const modal = document.getElementById('feedbackModal');
  const commentBox = document.getElementById('feedbackComment');
  const submitBtn = document.getElementById('submitFeedback');
  const cancelBtn = document.getElementById('cancelFeedback');

  modal.style.display = 'flex';
  commentBox.value = '';
  commentBox.focus();

  // Handle submit
  submitBtn.onclick = async () => {
    const comment = commentBox.value.trim();
    modal.style.display = 'none';

    // Send feedback to backend
    try {
      await fetch(`${BACKEND_URL}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message_id: messageId,
          rating: rating,
          comment: comment,
          user_question: userQuestion,
          response: response,
          timestamp: new Date().toISOString()
        })
      });

      // Show success message
      const msgEl = document.querySelector(`[data-message-id="${messageId}"]`);
      if (msgEl) {
        const statusDiv = msgEl.querySelector('.feedback-status');
        const buttonsDiv = msgEl.querySelector('.feedback-buttons');
        buttonsDiv.style.display = 'none';
        statusDiv.style.display = 'block';
        statusDiv.textContent = '✓ Thank you for your feedback!';
        statusDiv.className = 'feedback-status success';
      }
    } catch (err) {
      console.error('Feedback error:', err);
      const msgEl = document.querySelector(`[data-message-id="${messageId}"]`);
      if (msgEl) {
        const statusDiv = msgEl.querySelector('.feedback-status');
        statusDiv.style.display = 'block';
        statusDiv.textContent = '✗ Failed to send feedback';
        statusDiv.className = 'feedback-status error';
      }
    }
  };

  // Handle cancel
  cancelBtn.onclick = () => {
    modal.style.display = 'none';
  };

  // Close on outside click
  modal.onclick = (e) => {
    if (e.target === modal) {
      modal.style.display = 'none';
    }
  };
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  const hasImages = pendingImageAttachments.length > 0;
  
  // Don't submit if there's no text and no images
  if (!text && !hasImages) return;

  currentUserMessage = text;
  
  // Capture attachments before clearing
  const imagesToSend = [...pendingImageAttachments];  // Copy the array
  
  // Add to query history (only if it's different from the last query)
  if (text && (queryHistory.length === 0 || queryHistory[queryHistory.length - 1] !== text)) {
    queryHistory.push(text);
    // Keep only last 50 queries to prevent memory issues
    if (queryHistory.length > 50) {
      queryHistory.shift();
    }
  }
  
  input.value = '';
  input.style.height = '40px';  // Reset textarea height
  input.style.overflowY = 'hidden';
  
  // Clear attachments after capturing
  pendingImageAttachments = [];
  updateAttachmentPreview();
  
  // Create user message with optional images
  const userMsgEl = document.createElement('div');
  userMsgEl.className = 'msg user';
  
  if (text) {
    const textDiv = document.createElement('div');
    textDiv.textContent = text;
    userMsgEl.appendChild(textDiv);
  }
  
  // Add all images to user message
  if (imagesToSend.length > 0) {
    const imagesContainer = document.createElement('div');
    imagesContainer.className = 'user-images-container';
    imagesToSend.forEach(img => {
      const imgEl = document.createElement('img');
      imgEl.src = img.preview;
      imgEl.alt = img.fileName;
      imgEl.className = 'user-image-attachment';
      imagesContainer.appendChild(imgEl);
    });
    userMsgEl.appendChild(imagesContainer);
  }
  
  messages.appendChild(userMsgEl);
  messages.scrollTop = messages.scrollHeight;
  sendBtn.disabled = true;
  sendBtn.textContent = 'Thinking...';

  // Add loading message with typing indicator
  const loadingMsgEl = document.createElement('div');
  loadingMsgEl.id = 'loading-message';
  loadingMsgEl.className = 'msg bot loading-message';
  loadingMsgEl.innerHTML = `
    <div class="loading-text">
      <div class="typing-indicator">
        <span></span>
        <span></span>
        <span></span>
      </div>
      <div class="status-text">Sid is thinking...</div>
    </div>
  `;
  messages.appendChild(loadingMsgEl);
  messages.scrollTop = messages.scrollHeight;

  // Expanded dynamic loading messages to keep users engaged during longer queries
  // Add image-specific messages if images are attached
  const imageMessages = imagesToSend.length > 0 ? [
    `Analyzing ${imagesToSend.length > 1 ? 'your images' : 'your image'}...`,
    "Extracting details from screenshots...",
    "Reading text and annotations...",
    "Identifying technical content...",
  ] : [];
  
  const statusMessages = [
    "Sid is thinking...",
    ...imageMessages,
    "Planning query strategy...",
    "Routing to appropriate data sources...",
    "Searching through project files...",
    "Analyzing drawings and specifications...",
    "Retrieving relevant documents...",
    "Cross-referencing engineering notes...",
    "Grading document relevance...",
    "Filtering results for accuracy...",
    "Querying database records...",
    "Gathering code snippets...",
    "Synthesizing answer with AI...",
    "Verifying response quality...",
    "Checking citation accuracy...",
    "Compiling your answer...",
    "Almost there...",
    "Finalizing response...",
    "Still processing...",
    "Working on complex details...",
    "Just a moment more..."
  ];

  // Engaging messages to cycle through if query takes very long
  const extendedMessages = [
    "Deep diving into project data...",
    "Cross-checking multiple sources...",
    "Ensuring accuracy...",
    "Processing detailed information...",
    "Almost ready...",
    "Hang tight..."
  ];

  let messageIndex = 0;
  const startTime = Date.now();

  const statusInterval = setInterval(() => {
    let currentMessage;

    // Use main messages first (20 messages × 4s = 80 seconds)
    if (messageIndex < statusMessages.length) {
      currentMessage = statusMessages[messageIndex];
      messageIndex++;
    } else {
      // After main messages, cycle through extended messages
      const extendedIndex = (messageIndex - statusMessages.length) % extendedMessages.length;
      currentMessage = extendedMessages[extendedIndex];
      messageIndex++;
    }

    // Show processing time
    const elapsed = Math.round((Date.now() - startTime) / 1000);
    const statusText = `${currentMessage} (${elapsed}s)`;

    loadingMsgEl.querySelector('.status-text').textContent = statusText;
  }, 4000); // Update every 4 seconds for longer engagement per message

  try {
    // Get user identifier from localStorage
    const userIdentifier = getUserIdentifier();
    const sessionId = getOrCreateSessionId();
    
    // Get database toggle states
    const projectDbEnabled = document.getElementById('toggleProject').classList.contains('active');
    const codeDbEnabled = document.getElementById('toggleCode').classList.contains('active');
    const coopDbEnabled = document.getElementById('toggleCoop').classList.contains('active');
    
    // Prepare request body (include images if attached)
    const requestBody = {
      message: text || "What is shown in these images?",  // Default question if only images
      session_id: sessionId,
      user_identifier: userIdentifier,
      data_sources: {
        project_db: projectDbEnabled,
        code_db: codeDbEnabled,
        coop_manual: coopDbEnabled
      },
      // Support both single image (backwards compatible) and multiple images
      image_base64: imagesToSend.length === 1 ? imagesToSend[0].base64 : null,
      images_base64: imagesToSend.length > 0 ? imagesToSend.map(img => img.base64) : null
    };
    
    const response = await fetch(`${BACKEND_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    console.log('Backend response:', data);

    const messageId = data.message_id || generateMessageId();

    // Remove loading message
    const loadingMain = document.getElementById('loading-message');
    if (loadingMain) loadingMain.remove();

    clearInterval(statusInterval);

    // Check which answers exist (multi-database mode)
    const hasProjectAnswer = data.project_answer && data.project_answer.trim();
    const hasCodeAnswer = data.code_answer && data.code_answer.trim();
    const hasCoopAnswer = data.coop_answer && data.coop_answer.trim();
    const enabledCount = [hasProjectAnswer, hasCodeAnswer, hasCoopAnswer].filter(Boolean).length;
    const multipleEnabled = enabledCount > 1;

    if (multipleEnabled) {
      // Multi-database mode - show separate bubbles for each enabled database
      
      // Show project answer if it exists
      if (hasProjectAnswer) {
        let projectMessage = data.project_answer;
        if (data.route) {
          projectMessage += `\n\n_Route: ${data.route} | Citations: ${data.project_citations || 0}_`;
        }
        addMessage(projectMessage, 'bot', messageId + '_project', currentUserMessage);
      }

      // Show code answer in a separate bubble if it exists
      if (hasCodeAnswer) {
        let codeMessage = data.code_answer;
        // Add a header to distinguish it
        codeMessage = `## Code References\n\n${codeMessage}`;
        addMessage(codeMessage, 'bot', messageId + '_code', currentUserMessage);
      }

      // Show coop answer in a separate bubble if it exists
      if (hasCoopAnswer) {
        let coopMessage = data.coop_answer;
        // Add a header to distinguish it
        coopMessage = `## Training Manual References\n\n${coopMessage}`;
        addMessage(coopMessage, 'bot', messageId + '_coop', currentUserMessage);
      }
    } else {
      // Single answer mode (backward compatible)
      const reply = data.reply || data.answer || data.project_answer || data.code_answer || data.coop_answer || 'No response';
      let finalMessage = reply;
      if (data.route) {
        finalMessage = reply + `\n\n_Route: ${data.route} | Citations: ${data.citations || 0}_`;
      }
      addMessage(finalMessage, 'bot', messageId, currentUserMessage);
    }

  } catch (err) {
    // Remove loading message on error too
    const loadingMain = document.getElementById('loading-message');
    if (loadingMain) loadingMain.remove();
    clearInterval(statusInterval);

    console.error('Chat error:', err);
    addMessage(`❌ Error: ${err.message}`, 'bot');
  } finally {
    sendBtn.disabled = false;
    sendBtn.textContent = 'Send';
    // Re-focus input for next question
    input.focus();
  }
});

// Welcome modal logic
const welcomeModal = document.getElementById('welcomeModal');
const userNameInput = document.getElementById('userName');
const submitUserNameBtn = document.getElementById('submitUserName');

// Check if user identifier exists in localStorage
const storedUserIdentifier = getUserIdentifier();

if (!storedUserIdentifier) {
  // Show welcome modal on first launch
  welcomeModal.style.display = 'flex';
  userNameInput.focus();
  
  // Handle submit
  submitUserNameBtn.onclick = () => {
    const userName = userNameInput.value.trim();
    if (userName) {
      localStorage.setItem('user_identifier', userName);
      welcomeModal.style.display = 'none';
      // Focus input after modal closes
      setTimeout(() => {
        if (input && !input.disabled) {
          input.focus();
        }
      }, 100);
    } else {
      alert('Please enter your name to continue');
    }
  };
  
  // Handle enter key in input
  userNameInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      submitUserNameBtn.click();
    }
  });
} else {
  // User already registered, hide modal
  welcomeModal.style.display = 'none';
  // Focus input since modal won't show
  setTimeout(() => {
    if (input && !input.disabled) {
      input.focus();
    }
  }, 100);
}

// Database toggle click handlers
const toggleProject = document.getElementById('toggleProject');
const toggleCode = document.getElementById('toggleCode');
const toggleCoop = document.getElementById('toggleCoop');

toggleProject.addEventListener('click', () => {
  // Toggle state
  toggleProject.classList.toggle('active');
  
  // Ensure at least one is always active
  if (!toggleProject.classList.contains('active') && !toggleCode.classList.contains('active') && !toggleCoop.classList.contains('active')) {
    toggleCode.classList.add('active');
  }
  
  console.log('Project DB:', toggleProject.classList.contains('active') ? 'enabled' : 'disabled');
  console.log('Code DB:', toggleCode.classList.contains('active') ? 'enabled' : 'disabled');
  console.log('Coop DB:', toggleCoop.classList.contains('active') ? 'enabled' : 'disabled');
});

toggleCode.addEventListener('click', () => {
  // Toggle state
  toggleCode.classList.toggle('active');
  
  // Ensure at least one is always active
  if (!toggleProject.classList.contains('active') && !toggleCode.classList.contains('active') && !toggleCoop.classList.contains('active')) {
    toggleProject.classList.add('active');
  }
  
  console.log('Project DB:', toggleProject.classList.contains('active') ? 'enabled' : 'disabled');
  console.log('Code DB:', toggleCode.classList.contains('active') ? 'enabled' : 'disabled');
  console.log('Coop DB:', toggleCoop.classList.contains('active') ? 'enabled' : 'disabled');
});

toggleCoop.addEventListener('click', () => {
  // Toggle state
  toggleCoop.classList.toggle('active');
  
  // Ensure at least one is always active
  if (!toggleProject.classList.contains('active') && !toggleCode.classList.contains('active') && !toggleCoop.classList.contains('active')) {
    toggleProject.classList.add('active');
  }
  
  console.log('Project DB:', toggleProject.classList.contains('active') ? 'enabled' : 'disabled');
  console.log('Code DB:', toggleCode.classList.contains('active') ? 'enabled' : 'disabled');
  console.log('Coop DB:', toggleCoop.classList.contains('active') ? 'enabled' : 'disabled');
});

// Instructions modal functionality
const helpBtn = document.getElementById('helpBtn');
const instructionsModal = document.getElementById('instructionsModal');
const instructionsContent = document.getElementById('instructionsContent');
const closeInstructionsBtn = document.getElementById('closeInstructions');

// Function to convert markdown to HTML (simplified version for instructions)
function markdownToHTML(markdown) {
  let html = markdown;
  
  // Headers
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
  
  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  
  // Lists (numbered)
  html = html.replace(/^\d+\.\s+(.+)$/gim, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/s, '<ol>$1</ol>');
  
  // Lists (bullets)
  html = html.replace(/^-\s+(.+)$/gim, '<li>$1</li>');
  const bulletLists = html.match(/(<li>.*<\/li>)/s);
  if (bulletLists) {
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
  }
  
  // Line breaks
  html = html.replace(/\n\n/g, '</p><p>');
  html = html.replace(/\n/g, '<br>');
  
  // Wrap in paragraphs
  html = '<p>' + html + '</p>';
  
  return html;
}

// Function to fetch and display instructions
async function showInstructions() {
  instructionsModal.style.display = 'flex';
  instructionsContent.innerHTML = '<div class="loading-text">Loading instructions...</div>';
  
  try {
    const response = await fetch(`${BACKEND_URL}/instructions`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    const content = data.content || 'Instructions not available.';
    const format = data.format || 'text';
    
    // Format the content based on format type
    if (format === 'markdown') {
      // Use the same formatting function used for messages
      instructionsContent.innerHTML = formatMessageText(content);
    } else {
      // Plain text - preserve line breaks
      instructionsContent.innerHTML = '<pre style="white-space: pre-wrap; font-family: inherit;">' + 
        content.replace(/</g, '&lt;').replace(/>/g, '&gt;') + 
        '</pre>';
    }
  } catch (err) {
    console.error('Error fetching instructions:', err);
    instructionsContent.innerHTML = `
      <div style="color: #FF3B30; padding: 20px; text-align: center;">
        <p>❌ Failed to load instructions</p>
        <p style="font-size: 12px; color: #8e8e93;">${err.message}</p>
      </div>
    `;
  }
}

// Help button click handler
helpBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  showInstructions();
});

// Close instructions modal
closeInstructionsBtn.addEventListener('click', () => {
  instructionsModal.style.display = 'none';
});

// Close on outside click
instructionsModal.addEventListener('click', (e) => {
  if (e.target === instructionsModal) {
    instructionsModal.style.display = 'none';
  }
});

// Close on Escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && instructionsModal.style.display === 'flex') {
    instructionsModal.style.display = 'none';
  }
});

// Auto-resize textarea as user types
input.addEventListener('input', () => {
  input.style.height = '40px';  // Reset to min
  const newHeight = Math.min(input.scrollHeight, 120);
  input.style.height = newHeight + 'px';
  input.style.overflowY = newHeight >= 120 ? 'auto' : 'hidden';
});

// Keyboard handling for textarea: Enter sends, Ctrl+Enter adds newline
input.addEventListener('keydown', (e) => {
  // Handle Enter key for sending vs new line
  if (e.key === 'Enter') {
    if (e.ctrlKey || e.metaKey) {
      // Ctrl+Enter or Cmd+Enter: Insert newline
      e.preventDefault();
      const start = input.selectionStart;
      const end = input.selectionEnd;
      const value = input.value;
      input.value = value.substring(0, start) + '\n' + value.substring(end);
      input.selectionStart = input.selectionEnd = start + 1;
      
      // Auto-resize textarea
      input.style.height = '40px';
      const newHeight = Math.min(input.scrollHeight, 120);
      input.style.height = newHeight + 'px';
      input.style.overflowY = newHeight >= 120 ? 'auto' : 'hidden';
      return;
    } else if (!e.shiftKey) {
      // Enter alone (without Shift): Submit form
      e.preventDefault();
      form.dispatchEvent(new Event('submit', { cancelable: true }));
      return;
    }
    // Shift+Enter: Let default behavior (newline) happen
  }
  
  // Only handle arrow keys if not in a modal
  const welcomeModal = document.getElementById('welcomeModal');
  const feedbackModal = document.getElementById('feedbackModal');
  const instructionsModal = document.getElementById('instructionsModal');
  
  const isModalOpen = welcomeModal.style.display === 'flex' || 
                      feedbackModal.style.display === 'flex' || 
                      instructionsModal.style.display === 'flex';
  
  if (isModalOpen) {
    return; // Don't handle arrow keys when modals are open
  }
  
  // Only handle arrow keys if input is empty or cursor is at the start/end
  // This allows normal text editing when typing
  const inputValue = input.value;
  const cursorPosition = input.selectionStart;
  const isAtStart = cursorPosition === 0;
  const isAtEnd = cursorPosition === inputValue.length;
  
  if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
    // Only scroll if input is empty or cursor is at the start/end
    if (inputValue.length === 0 || (e.key === 'ArrowUp' && isAtStart) || (e.key === 'ArrowDown' && isAtEnd)) {
      e.preventDefault();
      
      // Get all user message elements
      const userMessages = Array.from(messages.querySelectorAll('.msg.user'));
      
      if (userMessages.length === 0) {
        return; // No user messages to navigate
      }
      
      const messagesTop = messages.scrollTop;
      const messagesRect = messages.getBoundingClientRect();
      
      if (e.key === 'ArrowUp') {
        // Find the previous user message (above current scroll position)
        let targetMessage = null;
        
        for (let i = userMessages.length - 1; i >= 0; i--) {
          const msg = userMessages[i];
          const msgRect = msg.getBoundingClientRect();
          // Calculate message position relative to scroll container
          const msgTop = msgRect.top - messagesRect.top + messages.scrollTop;
          
          // Find the first message that's above the current viewport top
          if (msgTop < messagesTop - 10) { // 10px threshold to avoid jumping when already at top
            targetMessage = msg;
            break;
          }
        }
        
        if (targetMessage) {
          targetMessage.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
          // No previous message found, scroll to first user message or top
          if (userMessages.length > 0) {
            userMessages[0].scrollIntoView({ behavior: 'smooth', block: 'start' });
          } else {
            messages.scrollTop = 0;
          }
        }
      } else if (e.key === 'ArrowDown') {
        // Check if we're at the last user query
        const lastUserMessage = userMessages[userMessages.length - 1];
        if (lastUserMessage) {
          const lastMsgRect = lastUserMessage.getBoundingClientRect();
          const lastMsgTop = lastMsgRect.top - messagesRect.top + messages.scrollTop;
          const viewportBottom = messagesTop + messages.clientHeight;
          
          // Check if the last user message is visible or just above the viewport
          // (within 50px threshold to account for message height)
          const isAtLastQuery = lastMsgTop <= viewportBottom + 50;
          
          if (isAtLastQuery) {
            // We're at the last query, scroll all the way to the bottom
            messages.scrollTo({ top: messages.scrollHeight, behavior: 'smooth' });
            return;
          }
        }
        
        // Not at last query, find the next user message (below current scroll position)
        let targetMessage = null;
        const viewportBottom = messagesTop + messages.clientHeight;
        
        for (let i = 0; i < userMessages.length; i++) {
          const msg = userMessages[i];
          const msgRect = msg.getBoundingClientRect();
          // Calculate message position relative to scroll container
          const msgTop = msgRect.top - messagesRect.top + messages.scrollTop;
          
          // Find the first message that's below the current viewport bottom
          if (msgTop > viewportBottom + 10) { // 10px threshold
            targetMessage = msg;
            break;
          }
        }
        
        if (targetMessage) {
          targetMessage.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
          // No next message found, scroll to bottom
          messages.scrollTo({ top: messages.scrollHeight, behavior: 'smooth' });
        }
      }
    }
  }
});

// Auto-focus input when window regains focus (e.g., after being minimized and restored)
window.addEventListener('focus', () => {
  // Check if any modal is open
  const welcomeModal = document.getElementById('welcomeModal');
  const feedbackModal = document.getElementById('feedbackModal');
  const instructionsModal = document.getElementById('instructionsModal');
  
  const isModalOpen = welcomeModal.style.display === 'flex' || 
                      feedbackModal.style.display === 'flex' || 
                      instructionsModal.style.display === 'flex';
  
  // Only focus input if no modal is open
  if (!isModalOpen) {
    setTimeout(() => {
      if (input && !input.disabled) {
        input.focus();
      }
    }, 100);
  }
});

addMessage('Hi! I\'m Sid. Ask me anything.', 'bot');