export function downloadText(content: string, filename: string, mimeType = 'text/plain;charset=utf-8') {
  const url = URL.createObjectURL(new Blob([content], { type: mimeType }))
  const anchor = window.document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.hidden = true
  window.document.body.append(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}
