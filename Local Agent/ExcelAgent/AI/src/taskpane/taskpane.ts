/* global Excel, Office */

import { getEndpoint, getAuthToken } from "../config/api.config";

Office.onReady((info) => {
  if (info.host === Office.HostType.Excel) {
    document.getElementById("send-command")!.onclick = sendCommand;
    
    // Allow Enter key to send
    const input = document.getElementById("command-input") as HTMLInputElement;
    input.addEventListener("keypress", (e) => {
      if (e.key === "Enter" && !(e.shiftKey || e.ctrlKey)) {
        e.preventDefault();
        sendCommand();
      }
    });

    // Enable intelligent awareness
    setupIntelligentAwareness();
    
    // Add welcome message - will be added after chat functions are defined
    setTimeout(() => {
      addChatMessage("assistant", "👋 Hi! I'm your intelligent Excel design assistant. Ask me anything about your spreadsheet - I can update values, verify formulas, explain building codes, and analyze your sheet structure.");
    }, 100);
  }
});

// ============================================================================
// INTELLIGENT AWARENESS SYSTEM
// ============================================================================

async function setupIntelligentAwareness() {
  try {
    await Excel.run(async (context) => {
      const sheet = context.workbook.worksheets.getActiveWorksheet();
      const workbook = context.workbook;
      
      // 1. Listen for selection changes - know what user is looking at
      sheet.onSelectionChanged.add(handleSelectionChange);
      
      // 2. Listen for cell edits - detect when user changes values
      sheet.onChanged.add(handleCellChange);
      
      await context.sync();
      
      console.log("✓ Intelligent awareness enabled");
      logAwareness("✅ Monitoring Excel for user actions");
    });
  } catch (error) {
    console.error("Failed to setup awareness:", error);
  }
}

// Selection changed - user clicked on different cells
async function handleSelectionChange(event: Excel.WorksheetSelectionChangedEventArgs) {
  try {
    await Excel.run(async (context) => {
      const selectedRange = context.workbook.getSelectedRange();
      selectedRange.load("address, values, formulas, numberFormat");
      await context.sync();
      
      const address = selectedRange.address;
      const value = selectedRange.values[0]?.[0];
      const formula = selectedRange.formulas[0]?.[0];
      
      logAwareness(`👁️ User selected: ${address}`);
      
      // Analyze what user is looking at
      const analysis = analyzeSelection(selectedRange);
      
      // Show contextual help in task pane
      if (analysis.suggestion) {
        showContextualSuggestion(analysis);
      }
      
    });
  } catch (error) {
    console.error("Selection change handler error:", error);
  }
}

// Cell changed - user edited a value
async function handleCellChange(event: Excel.WorksheetChangedEventArgs) {
  try {
    const changedAddress = event.address;
    const details = event.details;
    
    logAwareness(`✏️ Cell changed: ${changedAddress}`);
    
    // Check if this is a critical design parameter
    const isCritical = await isCriticalParameter(changedAddress);
    
    if (isCritical) {
      logAwareness(`🎯 Critical parameter changed: ${changedAddress}`);
      
      // Automatically trigger intelligent recalculation
      await handleCriticalChange(changedAddress, details);
    }
    
  } catch (error) {
    console.error("Cell change handler error:", error);
  }
}

// Worksheet activated - user switched to different sheet
async function handleWorksheetChange(event: Excel.WorksheetActivatedEventArgs) {
  try {
    await Excel.run(async (context) => {
      // Get worksheet by ID
      const sheet = context.workbook.worksheets.getItem(event.worksheetId);
      sheet.load("name");
      await context.sync();
      
      logAwareness(`📄 User switched to sheet: ${sheet.name}`);
      
      // Offer contextual help based on sheet
      const sheetContext = analyzeSheetContext(sheet.name);
      if (sheetContext.suggestion) {
        showStatus(`💡 In "${sheet.name}": ${sheetContext.suggestion}`);
      }
    });
  } catch (error) {
    console.error("Worksheet change handler error:", error);
  }
}

// Check if a cell is a critical design parameter
async function isCriticalParameter(address: string): Promise<boolean> {
  // Extract row number from address (e.g., "B15" -> 15)
  const rowMatch = address.match(/\d+/);
  if (!rowMatch) return false;
  
  const rowNum = parseInt(rowMatch[0]);
  
  try {
    let result = false;
    await Excel.run(async (context) => {
      const sheet = context.workbook.worksheets.getActiveWorksheet();
      const rowRange = sheet.getRange(`${rowNum}:${rowNum}`);
      rowRange.load("values");
      await context.sync();
      
      // Check if the row label indicates a critical parameter
      const rowData = rowRange.values[0];
      const labels = rowData.join(" ").toLowerCase();
      
      const criticalKeywords = [
        "span", "load", "strength", "force", "moment", "shear",
        "deflection", "concrete", "steel", "width", "depth"
      ];
      
      result = criticalKeywords.some(keyword => labels.includes(keyword));
    });
    return result;
  } catch (error) {
    return false;
  }
}

// Handle critical parameter changes intelligently
async function handleCriticalChange(address: string, details: any) {
  showStatus("🤔 Analyzing impact of your change...");
  
  try {
    // Get full workbook context
    const context = await extractWorkbookContext();
    
    // Get the new value
    let newValue = null;
    await Excel.run(async (context) => {
      const sheet = context.workbook.worksheets.getActiveWorksheet();
      const range = sheet.getRange(address);
      range.load("values");
      await context.sync();
      newValue = range.values[0][0];
    });
    
    // Create intelligent command for backend
    const command = `User changed cell ${address} to ${newValue}. This is a critical design parameter. Analyze the impact and recalculate all dependent values.`;
    
    // Send to backend for intelligent processing
    const response = await processCommandWithBackend(command, context);
    
    // Apply the response
    await applyResponse(response);
    
    showStatus(`✓ Intelligently updated dependent values`);
    
  } catch (error) {
    console.error("Critical change handler error:", error);
    showStatus("Error processing change", true);
  }
}

// Analyze what the user selected to provide context
function analyzeSelection(range: Excel.Range): any {
  const address = range.address;
  const values = range.values;
  const formulas = range.formulas;
  
  // Detect if user selected a formula
  if (formulas[0][0] && formulas[0][0].includes("=")) {
    return {
      type: "formula",
      suggestion: "I see you're looking at a calculated value. Would you like me to explain this formula or verify it against design codes?"
    };
  }
  
  // Detect if user selected a value
  if (values[0][0] !== null && typeof values[0][0] === 'number' && values[0][0] > 1000) {
    return {
      type: "large_value",
      suggestion: "This looks like it might need validation. Would you like me to check this against design codes?"
    };
  }
  
  return { type: "unknown", suggestion: null };
}

// Analyze sheet context
function analyzeSheetContext(sheetName: string): any {
  const nameLower = sheetName.toLowerCase();
  
  if (nameLower.includes("beam")) {
    return {
      suggestion: "Working on beam design? I can calculate forces and validate against AS3600."
    };
  } else if (nameLower.includes("column")) {
    return {
      suggestion: "Column design? I can check axial capacity and slenderness."
    };
  } else if (nameLower.includes("wall")) {
    return {
      suggestion: "Wall design? I can analyze loads and reinforcement."
    };
  }
  
  return { suggestion: null };
}

