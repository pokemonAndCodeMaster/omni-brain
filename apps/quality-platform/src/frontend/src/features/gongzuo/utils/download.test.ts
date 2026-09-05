import { afterEach, describe, expect, it, vi } from 'vitest'
import { downloadText } from './download'

describe('downloadText', () => {
  afterEach(() => vi.restoreAllMocks())

  it('通过真实 DOM 锚点下载固定正文并在完成后清理', () => {
    vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:result')
    const revoke = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined)
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined)
    downloadText('真实结果', 'run-1-result.txt')
    expect(click).toHaveBeenCalledOnce()
    expect(revoke).toHaveBeenCalledWith('blob:result')
    expect(document.querySelector('a[download="run-1-result.txt"]')).toBeNull()
  })
})
