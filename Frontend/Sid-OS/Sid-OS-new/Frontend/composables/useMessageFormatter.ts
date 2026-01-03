/**
 * Message formatting utility - formats backend responses with HTML links, markdown, etc.
 * Based on the web-app formatting logic
 */

export const useMessageFormatter = () => {
  function formatMessageText(text: string): string {
    if (!text) return ''
    
    let formatted = text
    
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
    
    // Bold
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold">$1</strong>')
    
    // Italic
    formatted = formatted.replace(/\*(.*?)\*/g, '<em class="italic">$1</em>')
    
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
    
    // Line breaks
    formatted = formatted.replace(/\n\n/g, '</p><p class="mb-2">')
    formatted = formatted.replace(/\n/g, '<br>')
    
    // Wrap in paragraph if not already wrapped
    if (!formatted.includes('<p') && !formatted.includes('<h')) {
      formatted = '<p class="mb-2">' + formatted + '</p>'
    } else if (!formatted.startsWith('<')) {
      formatted = '<p class="mb-2">' + formatted
    }
    
    return formatted
  }
  
  return {
    formatMessageText
  }
}

