/**
 * RFP Proposal Workflow Composable
 * Handles the complete RFP proposal workflow: finding RFP, analyzing, finding examples, and writing proposal
 */

export interface RFPProposalState {
  step: 'initial' | 'rfp_found' | 'rfp_opened' | 'keypoints_shared' | 'examples_added' | 'template_added' | 'proposal_written' | 'section_added'
  rfpPath?: string
  rfpFileName?: string
  projectFolder?: string
  keypoints?: string
}

export interface Document {
  id: string
  title: string
  name?: string
  filePath?: string
  url?: string
  description?: string
  metadata?: Record<string, string | number | undefined>
  reason?: string
}

/**
 * Extract project folder from user message
 * Examples: "new RFP in project 2025-12-001", "RFP in 2025-12-001"
 */
export function extractProjectFolder(message: string): string | null {
  const projectPattern = /\b(?:project\s+)?(\d{4}-\d{2}-\d{3})\b/i
  const match = message.match(projectPattern)
  return match && match[1] ? match[1] : null
}

/**
 * Search for RFP files in a project folder
 * In production, this would call the backend to search for files
 * For now, we'll use the hardcoded path
 */
export async function searchRFPInFolder(projectFolder: string): Promise<{ path: string; fileName: string } | null> {
  // Simulate async search
  await new Promise(resolve => setTimeout(resolve, 500))
  
  // For demo, always return the known RFP
  // In production, this would search the actual folder
  if (projectFolder === '2025-12-001' || true) {
    return {
      path: '/writing/Structural Engineer RFP 63023.pdf',
      fileName: 'Structural Engineer RFP 63023.pdf'
    }
  }
  
  return null
}

/**
 * Read keypoints from file
 * In production, this would call the backend to read the file
 */
export async function readKeypoints(): Promise<string> {
  // For demo, return the hardcoded keypoints
  // In production, this would read from the file
  return `Key Structural Components & Considerations for the Cooper Master Campus Plan RFP

The Cooper Master Campus Plan represents a highly complex, multi-phase healthcare development in an active urban environment. From a structural engineering standpoint, several critical components require early, deliberate consideration to reduce risk and preserve long-term flexibility.

First, deep foundations and below-grade construction are a primary driver of structural complexity. Tower A, and future Towers B and C, include basements extending below the anticipated groundwater table, requiring careful coordination with geotechnical engineering to address hydrostatic uplift, waterproofing, shoring, and underpinning of adjacent existing facilities. Structural solutions must minimize settlement and vibration impacts to the operational hospital campus.

Second, integration with existing structures is a major consideration. Tower A must physically connect to the Kelemen and Roberts Pavilion buildings and support a multi-story pedestrian bridge over Haddon Avenue. Structural design must account for differential movement, seismic and wind compatibility, phased construction tolerances, and the modification or strengthening of existing structural systems.

Third, lateral system selection and future expandability are essential. Tower A establishes structural precedents for the campus and must be designed with an understanding of future Towers B and C, shared podiums, and potential vertical or lateral expansion. Early decisions regarding column grids, shear walls, cores, and transfer systems will significantly influence future constructability and cost.

Fourth, structural support of major MEP and energy infrastructure is critical. The RFP anticipates geothermal wells beneath Tower A, rooftop mechanical screening structures, and potential vertical expansion of the existing Boiler House—none of which were originally designed for additional load. Structural engineers must coordinate closely with MEP to ensure load paths, vibration control, and constructability are fully resolved.

Finally, phasing, early bid packages, and constructability are central to meeting the aggressive schedule. Early foundation and steel packages, coordination with target value design (TVD), and constructability reviews during design are required to enable construction to proceed while maintaining uninterrupted healthcare operations.`
}

/**
 * Get example report document
 */
