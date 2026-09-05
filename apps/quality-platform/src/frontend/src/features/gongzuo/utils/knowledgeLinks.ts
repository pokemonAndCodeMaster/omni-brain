export function resolveKnowledgePath(current: string, href: string) {
  const raw = href.split('#')[0]?.split('?')[0] ?? ''
  if (!raw || raw.startsWith('/') || /^[a-z][a-z0-9+.-]*:/i.test(raw) || !raw.toLowerCase().endsWith('.md')) return null
  const parts = current.split('/').slice(0, -1)
  for (const part of raw.split('/')) {
    if (!part || part === '.') continue
    if (part === '..') { if (!parts.length) return null; parts.pop() }
    else parts.push(part)
  }
  return parts.join('/')
}
