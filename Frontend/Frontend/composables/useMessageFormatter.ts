/**
 * Message formatting utility - formats backend responses with HTML, markdown, and MathJax equations
 */

export const useMessageFormatter = () => {
  /**
   * State-based markdown parser for streaming support
   * Applies formatting optimistically when opening tags are detected
   */
  function formatMarkdownWithState(text: string): string {
    if (!text) return ''
    
    let result = ''
    let i = 0
    const len = text.length
    let boldOpen = false
    let italicOpen = false
    
    while (i < len) {
      // Skip MathJax placeholders
      if (text.slice(i).startsWith('__MATH_BLOCK_') || text.slice(i).startsWith('__MATH_INLINE_')) {
        const placeholderEnd = text.indexOf('__', i + 2)
        if (placeholderEnd !== -1) {
          result += text.slice(i, placeholderEnd + 2)
          i = placeholderEnd + 2
          continue
        }
      }
      
      // Headers (must be at start of line)
      if (i === 0 || text[i - 1] === '\n') {
        const headerMatch = text.slice(i).match(/^(#{1,6})\s/)
        if (headerMatch && headerMatch[1]) {
          const level = headerMatch[1].length
          const afterHash = i + level + 1
          let headerEnd = text.indexOf('\n', afterHash)
          if (headerEnd === -1) headerEnd = len
          
          if (boldOpen) { result += '</strong>'; boldOpen = false }
          if (italicOpen) { result += '</em>'; italicOpen = false }
          
          const headerText = text.slice(afterHash, headerEnd)
          const tag = `h${level}` as 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6'
          const classAttr = 
            level === 1 ? 'class="text-xl font-bold mt-6 mb-4"'
            : level === 2 ? 'class="text-lg font-bold mt-5 mb-3"'
            : level === 3 ? 'class="text-base font-bold mt-4 mb-2"'
            : 'class="text-sm font-bold mt-3 mb-2"'
          
          result += `<${tag} ${classAttr}>${headerText}</${tag}>`
          i = headerEnd
          continue
        }
      }
      
      // Bold: **text**
      if (!boldOpen && i + 1 < len && text[i] === '*' && text[i + 1] === '*') {
        // Skip if inside HTML entity
        if (i > 0) {
          const recentText = text.substring(Math.max(0, i - 10), i)
          const lastAmpersand = recentText.lastIndexOf('&')
          if (lastAmpersand !== -1 && !recentText.substring(lastAmpersand).includes(';')) {
            result += text[i]
            i++
            continue
          }
        }
        
        // Skip if inside math placeholder
        if (text.slice(Math.max(0, i - 20), i + 20).includes('__MATH_')) {
          result += text[i]
          i++
          continue
        }
        
        const nextDoubleStar = text.indexOf('**', i + 2)
        if (nextDoubleStar !== -1 && nextDoubleStar > i + 2) {
          const content = text.slice(i + 2, nextDoubleStar)
          if (content.length > 0) {
            result += `<strong class="font-semibold">${content}</strong>`
            i = nextDoubleStar + 2
            continue
          }
        } else {
          // Incomplete pattern - open optimistically for streaming
          result += '<strong class="font-semibold">'
          boldOpen = true
          i += 2
          continue
        }
      }
      
      // Closing bold **
      if (boldOpen && i + 1 < len && text[i] === '*' && text[i + 1] === '*') {
        // Skip if inside HTML entity
        if (i > 0) {
          for (let j = i - 1; j >= 0 && j >= i - 10; j--) {
            if (text[j] === ';') break
            if (text[j] === '&') {
              result += text[i]
              i++
              continue
            }
          }
        }
        result += '</strong>'
        boldOpen = false
        i += 2
        continue
      }
      
      // Italic: *text* (not part of **)
      if (!boldOpen && text[i] === '*' && 
          (i === 0 || text[i - 1] !== '*') && 
          (i + 1 >= len || text[i + 1] !== '*')) {
        if (italicOpen) {
          result += '</em>'
          italicOpen = false
          i += 1
          continue
        } else {
          let nextStar = -1
          for (let j = i + 1; j < len; j++) {
            if (text[j] === '*') {
              if (j + 1 < len && text[j + 1] === '*') {
                j++
                continue
              } else {
                nextStar = j
                break
              }
            }
          }
          if (nextStar !== -1 && nextStar > i + 1) {
            result += `<em class="italic">${text.slice(i + 1, nextStar)}</em>`
            i = nextStar + 1
            continue
          } else {
            result += '<em class="italic">'
            italicOpen = true
            i += 1
            continue
          }
        }
      }
      
      // List items
      if ((i === 0 || text[i - 1] === '\n') && 
          (text[i] === '-' || text[i] === '*') && 
          text[i + 1] === ' ') {
        if (boldOpen) { result += '</strong>'; boldOpen = false }
        if (italicOpen) { result += '</em>'; italicOpen = false }
        
        let itemEnd = text.indexOf('\n', i + 2)
        if (itemEnd === -1) itemEnd = len
        result += `<li class="ml-4 mb-1">${text.slice(i + 2, itemEnd)}</li>`
        i = itemEnd
        continue
      }
      
      // Numbered list items
      if ((i === 0 || text[i - 1] === '\n') && /^\d+\. /.test(text.slice(i))) {
        if (boldOpen) { result += '</strong>'; boldOpen = false }
        if (italicOpen) { result += '</em>'; italicOpen = false }
        
        const match = text.slice(i).match(/^(\d+\. )/)
        if (match && match[1]) {
          let itemEnd = text.indexOf('\n', i)
          if (itemEnd === -1) itemEnd = len
          result += `<li class="ml-4 mb-1">${text.slice(i + match[1].length, itemEnd)}</li>`
          i = itemEnd
          continue
        }
      }
      
      // LaTeX subscripts: x_2 or x_{12}
      if (text[i] === '_' && i + 1 < len && text[i + 1] !== ' ' && text[i + 1] !== '\n') {
        let subEnd = -1
        let subContent = ''
        
        if (text[i + 1] === '{') {
          const braceEnd = text.indexOf('}', i + 2)
          if (braceEnd !== -1 && braceEnd > i + 2) {
            subContent = text.slice(i + 2, braceEnd)
            subEnd = braceEnd + 1
          } else {
            subContent = text.slice(i + 2)
            subEnd = len
          }
        } else {
          let j = i + 1
          while (j < len) {
            const char = text[j]
            if (char === undefined || !/[a-zA-Z0-9]/.test(char)) break
            j++
          }
          if (j > i + 1) {
            subContent = text.slice(i + 1, j)
            subEnd = j
          }
        }
        
        if (subContent && subEnd > i) {
          result += `<sub>${subContent}</sub>`
          i = subEnd
          continue
        }
      }
      
      // LaTeX superscripts: x^2 or x^{2}
      if (text[i] === '^' && i + 1 < len && text[i + 1] !== ' ' && text[i + 1] !== '\n') {
        let supEnd = -1
        let supContent = ''
        
        if (text[i + 1] === '{') {
          const braceEnd = text.indexOf('}', i + 2)
          if (braceEnd !== -1 && braceEnd > i + 2) {
            supContent = text.slice(i + 2, braceEnd)
            supEnd = braceEnd + 1
          } else {
            supContent = text.slice(i + 2)
            supEnd = len
          }
        } else {
          let j = i + 1
          while (j < len) {
            const char = text[j]
            if (char === undefined || !/[a-zA-Z0-9]/.test(char)) break
            j++
          }
          if (j > i + 1) {
            supContent = text.slice(i + 1, j)
            supEnd = j
          }
        }
        
        if (supContent && supEnd > i) {
          result += `<sup>${supContent}</sup>`
          i = supEnd
          continue
        }
      }
      
      result += text[i]
      i++
    }
    
    // Close any open tags
    if (boldOpen) result += '</strong>'
    if (italicOpen) result += '</em>'
    
    // Wrap consecutive list items in <ul> tags
    result = result.replace(/(<li[^>]*>.*?<\/li>(?:\s*<li[^>]*>.*?<\/li>)*)/gs, (match) => {
      if (!match.includes('<ul') && !match.includes('<ol')) {
        return '<ul class="list-disc list-inside space-y-1 my-2 ml-4">' + match + '</ul>'
      }
      return match
    })
    
    return result
  }

  function formatMessageText(text: string): string {
    if (!text) return ''
    
    let formatted = text
    const mathPlaceholders: Array<{ type: 'block' | 'inline'; equation: string; isComplete: boolean }> = []
    
    // Helper: Check if content is a dimension (not math)
    // Only filter obvious dimensions - be conservative to avoid filtering real math
    function isDimension(content: string): boolean {
      // Dimensions have quotes (inches/feet) or text commands with dimension-like content
      const hasQuotes = content.includes('"') || content.includes("'")
      const hasTextCommand = /\\text\{/.test(content)
      // Only check for dimension patterns if quotes are present (to avoid false positives)
      if (hasQuotes) {
        const hasDimensionPattern = /\d+\s*["']+\s*[x×\\times]/.test(content)
        const hasFractionWithUnit = /\d+\/\d+\s*["']/.test(content)
        if (hasDimensionPattern || hasFractionWithUnit) return true
      }
      return hasQuotes || hasTextCommand
    }
    
    // STEP 1: Extract MathJax equations BEFORE processing (preserves LaTeX syntax)
    // Block equations: $$...$$
    formatted = formatted.replace(/\$\$([\s\S]*?)\$\$/g, (match, equation) => {
      const placeholder = `__MATH_BLOCK_${mathPlaceholders.length}__`
      mathPlaceholders.push({ type: 'block', equation: equation.trim(), isComplete: true })
      return placeholder
    })
    
    // Incomplete block equations (streaming)
    const incompleteBlock = formatted.match(/\$\$([\s\S]*?)(?=\$\$|__MATH_BLOCK_|$)/g)
    if (incompleteBlock) {
      incompleteBlock.forEach((match) => {
        if (!match.includes('__MATH_BLOCK_') && match.startsWith('$$') && !match.endsWith('$$')) {
          const placeholder = `__MATH_BLOCK_${mathPlaceholders.length}__`
          mathPlaceholders.push({ type: 'block', equation: match.slice(2).trim(), isComplete: false })
          formatted = formatted.replace(match, placeholder)
        }
      })
    }
    
    // Block equations: \[...\]
    formatted = formatted.replace(/\\\[([\s\S]*?)\\\]/g, (match, equation) => {
      const placeholder = `__MATH_BLOCK_${mathPlaceholders.length}__`
      mathPlaceholders.push({ type: 'block', equation: equation.trim(), isComplete: true })
      return placeholder
    })
    
    // Inline equations: $...$ (extract ALL, filter dimensions later)
    formatted = formatted.replace(/\$([^$\n]+?)\$/g, (match, equation) => {
      if (match.includes('__MATH_BLOCK_')) return match // Skip if already processed as block
      
      // Extract all inline math - we'll filter dimensions in cleanup step
      const placeholder = `__MATH_INLINE_${mathPlaceholders.length}__`
      mathPlaceholders.push({ type: 'inline', equation: equation.trim(), isComplete: true })
      return placeholder
    })
    
    // Inline equations: \(...\)
    formatted = formatted.replace(/\\\(([\s\S]*?)\\\)/g, (match, equation) => {
      if (match.includes('__MATH_BLOCK_')) return match
      const placeholder = `__MATH_INLINE_${mathPlaceholders.length}__`
      mathPlaceholders.push({ type: 'inline', equation: equation.trim(), isComplete: true })
      return placeholder
    })
    
    // STEP 2: HTML escape
    formatted = formatted
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
    
    // STEP 3: Process markdown
    formatted = formatMarkdownWithState(formatted)
    
    // STEP 4: Clean up remaining markdown bolding (fallback)
    if (formatted.includes('**') && !formatted.includes('__MATH_')) {
      formatted = formatted.replace(/\*\*([^*]+?)\*\*/g, '<strong class="font-semibold">$1</strong>')
      formatted = formatted.replace(/\*\*([^*]+)$/g, '<strong class="font-semibold">$1</strong>')
    }
    
    // STEP 5: Restore MathJax equations and filter out dimensions
    // Process in reverse order to avoid index shifting issues
    for (let index = mathPlaceholders.length - 1; index >= 0; index--) {
      const math = mathPlaceholders[index]
      if (!math) continue
      
      // Unescape HTML entities to restore LaTeX syntax
      const equation = math.equation
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'")
      
      const placeholder = math.type === 'block' 
        ? `__MATH_BLOCK_${index}__`
        : `__MATH_INLINE_${index}__`
      
      // For inline math, check if it's actually a dimension
      if (math.type === 'inline' && isDimension(equation)) {
        // Convert dimension to plain text
        const cleaned = equation
          .replace(/\\times/g, '×')
          .replace(/\\cdot/g, '·')
          .replace(/\\text\{([^}]+)\}/g, '$1')
          .replace(/\s*×\s*/g, 'x')
          .replace(/\s*\+\s*/g, ' + ')
          .replace(/\s*-\s*/g, ' - ')
          .replace(/\s+/g, ' ')
          .trim()
        // Replace placeholder (placeholders don't have special regex chars, so simple replace works)
        formatted = formatted.split(placeholder).join(cleaned)
      } else {
        // Restore real math equations with proper delimiters
        if (math.type === 'block') {
          const delimiters = math.isComplete ? '$$' : ''
          const replacement = `<div class="my-4 text-center">$$${equation}${delimiters}</div>`
          formatted = formatted.split(placeholder).join(replacement)
        } else {
          const delimiters = math.isComplete ? '$' : ''
          const replacement = `$${equation}${delimiters}`
          formatted = formatted.split(placeholder).join(replacement)
        }
      }
    }
    
    // STEP 7: Format line breaks and wrap in paragraphs
    formatted = formatted.replace(/\n\n/g, '</p><p class="mb-2">')
    formatted = formatted.replace(/\n/g, '<br>')
    
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
