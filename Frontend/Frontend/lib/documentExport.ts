import { Document as DocxDocument, HeadingLevel, Packer, Paragraph, Table, TableCell, TableRow, TextRun } from 'docx'
import { PDFDocument, StandardFonts, rgb, type PDFFont } from 'pdf-lib'
import type { DocumentBlock, StructuredDocument } from '~/composables/useDocumentWorkflow'

function sanitizeFilename(name: string) {
  const trimmed = name.trim().replace(/[\\/:*?"<>|]/g, '')
  return trimmed || 'document'
}

function triggerDownload(blob: Blob, filename: string) {
  if (typeof window === 'undefined') return
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

function toHeadingLevel(level?: number) {
  if (level === 3) return HeadingLevel.HEADING_3
  if (level === 2) return HeadingLevel.HEADING_2
  return HeadingLevel.HEADING_1
}

function blockToDocx(block: DocumentBlock): Array<Paragraph | Table> {
  switch (block.type) {
    case 'heading':
      return [
        new Paragraph({
          text: block.text || '',
          heading: toHeadingLevel(block.level),
          spacing: { after: 200 }
        })
      ]
    case 'list':
      return (block.items || []).map(
        item =>
          new Paragraph({
            text: item,
            bullet: { level: 0 },
            spacing: { after: 80 }
          })
      )
    case 'table': {
      const rows = (block.rows || []).map(
        row =>
          new TableRow({
            children: row.map(cell => new TableCell({ children: [new Paragraph(cell ?? '')] }))
          })
      )
      return [new Table({ rows })]
    }
    case 'quote':
      return [
        new Paragraph({
          children: [new TextRun({ text: block.text || '', italics: true })],
          spacing: { after: 160 }
        })
      ]
    default:
      return [
        new Paragraph({
          children: [
            new TextRun({
              text: block.text || '',
              bold: block.style?.bold,
              italics: block.style?.italic
            })
          ],
          spacing: { after: 200 }
        })
      ]
  }
}

export async function exportDocumentAsDocx(doc: StructuredDocument) {
  if (typeof window === 'undefined') return
  const children: Array<Paragraph | Table> = []

  doc.sections.forEach(section => {
    children.push(
      new Paragraph({
        text: section.title || '',
        heading: HeadingLevel.HEADING_2,
        spacing: { after: 120 }
      })
    )
    section.blocks.forEach(block => {
      children.push(...blockToDocx(block))
    })
  })

  const docxDoc = new DocxDocument({
    sections: [
      {
        children
      }
    ]
  })

  const blob = await Packer.toBlob(docxDoc)
  triggerDownload(blob, `${sanitizeFilename(doc.title || 'document')}.docx`)
}

function wrapText(text: string, width: number, font: PDFFont, size: number) {
  const words = text.split(' ')
  const lines: string[] = []
  let current = ''
  for (const word of words) {
    const tentative = current ? `${current} ${word}` : word
    const w = font.widthOfTextAtSize(tentative, size)
    if (w < width) {
      current = tentative
    } else {
      if (current) lines.push(current)
      current = word
    }
  }
  if (current) lines.push(current)
  return lines
}

export async function exportDocumentAsPdf(doc: StructuredDocument) {
  if (typeof window === 'undefined') return

  const pdf = await PDFDocument.create()
  const font = await pdf.embedFont(StandardFonts.Helvetica)
  const boldFont = await pdf.embedFont(StandardFonts.HelveticaBold)
  let page = pdf.addPage()
  let y = page.getHeight() - 50
  const maxWidth = page.getWidth() - 80

  const writeLine = (text: string, size = 12, gap = 16, bold = false) => {
    const lines = wrapText(text, maxWidth, font, size)
    for (const line of lines) {
      if (y < 60) {
        page = pdf.addPage()
        y = page.getHeight() - 50
      }
      page.drawText(line, {
        x: 40,
        y,
        size,
        font: bold ? boldFont : font,
        color: rgb(0.95, 0.95, 0.98)
      })
      y -= gap
    }
  }

  doc.sections.forEach(section => {
    writeLine(section.title || 'Section', 14, 18, true)
    section.blocks.forEach(block => {
      if (block.type === 'heading') {
        writeLine(block.text || '', 13, 18, true)
      } else if (block.type === 'list') {
        (block.items || []).forEach(item => writeLine(`• ${item}`, 11, 14))
      } else if (block.type === 'table') {
        const rows = block.rows || []
        rows.forEach(row => writeLine(row.join(' | '), 11, 14))
      } else {
        writeLine(block.text || '', 11, 16)
      }
    })
    y -= 10
  })

  const bytes = await pdf.save()
  triggerDownload(new Blob([bytes], { type: 'application/pdf' }), `${sanitizeFilename(doc.title || 'document')}.pdf`)
}
