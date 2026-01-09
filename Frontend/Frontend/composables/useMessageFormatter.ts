/**
 * Message formatting utility - formats backend responses with HTML links, markdown, MathJax equations, etc.
 * Based on the web-app formatting logic
 */

export const useMessageFormatter = () => {
  /**
   * State-based markdown parser that applies formatting optimistically
   * When it sees an opening tag (like **), it immediately starts formatting
   * This works well for streaming where tags may be incomplete
   */
  function formatMarkdownWithState(text: string): string {
    if (!text) return ''
    
    let result = ''
    let i = 0
    const len = text.length
    
    // State tracking for open tags
    let boldOpen = false
    let italicOpen = false
    
    while (i < len) {
      // Skip MathJax placeholders - they're already processed
      if (text.slice(i).startsWith('__MATH_BLOCK_') || text.slice(i).startsWith('__MATH_INLINE_')) {
        // Find the end of the placeholder
        const placeholderEnd = text.indexOf('__', i + 2)
        if (placeholderEnd !== -1) {
          result += text.slice(i, placeholderEnd + 2)
          i = placeholderEnd + 2
          continue
        }
      }
      
      // LINKS DISABLED: No longer skipping link placeholders
      
      // Check for headers (must be at start of line)
      // Support h1-h6 (1-6 hashes)
      if (i === 0 || text[i - 1] === '\n') {
        // Match 1-6 hashes followed by a space
        const headerMatch = text.slice(i).match(/^(#{1,6})\s/)
        if (headerMatch && headerMatch[1]) {
          const level = headerMatch[1].length
          const afterHash = i + level + 1
          let headerEnd = text.indexOf('\n', afterHash)
          if (headerEnd === -1) headerEnd = len
          
          // Close any open tags before starting header
          if (boldOpen) {
            result += '</strong>'
            boldOpen = false
          }
          if (italicOpen) {
            result += '</em>'
            italicOpen = false
          }
          
          const headerText = text.slice(afterHash, headerEnd)
          const tag = `h${level}` as 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6'
          const classAttr = 
            level === 1 ? 'class="text-xl font-bold mt-6 mb-4"'
            : level === 2 ? 'class="text-lg font-bold mt-5 mb-3"'
            : level === 3 ? 'class="text-base font-bold mt-4 mb-2"'
            : level === 4 ? 'class="text-sm font-bold mt-3 mb-2"'
            : level === 5 ? 'class="text-xs font-bold mt-2 mb-1"'
            : 'class="text-xs font-bold mt-2 mb-1"'
          
          result += `<${tag} ${classAttr}>${headerText}</${tag}>`
          i = headerEnd
          continue
        }
      }
      
      // Check for complete bold pattern first **text** (if not already in bold)
      // Only match ** if it's not part of an escaped sequence or HTML entity
      if (!boldOpen && i + 1 < len && text[i] === '*' && text[i + 1] === '*') {
        // Debug: Log when we find ** pattern
        console.log('🔍 Found ** at position', i, 'boldOpen:', boldOpen, 'text preview:', text.substring(Math.max(0, i-10), Math.min(i+30, len)))
        // Make sure we're not in the middle of an HTML entity (like &amp;, &lt;, etc.)
        // Check backwards to see if we're inside an HTML entity
        // Simplified check: if we see & in the last 10 chars without a ; after it, skip
        let inEntity = false
        if (i > 0) {
          const recentText = text.substring(Math.max(0, i - 10), i)
          const lastAmpersand = recentText.lastIndexOf('&')
          if (lastAmpersand !== -1) {
            const afterAmpersand = recentText.substring(lastAmpersand)
            // If there's an & without a ; before our **, we might be in an entity
            if (!afterAmpersand.includes(';')) {
              inEntity = true
            }
          }
        }
        
        if (inEntity) {
          // We're inside an HTML entity, skip this
          console.log('⏭️ Skipping ** at', i, 'because in HTML entity')
          result += text[i]
          i++
          continue
        }
        
        // LINKS DISABLED: No longer checking for link placeholders
        
        // Make sure we're not inside a MathJax placeholder
        if (text.slice(Math.max(0, i - 20), i + 20).includes('__MATH_')) {
          result += text[i]
          i++
          continue
        }
        
        // Look ahead to see if there's a closing **
        const nextDoubleStar = text.indexOf('**', i + 2)
        
        if (nextDoubleStar !== -1 && nextDoubleStar > i + 2) {
          // Complete pattern - format it
          const content = text.slice(i + 2, nextDoubleStar)
          // Handle empty bold (****)
          if (content.length === 0) {
            // Just skip it - empty bold doesn't make sense
            result += '****'
            i = nextDoubleStar + 2
            continue
          }
          result += `<strong class="font-semibold">${content}</strong>`
          i = nextDoubleStar + 2
          continue
        } else {
          // Incomplete pattern (no closing ** found) - open optimistically for streaming
          result += '<strong class="font-semibold">'
          boldOpen = true
          i += 2
          continue
        }
      }
      
      // Check for closing bold ** (only if bold is open)
      if (boldOpen && i + 1 < len && text[i] === '*' && text[i + 1] === '*') {
        // Make sure we're not in the middle of an HTML entity
        let inEntity = false
        if (i > 0) {
          // Look backwards for unclosed &
          for (let j = i - 1; j >= 0 && j >= i - 10; j--) {
            if (text[j] === ';') break // Found entity end, we're safe
            if (text[j] === '&') {
              // Found & without ; - we might be inside an entity
              inEntity = true
              break
            }
          }
        }
        
        if (inEntity) {
          // We're inside an HTML entity, skip this
          result += text[i]
          i++
          continue
        }
        
        result += '</strong>'
        boldOpen = false
        i += 2
        continue
      }
      
      // Check for italic * (only if not part of **)
      // Make sure previous char is not * and next char is not *
      if (!boldOpen && text[i] === '*' && 
          (i === 0 || text[i - 1] !== '*') && 
          (i + 1 >= len || text[i + 1] !== '*')) {
        // Check if it's a closing italic
        if (italicOpen) {
          result += '</em>'
          italicOpen = false
          i += 1
          continue
        } else {
          // Look ahead for next * that's not part of **
          let nextStar = -1
          for (let j = i + 1; j < len; j++) {
            if (text[j] === '*') {
              // Make sure it's not part of **
              if (j + 1 < len && text[j + 1] === '*') {
                // Skip the **
                j++
                continue
              } else {
                nextStar = j
                break
              }
            }
          }
          
          if (nextStar !== -1 && nextStar > i + 1) {
            // Complete pattern
            const content = text.slice(i + 1, nextStar)
            result += `<em class="italic">${content}</em>`
            i = nextStar + 1
            continue
          } else {
            // Incomplete pattern - open optimistically
            result += '<em class="italic">'
            italicOpen = true
            i += 1
            continue
          }
        }
      }
      
      // Check for list items (- or * followed by space)
      if ((i === 0 || text[i - 1] === '\n') && 
          (text[i] === '-' || text[i] === '*') && 
          text[i + 1] === ' ') {
        // Close any open tags before list item
        if (boldOpen) {
          result += '</strong>'
          boldOpen = false
        }
        if (italicOpen) {
          result += '</em>'
          italicOpen = false
        }
        
        let itemEnd = text.indexOf('\n', i + 2)
        if (itemEnd === -1) itemEnd = len
        const itemText = text.slice(i + 2, itemEnd)
        result += `<li class="ml-4 mb-1">${itemText}</li>`
        i = itemEnd
        continue
      }
      
      // Check for numbered list items (digits followed by . and space)
      if ((i === 0 || text[i - 1] === '\n') && /^\d+\. /.test(text.slice(i))) {
        // Close any open tags before list item
        if (boldOpen) {
          result += '</strong>'
          boldOpen = false
        }
        if (italicOpen) {
          result += '</em>'
          italicOpen = false
        }
        
        const match = text.slice(i).match(/^(\d+\. )/)
        if (match && match[1]) {
          let itemEnd = text.indexOf('\n', i)
          if (itemEnd === -1) itemEnd = len
          const itemText = text.slice(i + match[1].length, itemEnd)
          result += `<li class="ml-4 mb-1">${itemText}</li>`
          i = itemEnd
          continue
        }
      }
      
      // Check for LaTeX subscripts (_) and superscripts (^)
      // Format them as HTML sub/sup tags for immediate visual feedback during streaming
      if (text[i] === '_' && i + 1 < len && text[i + 1] !== ' ' && text[i + 1] !== '\n') {
        // Look ahead to find the subscript content
        // Subscript can be single char like x_2 or grouped like x_{12}
        let subEnd = -1
        let subContent = ''
        
        if (i + 1 < len && text[i + 1] === '{') {
          // Grouped subscript: x_{12}
          const braceEnd = text.indexOf('}', i + 2)
          if (braceEnd !== -1 && braceEnd > i + 2) {
            subContent = text.slice(i + 2, braceEnd)
            subEnd = braceEnd + 1
          } else {
            // Incomplete grouped subscript - format optimistically
            subContent = text.slice(i + 2)
            subEnd = len
          }
        } else {
          // Single char subscript: x_2
          // Find next non-alphanumeric or end of text
          let j = i + 1
          while (j < len) {
            const char = text[j]
            if (char === undefined || !/[a-zA-Z0-9]/.test(char)) {
              break
            }
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
      
      // Check for LaTeX superscripts (^)
      if (text[i] === '^' && i + 1 < len && text[i + 1] !== ' ' && text[i + 1] !== '\n') {
        // Look ahead to find the superscript content
        let supEnd = -1
        let supContent = ''
        
        if (i + 1 < len && text[i + 1] === '{') {
          // Grouped superscript: x^{2}
          const braceEnd = text.indexOf('}', i + 2)
          if (braceEnd !== -1 && braceEnd > i + 2) {
            supContent = text.slice(i + 2, braceEnd)
            supEnd = braceEnd + 1
          } else {
            // Incomplete grouped superscript - format optimistically
            supContent = text.slice(i + 2)
            supEnd = len
          }
        } else {
          // Single char superscript: x^2
          let j = i + 1
          while (j < len) {
            const char = text[j]
            if (char === undefined || !/[a-zA-Z0-9]/.test(char)) {
              break
            }
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
      
      // Regular character - append to result
      result += text[i]
      i++
    }
    
    // Close any open tags at the end (for streaming/incomplete patterns)
    if (boldOpen) {
      result += '</strong>'
    }
    if (italicOpen) {
      result += '</em>'
    }
    
    // Wrap consecutive list items in <ul> tags
    result = result.replace(/(<li[^>]*>.*?<\/li>(?:\s*<li[^>]*>.*?<\/li>)*)/gs, (match) => {
      // Check if already wrapped
      if (match.includes('<ul') || match.includes('<ol')) {
        return match
      }
      // Wrap consecutive list items
      return '<ul class="list-disc list-inside space-y-1 my-2 ml-4">' + match + '</ul>'
    })
    
    return result
  }

  // DISABLED: Math equation detection - uncomment if math extraction is re-enabled
  // function looksLikeEquation(text: string): boolean {
  //   if (!text || text.length < 3) return false
  //   const hasSubscript = /[A-Za-z]_[A-Za-z0-9]/.test(text)
  //   const hasSuperscript = /[A-Za-z0-9]\^[0-9A-Za-z]/.test(text)
  //   const hasOperators = /[=+\-*\/<>≤≥±]/.test(text)
  //   return hasSubscript || hasSuperscript || (hasOperators && text.includes('='))
  // }

  function formatMessageText(text: string): string {
    if (!text) return ''
    
    // Debug: Log raw input
    if (text.includes('**')) {
      console.log('🔍 formatMessageText received text with **:', text.substring(0, 200))
    }
    
    let formatted = text
    
    // MATH EXTRACTION TEMPORARILY DISABLED - was interfering with bold ** formatting
    // Extract and preserve MathJax equations before processing
    // Handle both complete and incomplete equations optimistically for streaming
    // Support multiple delimiter formats: $$...$$, \[...\], $...$, \(...\)
    // const mathPlaceholders: Array<{ type: 'block' | 'inline'; equation: string; isComplete: boolean }> = []
    
    // DISABLED: Math extraction - uncomment if needed
    /*
    // Step 1: Extract complete block equations with $$...$$ delimiters (most common)
    formatted = formatted.replace(/\$\$([\s\S]*?)\$\$/g, (match, equation) => {
      const placeholder = `__MATH_BLOCK_${mathPlaceholders.length}__`
      mathPlaceholders.push({ type: 'block', equation: equation.trim(), isComplete: true })
      return placeholder
    })
    
    // Step 2: Extract incomplete block equations $$... (for streaming)
    const incompleteBlockDoubleDollar = formatted.match(/\$\$([\s\S]*?)(?=\$\$|__MATH_BLOCK_|$)/g)
    if (incompleteBlockDoubleDollar) {
      incompleteBlockDoubleDollar.forEach((match) => {
        if (!match.includes('__MATH_BLOCK_') && match.startsWith('$$') && !match.endsWith('$$')) {
          const equation = match.slice(2) // Remove leading $$
          const placeholder = `__MATH_BLOCK_${mathPlaceholders.length}__`
          mathPlaceholders.push({ type: 'block', equation: equation.trim(), isComplete: false })
          formatted = formatted.replace(match, placeholder)
        }
      })
    }
    
    // Step 3: Extract complete block equations with \[...\] delimiters
    formatted = formatted.replace(/\\\[([\s\S]*?)\\\]/g, (match, equation) => {
      const placeholder = `__MATH_BLOCK_${mathPlaceholders.length}__`
      mathPlaceholders.push({ type: 'block', equation: equation.trim(), isComplete: true })
      return placeholder
    })
    
    // Step 4: Extract incomplete block equations \[... (for streaming)
    const incompleteBlockMatch = formatted.match(/\\\[([\s\S]*?)(?=\\\]|__MATH_BLOCK_|$)/g)
    if (incompleteBlockMatch) {
      incompleteBlockMatch.forEach((match) => {
        if (!match.includes('__MATH_BLOCK_') && match.startsWith('\\[') && !match.endsWith('\\]')) {
          const equation = match.slice(2) // Remove leading \[
          const placeholder = `__MATH_BLOCK_${mathPlaceholders.length}__`
          mathPlaceholders.push({ type: 'block', equation: equation.trim(), isComplete: false })
          formatted = formatted.replace(match, placeholder)
        }
      })
    }
    
    // Step 5: Extract complete inline equations $...$ (not $$)
    formatted = formatted.replace(/\$([^$\n]+?)\$/g, (match, equation) => {
      // Skip if it's part of a block equation (already processed)
      if (match.includes('__MATH_BLOCK_')) return match
      // Skip if it looks like currency or other non-math usage
      if (match.length < 5 || !looksLikeEquation(equation)) return match
      const placeholder = `__MATH_INLINE_${mathPlaceholders.length}__`
      mathPlaceholders.push({ type: 'inline', equation: equation.trim(), isComplete: true })
      return placeholder
    })
    
    // Step 6: Extract complete inline equations \(...\) (not part of \[)
    formatted = formatted.replace(/\\\(([\s\S]*?)\\\)/g, (match, equation) => {
      // Skip if it's part of a block equation (already processed)
      if (match.includes('__MATH_BLOCK_')) return match
      const placeholder = `__MATH_INLINE_${mathPlaceholders.length}__`
      mathPlaceholders.push({ type: 'inline', equation: equation.trim(), isComplete: true })
      return placeholder
    })
    
    // Step 7: Extract incomplete inline equations $... (for streaming) - be careful to not match single $
    const incompleteInlineDollarRegex = /\$([^$\n]+?)(?=\$|__MATH_|\n|$)/g
    let inlineDollarMatch: RegExpExecArray | null
    while ((inlineDollarMatch = incompleteInlineDollarRegex.exec(formatted)) !== null) {
      const fullMatch = inlineDollarMatch[0]
      const equation = inlineDollarMatch[1]
      
      // Skip if already processed or doesn't look like math
      if (!equation || fullMatch.includes('__MATH_BLOCK_') || fullMatch.includes('__MATH_INLINE_')) continue
      if (!looksLikeEquation(equation)) continue
      // Skip if next char is $ (would be $$ which is handled above)
      const matchIndex = inlineDollarMatch.index
      if (matchIndex !== undefined && matchIndex + fullMatch.length < formatted.length && formatted[matchIndex + fullMatch.length] === '$') continue
      
      // This is an incomplete inline equation
      const placeholder = `__MATH_INLINE_${mathPlaceholders.length}__`
      mathPlaceholders.push({ type: 'inline', equation: equation.trim(), isComplete: false })
      if (matchIndex !== undefined) {
        formatted = formatted.substring(0, matchIndex) + placeholder + formatted.substring(matchIndex + fullMatch.length)
        incompleteInlineDollarRegex.lastIndex = 0
      }
    }
    
    // Step 8: Extract incomplete inline equations \(... (for streaming)
    const incompleteInlineRegex = /\\\(([\s\S]*?)(?=\\\)|__MATH_|$)/g
    let inlineMatch: RegExpExecArray | null
    while ((inlineMatch = incompleteInlineRegex.exec(formatted)) !== null) {
      const fullMatch = inlineMatch[0]
      const equation = inlineMatch[1]
      
      // Skip if equation is undefined or already processed
      if (!equation || fullMatch.includes('__MATH_BLOCK_') || fullMatch.includes('__MATH_INLINE_')) continue
      // Skip if this is part of a \[ block equation
      const matchIndex = inlineMatch.index
      if (matchIndex !== undefined && matchIndex > 0 && formatted[matchIndex - 1] === '[') continue
      // Skip if this is actually a complete equation (ends with \))
      if (fullMatch.endsWith('\\)') && fullMatch.length > 3) continue
      
      // This is an incomplete inline equation
      const placeholder = `__MATH_INLINE_${mathPlaceholders.length}__`
      mathPlaceholders.push({ type: 'inline', equation: equation.trim(), isComplete: false })
      if (matchIndex !== undefined) {
        formatted = formatted.substring(0, matchIndex) + placeholder + formatted.substring(matchIndex + fullMatch.length)
        // Reset regex to avoid issues with string modification
        incompleteInlineRegex.lastIndex = 0
      }
    }
    
    // Step 9: Auto-detect equations without delimiters and wrap them
    // Look for standalone equations on their own lines (block) or inline patterns
    // Split by lines to process separately
    const lines = formatted.split('\n')
    const processedLines: string[] = []
    
    for (let lineIdx = 0; lineIdx < lines.length; lineIdx++) {
      const line = lines[lineIdx]
      if (!line) {
        processedLines.push('')
        continue
      }
      
      // Skip lines that already have math placeholders
      if (line.includes('__MATH_BLOCK_') || line.includes('__MATH_INLINE_')) {
        processedLines.push(line)
        continue
      }
      
      // Check if entire line looks like an equation (block equation)
      const trimmedLine = line.trim()
      if (trimmedLine && looksLikeEquation(trimmedLine) && !trimmedLine.includes('__MATH_')) {
        // Check if previous/next lines are empty or contain placeholders (likely a standalone equation)
        const prevLine = lineIdx > 0 ? (lines[lineIdx - 1]?.trim() || '') : ''
        const nextLine = lineIdx < lines.length - 1 ? (lines[lineIdx + 1]?.trim() || '') : ''
        const isStandalone = (!prevLine || prevLine.includes('__MATH_') || prevLine === '') && 
                            (!nextLine || nextLine.includes('__MATH_') || nextLine === '')
        
        if (isStandalone && trimmedLine.length > 5) {
          // Wrap as block equation
          const placeholder = `__MATH_BLOCK_${mathPlaceholders.length}__`
          mathPlaceholders.push({ type: 'block', equation: trimmedLine, isComplete: true })
          processedLines.push(placeholder)
          continue
        }
      }
      
      // For now, we only auto-detect standalone block equations
      // Inline equations without delimiters are trickier to detect reliably
      // Users should wrap them in $...$ or \(...\) delimiters
      processedLines.push(line)
    }
    
    formatted = processedLines.join('\n')
    */
    
    // LINKS DISABLED: No longer extracting or preserving HTML links
    // Escape HTML
    formatted = formatted
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
    
    // Convert markdown-style formatting with optimistic streaming support
    // This function tracks open tags and applies formatting immediately when opening tags are detected
    console.log('📝 Before formatMarkdownWithState, formatted contains **:', formatted.includes('**'), 'Sample:', formatted.substring(0, 150))
    formatted = formatMarkdownWithState(formatted)
    console.log('📝 After formatMarkdownWithState, formatted contains **:', formatted.includes('**'), 'Sample:', formatted.substring(0, 150))
    
    // Debug: Check if ** patterns remain (they should be converted to <strong>)
    if (formatted.includes('**') && !formatted.includes('__MATH_')) {
      console.warn('⚠️ Unprocessed ** pattern detected in formatted text after markdown processing:', formatted.substring(0, 300))
    }
    
    // DISABLED: MathJax restoration - uncomment if math extraction is re-enabled
    /*
    // Restore MathJax equations with proper LaTeX delimiters
    // IMPORTANT: Equations are extracted BEFORE markdown processing, so their LaTeX syntax
    // (including subscripts _ and superscripts ^) is preserved intact for MathJax to render
    // Use $$...$$ for block equations and $...$ for inline equations (standard MathJax format)
    mathPlaceholders.forEach((math, index) => {
      // Unescape HTML entities that were applied during HTML escaping
      // This restores the original LaTeX syntax (e.g., C_e, V^2, \cdot, etc.)
      const equation = math.equation
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'")
      
      // Render equation with proper LaTeX delimiters
      // MathJax will process the LaTeX syntax including subscripts (_), superscripts (^), etc.
      // Use $$...$$ for block equations and $...$ for inline equations
      // For incomplete equations, still render with opening delimiter so MathJax can process them when complete
      if (math.type === 'block') {
        const placeholder = `__MATH_BLOCK_${index}__`
        const openDelimiter = '$$'
        const closeDelimiter = math.isComplete ? '$$' : ''
        formatted = formatted.replace(
          placeholder, 
          `<div class="my-4 text-center">${openDelimiter}${equation}${closeDelimiter}</div>`
        )
      } else {
        const placeholder = `__MATH_INLINE_${index}__`
        const openDelimiter = '$'
        const closeDelimiter = math.isComplete ? '$' : ''
        formatted = formatted.replace(
          placeholder, 
          `${openDelimiter}${equation}${closeDelimiter}`
        )
      }
    })
    */
    
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

