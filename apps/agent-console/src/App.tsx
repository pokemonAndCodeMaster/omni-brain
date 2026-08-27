import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Button,
  InlineLoading,
  InlineNotification,
  Modal,
  Select,
  SelectItem,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  Tag,
  TextArea,
  TextInput,
  Theme,
} from '@carbon/react'
import {
  Add,
  ArrowRight,
  Branch,
  Catalog,
  ChartLine,
  Checkmark,
  Code,
  Document,
  Renew,
  Stop,
  Task,
  Time,
  WarningAlt,
} from '@carbon/icons-react'
import { api, post } from './api'
import type { Agent, EvalCase, Evaluation, Evolution, Run, TraceEvent, Trial } from './types'

type Page = 'agents' | 'runs' | 'evals' | 'evolution'
type RunTab = 'output' | 'trace' | 'changes' | 'evaluation'

const pages: Array<{ id: Page; label: string; icon: typeof Catalog }> = [
  { id: 'agents', label: '能力目录', icon: Catalog },
  { id: 'runs', label: '任务运行', icon: Task },
  { id: 'evals', label: '评测中心', icon: Checkmark },
  { id: 'evolution', label: '进化实验', icon: ChartLine },
]

const terminalStates = new Set(['completed', 'failed', 'cancelled', 'interrupted'])

function statusLabel(status: string): string {
  return {
    queued: '排队中',
    preparing: '准备工作区',
    running: '运行中',
    evaluating: '评测中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已停止',
    interrupted: '已中断',
    not_started: '未评测',
    verified: '已验证',
    implemented: '已实现待验证',
    experimental: '试验中',
  }[status] ?? status
}

function tagType(status: string): 'green' | 'blue' | 'red' | 'gray' | 'purple' | 'warm-gray' {
  if (status === 'completed' || status === 'verified') return 'green'
  if (['running', 'preparing', 'queued', 'evaluating'].includes(status)) return 'blue'
  if (status === 'failed') return 'red'
  if (status === 'implemented') return 'purple'
  if (status === 'cancelled' || status === 'interrupted') return 'warm-gray'
  return 'gray'
}

function timeLabel(value?: string): string {
  if (!value) return '未记录'
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(new Date(value))
}

function compactRevision(value?: string): string {
  return value?.slice(0, 7) || 'pending'
}

function Score({ label, value }: { label: string; value: number }) {
  return (
    <div className="score-block">
      <div className="score-heading">
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
      <div className="score-track" aria-label={`${label} ${value} 分`}>
        <span style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
      </div>
    </div>
  )
}

function EvaluationView({ evaluation }: { evaluation: Evaluation }) {
  return (
    <div className="evaluation-view">
      <div className="score-grid">
        <Score label="任务完成" value={evaluation.completion_score} />
        <Score label="执行过程" value={evaluation.process_score} />
      </div>
      <div className="evaluation-summary">
        <Tag type={evaluation.success ? 'green' : 'red'}>
          {evaluation.success ? '任务成功' : '仍未达标'}
        </Tag>
        <p>{evaluation.summary}</p>
      </div>
      <div className="evaluation-columns">
        <section>
          <h4>做得好的地方</h4>
          {evaluation.strengths.length ? (
            <ul>{evaluation.strengths.map((item) => <li key={item}>{item}</li>)}</ul>
          ) : <p className="muted">暂无</p>}
        </section>
        <section>
          <h4>需要改进</h4>
          {evaluation.problems.length ? (
            <ul>{evaluation.problems.map((item) => <li key={item}>{item}</li>)}</ul>
          ) : <p className="muted">暂无</p>}
        </section>
      </div>
      <div className="recommendation">
        <span>下一步建议</span>
        <p>{evaluation.improvement_suggestion}</p>
      </div>
      <details>
        <summary>查看证据引用</summary>
        <ul>{evaluation.evidence_refs.map((item) => <li key={item}>{item}</li>)}</ul>
      </details>
    </div>
  )
}