// Show contextual suggestion to user (via chat if available)
function showContextualSuggestion(analysis: any) {
  if (analysis.suggestion && typeof addChatMessage !== 'undefined') {
    // If chat is available, use it; otherwise just log
    try {
      addChatMessage("assistant", `💡 **Suggestion:** ${analysis.suggestion}`);
    } catch {
      console.log(`💡 Suggestion: ${analysis.suggestion}`);
    }
  } else if (analysis.suggestion) {
    console.log(`💡 Suggestion: ${analysis.suggestion}`);
  }
}

// Log awareness events for debugging
function logAwareness(message: string) {
  console.log(`[AWARENESS] ${message}`);
}

// ============================================================================
// CHAT MESSAGE FUNCTIONS
// ============================================================================

// Format plain text to HTML with paragraphs, bullets, and structure
function formatMessage(text: string): string {
  if (!text) return "";
  
  // Split by double newlines to create paragraphs
  let formatted = text
    // Convert markdown-style headers
    .replace(/^### (.*$)/gim, '<h4>$1</h4>')
    .replace(/^## (.*$)/gim, '<h3>$1</h3>')
    // Convert bullet points (• or -)
    .replace(/^[•\-]\s+(.+)$/gim, '<li>$1</li>')
    // Convert numbered lists
    .replace(/^\d+\.\s+(.+)$/gim, '<li>$1</li>')
    // Convert code blocks
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // Wrap consecutive list items in <ul>
    .replace(/(<li>.*<\/li>\n?)+/g, (match) => {
      return '<ul>' + match.replace(/\n/g, '') + '</ul>';
    })
    // Convert line breaks to paragraphs
    .split('\n\n')
    .filter(para => para.trim().length > 0)
    .map(para => {
      para = para.trim();
      // If already wrapped in HTML tags, don't wrap in <p>
      if (para.startsWith('<') || para.match(/^<[hlu]/)) {
        return para;
      }
      // Otherwise wrap in <p>
      return '<p>' + para.replace(/\n/g, '<br>') + '</p>';
    })
    .join('');
  
  return formatted;
}

// Add a message to the chat
function addChatMessage(role: "user" | "assistant", text: string, isTyping: boolean = false) {
  const chatMessages = document.getElementById("chat-messages")!;
  
  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${role}`;
  
  const bubbleDiv = document.createElement("div");
  bubbleDiv.className = "message-bubble";
  
  if (isTyping) {
    bubbleDiv.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
  } else {
    bubbleDiv.innerHTML = formatMessage(text);
  }
  
  messageDiv.appendChild(bubbleDiv);
  chatMessages.appendChild(messageDiv);
  
  // Auto-scroll to bottom
  chatMessages.scrollTop = chatMessages.scrollHeight;
  
  return messageDiv;
}

// Show typing indicator
function showTypingIndicator(): HTMLElement {
  return addChatMessage("assistant", "", true);
}

// Remove typing indicator
function removeTypingIndicator(indicator: HTMLElement) {
  indicator.remove();
}

// Pretty-print label map into the chat (and console with full JSON)
function showLabelMapInChat(context: any) {
  try {
    const labelMap = context?.labelMap || {};
    const entries = Object.entries(labelMap) as Array<[string, string]>;
    const count = entries.length;
    // Sort by label for readability
    entries.sort((a, b) => a[0].localeCompare(b[0]));
    const maxToShow = 200;
    const shown = entries.slice(0, maxToShow);
    const list = shown.map(([k, v]) => `- ${k} → ${v}`).join('\n');
    // Log full JSON to console for copy/export
    console.log("LabelMap (full JSON):", JSON.stringify(labelMap, null, 2));
    addChatMessage(
      "assistant",
      `### Label Map (${count} entries)\n\n${list}${count > maxToShow ? `\n\n…and ${count - maxToShow} more (full JSON in console).` : ''}`
    );
  } catch (e) {
    addChatMessage("assistant", `Failed to display label map: ${e}`);
  }
}

async function writeSampleData() {
  try {
    await Excel.run(async (context) => {
      const sheet = context.workbook.worksheets.getActiveWorksheet();
      const range = sheet.getRange("B2:D4");

      range.values = [
        ["Component", "Value", "Unit"],
        ["Beam Span", 12, "m"],
        ["Load", 5.5, "kN/m"],
      ];

      range.format.autofitColumns();

      await context.sync();
      showStatus("✓ Sample data written to B2:D4");
    });
  } catch (error) {
    showStatus("Error: " + error, true);
  }
}

async function readActiveCell() {
  try {
    await Excel.run(async (context) => {
      const range = context.workbook.getSelectedRange();
      range.load("address, values");

      await context.sync();

      const address = range.address;
      const value = range.values[0][0];

      showStatus(`✓ Read ${address}: ${value}`);
    });
  } catch (error) {
    showStatus("Error: " + error, true);
  }
}

async function formatSelection() {
  try {
    await Excel.run(async (context) => {
      const range = context.workbook.getSelectedRange();
      range.format.fill.color = "#E8F4F8";
      range.format.font.bold = true;
      range.format.font.color = "#0078D4";

      await context.sync();
      showStatus("✓ Selection formatted");
    });
  } catch (error) {
    showStatus("Error: " + error, true);
  }
}

async function createTable() {
  try {
    await Excel.run(async (context) => {
      const sheet = context.workbook.worksheets.getActiveWorksheet();

      // Create sample data
      const dataRange = sheet.getRange("F2:H5");
      dataRange.values = [
        ["Element", "Dimension", "Material"],
        ["Column", "300x300", "Concrete"],
        ["Beam", "400x600", "Concrete"],
        ["Slab", "200", "Concrete"],
      ];

      // Create table from the range
      const table = sheet.tables.add("F2:H5", true);
      table.name = "DesignTable";
      table.getHeaderRowRange().format.fill.color = "#0078D4";
      table.getHeaderRowRange().format.font.color = "white";

      await context.sync();
      showStatus("✓ Design table created at F2:H5");
    });
  } catch (error) {
    showStatus("Error: " + error, true);
  }
}

