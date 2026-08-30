import { fireEvent, render, screen } from '@testing-library/vue'
import { describe, expect, it } from 'vitest'
import WorkPlanTimeline from './WorkPlanTimeline.vue'
import type { PlanStep } from '../types'

function step(overrides: Partial<PlanStep>): PlanStep {
  return {
    id: 'step-1',
    work_plan_id: 'plan-1',
    position: 1,
    step_key: 'knowledge_context',
    title: '知识上下文',
    description: '取得最低充分背景',
    actor_kind: 'agent',
    agent_id: 'knowledge-assistant',
    default_executor: 'codex',
    status: 'ready',
    display_status: 'ready',
    completion_note: null,
    completed_by: null,
    completed_at: null,
    created_at: '2026-08-30T00:00:00Z',
    updated_at: '2026-08-30T00:00:00Z',
    runs: [],
    ...overrides,
  }
}

describe('WorkPlanTimeline', () => {
  it('只给可执行步骤显示启动动作，阻塞步骤不显示', async () => {
    const view = render(WorkPlanTimeline, {
      props: {
        workStatus: 'planned',
        steps: [
          step({}),
          step({ id: 'step-2', position: 2, title: '方案', status: 'pending', display_status: 'blocked' }),
        ],
      },
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } },
    })

    expect(screen.getByText('可启动')).toBeTruthy()
    expect(screen.getByText('等待前序')).toBeTruthy()
    expect(screen.getAllByRole('button', { name: '启动步骤' })).toHaveLength(1)

    await fireEvent.click(screen.getByRole('button', { name: '启动步骤' }))
    expect(view.emitted().launch?.[0]).toEqual([
      'step-1',
      { executor: 'codex', instruction: undefined },
    ])
  })

  it('成功 Run 仍需人的完成依据才能解锁下一步', async () => {
    const view = render(WorkPlanTimeline, {
      props: {
        workStatus: 'in_progress',
        steps: [
          step({
            display_status: 'awaiting_gate',
            runs: [
              {
                id: 'run-1',
                agent_id: 'knowledge-assistant',
                agent_name: '知识问答 Agent',
                title: '知识上下文',
                actor_id: 'admin',
                status: 'succeeded',
                model: null,
                branch_name: 'agent-work/work-1',
                executor: 'codex',
                executor_session_id: 'session-1',
                subject_type: 'work',
                subject_id: 'work-1',
                thread_id: null,
                trigger_action: 'knowledge_context',
                work_id: 'work-1',
                plan_step_id: 'step-1',
                exit_code: 0,
                failure_code: null,
                created_at: '2026-08-30T00:00:00Z',
                started_at: '2026-08-30T00:00:01Z',
                finished_at: '2026-08-30T00:00:02Z',
                updated_at: '2026-08-30T00:00:02Z',
              },
            ],
          }),
        ],
      },
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } },
    })

    const gate = screen.getByRole('button', { name: '人工确认并解锁下一步' })
    expect(gate.getAttribute('disabled')).not.toBeNull()
    await fireEvent.update(screen.getByPlaceholderText('说明为什么这一步可以通过'), '背景边界明确')
    await fireEvent.click(gate)
    expect(view.emitted().complete?.[0]).toEqual(['step-1', '背景边界明确'])
  })
})
