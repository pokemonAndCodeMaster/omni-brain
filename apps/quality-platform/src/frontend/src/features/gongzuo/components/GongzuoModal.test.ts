import { fireEvent, render, screen } from '@testing-library/vue'
import { defineComponent, nextTick, shallowRef } from 'vue'
import { describe, expect, it } from 'vitest'
import GongzuoModal from './GongzuoModal.vue'

const Harness = defineComponent({
  components: { GongzuoModal },
  setup() { const open = shallowRef(false); return { open } },
  template: `<button data-testid="trigger" @click="open = true">打开</button><GongzuoModal v-if="open" title="键盘测试" @close="open = false"><input aria-label="第一项" autofocus /><button>末项</button></GongzuoModal>`,
})

describe('GongzuoModal', () => {
  it('打开后聚焦内容、约束 Tab、Escape 关闭并把焦点还给触发按钮', async () => {
    render(Harness)
    const trigger = screen.getByTestId('trigger')
    trigger.focus()
    await fireEvent.click(trigger)
    await nextTick()
    const first = screen.getByRole('textbox', { name: '第一项' })
    const last = screen.getByRole('button', { name: '末项' })
    const close = screen.getByRole('button', { name: '关闭弹窗' })
    expect(document.activeElement).toBe(first)

    last.focus()
    await fireEvent.keyDown(last, { key: 'Tab' })
    expect(document.activeElement).toBe(close)
    await fireEvent.keyDown(close, { key: 'Tab', shiftKey: true })
    expect(document.activeElement).toBe(last)

    await fireEvent.keyDown(last, { key: 'Escape' })
    await nextTick()
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(document.activeElement).toBe(trigger)
  })
})