// Intelligently resolve a cell address to its label and symbol - NO HARDCODED COLUMNS!
// Works for ANY spreadsheet layout by analyzing cell content patterns
function resolveCellToVariable(
  cellAddress: string,
  allData: any[][],
  layoutStructure?: any,
  strictSameRow: boolean = false,
  startRow: number = 1,
  startColumn: number = 1
): { label: string; symbol: string; value: any } {
  const match = cellAddress.match(/([A-Z]+)(\d+)/);
  if (!match) return { label: "", symbol: "", value: null };
  
  const colLetters = match[1];
  const absRow = parseInt(match[2]);
  // Convert letters to absolute column number
  let absCol = 0;
  for (let i = 0; i < colLetters.length; i++) {
    absCol = absCol * 26 + (colLetters.charCodeAt(i) - 64);
  }
  
  // Convert to 0-based indices relative to usedRange top-left
  const rowNum = absRow - startRow; // 0-based row within allData
  const colNum = absCol - startColumn; // 0-based col within allData
  
  if (rowNum < 0 || rowNum >= allData.length || !allData[rowNum]) {
    return { label: "", symbol: "", value: null };
  }
  
  const row = allData[rowNum];
  const value = (colNum >= 0 && colNum < row.length) ? row[colNum] : null;
  
  let label = "";
  let symbol = "";
  
  // ENHANCED: Extract column info from layout structure
  const labelColumns: number[] = [];
  const symbolColumns: number[] = [];
  
  if (layoutStructure) {
    if (layoutStructure.label_column) {
      const lc = layoutStructure.label_column.charCodeAt(0) - 65;
      if (lc >= 0) labelColumns.push(lc);
    }
    if (layoutStructure.symbol_column) {
      const sc = layoutStructure.symbol_column.charCodeAt(0) - 65;
      if (sc >= 0) symbolColumns.push(sc);
    }
  }
  
  // INTELLIGENT SCANNING: Collect and classify all text cells in neighborhood
  const candidates: Array<{col: number, text: string, looksLikeSymbol: boolean, looksLikeLabel: boolean, rowOffset: number, score: number}> = [];
  
  // Priority 1: Scan SAME ROW (highest priority)
  for (let c = colNum - 1; c >= Math.max(0, colNum - 10); c--) {
    if (c < row.length && row[c] && typeof row[c] === 'string') {
      let cellText = String(row[c]).trim();
      // Remove trailing commas/punctuation
      cellText = cellText.replace(/[,\s]+$/, '');
      
      // Skip if it's just a number or empty
      if (cellText.length === 0 || /^[0-9.E+\-()]+$/i.test(cellText)) {
        continue;
      }
      
      // Classify by content pattern
      const cleanText = cellText.replace(/\s/g, '');
      
      // SYMBOL PATTERNS: Very specific - short engineering notation (2-6 chars)
      // Examples: K_T, E_os, E05, P_e, Led, Le, Ccs, Ccw, KT, KSE, I, A
      const looksLikeSymbol = (
        cellText.length >= 2 && cellText.length <= 6 &&  // Very short (Led=3, Ccs=3, K_T=3)
        /^[A-Z]/i.test(cellText) &&  // Starts with letter
        !cellText.includes(' ') &&  // NO spaces (symbols are compact)
        (
          /_/.test(cellText) ||  // Contains underscore (K_T, E_os, P_e)
          /[0-9]/.test(cleanText) ||  // Contains number (E05, E05S)
          // 2-4 letter engineering symbols (Led, Le, Ccs, Ccw, KT, I, A)
          /^[A-Z][a-z]*$/i.test(cleanText)
        )
      );
      
      // LABEL PATTERNS: Longer descriptive text with engineering keywords
      // Examples: "Treatment factor", "Effective Length, Strong Axis", "Euler Buckling Load"
      const looksLikeLabel = (
        cellText.length > 10 ||  // Definitely long (10+ chars)
        (cellText.includes(' ') && cellText.length > 5) ||  // Multi-word and not too short
        /factor|modulus|elasticity|buckling|resistance|strength|length|inertia|treatment|service|condition|effective|slenderness|ratio|parallel|grain|section|moment|tensile|compressive|bending|axial/i.test(cellText) ||  // Engineering keywords
        (cellText.includes(',') && cellText.length > 5) ||  // Contains comma (often in labels like "Effective Length, Strong Axis")
        (cellText.length > 15 && !/_/.test(cellText) && !/[0-9]/.test(cellText))  // Very long descriptive text
      );
      
      // Score based on layout structure match and position
      let score = 100; // Base score for same-row
      if (layoutStructure) {
        if (labelColumns.includes(c) && looksLikeLabel) score += 50; // Bonus for layout-matched label column
        if (symbolColumns.includes(c) && looksLikeSymbol) score += 50; // Bonus for layout-matched symbol column
      }
      
      candidates.push({
        col: c,
        text: cellText,
        looksLikeSymbol,
        looksLikeLabel,
        rowOffset: 0, // Same row
        score: score
      });
    }
  }
  
  // Priority 2: If layout says labels can be in other rows, check adjacent rows
  const labelPositions = layoutStructure?.label_positions || [];
  if ((labelPositions.includes("above-row") || labelPositions.includes("header-row")) || strictSameRow) {
    // Check row above (rowNum - 1)
    if (rowNum > 0) {
      const rowAbove = allData[rowNum - 1];
      if (rowAbove) {
        // Check columns from layout structure or common positions
        const colsToCheck = labelColumns.length > 0 ? labelColumns : [Math.max(0, colNum - 5), Math.max(0, colNum - 3), Math.max(0, colNum - 1)];
        for (const c of colsToCheck) {
          if (c >= 0 && c < rowAbove.length && rowAbove[c] && typeof rowAbove[c] === 'string') {
            const cellText = String(rowAbove[c]).trim().replace(/[\,\s]+$/, '');
            if (cellText.length > 5 && !/^[0-9.E+\-()]+$/i.test(cellText)) {
              const looksLikeLabel = cellText.length > 10 || cellText.includes(' ') || 
                /factor|modulus|elasticity|buckling|resistance|strength|length|effective|inertia|section|neutral|volume/i.test(cellText);
              
              if (looksLikeLabel) {
                candidates.push({
                  col: c,
                  text: cellText,
                  looksLikeSymbol: false,
                  looksLikeLabel: true,
                  rowOffset: -1,
                  score: 70 // Lower score for adjacent row
                });
              }
            }
          }
        }
      }
    }
  }
  
  // CRITICAL: Prioritize SAME-ROW matches (labels/symbols are usually in same row as value)
  // Then use classification confidence to pick best matches
  
  // Score candidates: same-row gets priority, then classification confidence
  const scoredSymbols: Array<{text: string, score: number}> = [];
  const scoredLabels: Array<{text: string, score: number}> = [];
  
  for (const candidate of candidates) {
    // Use candidate's score (already includes layout bonuses and row offset)
    // Additional proximity bonus: closer to value cell = higher score
    const distance = colNum - candidate.col;
    let finalScore = candidate.score;
    if (distance <= 5 && candidate.rowOffset === 0) {
      finalScore += (6 - distance) * 5; // Bonus decreases with distance
    }
    
    if (candidate.looksLikeSymbol) {
      scoredSymbols.push({
        text: candidate.text,
        score: finalScore
      });
    } else if (!symbol && candidate.text.length <= 10 && !candidate.text.includes(' ') && /^[A-Z]/i.test(candidate.text)) {
      scoredSymbols.push({
        text: candidate.text,
        score: finalScore * 0.3
      });
    }
    
    if (candidate.looksLikeLabel) {
      scoredLabels.push({
        text: candidate.text,
        score: finalScore
      });
    } else if (!label && (candidate.text.length > 8 || candidate.text.includes(' '))) {
      scoredLabels.push({
        text: candidate.text,
        score: finalScore * 0.4
      });
    }
  }
  
  // Select best symbol (highest score)
  if (scoredSymbols.length > 0) {
    scoredSymbols.sort((a, b) => b.score - a.score);
    symbol = scoredSymbols[0].text;
  }
  
  // Select best label (highest score, exclude selected symbol, prefer same-row)
  if (scoredLabels.length > 0) {
    scoredLabels.sort((a, b) => b.score - a.score);
    // Prefer same-row candidates (rowOffset = 0)
    const sameRowLabels = scoredLabels.filter(l => {
      const candidate = candidates.find(c => c.text === l.text);
      return candidate && candidate.rowOffset === 0;
    });
    const labelsToUse = sameRowLabels.length > 0 ? sameRowLabels : scoredLabels;
    label = labelsToUse.find(l => l.text !== symbol)?.text || labelsToUse[0].text;
  }
  
  // Fallback: if still missing, use longest/shortest heuristics
  if (!symbol && candidates.length > 0) {
    const potentialSymbols = candidates
      .filter(c => !label || c.text !== label)
      .filter(c => c.text.length <= 10 && !c.text.includes(' ') && /^[A-Z]/i.test(c.text));
    if (potentialSymbols.length > 0) {
      symbol = potentialSymbols.reduce((prev, curr) => 
        curr.text.length < prev.text.length ? curr : prev
      ).text;
    }
  }
  
  if (!label && candidates.length > 0) {
    const potentialLabels = candidates
      .filter(c => !symbol || c.text !== symbol)
      .filter(c => c.text.length > 5);
    if (potentialLabels.length > 0) {
      label = potentialLabels.reduce((prev, curr) => 
        curr.text.length > prev.text.length ? curr : prev
      ).text;
    }
  }
  
  // Clean up
  if (label) {
    label = label.replace(/[,\s]+$/, '').trim();
  }
  if (symbol) {
    symbol = symbol.trim();
  }
  
  return { label, symbol, value };
}