export function getExampleReport(): Document {
  return {
    id: 'example-report-1',
    title: 'Multi-level parking Garage.pdf',
    name: 'Multi-level parking Garage',
    filePath: '/writing/Multi-level parking Garage.pdf',
    url: '/writing/Multi-level parking Garage.pdf',
    description: 'Example report from a similar past project',
    reason: 'Similar structural engineering scope and complexity'
  }
}

/**
 * Get proposal template document
 */
export function getProposalTemplate(): Document {
  return {
    id: 'proposal-template-1',
    title: 'Template Proposal.pdf',
    name: 'RFP Template',
    filePath: '/writing/Template Proposal.pdf',
    url: '/writing/Template Proposal.pdf',
    description: 'Company standard proposal template',
    reason: 'Standard format and structure for proposals'
  }
}

/**
 * Read proposal content from finalword.txt
 */
export async function readProposalContent(): Promise<string> {
  try {
    // Load content from finalword.txt
    const response = await fetch('/writing/finalword.txt')
    if (!response.ok) {
      throw new Error('Failed to load finalword.txt')
    }
    const textContent = await response.text()
    
    // Convert plain text to HTML format for the editor
    // Split by double newlines to identify paragraphs
    const paragraphs = textContent.split(/\n\n+/).filter(p => p.trim())
    
    let htmlContent = ''
    
    for (const para of paragraphs) {
      const trimmed = para.trim()
      if (!trimmed) continue
      
      // Check if it's a heading (all caps or starts with number)
      const firstLine = trimmed.split('\n')[0]?.trim() || ''
      if (/^\d+\.\s+[A-Z]/.test(trimmed) || (firstLine && /^[A-Z][A-Z\s]{20,}$/.test(firstLine))) {
        // It's likely a heading
        const lines = trimmed.split('\n')
        const headingFirstLine = lines[0]?.trim() || ''
        
        // Remove leading numbers if present
        const headingText = headingFirstLine.replace(/^\d+\.\s*/, '')
        
        // Determine heading level based on formatting
        if (headingText && /^[A-Z][A-Z\s]{30,}$/.test(headingText)) {
          // All caps long line = H1
          htmlContent += `<h1>${headingText}</h1>\n\n`
        } else if (headingFirstLine && /^\d+\./.test(headingFirstLine)) {
          // Numbered section = H2
          htmlContent += `<h2>${headingText}</h2>\n\n`
        } else if (headingText) {
          // Regular heading = H2
          htmlContent += `<h2>${headingText}</h2>\n\n`
        }
        
        // Add remaining lines as paragraphs
        if (lines.length > 1) {
          for (let i = 1; i < lines.length; i++) {
            const line = lines[i]?.trim()
            if (line) {
              htmlContent += `<p>${line}</p>\n\n`
            }
          }
        }
      } else if (trimmed.startsWith('•') || trimmed.startsWith('-') || trimmed.startsWith('*') || trimmed.includes('•')) {
        // It's a list item
        const items = trimmed.split(/\n(?=[•\-*])/).filter(item => item.trim())
        htmlContent += '<ul>\n'
        for (const item of items) {
          const cleanItem = item.replace(/^[•\-*]\s*/, '').trim()
          if (cleanItem) {
            htmlContent += `<li>${cleanItem}</li>\n`
          }
        }
        htmlContent += '</ul>\n\n'
      } else {
        // Regular paragraph
        // Replace single newlines with spaces, but preserve structure
        const formatted = trimmed.split('\n').map(line => line.trim()).filter(line => line).join(' ')
        if (formatted) {
          htmlContent += `<p>${formatted}</p>\n\n`
        }
      }
    }
    
    return htmlContent
  } catch (error) {
    console.error('Error loading finalword.txt:', error)
    // Fallback to a simple message
    return '<p>Error loading proposal content. Please check that finalword.txt exists.</p>'
  }
}

export const useRFPProposalWorkflow = () => {
  return {
    extractProjectFolder,
    searchRFPInFolder,
    readKeypoints,
    getExampleReport,
    getProposalTemplate,
    readProposalContent
  }
}