export default function App() {
  const [page, setPage] = useState<Page>('agents')
  const [agents, setAgents] = useState<Agent[]>([])
  const [runs, setRuns] = useState<Run[]>([])
  const [evalCases, setEvalCases] = useState<EvalCase[]>([])
  const [trials, setTrials] = useState<Trial[]>([])
  const [evolutions, setEvolutions] = useState<Evolution[]>([])
  const [selectedRunId, setSelectedRunId] = useState<string>()
  const [selectedRun, setSelectedRun] = useState<Run>()
  const [events, setEvents] = useState<TraceEvent[]>([])
  const [runTab, setRunTab] = useState<RunTab>('output')
  const [loading, setLoading] = useState(true)
  const [actionPending, setActionPending] = useState(false)
  const [error, setError] = useState<string>()

  const [launchOpen, setLaunchOpen] = useState(false)
  const [launchAgentId, setLaunchAgentId] = useState('')
  const [launchCaseId, setLaunchCaseId] = useState('')
  const [launchPrompt, setLaunchPrompt] = useState('')
  const [launchExecutor, setLaunchExecutor] = useState('codex')
  const [launchModel, setLaunchModel] = useState('')

  const [resumeOpen, setResumeOpen] = useState(false)
  const [resumePrompt, setResumePrompt] = useState('')
  const [commitOpen, setCommitOpen] = useState(false)
  const [commitMessage, setCommitMessage] = useState('agent-console: save run changes')
  const [releaseOpen, setReleaseOpen] = useState(false)

  const [evolutionOpen, setEvolutionOpen] = useState(false)
  const [evolutionAgentId, setEvolutionAgentId] = useState('')
  const [evolutionCaseId, setEvolutionCaseId] = useState('')
  const [evolutionPrompt, setEvolutionPrompt] = useState('')
  const [evolutionExecutor, setEvolutionExecutor] = useState('codex')
  const [evolutionIterations, setEvolutionIterations] = useState('1')

  const refreshSelected = useCallback(async (runId: string) => {
    const [detail, trace] = await Promise.all([
      api<Run>(`/api/runs/${runId}`),
      api<TraceEvent[]>(`/api/runs/${runId}/events`),
    ])
    setSelectedRun(detail)
    setEvents(trace)
  }, [])

  const loadAll = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true)
    try {
      const [agentData, runData, caseData, trialData, evolutionData] = await Promise.all([
        api<Agent[]>('/api/agents'),
        api<Run[]>('/api/runs'),
        api<EvalCase[]>('/api/eval-cases'),
        api<Trial[]>('/api/trials'),
        api<Evolution[]>('/api/evolutions'),
      ])
      setAgents(agentData)
      setRuns(runData)
      setEvalCases(caseData)
      setTrials(trialData)
      setEvolutions(evolutionData)
      const nextSelected = selectedRunId || runData[0]?.id
      if (!selectedRunId && nextSelected) setSelectedRunId(nextSelected)
      if (nextSelected) await refreshSelected(nextSelected)
      setError(undefined)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason))
    } finally {
      setLoading(false)
    }
  }, [refreshSelected, selectedRunId])

  useEffect(() => {
    void loadAll()
    const timer = window.setInterval(() => void loadAll(true), 2500)
    return () => window.clearInterval(timer)
  }, [loadAll])

  useEffect(() => {
    if (!selectedRunId) return
    void refreshSelected(selectedRunId)
    const source = new EventSource(`/api/runs/${selectedRunId}/events/stream`)
    source.addEventListener('trace', (message) => {
      const event = JSON.parse((message as MessageEvent).data) as TraceEvent
      setEvents((current) => {
        const bySequence = new Map(current.map((item) => [item.seq, item]))
        bySequence.set(event.seq, event)
        return [...bySequence.values()].sort((a, b) => a.seq - b.seq)
      })
    })
    source.addEventListener('done', () => {
      source.close()
      void loadAll(true)
    })
    return () => source.close()
  }, [loadAll, refreshSelected, selectedRunId])

  const groupedAgents = useMemo(() => {
    return agents.reduce<Record<string, Agent[]>>((groups, agent) => {
      groups[agent.category] = [...(groups[agent.category] || []), agent]
      return groups
    }, {})
  }, [agents])

  const activeRun = runs.find((run) => !terminalStates.has(run.status))
  const activeEvaluation = runs.find((run) => run.evaluation_status === 'running')
  const activeEvolution = evolutions.find((item) => item.status === 'queued' || item.status === 'running')
  const workbenchBusy = Boolean(activeRun || activeEvaluation || activeEvolution)
  const launchableCases = evalCases.filter((item) => item.launchable)

  function openLaunch(agent?: Agent, evalCase?: EvalCase) {
    const chosen = agent || agents[0]
    setLaunchAgentId(chosen?.id || '')
    setLaunchExecutor(chosen?.default_executor || 'codex')
    setLaunchCaseId(evalCase?.id || '')
    setLaunchPrompt(evalCase?.prompt || '')
    setLaunchModel('')
    setLaunchOpen(true)
  }

  function openEvolution(evalCase?: EvalCase) {
    const chosen = agents[0]
    setEvolutionAgentId(chosen?.id || '')
    setEvolutionExecutor(chosen?.default_executor || 'codex')
    setEvolutionCaseId(evalCase?.id || '')
    setEvolutionPrompt(evalCase?.prompt || '')
    setEvolutionIterations('1')
    setEvolutionOpen(true)
  }

  async function perform(action: () => Promise<unknown>, after?: () => void) {
    setActionPending(true)
    try {
      await action()
      after?.()
      setError(undefined)
      await loadAll(true)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason))
    } finally {
      setActionPending(false)
    }
  }

  async function submitRun() {
    await perform(async () => {
      const created = await post<Run>('/api/runs', {
        agent_id: launchAgentId,
        prompt: launchPrompt,
        executor: launchExecutor,
        model: launchModel || null,
        eval_case_id: launchCaseId || null,
      })
      setSelectedRunId(created.id)
    }, () => {
      setLaunchOpen(false)
      setPage('runs')
      setRunTab('trace')
    })
  }

  async function submitEvolution() {
    await perform(
      () => post<Evolution>('/api/evolutions', {
        agent_id: evolutionAgentId,
        prompt: evolutionPrompt,
        eval_case_id: evolutionCaseId || null,
        executor: evolutionExecutor,
        max_iterations: Number(evolutionIterations),
      }),
      () => {
        setEvolutionOpen(false)
        setPage('evolution')
      },
    )
  }

  function selectRun(runId: string, tab: RunTab = 'output') {
    setSelectedRunId(runId)
    setRunTab(tab)
    setPage('runs')
  }

  if (loading) {
    return (
      <Theme theme="g100">
        <main className="loading-screen">
          <InlineLoading description="正在读取 Agent 注册表和运行历史" />
        </main>
      </Theme>
    )
  }

  return (
    <Theme theme="g100">
      <a className="skip-link" href="#main-content">跳到主要内容</a>
      <div className="app-shell">
        <header className="topbar">
          <div className="brand-block">
            <div className="brand-mark" aria-hidden="true">OB</div>
            <div>
              <strong>Agent Control</strong>
              <span>Omni-Brain</span>
            </div>
          </div>
          <div className="environment-strip" aria-label="当前运行环境">
            <span className="environment-dot" />
            <span>LOCAL</span>
            <span className="strip-separator" />
            <Branch size={16} />
            <span>WORKTREE</span>
            <span className="strip-separator" />
            <span>{activeEvolution ? '进化流程运行中' : activeEvaluation ? 'Judge 评测中' : activeRun ? '1 个任务运行中' : '执行槽空闲'}</span>
          </div>
          <Button size="sm" renderIcon={Add} onClick={() => openLaunch()} disabled={workbenchBusy}>
            启动 Agent
          </Button>
        </header>

        <aside className="sidebar" aria-label="主导航">
          <nav>
            {pages.map((item) => {
              const Icon = item.icon
              return (
                <button
                  key={item.id}
                  className={page === item.id ? 'nav-item active' : 'nav-item'}
                  onClick={() => setPage(item.id)}
                  aria-current={page === item.id ? 'page' : undefined}
                >
                  <Icon size={18} />
                  <span>{item.label}</span>
                  {item.id === 'runs' && activeRun ? <span className="nav-live" aria-label="有任务运行中" /> : null}
                </button>
              )
            })}
          </nav>
          <div className="sidebar-note">
            <Code size={18} />
            <div>
              <span>隔离策略</span>
              <strong>单任务 · Git worktree</strong>
            </div>
          </div>
        </aside>

        <main id="main-content" className="main-content">
          {error ? (
            <InlineNotification
              className="global-notification"
              kind="error"
              title="操作未完成"
              subtitle={error}
              onCloseButtonClick={() => setError(undefined)}
            />
          ) : null}

          {page === 'agents' ? (
            <section aria-labelledby="agents-heading">
              <div className="page-heading">
                <div>
                  <p className="eyebrow">CAPABILITY REGISTRY</p>
                  <h1 id="agents-heading">Agent 能力目录</h1>
                  <p>按业务领域发现能力；Harness、Skill 和执行器保留在详情里。</p>
                </div>
                <div className="heading-metrics">
                  <div><strong>{agents.length}</strong><span>注册能力</span></div>
                  <div><strong>{agents.filter((item) => item.state === 'verified').length}</strong><span>已验证</span></div>
                  <div><strong>{runs.length}</strong><span>受管运行</span></div>
                </div>
              </div>

              {Object.entries(groupedAgents).map(([category, items]) => (
                <section className="agent-group" key={category} aria-labelledby={`group-${category}`}>
                  <div className="section-title-row">
                    <h2 id={`group-${category}`}>{category}</h2>
                    <span>{items.length} 项能力</span>
                  </div>
                  <div className="agent-grid">
                    {items.map((agent) => (
                      <article className="agent-card" key={agent.id}>
                        <div className="agent-card-topline">
                          <Tag type={tagType(agent.state)}>{statusLabel(agent.state)}</Tag>
                          <span className="revision"><Branch size={14} /> {agent.revision_short}</span>
                        </div>
                        <h3>{agent.name}</h3>
                        <p>{agent.description}</p>
                        <div className="capability-list">
                          {agent.capabilities.map((capability) => (
                            <div key={capability.id}>
                              <span>{capability.id.replaceAll('_', ' ')}</span>
                              <small>{capability.adoption_label}</small>
                            </div>
                          ))}
                        </div>
                        <div className="agent-meta">
                          <span>{agent.default_executor}</span>
                          <span>{agent.run_count} 次运行</span>
                        </div>
                        <Button
                          kind="ghost"
                          size="sm"
                          renderIcon={ArrowRight}
                          onClick={() => openLaunch(agent)}
                          disabled={workbenchBusy}
                        >
                          用此 Agent 启动任务
                        </Button>
                      </article>
                    ))}
                  </div>
                </section>
              ))}
            </section>
          ) : null}

          {page === 'runs' ? (
            <section aria-labelledby="runs-heading">
              <div className="page-heading compact">
                <div>
                  <p className="eyebrow">RUN OPERATIONS</p>
                  <h1 id="runs-heading">任务运行</h1>
                  <p>从输入到轨迹、输出、差异与评测的同一份运行记录。</p>
                </div>
                <Button size="sm" renderIcon={Add} onClick={() => openLaunch()} disabled={workbenchBusy}>
                  新建任务
                </Button>
              </div>
              <div className="run-workspace">
                <aside className="run-list" aria-label="任务历史">
                  <div className="panel-heading"><span>运行历史</span><small>{runs.length}</small></div>
                  {runs.length ? runs.map((run) => (
                    <button
                      key={run.id}
                      className={selectedRunId === run.id ? 'run-list-item selected' : 'run-list-item'}
                      onClick={() => selectRun(run.id, runTab)}
                    >
                      <div>
                        <Tag size="sm" type={tagType(run.status)}>{statusLabel(run.status)}</Tag>
                        <span>{timeLabel(run.created_at)}</span>
                      </div>
                      <strong>{run.agent_name}</strong>
                      <p>{run.prompt}</p>
                      <small>{run.executor} · {run.event_count} events</small>
                    </button>
                  )) : <div className="empty-state small"><Task size={24} /><p>还没有运行记录</p></div>}
                </aside>

                <div className="run-detail">
                  {selectedRun ? (
                    <>
                      <div className="run-detail-head">
                        <div>
                          <div className="run-title-line">
                            <Tag type={tagType(selectedRun.status)}>{statusLabel(selectedRun.status)}</Tag>
                            {selectedRun.run_role && selectedRun.run_role !== 'task' ? <Tag type="purple">{selectedRun.run_role}</Tag> : null}
                            <span>{selectedRun.id}</span>
                          </div>
                          <h2>{selectedRun.agent_name}</h2>
                          <p>{selectedRun.prompt}</p>
                        </div>
                        <div className="run-actions">
                          {!terminalStates.has(selectedRun.status) ? (
                            <Button
                              kind="danger--tertiary"
                              size="sm"
                              renderIcon={Stop}
                              disabled={actionPending}
                              onClick={() => perform(() => post(`/api/runs/${selectedRun.id}/stop`))}
                            >停止</Button>
                          ) : null}
                          {terminalStates.has(selectedRun.status) && selectedRun.session_id ? (
                            <Button kind="tertiary" size="sm" renderIcon={Renew} onClick={() => setResumeOpen(true)}>
                              续接会话
                            </Button>
                          ) : null}
                          {selectedRun.status === 'completed' && selectedRun.evaluation_status !== 'running' ? (
                            <Button
                              size="sm"
                              disabled={actionPending || workbenchBusy}
                              onClick={() => perform(() => post(`/api/runs/${selectedRun.id}/evaluate`))}
                            >{selectedRun.evaluation ? '重新评测' : '发起评测'}</Button>
                          ) : null}
                        </div>
                      </div>
                      <div className="run-facts">
                        <div><span>执行器</span><strong>{selectedRun.executor}{selectedRun.model ? ` / ${selectedRun.model}` : ''}</strong></div>
                        <div><span>Revision</span><strong>{compactRevision(selectedRun.head_revision || selectedRun.agent_revision)}</strong></div>
                        <div><span>分支</span><strong>{selectedRun.branch || '准备中'}</strong></div>
                        <div><span>会话</span><strong>{selectedRun.session_id?.slice(0, 12) || '尚未捕获'}</strong></div>
                      </div>
                      <div className="detail-tabs" role="tablist" aria-label="运行详情">
                        {([
                          ['output', '最终输出'],
                          ['trace', `可见轨迹 ${events.length}`],
                          ['changes', '文件变化'],
                          ['evaluation', '评测'],
                        ] as Array<[RunTab, string]>).map(([id, label]) => (
                          <button
                            key={id}
                            role="tab"
                            aria-selected={runTab === id}
                            className={runTab === id ? 'active' : ''}
                            onClick={() => setRunTab(id)}
                          >{label}</button>
                        ))}
                      </div>
                      <div className="detail-content">
                        {runTab === 'output' ? (
                          selectedRun.final_output ? <pre className="output-block">{selectedRun.final_output}</pre> : (
                            <div className="empty-state"><Document size={32} /><p>运行结束后在这里显示最终输出</p></div>
                          )
                        ) : null}
                        {runTab === 'trace' ? (
                          events.length ? (
                            <ol className="trace-list">
                              {events.map((event) => (
                                <li key={event.seq}>
                                  <div className={`trace-dot ${event.source}`} />
                                  <div>
                                    <div className="trace-meta">
                                      <span>#{event.seq}</span><strong>{event.type}</strong>
                                      <span>{event.source} / {event.channel}</span><time>{timeLabel(event.timestamp)}</time>
                                    </div>
                                    <p>{event.summary}</p>
                                    <details><summary>原始事件</summary><pre>{JSON.stringify(event.payload, null, 2)}</pre></details>
                                  </div>
                                </li>
                              ))}
                            </ol>
                          ) : <div className="empty-state"><Time size={32} /><p>正在等待第一个运行事件</p></div>
                        ) : null}
                        {runTab === 'changes' ? (
                          <div>
                            <div className="change-header">
                              <div><span>工作区状态</span><pre>{selectedRun.workspace_status || '没有文件变化'}</pre></div>
                              <div className="change-actions">
                                {selectedRun.workspace_status && !selectedRun.commit ? (
                                  <Button kind="tertiary" size="sm" onClick={() => setCommitOpen(true)}>提交候选分支</Button>
                                ) : null}
                                {selectedRun.commit ? <Tag type="green">已提交 {compactRevision(selectedRun.commit)}</Tag> : null}
                                {selectedRun.workspace_released_at ? (
                                  <Tag type="gray">工作区已释放</Tag>
                                ) : terminalStates.has(selectedRun.status) && selectedRun.worktree && !selectedRun.workspace_status ? (
                                  <Button kind="ghost" size="sm" onClick={() => setReleaseOpen(true)}>释放干净工作区</Button>
                                ) : null}
                              </div>
                            </div>
                            {selectedRun.workspace_patch ? <pre className="diff-block">{selectedRun.workspace_patch}</pre> : (
                              <div className="empty-state"><Code size={32} /><p>该任务没有产生文件差异</p></div>
                            )}
                          </div>
                        ) : null}
                        {runTab === 'evaluation' ? (
                          selectedRun.evaluation ? <EvaluationView evaluation={selectedRun.evaluation} /> : selectedRun.evaluation_status === 'running' ? (
                            <div className="empty-state"><InlineLoading description="Judge 正在评测任务完成与执行过程" /></div>
                          ) : selectedRun.evaluation_error ? (
                            <InlineNotification kind="error" title="评测失败" subtitle={selectedRun.evaluation_error} hideCloseButton />
                          ) : <div className="empty-state"><Checkmark size={32} /><p>发起评测后在这里查看双维度结果</p></div>
                        ) : null}
                      </div>
                    </>
                  ) : <div className="empty-state"><Task size={32} /><p>选择一条运行查看详情</p></div>}
                </div>
              </div>
            </section>
          ) : null}

          {page === 'evals' ? (
            <section aria-labelledby="evals-heading">
              <div className="page-heading">
                <div>
                  <p className="eyebrow">EVALUATION CATALOG</p>
                  <h1 id="evals-heading">评测中心</h1>
                  <p>Ground Truth 可选；一个 Judge 始终输出任务完成与执行过程两个维度。</p>
                </div>
                <div className="heading-metrics">
                  <div><strong>{evalCases.length}</strong><span>评测定义</span></div>
                  <div><strong>{launchableCases.length}</strong><span>可直接运行</span></div>
                  <div><strong>{trials.length}</strong><span>封存 Trial</span></div>
                </div>
              </div>
              <Tabs>
                <TabList aria-label="评测内容">
                  <Tab>评测用例</Tab>
                  <Tab>历史 Trial</Tab>
                </TabList>
                <TabPanels>
                  <TabPanel>
                    <div className="table-wrap">
                      <table>
                        <thead><tr><th>用例</th><th>类别</th><th>期望</th><th>来源</th><th><span className="visually-hidden">操作</span></th></tr></thead>
                        <tbody>
                          {evalCases.map((item) => (
                            <tr key={item.id}>
                              <td><strong>{item.name}</strong><small>{item.id}</small></td>
                              <td><Tag size="sm" type="cool-gray">{item.category}</Tag></td>
                              <td>{item.expected ? '有参考约束' : 'Judge 判定'}</td>
                              <td><code>{item.path.split('/').slice(-3).join('/')}</code></td>
                              <td>
                                <div className="row-actions">
                                  <Button kind="ghost" size="sm" onClick={() => openLaunch(undefined, item)} disabled={!item.launchable || workbenchBusy}>运行</Button>
                                  <Button kind="ghost" size="sm" onClick={() => openEvolution(item)} disabled={!item.launchable || workbenchBusy}>进化</Button>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </TabPanel>
                  <TabPanel>
                    <div className="table-wrap">
                      <table>
                        <thead><tr><th>Trial</th><th>任务</th><th>类型</th><th>开始</th><th>归档位置</th></tr></thead>
                        <tbody>
                          {trials.map((trial) => (
                            <tr key={trial.id}>
                              <td><strong>{trial.id}</strong></td>
                              <td>{trial.task_id || '未登记'}</td>
                              <td><Tag size="sm" type="gray">{trial.record_kind || 'trial'}</Tag></td>
                              <td>{timeLabel(trial.started_at)}</td>
                              <td><code>{trial.path.replace('/home/yyh/project/omni-brain/', '')}</code></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </TabPanel>
                </TabPanels>
              </Tabs>
            </section>
          ) : null}

          {page === 'evolution' ? (
            <section aria-labelledby="evolution-heading">
              <div className="page-heading compact">
                <div>
                  <p className="eyebrow">LINEAR EVOLUTION</p>
                  <h1 id="evolution-heading">进化实验</h1>
                  <p>基线、失败证据、候选修改、同题重跑与采用判断都保留为可审记录。</p>
                </div>
                <Button size="sm" renderIcon={Add} onClick={() => openEvolution()} disabled={workbenchBusy}>
                  新建进化
                </Button>
              </div>
              {evolutions.length ? evolutions.map((evolution) => (
                <article className="evolution-card" key={evolution.id}>
                  <div className="evolution-head">
                    <div>
                      <div className="run-title-line">
                        <Tag type={tagType(evolution.status)}>{statusLabel(evolution.status)}</Tag>
                        <span>{evolution.id}</span>
                      </div>
                      <h2>{evolution.agent_name}</h2>
                      <p>{evolution.prompt}</p>
                    </div>
                    <div className="evolution-current">
                      <span>当前阶段</span>
                      <strong>{evolution.stage.replaceAll('_', ' ')}</strong>
                      <small>best {compactRevision(evolution.best_revision)}</small>
                    </div>
                  </div>
                  {evolution.error ? <InlineNotification kind="error" title="进化中止" subtitle={evolution.error} hideCloseButton /> : null}
                  <div className="evolution-track">
                    <div className="evolution-step seed">
                      <div className="step-marker">S</div>
                      <div className="step-card">
                        <div><strong>Seed / 基线</strong><code>{compactRevision(evolution.seed_revision)}</code></div>
                        {evolution.baseline?.evaluation ? (
                          <>
                            <div className="candidate-score"><strong>{evolution.baseline.score}</strong><span>综合分</span></div>
                            <p>{evolution.baseline.evaluation.summary}</p>
                            <Button kind="ghost" size="sm" onClick={() => selectRun(evolution.baseline!.run_id, 'evaluation')}>查看基线 Run</Button>
                          </>
                        ) : <InlineLoading description="基线运行与评测中" />}
                      </div>
                    </div>
                    {evolution.candidates.map((candidate) => (
                      <div className={candidate.accepted ? 'evolution-step accepted' : 'evolution-step rejected'} key={candidate.iteration}>
                        <div className="step-marker">{candidate.iteration}</div>
                        <div className="step-card">
                          <div>
                            <strong>候选 {candidate.iteration}</strong>
                            <Tag size="sm" type={candidate.accepted ? 'green' : 'warm-gray'}>{candidate.accepted ? '实验内采用' : '不采用'}</Tag>
                            <code>{compactRevision(candidate.revision)}</code>
                          </div>
                          <div className="candidate-score"><strong>{candidate.score}</strong><span className={candidate.delta > 0 ? 'positive' : candidate.delta < 0 ? 'negative' : ''}>{candidate.delta > 0 ? '+' : ''}{candidate.delta}</span></div>
                          <p>{candidate.evaluation.summary}</p>
                          <div className="candidate-reason">
                            <span>发现的问题</span>
                            <ul>{candidate.evaluation.problems.slice(0, 3).map((item) => <li key={item}>{item}</li>)}</ul>
                          </div>
                          <div className="candidate-links">
                            <Button kind="ghost" size="sm" onClick={() => selectRun(candidate.optimizer_run_id, 'changes')}>改进与差异</Button>
                            <Button kind="ghost" size="sm" onClick={() => selectRun(candidate.evaluation_run_id, 'evaluation')}>重跑与评分</Button>
                          </div>
                        </div>
                      </div>
                    ))}
                    {evolution.status === 'running' ? (
                      <div className="evolution-step pending">
                        <div className="step-marker"><Renew size={16} /></div>
                        <div className="step-card"><InlineLoading description="正在产生下一份可审证据" /></div>
                      </div>
                    ) : null}
                  </div>
                </article>
              )) : (
                <div className="empty-panel">
                  <ChartLine size={40} />
                  <h2>还没有进化实验</h2>
                  <p>从一个可直接运行的评测用例开始，工作台会保存基线和每个候选。</p>
                  <Button onClick={() => openEvolution()} disabled={workbenchBusy}>创建第一条线性进化</Button>
                </div>
              )}
            </section>
          ) : null}
        </main>
      </div>

      <Modal
        open={launchOpen}
        modalHeading="启动 Agent 任务"
        modalLabel="独立 Git worktree"
        primaryButtonText={actionPending ? '正在创建' : '创建并运行'}
        secondaryButtonText="取消"
        primaryButtonDisabled={!launchAgentId || !launchPrompt.trim() || actionPending || workbenchBusy}
        onRequestClose={() => setLaunchOpen(false)}
        onRequestSubmit={() => void submitRun()}
      >
        <div className="modal-form">
          <Select id="launch-agent" labelText="Agent 能力" value={launchAgentId} onChange={(event) => {
            const value = event.target.value
            setLaunchAgentId(value)
            const agent = agents.find((item) => item.id === value)
            if (agent) setLaunchExecutor(agent.default_executor)
          }}>
            {agents.map((agent) => <SelectItem key={agent.id} value={agent.id} text={agent.name} />)}
          </Select>
          <Select id="launch-case" labelText="评测用例（可选）" value={launchCaseId} onChange={(event) => {
            const value = event.target.value
            setLaunchCaseId(value)
            const item = evalCases.find((entry) => entry.id === value)
            if (item?.prompt) setLaunchPrompt(item.prompt)
          }}>
            <SelectItem value="" text="不绑定评测用例" />
            {launchableCases.map((item) => <SelectItem key={item.id} value={item.id} text={`${item.category} / ${item.name}`} />)}
          </Select>
          <TextArea id="launch-prompt" labelText="任务内容" rows={8} value={launchPrompt} onChange={(event) => setLaunchPrompt(event.target.value)} />
          <div className="form-grid">
            <Select id="launch-executor" labelText="执行器" value={launchExecutor} onChange={(event) => setLaunchExecutor(event.target.value)}>
              <SelectItem value="codex" text="Codex CLI" />
              <SelectItem value="opencode" text="OpenCode CLI" />
            </Select>
            <TextInput id="launch-model" labelText="模型（可选）" placeholder="使用 CLI 默认模型" value={launchModel} onChange={(event) => setLaunchModel(event.target.value)} />
          </div>
          <InlineNotification kind="info" title="v0 隔离边界" subtitle="仅隔离仓库代码和文件，不隔离进程、网络与凭证。" hideCloseButton />
        </div>
      </Modal>

      <Modal
        open={resumeOpen}
        modalHeading="续接已有会话"
        primaryButtonText="续接运行"
        secondaryButtonText="取消"
        primaryButtonDisabled={!resumePrompt.trim() || actionPending || workbenchBusy}
        onRequestClose={() => setResumeOpen(false)}
        onRequestSubmit={() => selectedRun && void perform(
          () => post(`/api/runs/${selectedRun.id}/resume`, { prompt: resumePrompt }),
          () => { setResumeOpen(false); setResumePrompt(''); setRunTab('trace') },
        )}
      >
        <TextArea id="resume-prompt" labelText="继续要求 Agent 做什么" rows={6} value={resumePrompt} onChange={(event) => setResumePrompt(event.target.value)} />
      </Modal>

      <Modal
        open={commitOpen}
        modalHeading="提交运行分支"
        modalLabel={selectedRun?.branch || ''}
        primaryButtonText="创建 Git commit"
        secondaryButtonText="取消"
        primaryButtonDisabled={!commitMessage.trim() || actionPending}
        onRequestClose={() => setCommitOpen(false)}
        onRequestSubmit={() => selectedRun && void perform(
          () => post(`/api/runs/${selectedRun.id}/commit`, { message: commitMessage }),
          () => setCommitOpen(false),
        )}
      >
        <TextInput id="commit-message" labelText="Commit message" value={commitMessage} onChange={(event) => setCommitMessage(event.target.value)} />
        <div className="modal-warning"><WarningAlt size={18} /><span>此操作只提交候选分支，不会自动合入 Release。</span></div>
      </Modal>

      <Modal
        danger
        open={releaseOpen}
        modalHeading="释放干净工作区"
        modalLabel={selectedRun?.worktree || ''}
        primaryButtonText="移除 worktree"
        secondaryButtonText="取消"
        primaryButtonDisabled={actionPending}
        onRequestClose={() => setReleaseOpen(false)}
        onRequestSubmit={() => selectedRun && void perform(
          () => post(`/api/runs/${selectedRun.id}/release-worktree`),
          () => setReleaseOpen(false),
        )}
      >
        <p className="release-copy">运行记录、轨迹、分支和 commit 会保留；本地 worktree 目录会被移除。若存在未提交变化，后端会拒绝此操作。</p>
      </Modal>

      <Modal
        open={evolutionOpen}
        modalHeading="创建线性进化"
        modalLabel="执行 → 评测 → 改进 → 选择"
        primaryButtonText={actionPending ? '正在创建' : '开始进化'}
        secondaryButtonText="取消"
        primaryButtonDisabled={!evolutionAgentId || !evolutionPrompt.trim() || actionPending || workbenchBusy}
        onRequestClose={() => setEvolutionOpen(false)}
        onRequestSubmit={() => void submitEvolution()}
      >
        <div className="modal-form">
          <Select id="evolution-agent" labelText="要改进的 Agent 能力" value={evolutionAgentId} onChange={(event) => {
            const value = event.target.value
            setEvolutionAgentId(value)
            const agent = agents.find((item) => item.id === value)
            if (agent) setEvolutionExecutor(agent.default_executor)
          }}>
            {agents.map((agent) => <SelectItem key={agent.id} value={agent.id} text={agent.name} />)}
          </Select>
          <Select id="evolution-case" labelText="固定评测用例（推荐）" value={evolutionCaseId} onChange={(event) => {
            const value = event.target.value
            setEvolutionCaseId(value)
            const item = evalCases.find((entry) => entry.id === value)
            if (item?.prompt) setEvolutionPrompt(item.prompt)
          }}>
            <SelectItem value="" text="自定义任务，由 Judge 判定" />
            {launchableCases.map((item) => <SelectItem key={item.id} value={item.id} text={`${item.category} / ${item.name}`} />)}
          </Select>
          <TextArea id="evolution-prompt" labelText="固定任务" rows={7} value={evolutionPrompt} onChange={(event) => setEvolutionPrompt(event.target.value)} />
          <div className="form-grid">
            <Select id="evolution-executor" labelText="目标执行器" value={evolutionExecutor} onChange={(event) => setEvolutionExecutor(event.target.value)}>
              <SelectItem value="codex" text="Codex CLI" />
              <SelectItem value="opencode" text="OpenCode CLI" />
            </Select>
            <Select id="evolution-iterations" labelText="候选轮数" value={evolutionIterations} onChange={(event) => setEvolutionIterations(event.target.value)}>
              <SelectItem value="1" text="1 轮（推荐）" />
              <SelectItem value="2" text="2 轮" />
              <SelectItem value="3" text="3 轮" />
            </Select>
          </div>
          <InlineNotification kind="warning" title="不会自动合入" subtitle="候选会提交到独立分支；只有评分严格提高才标记为实验内采用。" hideCloseButton />
        </div>
      </Modal>
    </Theme>
  )
}