// Parse formula and extract all cell references with their meanings
function parseFormulaDependencies(formula: string, allData: any[][], layoutStructure?: any, startRow?: number, startColumn?: number): Array<{ cell: string; label: string; symbol: string; value: any }> {
  if (!formula || !formula.startsWith('=')) {
    return [];
  }
  const cellRefRegex = /([A-Z]{1,3}\d{1,7})/g;
  const matches = formula.match(cellRefRegex) || [];
  const m = matches as string[];
  const cellRefs = m.filter((ref, idx) => m.indexOf(ref) === idx);
  const dependencies = cellRefs.map(cellAddr => {
    const resolved = resolveCellToVariable(cellAddr, allData, layoutStructure, true, startRow || 1, startColumn || 1);
    return { cell: cellAddr, label: resolved.label, symbol: resolved.symbol, value: resolved.value };
  });
  return dependencies;
}

// Extract intelligent context about the selected cell
async function getSelectedCellContext(context: any): Promise<string> {
  try {
    const selectedRange = context.selectedRange || {};
    const address = selectedRange.address || "";
    const value = selectedRange.values?.[0]?.[0];
    const formula = selectedRange.formulas?.[0]?.[0];
    
    if (!address || address === "Unknown") {
      return "";
    }
    
    const labelMap = context.labelMap || {};
    const usedRange = context.usedRange || {};
    const allData = usedRange.allData || [];
    
    // Find what this cell represents
    let cellLabel = "";
    let cellSymbol = "";
    let cellDescription = "";
    
    // Check labelMap reverse lookup (normalize sheet-qualified address like 'Sheet!G77' → 'G77')
    const bareAddress = (address.includes('!') ? address.split('!')[1] : address);
    for (const [label, mappedAddr] of Object.entries(labelMap)) {
      if (mappedAddr === bareAddress) {
        cellLabel = label;
        break;
      }
    }
    
    // If no label in map, use row pattern resolution with layout structure
    if (!cellLabel) {
      const match = address.match(/([A-Z]+)(\d+)/);
      if (match) {
        const layoutStructure = context.layoutStructure || null;
        const startRow = context.usedRange?.dimensions?.startRow || 1;
        const startColumn = context.usedRange?.dimensions?.startColumn || 1;
        const resolved = resolveCellToVariable(address, allData, layoutStructure, true, startRow, startColumn);
        cellLabel = resolved.label;
        cellSymbol = resolved.symbol || cellSymbol;
      }
    }
    
    // Try to extract symbol/notation from label (e.g., "Euler Buckling Load, PE")
    if (cellLabel) {
      const symbolMatch = cellLabel.match(/[,:]([A-Z][_0-9A-Za-z]+)/);
      if (symbolMatch) {
        cellSymbol = symbolMatch[1];
      }
      
      // Common engineering symbols in labels
      const symbolPatterns = [
        /\b([A-Z][_0-9A-Za-z]+)\b/g,
        /\(([A-Z][_0-9A-Za-z]+)\)/g
      ];
      
      for (const pattern of symbolPatterns) {
        const matches = cellLabel.match(pattern);
        if (matches) {
          // Look for common engineering symbols
          const engineeringSymbols = ['PE', 'Pr', 'Mr', 'Mf', 'Pf', 'Tr', 'Tf', 'Vf', 'Vr', 'Le', 'Ce', 'Ck', 'E05', 'E05S', 'KSE', 'KT', 'KM', 'I', 'A', 'F'];
          for (const match of matches) {
            const cleanSymbol = match.replace(/[(),:]/g, '');
            if (engineeringSymbols.includes(cleanSymbol)) {
              cellSymbol = cleanSymbol;
              break;
            }
          }
          if (cellSymbol) break;
        }
      }
    }
    
    // STEP 2: If cell has a formula, parse and track all dependencies
    let formulaDependencies = "";
    if (formula && formula.startsWith('=')) {
      const layoutStructure = context.layoutStructure || null;
      const startRow = context.usedRange?.dimensions?.startRow || 1;
      const startColumn = context.usedRange?.dimensions?.startColumn || 1;
      const dependencies = parseFormulaDependencies(formula, allData, layoutStructure, startRow, startColumn);
      
      if (dependencies.length > 0) {
        formulaDependencies = "\n\nFormula Dependencies:\n";
        dependencies.forEach(dep => {
          let depInfo = `  • ${dep.cell}`;
          if (dep.symbol) {
            depInfo += ` = ${dep.symbol}`;
          }
          if (dep.label) {
            depInfo += ` (${dep.label})`;
          }
          if (dep.value !== null && dep.value !== undefined) {
            depInfo += ` = ${dep.value}`;
          }
          formulaDependencies += depInfo + "\n";
        });
        
        // Add formula structure explanation
        formulaDependencies += `\nFormula Structure: ${formula}`;
      }
    }
    
    // STEP 3: Build comprehensive description
    let description = `Selected cell ${address}`;
    if (cellLabel) {
      description += ` represents "${cellLabel}"`;
    }
    if (cellSymbol) {
      description += ` (symbol: ${cellSymbol})`;
    }
    if (value !== null && value !== undefined) {
      description += `\nCurrent value: ${value}`;
    }
    if (formulaDependencies) {
      description += formulaDependencies;
    } else if (formula && formula.startsWith('=')) {
      description += `\nFormula: ${formula}`;
    }
    
    return description;
  } catch (error) {
    console.error("Error extracting selected cell context:", error);
    return "";
  }
}

