/**
 * RFP Workflow Composable
 * Handles the intelligent RFP analysis and proposal generation workflow
 */

import { useChat } from './useChat'
import { useRuntimeConfig } from '#app'

export interface SimilarProject {
  id: string
  title: string
  name?: string
  description?: string
  url?: string
  filePath?: string
  metadata?: {
    projectType?: string
    client?: string
    location?: string
    year?: string
    [key: string]: string | undefined
  }
  reason?: string
  similarityScore?: number
}

export interface RFPAnalysis {
  projectType?: string
  client?: string
  location?: string
  scope?: string
  requirements?: string[]
  similarProjects?: SimilarProject[]
}

export const useRFPWorkflow = () => {
  const config = useRuntimeConfig()
  const { sendChatMessage } = useChat()

  /**
   * Analyze RFP and find similar past projects
   */
  async function analyzeRFPAndFindSimilar(
    rfpPath: string,
    criteria?: {
      projectType?: boolean
      client?: boolean
      location?: boolean
    }
  ): Promise<RFPAnalysis> {
    const message = `Analyze this RFP and find similar past projects that would be good examples for writing a proposal. 
    
RFP Path: ${rfpPath}

Please:
1. Analyze the RFP to extract:
   - Project type
   - Client name
   - Location
   - Scope of work
   - Key requirements

2. Find 3 similar past projects based on:
   ${criteria?.projectType ? '- Project type similarity' : ''}
   ${criteria?.client ? '- Same or similar client' : ''}
   ${criteria?.location ? '- Same or similar location' : ''}
   - Overall scope similarity

3. For each similar project, explain why it was chosen and provide the document path.

Return the results in a structured format.`

    try {
      const response = await sendChatMessage(message, 'rfp-analysis')
      
      // Parse response to extract structured data
      // The backend should return structured data, but we'll also parse the text
      const analysis: RFPAnalysis = {
        similarProjects: []
      }

      // Extract similar projects from response
      // This is a simplified parser - backend should ideally return JSON
      const projectMatches = response.reply.match(/Project \d+:|Similar Project \d+:/gi)
      if (projectMatches) {
        // Parse projects from response
        // Backend should return structured data
      }

      return analysis
    } catch (error) {
      console.error('RFP analysis error:', error)
      throw error
    }
  }

  /**
   * Generate proposal based on RFP and similar projects
   */
  async function generateProposal(
    rfpPath: string,
    similarProjects: SimilarProject[],
    userInstructions?: string
  ): Promise<string> {
    const projectRefs = similarProjects.map((p, i) => 
      `${i + 1}. ${p.title}${p.reason ? ` (${p.reason})` : ''}`
    ).join('\n')

    const message = `Write a professional engineering proposal based on this RFP and similar past projects.

RFP Path: ${rfpPath}

Similar Projects to Reference:
${projectRefs}

${userInstructions ? `\nAdditional Instructions:\n${userInstructions}` : ''}

Please:
1. Reference the company standard proposal format and templates
2. Use the similar projects as examples for structure and content
3. Address all requirements from the RFP
4. Write in a professional, engineering-appropriate tone
5. Include all standard sections (executive summary, scope, methodology, timeline, etc.)

Generate the complete proposal text.`

    try {
      const response = await sendChatMessage(message, 'proposal-generation')
      return response.reply
    } catch (error) {
      console.error('Proposal generation error:', error)
      throw error
    }
  }

  /**
   * Export proposal to Word via backend API
   */
  async function exportToWord(content: string, fileName: string): Promise<void> {
    const url = `${config.public.orchestratorUrl}/export/word`
    
    try {
      // Use Nuxt's $fetch (auto-imported) to get the file as blob
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          content,
          file_name: fileName
        })
      })
      
      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`)
      }
      
      // Get the blob and trigger download
      const blob = await response.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = fileName
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
    } catch (error) {
      console.error('Word export error:', error)
      throw error
    }
  }

  return {
    analyzeRFPAndFindSimilar,
    generateProposal,
    exportToWord
  }
}

