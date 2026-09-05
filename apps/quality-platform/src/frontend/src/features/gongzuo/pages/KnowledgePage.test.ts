import { describe, expect, it } from 'vitest'
import { resolveKnowledgePath } from '../utils/knowledgeLinks'

describe('KnowledgePage links', () => {
  it('把知识目录内的相对 Markdown 链接解析为可读取路径', () => {
    expect(resolveKnowledgePath('docs/specs/current.md', '../blueprint.md#section')).toBe('docs/blueprint.md')
    expect(resolveKnowledgePath('README.md', 'docs/now.md')).toBe('docs/now.md')
  })

  it('不把目录外定位、源码或危险协议伪装成可导航知识', () => {
    expect(resolveKnowledgePath('README.md', '../outside.md')).toBeNull()
    expect(resolveKnowledgePath('docs/current.md', '../src/app.py')).toBeNull()
    expect(resolveKnowledgePath('docs/current.md', 'javascript:alert(1)')).toBeNull()
  })
})