async function sendCommand() {
  const input = document.getElementById("command-input") as HTMLInputElement;
  let command = input.value.trim();

  if (!command) {
    return;
  }

  // Add user message to chat
  addChatMessage("user", command);
  
  // Clear input and disable button
  input.value = "";
  const sendButton = document.getElementById("send-command") as HTMLButtonElement;
  sendButton.disabled = true;
  
  // Show typing indicator
  const typingIndicator = showTypingIndicator();

  try {
    // Extract current workbook context
    const workbookContext = await extractWorkbookContext();
    
    // Quick debug command: show label map
    const cmdLower = command.toLowerCase();
    if (cmdLower.includes("show label map") || cmdLower === "label map" || cmdLower.includes("list labels")) {
      showLabelMapInChat(workbookContext);
      removeTypingIndicator(typingIndicator);
      return;
    }

    // Check if command references "clicked cell", "selected cell", "this cell"
    const cellReferencePattern = /(clicked cell|selected cell|this cell|current cell)/i;
    if (cellReferencePattern.test(command)) {
      const cellContext = await getSelectedCellContext(workbookContext);
      if (cellContext) {
        // Enhance command with cell context
        command = `${command} (Context: ${cellContext})`;
      }
    }
    
    // Send to backend for intelligent processing
    const response = await processCommandWithBackend(command, workbookContext);
    
    // Apply the intelligent response
    await applyResponse(response);
    
    // Remove typing indicator and add assistant response
    removeTypingIndicator(typingIndicator);
    addChatMessage("assistant", response.message || "Done!");
    
  } catch (error) {
    // Remove typing indicator and show error
    removeTypingIndicator(typingIndicator);
    addChatMessage("assistant", `❌ Error: ${error}. Please check that the backend is running.`);
    console.error("Command error:", error);
  } finally {
    // Re-enable button
    sendButton.disabled = false;
    input.focus();
  }
}

// Extract meaningful context from the workbook for the AI
async function extractWorkbookContext(): Promise<any> {
  return await Excel.run(async (context) => {
    const workbook = context.workbook;
    const sheet = context.workbook.worksheets.getActiveWorksheet();
    const selectedRange = context.workbook.getSelectedRange();
    
    // Load workbook properties
    workbook.load("name");
    sheet.load("name");
    selectedRange.load("address, values, formulas, numberFormat");
    
    // Get all tables in the sheet
    const tables = sheet.tables;
    tables.load("items");
    
    await context.sync();
    
    // Extract table data if available
    const tableData = [];
    for (let i = 0; i < tables.items.length; i++) {
      const table = tables.items[i];
      table.load("name, rows/items, columns/items");
      await context.sync();
      
      const headerRange = table.getHeaderRowRange();
      headerRange.load("values");
      await context.sync();
      
      tableData.push({
        name: table.name,
        headers: headerRange.values[0],
        rowCount: table.rows.items.length
      });
    }
    
    // Try to detect common engineering patterns in the sheet
    const usedRange = sheet.getUsedRange();
    usedRange.load("address, values, rowCount, columnCount");
    await context.sync();
    
    // Get ALL data from the sheet
    const allData = usedRange.values;

    // Parse usedRange top-left (start row/col)
    // Examples: "A1:D200" or "G41:O200"
    let startRow = 1;
    let startCol = 1;
    try {
      const addr = usedRange.address || "A1";
      const firstCell = addr.split(":")[0];
      const match = firstCell.match(/([A-Z]+)(\d+)/);
      if (match) {
        const colLetters = match[1];
        const rowNumber = parseInt(match[2], 10);
        // Convert letters to number (A=1, B=2, ..., Z=26, AA=27, ...)
        let colNumber = 0;
        for (let i = 0; i < colLetters.length; i++) {
          colNumber = colNumber * 26 + (colLetters.charCodeAt(i) - 64);
        }
        startRow = rowNumber;
        startCol = colNumber;
      }
    } catch (e) {
      console.warn("Failed to parse usedRange address for offsets:", e);
    }
    
    // Build intelligent label mapping - find where each parameter is
    const labelMap: { [label: string]: string } = {};
    
    // Scan entire sheet for labels and their associated values
    // Many engineering sheets place the value 2-5 columns to the right of the label
    for (let i = 0; i < allData.length; i++) {
      const row = allData[i];
      for (let j = 0; j < row.length - 1; j++) {
        const cell = row[j];
        
        if (cell && typeof cell === 'string' && !cell.startsWith('=')) {
          const normalLabel = cell.trim().replace(/[,:;]+$/,'').toLowerCase();
          
          // Filter out garbage: skip single letters, numbers, or very short labels
          if (normalLabel.length > 2 && !/^[0-9.]+$/.test(normalLabel)) {
            // Search up to 5 columns to the right for the first numeric-looking value
            let foundAddress: string | null = null;
            for (let offset = 1; offset <= 5 && (j + offset) < row.length; offset++) {
              const candidate = row[j + offset];
              const isNumeric = candidate !== null && candidate !== undefined &&
                (typeof candidate === 'number' || !isNaN(parseFloat(candidate)));
              if (isNumeric) {
                // Convert from usedRange-relative indices to absolute worksheet address
                const absColNumber = startCol + (j + offset); // startCol is 1-based, j is 0-based
                const absRowNumber = startRow + i; // startRow is 1-based, i is 0-based
                const colLetter = getColumnLetter(absColNumber);
                foundAddress = `${colLetter}${absRowNumber}`;
                break;
              }
            }
            if (foundAddress) {
              labelMap[normalLabel] = foundAddress;
            }
          }
        }
      }
    }
    
    // Detect sheet structure - find section headers
    const sectionHeaders: { [label: string]: string } = {};
    for (let i = 0; i < Math.min(50, allData.length); i++) {
      const row = allData[i];
      if (row && row[0] && typeof row[0] === 'string') {
        const cellText = (row[0] as string).trim();
        // Detect section headers (usually bold or numbered sections)
        if (cellText.match(/^\d+\.\s+[A-Z]/) || cellText.match(/^[A-Z][A-Z\s]+$/)) {
          const colLetter = getColumnLetter(1);
          sectionHeaders[cellText.toLowerCase()] = `${colLetter}${i + 1}`;
        }
      }
    }
    
    // Detect material type from labels
    const labelsText = Object.keys(labelMap).join(" ").toLowerCase();
    let detectedMaterial = "unknown";
    if (labelsText.includes("glulam") || labelsText.includes("wood species") || labelsText.includes("timber")) {
      detectedMaterial = "timber";
    } else if (labelsText.includes("f'c") || labelsText.includes("concrete strength")) {
      detectedMaterial = "concrete";
    } else if (labelsText.includes("fy") || labelsText.includes("steel")) {
      detectedMaterial = "steel";
    }
    
    // Intelligently detect legend using AI (if backend available)
    const legendInfo = await detectLegendIntelligently(sheet, allData);
    
    // STEP: Use LLM to analyze layout structure for smarter label mapping
    let layoutStructure: any = null;
    try {
      layoutStructure = await analyzeSheetLayout(workbook.name || "Unknown", sheet.name, allData);
      logToScreen(`📐 Layout analysis: ${layoutStructure?.layout_pattern || 'unknown'} pattern detected`);
    } catch (error) {
      console.warn("Layout analysis failed, using fallback:", error);
      // Fallback to default structure
      layoutStructure = {
        layout_pattern: "same-row",
        label_column: "B",
        symbol_column: "D",
        value_column: "G"
      };
    }
    
    return {
      workbookName: workbook.name || "Unknown",
      sheetName: sheet.name,
      selectedRange: {
        address: selectedRange.address,
        values: selectedRange.values,
        formulas: selectedRange.formulas,
      },
      tables: tableData,
      usedRange: {
        address: usedRange.address,
        allData: allData.slice(0, 500), // Send first 500 rows for better context
        dimensions: {
          rows: usedRange.rowCount,
          columns: usedRange.columnCount,
          startRow: startRow,
          startColumn: startCol
        }
      },
      labelMap: labelMap, // Intelligent mapping of labels to cell addresses
      sectionHeaders: sectionHeaders, // Section headers and their locations
      detectedMaterial: detectedMaterial, // Auto-detected material type
      legend: legendInfo, // AI-detected legend mapping colors to cell types
      layoutStructure: layoutStructure, // LLM-analyzed layout pattern (columns, positions)
      timestamp: new Date().toISOString()
    };
  });
}

