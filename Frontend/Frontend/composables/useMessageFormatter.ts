/**
 * Message formatting utility - formats backend responses with HTML links, markdown, MathJax equations, etc.
 * Based on the web-app formatting logic
 */

export const useMessageFormatter = () => {
  function formatMessageText(text: string): string {
    if (!text) return ''
    
    let formatted = text
    
    // Extract and preserve MathJax equations before processing
    const mathPlaceholders: Array<{ type: 'block' | 'inline', equation: string }> = []
    
    // Extract block equations $$...$$ first (must be on separate lines or standalone)
    formatted = formatted.replace(/\$\$([\s\S]*?)\$\$/g, (match, equation) => {
      const placeholder = `__MATH_BLOCK_${mathPlaceholders.length}__`
      mathPlaceholders.push({ type: 'block', equation: equation.trim() })
      return placeholder
    })
    
    // Extract inline equations $...$ (not $$)
    // Simple pattern: $...$ where ... doesn't contain $ or newlines
    // This avoids matching $$...$$ which we already processed
    formatted = formatted.replace(/(?<!\$)\$([^$\n]+?)\$(?!\$)/g, (match, equation) => {
      // Skip if this is part of a placeholder we already created
      if (match.includes('__MATH_BLOCK_') || match.includes('__MATH_INLINE_')) {
        return match
      }
      const placeholder = `__MATH_INLINE_${mathPlaceholders.length}__`
      mathPlaceholders.push({ type: 'inline', equation: equation.trim() })
      return placeholder
    })
    
    // Extract and preserve fully-formed HTML links from backend before HTML escaping
    const linkPlaceholders: string[] = []
    
    // Extract folder-link HTML elements (class="folder-link")
    formatted = formatted.replace(/<a\s+href="#"\s+class="folder-link"[\s\S]*?<\/a>/g, (match) => {
      const placeholder = `__LINK_${linkPlaceholders.length}__`
      linkPlaceholders.push(match) // Store the full HTML link
      return placeholder
    })
    
    // Extract file-link HTML elements (class="file-link")
    formatted = formatted.replace(/<a\s+href="#"\s+class="file-link"[\s\S]*?<\/a>/g, (match) => {
      const placeholder = `__LINK_${linkPlaceholders.length}__`
      linkPlaceholders.push(match) // Store the full HTML link
      return placeholder
    })
    
    // Escape HTML (except our placeholders)
    formatted = formatted
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
    
    // Restore link placeholders (they're already HTML)
    linkPlaceholders.forEach((link, index) => {
      formatted = formatted.replace(`__LINK_${index}__`, link)
    })
    
    // Convert markdown-style formatting
    // Headers
    formatted = formatted.replace(/^### (.*$)/gim, '<h3 class="text-base font-bold mt-4 mb-2">$1</h3>')
    formatted = formatted.replace(/^## (.*$)/gim, '<h2 class="text-lg font-bold mt-5 mb-3">$1</h2>')
    formatted = formatted.replace(/^# (.*$)/gim, '<h1 class="text-xl font-bold mt-6 mb-4">$1</h1>')
    
    // Bold - format complete patterns (both ** present)
    // Use non-greedy matching to handle multiple bold sections in one line
    // During streaming, incomplete patterns (e.g., **text without closing **) won't format until complete
    // This is correct behavior - we can't format incomplete markdown
    formatted = formatted.replace(/\*\*([^*\n]+?)\*\*/g, '<strong class="font-semibold">$1</strong>')
    
    // Italic - be careful not to match bold patterns
    // Only match single * that's not part of **
    formatted = formatted.replace(/(?<!\*)\*([^*\n]+?)\*(?!\*)/g, '<em class="italic">$1</em>')
    
    // Bullet points
    formatted = formatted.replace(/^[-*] (.*$)/gim, '<li class="ml-4 mb-1">$1</li>')
    
    // Numbered lists
    formatted = formatted.replace(/^\d+\. (.*$)/gim, '<li class="ml-4 mb-1">$1</li>')
    
    // Wrap lists
    formatted = formatted.replace(/(<li.*<\/li>)/gs, (match) => {
      if (!match.includes('<ul') && !match.includes('<ol')) {
        return '<ul class="list-disc list-inside space-y-1 my-2 ml-4">' + match + '</ul>'
      }
      return match
    })
    
    // Restore MathJax equations with proper formatting and bolding
    mathPlaceholders.forEach((math, index) => {
      // Unescape the equation (it was escaped during HTML escaping)
      const equation = math.equation
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'")
      
      // MathJax needs to see the raw delimiters ($ or $$) to process equations
      // We wrap in a span with a class, then use CSS to bold the MathJax output
      if (math.type === 'block') {
        const placeholder = `__MATH_BLOCK_${index}__`
        // Block equations: center and add class for bolding
        formatted = formatted.replace(placeholder, `<div class="my-4 text-center math-bold">$$${equation}$$</div>`)
      } else {
        const placeholder = `__MATH_INLINE_${index}__`
        // Inline equations: add class for bolding
        formatted = formatted.replace(placeholder, `<span class="math-bold">$${equation}$</span>`)
      }
    })
    
    // Line breaks - preserve spacing
    // Double line breaks create new paragraphs
    formatted = formatted.replace(/\n\n+/g, '</p><p class="mb-2">')
    // Single line breaks become <br>
    formatted = formatted.replace(/\n/g, '<br>')
    
    // Wrap in paragraph if not already wrapped
    if (!formatted.includes('<p') && !formatted.includes('<h') && !formatted.includes('<div')) {
      formatted = '<p class="mb-2">' + formatted + '</p>'
    } else if (!formatted.startsWith('<')) {
      formatted = '<p class="mb-2">' + formatted
    }
    
    // Ensure proper spacing between elements
    formatted = formatted.replace(/<\/p><p/g, '</p>\n<p')
    formatted = formatted.replace(/<\/h([1-6])><h/g, '</h$1>\n<h')
    formatted = formatted.replace(/<\/strong><strong/g, '</strong><strong')
    
    return formatted
  }
  
  return {
    formatMessageText
  }
}