// Analyze sheet layout using backend LLM
async function analyzeSheetLayout(workbookName: string, sheetName: string, allData: any[][]): Promise<any> {
  try {
    // Format sample data for LLM
    const sampleRows = allData.slice(0, 50); // First 50 rows
    const sampleText = sampleRows.map((row, idx) => {
      const rowData = row.slice(0, 15).map((cell, colIdx) => {
        const colLetter = String.fromCharCode(65 + colIdx); // A, B, C...
        return `${colLetter}${idx + 1}: ${cell !== null && cell !== undefined ? String(cell).substring(0, 50) : ''}`;
      }).join(' | ');
      return `Row ${idx + 1}: ${rowData}`;
    }).join('\n');
    
    const { API_CONFIG } = await import('../config/api.config');
    const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.analyzeLayout}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sampleData: sampleText,
        sheetName: sheetName,
        workbookName: workbookName
      })
    });
    
    if (!response.ok) {
      throw new Error(`Layout analysis failed: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error("Layout analysis error:", error);
    // Return fallback structure
    return {
      layout_pattern: "same-row",
      label_column: "B",
      symbol_column: "D",
      value_column: "G"
    };
  }
}

// Intelligently detect legend using Excel API - identifies Input/Output/Calculation/Override cells
async function detectLegendIntelligently(sheet: Excel.Worksheet, allData: any[][]): Promise<any> {
  try {
    // First, search for a "Legend" or "Key" section in the sheet
    let legendStartRow = -1;
    let legendCells: any[] = [];
    
    // Scan first 100 rows for legend keywords
    for (let i = 0; i < Math.min(100, allData.length); i++) {
      const row = allData[i];
      if (!row) continue;
      
      // Look for cells containing "Legend", "Key", "Category", "Type", etc.
      const rowText = row.join(" ").toLowerCase();
      if (rowText.includes("legend") || rowText.includes("key") || 
          rowText.includes("category") || rowText.includes("type")) {
        // Found potential legend - extract it
        legendStartRow = i;
        
        // Get cell colors and formatting for legend rows (next 5-10 rows)
        for (let legendRow = i; legendRow < Math.min(i + 10, allData.length); legendRow++) {
          const legendRowData = allData[legendRow];
          if (!legendRowData) continue;
          
          // Check if this row looks like legend items (has text labels)
          const hasLabels = legendRowData.some((cell: any) => 
            cell && typeof cell === 'string' && 
            (cell.toLowerCase().includes("input") || 
             cell.toLowerCase().includes("output") ||
             cell.toLowerCase().includes("calc") ||
             cell.toLowerCase().includes("override") ||
             cell.toLowerCase().includes("result") ||
             cell.toLowerCase().includes("parameter"))
          );
          
          if (hasLabels) {
            // Extract legend item info with colors
            await Excel.run(async (context) => {
              const range = sheet.getRange(`${legendRow + 1}:${legendRow + 1}`);
              range.load("address, values, fill/color, font/color, format/fill");
              await context.sync();
              
              // Check each cell in the row
              for (let col = 0; col < range.values[0].length; col++) {
                const cellValue = range.values[0][col];
                if (cellValue && typeof cellValue === 'string') {
                  const cellAddress = getColumnLetter(col + 1) + (legendRow + 1);
                  const cellRange = sheet.getRange(cellAddress);
                  cellRange.load("fill/color, font/color, format/fill");
                  await context.sync();
                  
                  // Get color info (Office.js format)
                  const fillColor = cellRange.format.fill.color || null;
                  
                  legendCells.push({
                    address: cellAddress,
                    text: cellValue,
                    fillColor: fillColor,
                    row: legendRow + 1
                  });
                }
              }
            });
          }
        }
        break;
      }
    }
    
    // If we found legend cells, send to backend for intelligent classification
    if (legendCells.length > 0) {
      try {
        const endpoint = getEndpoint("command");
        const response = await fetch(`${endpoint.replace('/api/excel/command', '/api/excel/detect-legend')}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            legendCells: legendCells,
            sheetName: sheet.name || "Sheet1"
          })
        });
        
        if (response.ok) {
          const result = await response.json();
          return result;
        }
      } catch (error) {
        console.warn("Legend detection API unavailable, using local logic:", error);
      }
    }
    
    // Fallback: Use local pattern matching for common legend formats
    const localLegend = {
      legendFound: legendCells.length > 0,
      colorMappings: {} as any,
      cellClassifications: {} as any
    };
    
    // Simple pattern matching for common legend formats
    for (const cell of legendCells) {
      const text = cell.text.toLowerCase();
      let category = "unknown";
      
      if (text.includes("input") || text.includes("parameter") || text.includes("editable")) {
        category = "user_input";
      } else if (text.includes("output") || text.includes("result")) {
        category = "calculated_output";
      } else if (text.includes("calc") || text.includes("formula")) {
        category = "calculation";
      } else if (text.includes("override") || text.includes("manual")) {
        category = "override";
      }
      
      if (category !== "unknown" && cell.fillColor) {
        localLegend.colorMappings[cell.fillColor] = {
          category: category,
          description: cell.text,
          confidence: 0.7
        };
      }
    }
    
    return localLegend;
    
  } catch (error) {
    console.error("Legend detection error:", error);
    return { legendFound: false, colorMappings: {}, cellClassifications: {} };
  }
}

// Process command with intelligent backend
async function processCommandWithBackend(command: string, context: any): Promise<any> {
  const endpoint = getEndpoint("command");
  const token = getAuthToken();
  
  // DEBUG LOGGING
  console.log("🔍 DEBUG: Sending command to:", endpoint);
  console.log("🔍 DEBUG: Command:", command);
  console.log("🔍 DEBUG: Context keys:", Object.keys(context));
  console.log("🔍 DEBUG: Label map size:", context.labelMap ? Object.keys(context.labelMap).length : 0);
  // Connecting to backend... (no status display needed - chat UI handles it)
  console.log("🔄 Connecting to backend...");
  
  try {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };
    
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    
    const response = await fetch(endpoint, {
      method: "POST",
      headers,
      body: JSON.stringify({
        command: command,
        context: context,
        capabilities: [
          "write_cells",
          "read_cells",
          "format_cells",
          "create_tables",
          "calculate_engineering_values",
          "validate_designs"
        ]
      }),
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      logToScreen(`❌ Backend error ${response.status}: ${errorText}`);
      throw new Error(`Backend returned ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    
    // DETAILED RESPONSE LOGGING
    logToScreen(`✅ Backend response received: action="${result.action}"`);
    logToScreen(`📋 Response keys: ${Object.keys(result).join(', ')}`);
    
    if (result.action === "update_value") {
      logToScreen(`   🔹 Property: ${result.property !== undefined ? result.property : 'MISSING'}`);
      logToScreen(`   🔹 Target: ${result.target !== undefined ? result.target : 'MISSING'}`);
      logToScreen(`   🔹 Value: ${result.value !== undefined ? result.value : 'MISSING'}`);
      logToScreen(`   🔹 Updates array: ${result.updates ? JSON.stringify(result.updates).substring(0, 200) : 'MISSING'}`);
      logToScreen(`   🔹 Message: ${result.message || 'No message'}`);
    } else if (result.action === "message") {
      const msg = result.message || 'MISSING MESSAGE';
      logToScreen(`   🔹 Message (length: ${msg.length}):`);
      logToScreen(`   ${msg.substring(0, 300)}${msg.length > 300 ? '...' : ''}`);
    }
    
    // Log full response structure (truncated for readability)
    const responseStr = JSON.stringify(result);
    logToScreen(`📦 Full response (${responseStr.length} chars):`);
    logToScreen(`   ${responseStr.substring(0, 600)}${responseStr.length > 600 ? '...' : ''}`);
    
    // If backend returned acknowledge, it might not have processed correctly
    if (result.action === "acknowledge" && command.toLowerCase().includes("building code")) {
      logToScreen(`⚠️ WARNING: Building code query returned 'acknowledge' - backend may not be processing correctly`);
    }
    
    return result;
  } catch (error) {
    // Fallback to local intelligent processing if backend unavailable
    console.error("❌ Backend error:", error);
    logToScreen(`❌ Backend connection failed: ${error}`);
    logToScreen(`💡 Make sure backend is running: cd backend && python api_server.py`);
    
    // Check if this is a building code query
    const commandLower = command.toLowerCase();
    if (commandLower.includes("building code") || commandLower.includes("applicable code") || 
        commandLower.includes("clause") || commandLower.includes("code reference")) {
      return {
        action: "message",
        message: "⚠️ Building code queries require the backend server to be running.\n\nPlease start the backend:\n1. Open terminal\n2. cd backend\n3. python api_server.py\n\nThen try your query again.",
        reasoning: "Backend unavailable for building code queries"
      };
    }
    
    return await processCommandLocally(command, context);
  }
}

// Fallback: Local intelligent processing for demo purposes
async function processCommandLocally(command: string, context: any): Promise<any> {
  const lowerCommand = command.toLowerCase();
  
  // Engineering-specific pattern recognition
  const patterns = {
    // Design request (e.g., "Design me a beam with span of 15m")
    designRequest: /(?:design|create|make)\s+(?:me\s+)?(?:a\s+)?(\w+)\s+(?:with|having|for)\s+.*?(?:span|length).*?(?:of\s+)?(\d+\.?\d*)\s*([a-zA-Z]+)?/i,
    
    // Dimensional updates
    updateDimension: /(?:update|change|set|modify)\s+(?:the\s+)?(\w+(?:\s+\w+)?)\s+(?:to|=|:)?\s*(\d+\.?\d*)\s*([a-zA-Z]+)?/i,
    
    // Simple value with property (e.g., "span 15m")
    simpleValue: /(?:^|\s)(\w+)\s+(?:to\s+)?(\d+\.?\d*)\s*([a-zA-Z]+)?$/i,
    
    // Load calculations
    calculateLoad: /(?:calculate|compute|find|determine)\s+(?:the\s+)?(\w+(?:\s+\w+)?)\s*(?:for|on|at)?\s*(.*)?/i,
    
    // Design checks
    checkDesign: /(?:check|verify|validate|analyze)\s+(\w+(?:\s+\w+)?)/i,
    
    // Material properties
    changeMaterial: /(?:change|update|set)\s+(?:the\s+)?material\s+(?:to|=)?\s*(\w+)/i,
  };
  
  // Match design request pattern (e.g., "Design me a beam with span of 15m")
  const designMatch = command.match(patterns.designRequest);
  if (designMatch) {
    const [, element, value, unit] = designMatch;
    return {
      action: "update_value",
      property: "span",
      value: parseFloat(value),
      unit: unit || "m",
      message: `Designing ${element}: Set span to ${value}${unit || 'm'}`,
      target: findPropertyInSheet("span", context)
    };
  }
  
  // Match update dimension pattern (e.g., "update beam span to 15m")
  const dimMatch = command.match(patterns.updateDimension);
  if (dimMatch) {
    const [, property, value, unit] = dimMatch;
    const propertyName = property.trim().toLowerCase();
    
    // Find cell address using label map
    const labelMap = context.labelMap || {};
    let cellAddress = labelMap[propertyName];
    
    // Try partial match if exact match fails
    if (!cellAddress) {
      for (const [label, address] of Object.entries(labelMap)) {
        if (label.includes(propertyName) || propertyName.includes(label)) {
          cellAddress = address;
          break;
        }
      }
    }
    
    console.log(`🎯 Local processing: Found "${propertyName}" at cell ${cellAddress}`);
    
    return {
      action: "update_value",
      property: propertyName,
      value: parseFloat(value),
      unit: unit || detectUnit(property, context),
      message: `Updated ${property} to ${value}${unit || ''}`,
      target: cellAddress || findPropertyInSheet(property, context)
    };
  }
  
  // Match simple value pattern (e.g., "span 15m")
  const simpleMatch = command.match(patterns.simpleValue);
  if (simpleMatch) {
    const [, property, value, unit] = simpleMatch;
    const propertyName = property.trim().toLowerCase();
    
    // Find cell address using label map
    const labelMap = context.labelMap || {};
    let cellAddress = labelMap[propertyName];
    
    // Try partial match if exact match fails
    if (!cellAddress) {
      for (const [label, address] of Object.entries(labelMap)) {
        if (label.includes(propertyName) || propertyName.includes(label)) {
          cellAddress = address;
          break;
        }
      }
    }
    
    console.log(`🎯 Local processing: Found "${propertyName}" at cell ${cellAddress}`);
    
    return {
      action: "update_value",
      property: propertyName,
      value: parseFloat(value),
      unit: unit || detectUnit(property, context),
      message: `Set ${property} to ${value}${unit || ''}`,
      target: cellAddress || findPropertyInSheet(property, context)
    };
  }
  
  // Match calculation request
  const calcMatch = command.match(patterns.calculateLoad);
  if (calcMatch) {
    const [, calculation, target] = calcMatch;
    return {
      action: "calculate",
      calculation: calculation.trim(),
      target: target?.trim(),
      message: `Calculating ${calculation}... (Connect to backend for full calculations)`,
      requiresBackend: true
    };
  }
  
  // Match design check
  const checkMatch = command.match(patterns.checkDesign);
  if (checkMatch) {
    const [, element] = checkMatch;
    return {
      action: "design_check",
      element: element.trim(),
      message: `Design check for ${element} requires backend connection`,
      requiresBackend: true
    };
  }
  
  // Check for explanation requests
  const explainPattern = /explain.*sheet|tell.*about.*sheet|what.*sheet/i;
  if (explainPattern.test(command)) {
    const sheetInfo = analyzeSheetContent(context);
    return {
      action: "message",
      message: sheetInfo,
      requiresBackend: false
    };
  }
  
  // Default: acknowledge and suggest backend
  return {
    action: "acknowledge",
    message: `Command understood: "${command}". Connect to Mantle backend for intelligent processing.`,
    suggestion: "Configure BACKEND_API in taskpane.ts to enable full AI capabilities",
    requiresBackend: true
  };
}

function analyzeSheetContent(context: any): string {
  const sheetName = context.sheetName || "this sheet";
  const labelMap = context.labelMap || {};
  
  let info = `📊 Analysis of "${sheetName}":\n\n`;
  
  // Count parameters
  const paramCount = Object.keys(labelMap).length;
  info += `Found ${paramCount} design parameters:\n`;
  
  // List first 10 parameters
  const params = Object.entries(labelMap).slice(0, 10);
  params.forEach(([label, address]) => {
    info += `  • ${label}: ${address}\n`;
  });
  
  if (paramCount > 10) {
    info += `  ... and ${paramCount - 10} more\n`;
  }
  
  // Detect sheet type
  if (sheetName.toLowerCase().includes("beam")) {
    info += `\n🎯 Sheet Type: Beam Design\nThis appears to be for analyzing beam forces and moments.`;
  } else if (sheetName.toLowerCase().includes("column")) {
    info += `\n🎯 Sheet Type: Column Design\nThis appears to be for analyzing column capacity and buckling.`;
  }
  
  info += `\n\n💡 Tip: Try asking me to update specific parameters or calculate design values.`;
  
  return info;
}

// Apply the intelligent response to the workbook
async function applyResponse(response: any): Promise<void> {
  console.log("🔧 Applying response:", JSON.stringify(response, null, 2));
  
  if (!response.action) return;
  
  await Excel.run(async (context) => {
    const sheet = context.workbook.worksheets.getActiveWorksheet();
    
    switch (response.action) {
      case "update_value":
        logToScreen(`🔧 UPDATE_VALUE action triggered`);
        logToScreen(`   Target from backend: ${response.target || 'MISSING'}`);
        logToScreen(`   Property: ${response.property || 'MISSING'}`);
        logToScreen(`   Value: ${response.value !== undefined ? response.value : 'MISSING'}`);
        logToScreen(`   Updates array: ${response.updates ? JSON.stringify(response.updates) : 'MISSING'}`);
        
        // Get fresh context to lookup in label map
        const context_full = await extractWorkbookContext();
        const labelMap = context_full.labelMap || {};
        logToScreen(`   LabelMap size: ${Object.keys(labelMap).length}`);
        
        // PRIORITY 1: Use explicit target from backend if provided
        let cellAddress = response.target;
        
        // PRIORITY 2: If updates array has address, use that
        if (!cellAddress && response.updates && response.updates.length > 0 && response.updates[0].address) {
          cellAddress = response.updates[0].address;
          logToScreen(`   Using address from updates array: ${cellAddress}`);
        }
        
        // PRIORITY 3: Only do property lookup if no explicit target AND property is provided
        if (!cellAddress && response.property) {
          const propertyLower = response.property.toLowerCase();
          logToScreen(`🔍 Looking for "${propertyLower}" in labelMap...`);
          
          // Try exact match
          cellAddress = labelMap[propertyLower];
          
          // Try partial match - but only if both strings have meaningful content
          if (!cellAddress) {
            logToScreen(`   Trying partial match for "${propertyLower}"...`);
            for (const [label, address] of Object.entries(labelMap)) {
              // Only match if either string contains the other as a complete word
              const propertyWords = propertyLower.split(/\s+/);
              const labelWords = label.split(/\s+/);
              
              // Check if any word from property is in label
              const hasMatch = propertyWords.some((pw: string) => 
                labelWords.some((lw: string) => lw.includes(pw) || pw.includes(lw))
              );
              
              if (hasMatch && propertyLower.length > 2 && label.length > 2) {
                cellAddress = address as string;
                logToScreen(`   ✅ Found "${label}" → ${address}`);
                break;
              }
            }
          } else {
            logToScreen(`   ✅ Exact match: ${cellAddress}`);
          }
        }
        
        if (cellAddress) {
          logToScreen(`📝 Writing ${response.value} to cell ${cellAddress}`);
          const range = sheet.getRange(cellAddress);
          range.values = [[response.value]];
          await context.sync();
          logToScreen(`✅ Cell ${cellAddress} updated successfully!`);
        } else {
          logToScreen(`❌ ERROR: No cell address found`);
        }
        break;
        
      case "update_multiple":
        if (response.updates && Array.isArray(response.updates)) {
          for (const update of response.updates) {
            const range = sheet.getRange(update.address);
            range.values = [[update.value]];
          }
        }
        break;
        
      case "format_range":
        if (response.address) {
          const range = sheet.getRange(response.address);
          if (response.format) {
            range.format.fill.color = response.format.backgroundColor || "#FFFFFF";
            range.format.font.color = response.format.fontColor || "#000000";
            range.format.font.bold = response.format.bold || false;
          }
        }
        break;
        
      case "create_table":
        if (response.data && response.address) {
          const range = sheet.getRange(response.address);
          range.values = response.data;
        }
        break;
        
      case "calculate":
      case "design_check":
      case "acknowledge":
        // These require backend - no local action
        break;
    }
    
    await context.sync();
  });
}

// Helper: Find property location in sheet
function findPropertyInSheet(property: string, context: any): any {
  const normalized = property.toLowerCase().trim();
  
  // Search in sample data
  if (context.usedRange && context.usedRange.sampleData) {
    for (let i = 0; i < context.usedRange.sampleData.length; i++) {
      const row = context.usedRange.sampleData[i];
      for (let j = 0; j < row.length; j++) {
        const cell = String(row[j]).toLowerCase();
        if (cell.includes(normalized) || normalized.includes(cell)) {
          // Found likely property, return adjacent cell for value
          return {
            address: `${getColumnLetter(j + 1)}${i + 1}`,
            valueAddress: `${getColumnLetter(j + 2)}${i + 1}` // Usually value is next column
          };
        }
      }
    }
  }
  
  return null;
}

// Helper: Smart search for property
async function smartSearchProperty(context: any, sheet: any, property: string): Promise<string | null> {
  // For now, return common locations
  // In production, this would do intelligent sheet analysis
  const commonMappings: { [key: string]: string } = {
    "beam span": "B3",
    "span": "B3",
    "load": "B4",
    "moment": "D5",
    "shear": "D6"
  };
  
  return commonMappings[property.toLowerCase()] || null;
}

// Helper: Detect unit from context
function detectUnit(property: string, context: any): string {
  const prop = property.toLowerCase();
  
  // Common engineering units
  if (prop.includes("span") || prop.includes("length") || prop.includes("height")) return "m";
  if (prop.includes("load") || prop.includes("force")) return "kN";
  if (prop.includes("moment")) return "kN⋅m";
  if (prop.includes("stress") || prop.includes("pressure")) return "MPa";
  if (prop.includes("area")) return "m²";
  
  return "";
}

// Helper: Convert column number to letter
function getColumnLetter(column: number): string {
  let letter = "";
  while (column > 0) {
    const remainder = (column - 1) % 26;
    letter = String.fromCharCode(65 + remainder) + letter;
    column = Math.floor((column - 1) / 26);
  }
  return letter;
}

// Legacy status functions - now safe (won't crash if elements don't exist)
function showStatus(message: string, isError = false) {
  console.log(isError ? `❌ ${message}` : `✓ ${message}`);
  // Elements may not exist if using chat interface - that's ok
}

function logToScreen(message: string) {
  console.log(message); // Always log to console
  // Debug log UI is optional and may not exist
}

function showCommandStatus(message: string, isError = false) {
  console.log(isError ? `❌ ${message}` : `✓ ${message}`);
  // Chat interface handles user-facing messages now
}

