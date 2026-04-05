/**
 * PersonalOrganizer.jsx — Pessoal (personal organizer) page.
 *
 * Profile-scoped dashboard with:
 *   - Dashboard summary cards
 *   - Enhanced quick capture (task w/ due date & priority, note w/ content)
 *   - Full-featured task list with expandable rows, status cycling, project grouping
 *   - Horizontal scrollable project cards
 *   - Personal notes with project color-coding
 *   - Calendar (personal context — profile's selected calendars)
 *   - Reminders (Apple sidecar)
 */
import { useState, useMemo, useCallback, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { GridStack } from 'gridstack'
import 'gridstack/dist/gridstack.min.css'
import { useProfile } from '../context/ProfileContext'
import api from '../api/client'
import useDashboardState from '../hooks/useDashboardState'
import styles from './PersonalOrganizer.module.css'
import WIDGET_REGISTRY, { getWidgetCategories, getWidgetMeta, generateWidgetId, findNextPosition } from './widgets/WidgetRegistry'
import TextBlock from './widgets/TextBlock'
import ClockWidget from './widgets/ClockWidget'
import GreetingWidget from './widgets/GreetingWidget'
import { FinSaldo, FinSobra, FinFatura } from './widgets/FinanceWidgets'
import EmailWidget from './widgets/EmailWidget'
import DriveWidget from './widgets/DriveWidget'
import ChatWidget from './widgets/ChatWidget'

// Reminders sidecar runs on each user's own Mac.
// Try HTTPS localhost first (works from HTTPS pages), then HTTP, then Vite proxy.
const SIDECAR_HTTPS = 'https://localhost:5179'
const SIDECAR_HTTP = 'http://localhost:5177'
const SIDECAR_PROXY = '/api/home/reminders'
let _sidecarBase = null // cached after first successful probe

async function _getSidecarBase() {
  if (_sidecarBase) return _sidecarBase
  // Try HTTPS sidecar (no mixed-content issues)
  for (const base of [SIDECAR_HTTPS, SIDECAR_HTTP]) {
    try {
      const res = await fetch(`${base}/api/home/reminders/lists/?all=true`, { signal: AbortSignal.timeout(1500) })
      if (res.ok) { _sidecarBase = base; return _sidecarBase }
    } catch {}
  }
  // Fall back to Vite proxy (server's sidecar — not per-user)
  _sidecarBase = SIDECAR_PROXY
  return _sidecarBase
}

async function sidecarGet(path) {
  const base = await _getSidecarBase()
  const res = await fetch(`${base}${path}`)
  if (!res.ok) throw new Error(`Sidecar ${res.status}`)
  return res.json()
}
async function sidecarPost(path, data) {
  const base = await _getSidecarBase()
  const res = await fetch(`${base}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error(`Sidecar ${res.status}`)
  return res.json()
}

/* ── Helpers ─────────────────────────────────────────────── */

function timeAgo(dateStr) {
  const d = new Date(dateStr)
  const now = new Date()
  const mins = Math.floor((now - d) / 60000)
  if (mins < 1) return 'agora'
  if (mins < 60) return `${mins}min`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h`
  const days = Math.floor(hrs / 24)
  if (days < 7) return `${days}d`
  return d.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })
}

function formatDueDate(dateStr) {
  if (!dateStr) return null
  const d = new Date(dateStr + 'T12:00:00')
  const today = new Date()
  today.setHours(12, 0, 0, 0)
  const diff = Math.floor((d - today) / 86400000)
  if (diff < 0) return { text: `${Math.abs(diff)}d atrasada`, overdue: true }
  if (diff === 0) return { text: 'Hoje', overdue: false }
  if (diff === 1) return { text: 'Amanha', overdue: false }
  if (diff <= 7) return { text: `${diff}d`, overdue: false }
  return { text: d.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' }), overdue: false }
}

const PRIORITY_LABELS = { 0: '', 1: '!', 2: '!!', 3: '!!!' }
const PRIORITY_COLORS = { 0: 'transparent', 1: '#4caf50', 2: 'var(--color-accent)', 3: 'var(--color-red)' }
const STATUS_LABELS = { todo: 'A fazer', doing: 'Fazendo', done: 'Feita' }

/* ── KPI Card (individual stat widget) ──────────────────── */

function KpiCard({ value, label, danger }) {
  return (
    <div className={`${styles.dashCard} ${danger ? styles.dashCardDanger : ''}`}>
      <span className={styles.dashCardValue}>{value}</span>
      <span className={styles.dashCardLabel}>{label}</span>
    </div>
  )
}

/* ── Enhanced Quick Capture ─────────────────────────────── */

function QuickCapture({ onAddTask, onAddNote, projects }) {
  const [mode, setMode] = useState('task')
  const [title, setTitle] = useState('')
  const [dueDate, setDueDate] = useState('')
  const [priority, setPriority] = useState(0)
  const [projectId, setProjectId] = useState('')
  const [noteContent, setNoteContent] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (mode === 'task') {
      if (!title.trim()) return
      onAddTask({
        title: title.trim(),
        due_date: dueDate || undefined,
        priority,
        project: projectId || undefined,
      })
      setTitle('')
      setDueDate('')
      setPriority(0)
      setProjectId('')
    } else {
      if (!title.trim() && !noteContent.trim()) return
      onAddNote({
        title: title.trim() || undefined,
        content: noteContent.trim() || title.trim(),
        project: projectId || undefined,
      })
      setTitle('')
      setNoteContent('')
      setProjectId('')
    }
  }

  return (
    <form onSubmit={handleSubmit} className={styles.quickCapture}>
      <div className={styles.captureRow}>
        <div className={styles.captureToggle}>
          <button
            type="button"
            className={`${styles.captureToggleBtn} ${mode === 'task' ? styles.captureToggleActive : ''}`}
            onClick={() => setMode('task')}
          >
            Tarefa
          </button>
          <button
            type="button"
            className={`${styles.captureToggleBtn} ${mode === 'note' ? styles.captureToggleActive : ''}`}
            onClick={() => setMode('note')}
          >
            Nota
          </button>
        </div>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder={mode === 'task' ? 'Nova tarefa...' : 'Titulo da nota...'}
          className={styles.captureInput}
        />
        <button
          type="submit"
          className={styles.captureBtn}
          disabled={mode === 'task' ? !title.trim() : (!title.trim() && !noteContent.trim())}
        >
          +
        </button>
      </div>

      <div className={styles.captureOptions}>
        {mode === 'task' && (
          <>
            <input
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              className={styles.captureDateInput}
              title="Data de vencimento"
            />
            <div className={styles.priorityPicker}>
              {[1, 2, 3].map((p) => (
                <button
                  key={p}
                  type="button"
                  className={`${styles.priorityBtn} ${priority === p ? styles.priorityBtnActive : ''}`}
                  style={priority === p ? { background: PRIORITY_COLORS[p], color: 'white' } : {}}
                  onClick={() => setPriority(priority === p ? 0 : p)}
                  title={`Prioridade ${p}`}
                >
                  {'!'.repeat(p)}
                </button>
              ))}
            </div>
          </>
        )}

        {mode === 'note' && (
          <textarea
            value={noteContent}
            onChange={(e) => setNoteContent(e.target.value)}
            placeholder="Conteudo da nota..."
            className={styles.captureTextarea}
            rows={2}
          />
        )}

        {projects && projects.length > 0 && (
          <select
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            className={styles.captureSelect}
          >
            <option value="">Sem projeto</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        )}
      </div>
    </form>
  )
}

/* ── Projects Bar ───────────────────────────────────────── */

function ProjectsBar({ projects, activeProject, onSelectProject }) {
  const queryClient = useQueryClient()
  const [creating, setCreating] = useState(false)
  const [newName, setNewName] = useState('')
  const [newColor, setNewColor] = useState('#b86530')

  const COLORS = ['#b86530', '#4caf50', '#2196f3', '#9c27b0', '#f44336', '#ff9800', '#00bcd4', '#607d8b']

  const createMutation = useMutation({
    mutationFn: (data) => api.post('/pessoal/projects/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pessoal-projects'] })
      setCreating(false)
      setNewName('')
    },
  })

  const handleCreate = (e) => {
    e.preventDefault()
    if (!newName.trim()) return
    createMutation.mutate({ name: newName.trim(), color: newColor })
  }

  return (
    <div className={styles.projectsBar}>
      <div className={styles.projectsScroll}>
        <button
          className={`${styles.projectCard} ${!activeProject ? styles.projectCardActive : ''}`}
          onClick={() => onSelectProject(null)}
        >
          <span className={styles.projectDot} style={{ background: 'var(--color-text-secondary)' }} />
          <span className={styles.projectCardName}>Todos</span>
        </button>

        {(projects || []).map((p) => {
          const isActive = activeProject === p.id
          const pct = p.task_count > 0
            ? Math.round(((p.done_count || 0) / p.task_count) * 100)
            : 0
          return (
            <button
              key={p.id}
              className={`${styles.projectCard} ${isActive ? styles.projectCardActive : ''}`}
              onClick={() => onSelectProject(isActive ? null : p.id)}
            >
              <span className={styles.projectDot} style={{ background: p.color || '#888' }} />
              <span className={styles.projectCardName}>{p.name}</span>
              {p.task_count > 0 && (
                <span className={styles.projectCardCount}>{p.task_count}</span>
              )}
              {p.task_count > 0 && (
                <div className={styles.projectProgress}>
                  <div className={styles.projectProgressFill} style={{ width: `${pct}%`, background: p.color || 'var(--color-accent)' }} />
                </div>
              )}
            </button>
          )
        })}

        {creating ? (
          <form className={styles.projectCreateForm} onSubmit={handleCreate}>
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Nome..."
              className={styles.projectCreateInput}
              autoFocus
              onKeyDown={(e) => { if (e.key === 'Escape') setCreating(false) }}
            />
            <div className={styles.projectColorPicker}>
              {COLORS.map((c) => (
                <button
                  key={c}
                  type="button"
                  className={`${styles.projectColorDot} ${newColor === c ? styles.projectColorDotActive : ''}`}
                  style={{ background: c }}
                  onClick={() => setNewColor(c)}
                />
              ))}
            </div>
            <button type="submit" className={styles.projectCreateSubmit} disabled={!newName.trim()}>
              OK
            </button>
          </form>
        ) : (
          <button className={styles.projectAddBtn} onClick={() => setCreating(true)}>
            + Projeto
          </button>
        )}
      </div>
    </div>
  )
}

/* ── Task List — Full Featured ──────────────────────────── */

function TaskList({ activeProject }) {
  const queryClient = useQueryClient()
  const [filter, setFilter] = useState('active') // 'active' | 'doing' | 'done'
  const [groupBy, setGroupBy] = useState('all') // 'all' | 'project'
  const [expandedId, setExpandedId] = useState(null)
  const [editFields, setEditFields] = useState({})
  const [newTitle, setNewTitle] = useState('')
  const [newProject, setNewProject] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['pessoal-tasks'],
    queryFn: () => api.get('/pessoal/tasks/'),
  })

  const { data: projectsData } = useQuery({
    queryKey: ['pessoal-projects'],
    queryFn: () => api.get('/pessoal/projects/'),
  })

  const projects = projectsData?.results || projectsData || []

  const allTasks = useMemo(() => {
    let list = data?.results || data || []
    if (activeProject) list = list.filter((t) => t.project === activeProject)
    return list
  }, [data, activeProject])

  const tasks = useMemo(() => {
    if (filter === 'active') return allTasks.filter((t) => t.status === 'todo' || t.status === 'doing')
    if (filter === 'doing') return allTasks.filter((t) => t.status === 'doing')
    if (filter === 'done') return allTasks.filter((t) => t.status === 'done')
    return allTasks
  }, [allTasks, filter])

  const groupedTasks = useMemo(() => {
    if (groupBy !== 'project') return null
    const groups = {}
    const noProject = []
    tasks.forEach((t) => {
      if (t.project_name) {
        if (!groups[t.project_name]) groups[t.project_name] = { tasks: [], color: null }
        groups[t.project_name].tasks.push(t)
        // find color from projects
        const proj = projects.find((p) => p.id === t.project)
        if (proj) groups[t.project_name].color = proj.color
      } else {
        noProject.push(t)
      }
    })
    return { groups, noProject }
  }, [tasks, groupBy, projects])

  const cycleMutation = useMutation({
    mutationFn: ({ id, status }) => {
      const next = status === 'todo' ? 'doing' : status === 'doing' ? 'done' : 'todo'
      return api.patch(`/pessoal/tasks/${id}/`, { status: next })
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pessoal-tasks'] }),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, ...d }) => api.patch(`/pessoal/tasks/${id}/`, d),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pessoal-tasks'] })
      queryClient.invalidateQueries({ queryKey: ['pessoal-projects'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/pessoal/tasks/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pessoal-tasks'] })
      queryClient.invalidateQueries({ queryKey: ['pessoal-projects'] })
    },
  })

  const addMutation = useMutation({
    mutationFn: (data) => api.post('/pessoal/tasks/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pessoal-tasks'] })
      queryClient.invalidateQueries({ queryKey: ['pessoal-projects'] })
      setNewTitle('')
    },
  })

  const handleAddTask = (e) => {
    e.preventDefault()
    if (!newTitle.trim()) return
    const data = { title: newTitle.trim() }
    if (newProject) data.project = newProject
    if (activeProject) data.project = activeProject
    addMutation.mutate(data)
  }

  const activeCount = allTasks.filter((t) => t.status !== 'done').length
  const doingCount = allTasks.filter((t) => t.status === 'doing').length
  const doneCount = allTasks.filter((t) => t.status === 'done').length

  const expandTask = (task) => {
    if (expandedId === task.id) {
      setExpandedId(null)
    } else {
      setExpandedId(task.id)
      setEditFields({
        title: task.title,
        notes: task.notes || '',
        due_date: task.due_date || '',
        priority: task.priority || 0,
        project: task.project || '',
        status: task.status || 'todo',
      })
    }
  }

  const saveExpanded = (id) => {
    const updates = {}
    const task = allTasks.find((t) => t.id === id)
    if (!task) return
    if (editFields.title !== task.title) updates.title = editFields.title
    if (editFields.notes !== (task.notes || '')) updates.notes = editFields.notes
    if (editFields.due_date !== (task.due_date || '')) updates.due_date = editFields.due_date || null
    if (editFields.priority !== (task.priority || 0)) updates.priority = editFields.priority
    if (editFields.project !== (task.project || '')) updates.project = editFields.project || null
    if (editFields.status !== (task.status || 'todo')) updates.status = editFields.status
    if (Object.keys(updates).length > 0) {
      updateMutation.mutate({ id, ...updates })
    }
    setExpandedId(null)
  }

  const renderStatusIcon = (status) => {
    if (status === 'done') {
      return (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="var(--color-accent)" stroke="var(--color-accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <polyline points="16 8 10 16 7 13" stroke="white" />
        </svg>
      )
    }
    if (status === 'doing') {
      return (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <path d="M12 2 A10 10 0 0 1 22 12" fill="var(--color-accent)" stroke="none" />
        </svg>
      )
    }
    return (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
      </svg>
    )
  }

  const renderTask = (task) => {
    const due = formatDueDate(task.due_date)
    const isExpanded = expandedId === task.id
    const borderColor = PRIORITY_COLORS[task.priority || 0]

    return (
      <div key={task.id} className={`${styles.taskItem} ${task.status === 'done' ? styles.taskDone : ''}`} style={{ borderLeft: `3px solid ${borderColor}` }}>
        <div className={styles.taskMainRow}>
          <button
            className={styles.checkBtn}
            onClick={(e) => { e.stopPropagation(); cycleMutation.mutate({ id: task.id, status: task.status }) }}
            title={STATUS_LABELS[task.status === 'todo' ? 'doing' : task.status === 'doing' ? 'done' : 'todo']}
          >
            {renderStatusIcon(task.status)}
          </button>

          <div className={styles.taskContent} onClick={() => expandTask(task)}>
            <span className={styles.taskTitle}>{task.title}</span>
            <div className={styles.taskMeta}>
              {task.priority > 0 && (
                <span style={{ color: PRIORITY_COLORS[task.priority], fontWeight: 700, fontSize: '0.7rem' }}>
                  {PRIORITY_LABELS[task.priority]}
                </span>
              )}
              {due && (
                <span className={`${styles.taskDue} ${due.overdue ? styles.taskOverdue : ''}`}>
                  {due.text}
                </span>
              )}
              {task.project_name && groupBy !== 'project' && (
                <span className={styles.taskProject}>{task.project_name}</span>
              )}
              {task.notes && (
                <span className={styles.taskHasNotes} title="Tem notas">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                </span>
              )}
            </div>
          </div>

          <button
            className={styles.taskDeleteBtn}
            onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(task.id) }}
            title="Excluir"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {isExpanded && (
          <div className={styles.taskExpanded}>
            <div className={styles.taskExpandedField}>
              <label className={styles.taskFieldLabel}>Titulo</label>
              <input
                className={styles.taskEditInput}
                value={editFields.title}
                onChange={(e) => setEditFields({ ...editFields, title: e.target.value })}
              />
            </div>
            <div className={styles.taskExpandedField}>
              <label className={styles.taskFieldLabel}>Notas</label>
              <textarea
                className={styles.taskEditTextarea}
                value={editFields.notes}
                onChange={(e) => setEditFields({ ...editFields, notes: e.target.value })}
                rows={2}
              />
            </div>
            <div className={styles.taskExpandedRow}>
              <div className={styles.taskExpandedField}>
                <label className={styles.taskFieldLabel}>Vencimento</label>
                <input
                  type="date"
                  className={styles.taskEditInput}
                  value={editFields.due_date}
                  onChange={(e) => setEditFields({ ...editFields, due_date: e.target.value })}
                />
              </div>
              <div className={styles.taskExpandedField}>
                <label className={styles.taskFieldLabel}>Prioridade</label>
                <div className={styles.priorityPicker}>
                  {[0, 1, 2, 3].map((p) => (
                    <button
                      key={p}
                      type="button"
                      className={`${styles.priorityBtn} ${editFields.priority === p ? styles.priorityBtnActive : ''}`}
                      style={editFields.priority === p && p > 0 ? { background: PRIORITY_COLORS[p], color: 'white' } : {}}
                      onClick={() => setEditFields({ ...editFields, priority: p })}
                    >
                      {p === 0 ? '-' : '!'.repeat(p)}
                    </button>
                  ))}
                </div>
              </div>
              <div className={styles.taskExpandedField}>
                <label className={styles.taskFieldLabel}>Status</label>
                <select
                  className={styles.taskEditSelect}
                  value={editFields.status}
                  onChange={(e) => setEditFields({ ...editFields, status: e.target.value })}
                >
                  <option value="todo">A fazer</option>
                  <option value="doing">Fazendo</option>
                  <option value="done">Feita</option>
                </select>
              </div>
            </div>
            {projects.length > 0 && (
              <div className={styles.taskExpandedField}>
                <label className={styles.taskFieldLabel}>Projeto</label>
                <select
                  className={styles.taskEditSelect}
                  value={editFields.project}
                  onChange={(e) => setEditFields({ ...editFields, project: e.target.value })}
                >
                  <option value="">Sem projeto</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
            )}
            <div className={styles.taskExpandedActions}>
              <button className={styles.taskSaveBtn} onClick={() => saveExpanded(task.id)}>
                Salvar
              </button>
              <button className={styles.taskCancelBtn} onClick={() => setExpandedId(null)}>
                Cancelar
              </button>
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderTaskList = (taskArr) => taskArr.map(renderTask)

  return (
    <div className={styles.widget}>
      <div className={styles.widgetHeader}>
        <h3 className={styles.widgetTitle}>TAREFAS</h3>
        <div className={styles.widgetHeaderRight}>
          <button
            className={`${styles.groupToggle} ${groupBy === 'project' ? styles.groupToggleActive : ''}`}
            onClick={() => setGroupBy(groupBy === 'all' ? 'project' : 'all')}
            title={groupBy === 'all' ? 'Agrupar por projeto' : 'Visualizacao plana'}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>
            </svg>
          </button>
          {activeCount > 0 && <span className={styles.badge}>{activeCount}</span>}
        </div>
      </div>

      <div className={styles.filterTabs}>
        <button
          className={`${styles.filterTab} ${filter === 'active' ? styles.filterTabActive : ''}`}
          onClick={() => setFilter('active')}
        >
          Ativas {activeCount > 0 && `(${activeCount})`}
        </button>
        <button
          className={`${styles.filterTab} ${filter === 'doing' ? styles.filterTabActive : ''}`}
          onClick={() => setFilter('doing')}
        >
          Fazendo {doingCount > 0 && `(${doingCount})`}
        </button>
        <button
          className={`${styles.filterTab} ${filter === 'done' ? styles.filterTabActive : ''}`}
          onClick={() => setFilter('done')}
        >
          Feitas {doneCount > 0 && `(${doneCount})`}
        </button>
      </div>

      <form className={styles.taskAddForm} onSubmit={handleAddTask}>
        <input
          className={styles.taskAddInput}
          placeholder="Nova tarefa..."
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
        />
        {projects.length > 0 && !activeProject && (
          <select
            className={styles.taskAddProject}
            value={newProject}
            onChange={(e) => setNewProject(e.target.value)}
          >
            <option value="">Projeto</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        )}
        <button type="submit" className={styles.taskAddBtn} disabled={!newTitle.trim()}>+</button>
      </form>

      <div className={styles.taskList}>
        {isLoading && <div className={styles.emptyState}>Carregando...</div>}

        {!isLoading && groupBy === 'all' && renderTaskList(tasks)}

        {!isLoading && groupBy === 'project' && groupedTasks && (
          <>
            {Object.entries(groupedTasks.groups).map(([name, group]) => (
              <div key={name}>
                <div className={styles.taskGroupHeader}>
                  <span className={styles.projectDot} style={{ background: group.color || '#888' }} />
                  <span className={styles.taskGroupName}>{name}</span>
                  <span className={styles.taskGroupCount}>{group.tasks.length}</span>
                </div>
                {renderTaskList(group.tasks)}
              </div>
            ))}
            {groupedTasks.noProject.length > 0 && (
              <div>
                <div className={styles.taskGroupHeader}>
                  <span className={styles.projectDot} style={{ background: 'var(--color-text-secondary)' }} />
                  <span className={styles.taskGroupName}>Sem projeto</span>
                  <span className={styles.taskGroupCount}>{groupedTasks.noProject.length}</span>
                </div>
                {renderTaskList(groupedTasks.noProject)}
              </div>
            )}
          </>
        )}

        {tasks.length === 0 && !isLoading && (
          <div className={styles.emptyState}>
            {filter === 'done' ? 'Nenhuma tarefa concluida' : filter === 'doing' ? 'Nenhuma tarefa em andamento' : 'Nenhuma tarefa pendente'}
          </div>
        )}
      </div>
    </div>
  )
}

/* ── Notes List — Enhanced ──────────────────────────────── */

function NotesList({ activeProject, projects }) {
  const queryClient = useQueryClient()
  const [editId, setEditId] = useState(null)
  const [editContent, setEditContent] = useState('')
  const [editTitle, setEditTitle] = useState('')
  const [expandedId, setExpandedId] = useState(null)

  const { data, isLoading } = useQuery({
    queryKey: ['pessoal-notes'],
    queryFn: () => api.get('/pessoal/notes/'),
  })

  const notes = useMemo(() => {
    let list = data?.results || data || []
    if (activeProject) list = list.filter((n) => n.project === activeProject)
    return list
  }, [data, activeProject])

  const updateMutation = useMutation({
    mutationFn: ({ id, ...d }) => api.patch(`/pessoal/notes/${id}/`, d),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pessoal-notes'] })
      setEditId(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/pessoal/notes/${id}/`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pessoal-notes'] }),
  })

  const togglePinMutation = useMutation({
    mutationFn: ({ id, pinned }) => api.patch(`/pessoal/notes/${id}/`, { pinned: !pinned }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pessoal-notes'] }),
  })

  const getProjectColor = (projectId) => {
    if (!projectId || !projects) return 'transparent'
    const p = projects.find((proj) => proj.id === projectId)
    return p?.color || 'transparent'
  }

  return (
    <div className={styles.widget}>
      <div className={styles.widgetHeader}>
        <h3 className={styles.widgetTitle}>NOTAS</h3>
        {notes.length > 0 && <span className={styles.badge}>{notes.length}</span>}
      </div>

      <div className={styles.notesList}>
        {isLoading && <div className={styles.emptyState}>Carregando...</div>}
        {notes.map((note) => {
          const isExpanded = expandedId === note.id
          const projColor = getProjectColor(note.project)
          return (
            <div
              key={note.id}
              className={`${styles.noteCard} ${note.pinned ? styles.notePinned : ''}`}
              style={{ borderLeft: `3px solid ${projColor}` }}
            >
              <div className={styles.noteTop}>
                <span className={styles.noteTime}>{timeAgo(note.updated_at)}</span>
                <div className={styles.noteActions}>
                  <button
                    className={styles.noteActionBtn}
                    onClick={() => togglePinMutation.mutate({ id: note.id, pinned: note.pinned })}
                    title={note.pinned ? 'Desafixar' : 'Fixar'}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill={note.pinned ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth={note.pinned ? 1 : 2} strokeLinecap="round" strokeLinejoin="round">
                      <path d="M16 2L21 7L15 13L19 17H5L9 13L3 7L8 2L12 6L16 2Z" />
                    </svg>
                  </button>
                  <button
                    className={styles.noteActionBtn}
                    onClick={() => {
                      if (editId === note.id) { setEditId(null) }
                      else { setEditId(note.id); setEditContent(note.content); setEditTitle(note.title || '') }
                    }}
                    title="Editar"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                      <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                    </svg>
                  </button>
                  <button
                    className={styles.noteActionBtn}
                    onClick={() => deleteMutation.mutate(note.id)}
                    title="Excluir"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="3 6 5 6 21 6" />
                      <path d="M19 6l-1.5 14a2 2 0 01-2 2h-7a2 2 0 01-2-2L5 6" />
                    </svg>
                  </button>
                </div>
              </div>

              {note.title && <h4 className={styles.noteTitle}>{note.title}</h4>}

              {editId === note.id ? (
                <div className={styles.noteEditWrap}>
                  <input
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    placeholder="Titulo..."
                    className={styles.taskEditInput}
                  />
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    className={styles.noteTextarea}
                    rows={3}
                    autoFocus
                  />
                  <button
                    className={styles.noteSaveBtn}
                    onClick={() => updateMutation.mutate({ id: note.id, content: editContent, title: editTitle || null })}
                  >
                    Salvar
                  </button>
                </div>
              ) : (
                <p
                  className={`${styles.noteBody} ${!isExpanded ? styles.noteBodyTruncated : ''}`}
                  onClick={() => setExpandedId(isExpanded ? null : note.id)}
                >
                  {note.content}
                </p>
              )}

              {note.project_name && (
                <span className={styles.noteProject}>{note.project_name}</span>
              )}
            </div>
          )
        })}
        {notes.length === 0 && !isLoading && (
          <div className={styles.emptyState}>Nenhuma nota pessoal</div>
        )}
      </div>
    </div>
  )
}

/* ── Upcoming Events ─────────────────────────────────────── */

function UpcomingEvents() {
  const now = new Date()
  const timeMin = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  const future = new Date(now.getTime() + 14 * 86400000)
  const timeMax = `${future.getFullYear()}-${String(future.getMonth() + 1).padStart(2, '0')}-${String(future.getDate()).padStart(2, '0')}`

  const { data, isLoading } = useQuery({
    queryKey: ['pessoal-calendar', timeMin],
    queryFn: () => api.get(`/calendar/events/?context=personal&time_min=${timeMin}&time_max=${timeMax}`),
    staleTime: 60000,
  })

  const events = data?.events || []

  const formatTime = (iso) => {
    const d = new Date(iso)
    return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  }

  const getDateKey = (iso) => {
    const d = new Date(iso.includes('T') ? iso : iso + 'T12:00:00')
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  }

  const formatDateHeader = (dateKey) => {
    const d = new Date(dateKey + 'T12:00:00')
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const evtDate = new Date(d)
    evtDate.setHours(0, 0, 0, 0)
    const diff = Math.floor((evtDate - today) / 86400000)
    if (diff === 0) return 'Hoje'
    if (diff === 1) return 'Amanha'
    return d.toLocaleDateString('pt-BR', { weekday: 'long', day: '2-digit', month: 'short' })
  }

  // Group events by date
  const grouped = useMemo(() => {
    const groups = {}
    events.slice(0, 15).forEach((evt) => {
      const key = getDateKey(evt.start)
      if (!groups[key]) groups[key] = []
      groups[key].push(evt)
    })
    return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b))
  }, [events])

  const calendarLabel = (cal) => {
    if (!cal) return ''
    // Show just the part before @ or a short name
    const at = cal.indexOf('@')
    return at > 0 ? cal.slice(0, at) : cal
  }

  return (
    <div className={styles.widget}>
      <div className={styles.widgetHeader}>
        <h3 className={styles.widgetTitle}>PROXIMOS EVENTOS</h3>
        {events.length > 0 && <span className={styles.badge}>{events.length}</span>}
      </div>
      <div className={styles.eventsList}>
        {isLoading && <div className={styles.emptyState}>Carregando...</div>}
        {grouped.map(([dateKey, dayEvents]) => (
          <div key={dateKey}>
            <div className={styles.eventsDateHeader}>{formatDateHeader(dateKey)}</div>
            {dayEvents.map((evt, i) => (
              <div key={i} className={styles.eventItem}>
                <span className={styles.eventColorDot} style={{ background: evt.calendar_color || 'var(--color-accent)' }} />
                <div className={styles.eventInfo}>
                  <span className={styles.eventTitle}>{evt.title}</span>
                  <div className={styles.eventMeta}>
                    <span className={styles.eventTime}>
                      {evt.all_day ? 'Dia todo' : `${formatTime(evt.start)} — ${formatTime(evt.end)}`}
                    </span>
                    {evt.location && (
                      <span className={styles.eventLocation}>{evt.location.length > 30 ? evt.location.slice(0, 30) + '...' : evt.location}</span>
                    )}
                  </div>
                  {evt.calendar && (
                    <span className={styles.eventCalendar}>{calendarLabel(evt.calendar)}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ))}
        {events.length === 0 && !isLoading && (
          <div className={styles.emptyState}>Nenhum evento nos proximos 14 dias</div>
        )}
      </div>
    </div>
  )
}

/* ── Personal Calendar (Month Grid) ──────────────────────── */

const WEEKDAYS = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab']
const MONTH_NAMES = [
  'Janeiro', 'Fevereiro', 'Marco', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
]

function buildCalendarDays(year, month) {
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const startDow = firstDay.getDay()
  const daysInMonth = lastDay.getDate()
  const days = []
  const prevLast = new Date(year, month, 0).getDate()
  for (let i = startDow - 1; i >= 0; i--) days.push({ day: prevLast - i, month: month - 1, outside: true })
  for (let d = 1; d <= daysInMonth; d++) days.push({ day: d, month, outside: false })
  const trailing = days.length <= 35 ? 35 - days.length : 42 - days.length
  for (let d = 1; d <= trailing; d++) days.push({ day: d, month: month + 1, outside: true })
  return days
}

function PersonalCalendar() {
  const now = new Date()
  const [viewYear, setViewYear] = useState(now.getFullYear())
  const [viewMonth, setViewMonth] = useState(now.getMonth())
  const todayKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  const [selectedDate, setSelectedDate] = useState(todayKey)

  const timeMin = `${viewYear}-${String(viewMonth + 1).padStart(2, '0')}-01`
  const lastDay = new Date(viewYear, viewMonth + 1, 0).getDate()
  const timeMax = `${viewYear}-${String(viewMonth + 1).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`

  const { data, isLoading } = useQuery({
    queryKey: ['pessoal-cal-month', viewYear, viewMonth],
    queryFn: () => api.get(`/calendar/events/?context=personal&time_min=${timeMin}&time_max=${timeMax}`),
    refetchInterval: 60000,
  })

  const eventsByDate = useMemo(() => {
    const map = {}
    ;(data?.events || []).forEach((evt) => {
      const key = evt.start.includes('T') ? evt.start.slice(0, 10) : evt.start
      if (!map[key]) map[key] = []
      map[key].push(evt)
    })
    return map
  }, [data])

  const days = useMemo(() => buildCalendarDays(viewYear, viewMonth), [viewYear, viewMonth])

  const dateKey = (d) => {
    const m = d.month
    const y = m < 0 ? viewYear - 1 : m > 11 ? viewYear + 1 : viewYear
    const mm = ((m % 12) + 12) % 12
    return `${y}-${String(mm + 1).padStart(2, '0')}-${String(d.day).padStart(2, '0')}`
  }

  const prevMonth = () => { if (viewMonth === 0) { setViewYear(viewYear - 1); setViewMonth(11) } else setViewMonth(viewMonth - 1); setSelectedDate(null) }
  const nextMonth = () => { if (viewMonth === 11) { setViewYear(viewYear + 1); setViewMonth(0) } else setViewMonth(viewMonth + 1); setSelectedDate(null) }
  const goToday = () => { setViewYear(now.getFullYear()); setViewMonth(now.getMonth()); setSelectedDate(todayKey) }

  const selectedEvents = selectedDate ? (eventsByDate[selectedDate] || []) : []

  const formatTime = (iso) => new Date(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })

  const calendarLabel = (cal) => {
    if (!cal) return ''
    const at = cal.indexOf('@')
    return at > 0 ? cal.slice(0, at) : cal
  }

  const MAX_PREVIEW = 2

  return (
    <div className={styles.widget}>
      <div className={styles.calHeader}>
        <button className={styles.calNavBtn} onClick={prevMonth}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6" /></svg>
        </button>
        <h3 className={styles.calTitle} onClick={goToday} style={{ cursor: 'pointer' }}>{MONTH_NAMES[viewMonth]} {viewYear}</h3>
        <button className={styles.calNavBtn} onClick={nextMonth}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6" /></svg>
        </button>
      </div>

      <div className={styles.calGrid}>
        {WEEKDAYS.map((wd) => <div key={wd} className={styles.calWeekday}>{wd}</div>)}
        {days.map((d, i) => {
          const key = dateKey(d)
          const isToday = key === todayKey
          const isSelected = key === selectedDate
          const dayEvents = eventsByDate[key] || []
          const overflow = dayEvents.length - MAX_PREVIEW
          return (
            <button
              key={i}
              className={[styles.calDay, d.outside && styles.calDayOutside, isToday && styles.calDayToday, isSelected && styles.calDaySelected].filter(Boolean).join(' ')}
              onClick={() => setSelectedDate(key === selectedDate ? null : key)}
            >
              <span className={styles.calDayNum}>{d.day}</span>
              <div className={styles.calDayEvents}>
                {dayEvents.slice(0, MAX_PREVIEW).map((evt, j) => (
                  <span key={j} className={styles.calEventPill} style={{ borderLeftColor: evt.calendar_color || 'var(--color-accent)' }}>
                    {evt.title}
                  </span>
                ))}
                {overflow > 0 && <span className={styles.calEventMore}>+{overflow}</span>}
              </div>
            </button>
          )
        })}
      </div>

      {isLoading && <div className={styles.emptyState} style={{ padding: '8px' }}>Carregando...</div>}

      {selectedDate && (
        <div className={styles.calDetail}>
          <div className={styles.calDetailDate}>
            {new Date(selectedDate + 'T12:00:00').toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' })}
          </div>
          {selectedEvents.length > 0 ? (
            selectedEvents.map((evt, i) => (
              <div key={i} className={styles.calEvent}>
                <span className={styles.calEventDot} style={{ background: evt.calendar_color || 'var(--color-accent)' }} />
                <div className={styles.calEventBody}>
                  <span className={styles.calEventTitle}>{evt.title}</span>
                  <span className={styles.calEventTime}>
                    {evt.all_day ? 'Dia todo' : `${formatTime(evt.start)} — ${formatTime(evt.end)}`}
                  </span>
                  {evt.location && (
                    <span className={styles.calEventLocation}>
                      {evt.location.length > 40 ? evt.location.slice(0, 40) + '...' : evt.location}
                    </span>
                  )}
                  {evt.calendar && (
                    <span className={styles.calEventCalendar}>{calendarLabel(evt.calendar)}</span>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className={styles.emptyState} style={{ padding: '8px' }}>Sem eventos</div>
          )}
        </div>
      )}
    </div>
  )
}

/* ── Personal Reminders ──────────────────────────────────── */

function PersonalReminders({ config, onConfigChange }) {
  const queryClient = useQueryClient()
  const [activeListIdx, setActiveListIdx] = useState(0)
  const [newReminder, setNewReminder] = useState('')
  const enabled = config?.enabled === true

  // Fetch ALL reminder lists (not just R&R)
  const { data: listsData } = useQuery({
    queryKey: ['pessoal-reminders-lists'],
    queryFn: () => sidecarGet('/api/home/reminders/lists/?all=true'),
    retry: 1,
    staleTime: 5 * 60 * 1000,
    enabled,
  })

  const availableLists = listsData?.lists || []
  const listName = availableLists[activeListIdx] || availableLists[0] || ''

  const { data, isLoading, error } = useQuery({
    queryKey: ['pessoal-reminders', listName],
    queryFn: () => sidecarGet(`/api/home/reminders/?list=${encodeURIComponent(listName)}`),
    enabled: !!listName,
    refetchInterval: 30000,
  })

  const completeMutation = useMutation({
    mutationFn: (name) => sidecarPost('/api/home/reminders/complete/', { name, list: listName }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pessoal-reminders', listName] }),
  })

  const addMutation = useMutation({
    mutationFn: (name) => sidecarPost('/api/home/reminders/add/', { name, list: listName }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pessoal-reminders', listName] })
      setNewReminder('')
    },
  })

  const handleAdd = (e) => {
    e.preventDefault()
    if (newReminder.trim()) addMutation.mutate(newReminder.trim())
  }

  // Check if sidecar is reachable — auto-enable when detected
  const { data: sidecarStatus } = useQuery({
    queryKey: ['sidecar-check'],
    queryFn: async () => {
      try {
        const base = await _getSidecarBase()
        const res = await fetch(`${base}/api/home/reminders/lists/?all=true`, { signal: AbortSignal.timeout(2000) })
        return res.ok ? 'connected' : 'error'
      } catch { return 'not-running' }
    },
    staleTime: 10000,
    enabled: !enabled,
  })

  // Auto-enable when sidecar is detected
  useEffect(() => {
    if (!enabled && sidecarStatus === 'connected') {
      onConfigChange({ enabled: true })
    }
  }, [enabled, sidecarStatus])

  if (!enabled) {
    const setupCmd = `curl -fsSL ${window.location.origin}/reminders-setup.sh | bash`
    const sidecarUp = sidecarStatus === 'connected'

    return (
      <div className={styles.widget}>
        <div className={styles.widgetHeader}>
          <h3 className={styles.widgetTitle}>LEMBRETES</h3>
        </div>
        <div className={styles.emptyState}>
          {sidecarUp ? (
            <>
              <p style={{ margin: '0 0 8px' }}>Sidecar detectado</p>
              <button
                className={styles.captureBtn}
                style={{ width: 'auto', padding: '6px 16px', fontSize: '0.78rem', position: 'relative', zIndex: 5 }}
                onClick={(e) => { e.stopPropagation(); onConfigChange({ enabled: true }) }}
              >
                Conectar Apple Reminders
              </button>
            </>
          ) : (
            <>
              <p style={{ margin: '0 0 8px' }}>Abra o Terminal no seu Mac e execute:</p>
              <div
                style={{
                  background: 'var(--color-bg)', border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-sm)', padding: '8px 12px', fontSize: '0.72rem',
                  fontFamily: 'monospace', cursor: 'pointer', wordBreak: 'break-all', position: 'relative', zIndex: 5,
                }}
                onClick={() => { navigator.clipboard.writeText(setupCmd) }}
                title="Clique para copiar"
              >
                {setupCmd}
              </div>
              <p style={{ fontSize: '0.68rem', color: 'var(--color-text-secondary)', margin: '6px 0 0' }}>
                Clique para copiar. Apos rodar, atualize a pagina.
              </p>
            </>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className={styles.widget}>
      <div className={styles.widgetHeader}>
        <h3 className={styles.widgetTitle}>LEMBRETES</h3>
        {data?.count != null && <span className={styles.badge}>{data.count}</span>}
      </div>

      {/* List tabs — scrollable since there are many */}
      <div className={styles.reminderTabs}>
        {availableLists.map((name, idx) => (
          <button
            key={name}
            className={`${styles.reminderTab} ${activeListIdx === idx ? styles.reminderTabActive : ''}`}
            onClick={() => setActiveListIdx(idx)}
          >
            {name}
          </button>
        ))}
      </div>

      {/* Add form */}
      <form onSubmit={handleAdd} className={styles.reminderAddRow}>
        <input
          type="text"
          value={newReminder}
          onChange={(e) => setNewReminder(e.target.value)}
          placeholder="Novo lembrete..."
          className={styles.captureInput}
          style={{ padding: '6px 10px', fontSize: '0.8rem' }}
        />
        <button type="submit" className={styles.captureBtn} style={{ width: 28, height: 28, fontSize: '0.9rem' }} disabled={!newReminder.trim() || addMutation.isPending}>
          +
        </button>
      </form>

      {/* Reminders list */}
      <div className={styles.reminderList}>
        {isLoading && <div className={styles.emptyState}>Carregando...</div>}
        {error && <div className={styles.emptyState} style={{ color: 'var(--color-red)' }}>Erro ao conectar</div>}
        {data?.reminders?.map((r, i) => (
          <div key={`${r.name}-${i}`} className={styles.reminderItem}>
            <button
              className={styles.checkBtn}
              onClick={() => completeMutation.mutate(r.name)}
              disabled={completeMutation.isPending}
              title="Concluir"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
              </svg>
            </button>
            <div className={styles.reminderContent}>
              <span className={styles.reminderName}>{r.name}</span>
              {r.due_date && <span className={styles.reminderDue}>{r.due_date}</span>}
            </div>
          </div>
        ))}
        {data?.reminders?.length === 0 && !isLoading && (
          <div className={styles.emptyState}>Nenhum lembrete pendente</div>
        )}
      </div>
    </div>
  )
}

/* ── Main Component ──────────────────────────────────────── */

/* ── Grid Layout (gridstack) ──────────────────────────────── */

/* ── Tab Bar ────────────────────────────────────────────── */

function TabBar({ tabs, activeTabId, onSwitch, onAdd, onRename, onDelete }) {
  const [renamingId, setRenamingId] = useState(null)
  const [renameValue, setRenameValue] = useState('')
  const [contextMenu, setContextMenu] = useState(null)
  const contextRef = useRef(null)

  useEffect(() => {
    if (!contextMenu) return
    const handleClick = (e) => {
      if (contextRef.current && !contextRef.current.contains(e.target)) setContextMenu(null)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [contextMenu])

  const startRename = (tab) => {
    setRenamingId(tab.id)
    setRenameValue(tab.name)
    setContextMenu(null)
  }

  const commitRename = () => {
    if (renamingId && renameValue.trim()) {
      onRename(renamingId, renameValue.trim())
    }
    setRenamingId(null)
  }

  const handleContextMenu = (e, tab) => {
    e.preventDefault()
    setContextMenu({ tabId: tab.id, x: e.clientX, y: e.clientY })
  }

  return (
    <div className={styles.tabBar}>
      {tabs.map((tab) => {
        if (renamingId === tab.id) {
          return (
            <input
              key={tab.id}
              className={styles.tabRenameInput}
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              onBlur={commitRename}
              onKeyDown={(e) => {
                if (e.key === 'Enter') commitRename()
                if (e.key === 'Escape') setRenamingId(null)
              }}
              autoFocus
            />
          )
        }
        return (
          <div
            key={tab.id}
            className={`${styles.tab} ${tab.id === activeTabId ? styles.tabActive : ''}`}
            onClick={() => onSwitch(tab.id)}
            onDoubleClick={() => startRename(tab)}
            onContextMenu={(e) => handleContextMenu(e, tab)}
          >
            {tab.name}
            {tabs.length > 1 && (
              <button
                className={styles.tabClose}
                onClick={(e) => {
                  e.stopPropagation()
                  if (window.confirm('Excluir esta aba?')) onDelete(tab.id)
                }}
                title="Excluir aba"
              >
                ×
              </button>
            )}
          </div>
        )
      })}
      <button className={styles.tabAdd} onClick={onAdd} title="Nova aba">
        +
      </button>

      {contextMenu && (
        <div
          ref={contextRef}
          className={styles.tabContextMenu}
          style={{ position: 'fixed', top: contextMenu.y, left: contextMenu.x, zIndex: 200 }}
        >
          <button
            className={styles.tabContextItem}
            onClick={() => {
              const tab = tabs.find(t => t.id === contextMenu.tabId)
              if (tab) startRename(tab)
            }}
          >
            Renomear
          </button>
          {tabs.length > 1 && (
            <button
              className={styles.tabContextItem}
              onClick={() => {
                if (window.confirm('Excluir esta aba?')) {
                  onDelete(contextMenu.tabId)
                }
                setContextMenu(null)
              }}
            >
              Excluir
            </button>
          )}
        </div>
      )}
    </div>
  )
}

/* ── Widget Catalog Dropdown ────────────────────────────── */

function WidgetCatalog({ onAdd, activeWidgetTypes }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)
  const categories = useMemo(() => getWidgetCategories(), [])

  useEffect(() => {
    if (!open) return
    const handleClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [open])

  return (
    <div ref={ref} className={styles.catalogWrap}>
      <button
        className={styles.catalogBtn}
        onClick={() => setOpen(!open)}
        title="Adicionar widget"
      >
        +
      </button>
      {open && (
        <div className={styles.catalogDropdown}>
          {Object.entries(categories).map(([cat, widgets]) => (
            <div key={cat} className={styles.catalogCategory}>
              <div className={styles.catalogCategoryLabel}>{cat}</div>
              {widgets.map((w) => (
                <button
                  key={w.type}
                  className={styles.catalogItem}
                  onClick={() => { onAdd(w.type); setOpen(false) }}
                >
                  {w.label}
                </button>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

/* ── Main Component ──────────────────────────────────────── */

export default function PersonalOrganizer() {
  const { currentProfile } = useProfile()
  const profileId = currentProfile?.id || 'default'

  // Key forces full remount on profile switch — clean grid lifecycle
  return <PersonalOrganizerInner key={profileId} profileId={profileId} />
}

const PALMER_ID = 'a29184ea-9d4d-4c65-8300-386ed5b07fca'

function PersonalOrganizerInner({ profileId }) {
  const queryClient = useQueryClient()
  const [activeProject, setActiveProject] = useState(null)
  const [dashState, updateDashState, dashLoading, saveStatus] = useDashboardState(profileId)

  const tabs = dashState?.tabs || [{ id: 'default', name: 'Principal', widgets: [] }]
  const widgetConfigs = dashState?.configs || {}
  const [activeTabId, setActiveTabId] = useState(null)

  // Set initial active tab when state loads
  useEffect(() => {
    if (dashState && !activeTabId) {
      setActiveTabId(dashState.tabs?.[0]?.id || 'default')
    }
  }, [dashState, activeTabId])

  // Auto-enable reminders for Palmer
  useEffect(() => {
    if (dashState && profileId === PALMER_ID && !widgetConfigs.reminders) {
      updateDashState({ configs: { ...widgetConfigs, reminders: { enabled: true } } })
    }
  }, [dashState, profileId])

  const activeTab = tabs.find(t => t.id === activeTabId) || tabs[0]
  const widgets = activeTab?.widgets || []

  const setTabs = useCallback((updater) => {
    updateDashState((prev) => {
      const currentTabs = prev?.tabs || []
      const newTabs = typeof updater === 'function' ? updater(currentTabs) : updater
      return { tabs: newTabs }
    })
  }, [updateDashState])

  const setWidgetConfigs = useCallback((updater) => {
    updateDashState((prev) => {
      const currentConfigs = prev?.configs || {}
      const newConfigs = typeof updater === 'function' ? updater(currentConfigs) : updater
      return { configs: newConfigs }
    })
  }, [updateDashState])

  // ── Tab actions ──

  const switchTab = useCallback((tabId) => {
    setActiveTabId(tabId)
  }, [])

  const addTab = useCallback(() => {
    const name = window.prompt('Nome da nova aba:')
    if (!name?.trim()) return
    const id = `tab-${Date.now().toString(36)}`
    setTabs(prev => [...prev, { id, name: name.trim(), widgets: [] }])
    setActiveTabId(id)
  }, [])

  const renameTab = useCallback((tabId, newName) => {
    setTabs(prev => prev.map(t => t.id === tabId ? { ...t, name: newName } : t))
  }, [])

  const deleteTab = useCallback((tabId) => {
    setTabs(prev => {
      if (prev.length <= 1) return prev
      const next = prev.filter(t => t.id !== tabId)
      // If deleting the active tab, switch to first remaining
      if (tabId === activeTabId) {
        setActiveTabId(next[0].id)
      }
      return next
    })
  }, [activeTabId])

  // ── Add / Remove widgets (scoped to active tab) ──

  const addWidget = useCallback((type) => {
    const meta = getWidgetMeta(type)
    if (!meta) return
    const id = generateWidgetId(type)
    const pos = findNextPosition(widgets, meta.defaultW, meta.defaultH)
    const newWidget = { id, type, x: pos.x, y: pos.y, w: meta.defaultW, h: meta.defaultH }

    setTabs(prev => prev.map(tab =>
      tab.id === activeTabId ? { ...tab, widgets: [...tab.widgets, newWidget] } : tab
    ))
  }, [activeTabId, widgets])

  const removeWidget = useCallback((id) => {
    setTabs(prev => prev.map(tab =>
      tab.id === activeTabId ? { ...tab, widgets: tab.widgets.filter(w => w.id !== id) } : tab
    ))
    setWidgetConfigs(prev => {
      const next = { ...prev }
      delete next[id]
      return next
    })
  }, [activeTabId])

  const updateWidgetConfig = useCallback((id, config) => {
    setWidgetConfigs(prev => ({ ...prev, [id]: config }))
  }, [])

  // Sync gridstack layout changes back into the tab's widgets array
  const handleLayoutChange = useCallback((nodes) => {
    const posMap = {}
    for (const n of nodes) posMap[n.id] = n
    setTabs(prev => prev.map(tab => {
      if (tab.id !== activeTabId) return tab
      return {
        ...tab,
        widgets: tab.widgets.map(w => {
          const pos = posMap[w.id]
          return pos ? { ...w, x: pos.x, y: pos.y, w: pos.w, h: pos.h } : w
        }),
      }
    }))
  }, [activeTabId])

  // ── Data queries ──

  const { data: tasksData } = useQuery({
    queryKey: ['pessoal-tasks'],
    queryFn: () => api.get('/pessoal/tasks/'),
  })

  const { data: projectsData } = useQuery({
    queryKey: ['pessoal-projects'],
    queryFn: () => api.get('/pessoal/projects/'),
  })

  const tasks = tasksData?.results || tasksData || []
  const projects = projectsData?.results || projectsData || []

  const addTaskMutation = useMutation({
    mutationFn: (data) => api.post('/pessoal/tasks/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pessoal-tasks'] })
      queryClient.invalidateQueries({ queryKey: ['pessoal-projects'] })
    },
  })

  const addNoteMutation = useMutation({
    mutationFn: (data) => api.post('/pessoal/notes/', data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pessoal-notes'] }),
  })

  if (dashLoading) return <div className={styles.emptyState}>Carregando dashboard...</div>

  // KPI computations
  const todayStr = new Date().toISOString().slice(0, 10)
  const activeTasks = tasks.filter((t) => t.status !== 'done')
  const todayCount = activeTasks.filter((t) => t.due_date === todayStr).length
  const overdueCount = activeTasks.filter((t) => t.due_date && t.due_date < todayStr).length
  const activeProjectCount = projects.filter((p) => p.status === 'active').length

  // ── Render widget content by type ──

  const renderWidgetContent = (widget) => {
    const type = widget.type
    switch (type) {
      case 'kpi-hoje':      return <KpiCard value={todayCount} label="Hoje" />
      case 'kpi-atrasadas': return <KpiCard value={overdueCount} label="Atrasadas" danger={overdueCount > 0} />
      case 'kpi-ativas':    return <KpiCard value={activeTasks.length} label="Ativas" />
      case 'kpi-projetos':  return <KpiCard value={activeProjectCount} label="Projetos" />
      case 'capture':
        return (
          <QuickCapture
            onAddTask={(data) => addTaskMutation.mutate(data)}
            onAddNote={(data) => addNoteMutation.mutate(data)}
            projects={projects}
          />
        )
      case 'projects':
        return (
          <ProjectsBar
            projects={projects}
            activeProject={activeProject}
            onSelectProject={setActiveProject}
          />
        )
      case 'tasks':         return <TaskList activeProject={activeProject} />
      case 'reminders':
        return (
          <PersonalReminders
            config={widgetConfigs[widget.id]}
            onConfigChange={(cfg) => updateWidgetConfig(widget.id, cfg)}
          />
        )
      case 'calendar':      return <PersonalCalendar />
      case 'events':        return <UpcomingEvents />
      case 'notes':         return <NotesList activeProject={activeProject} projects={projects} />
      case 'text-block':
        return (
          <TextBlock
            config={widgetConfigs[widget.id]}
            onConfigChange={(cfg) => updateWidgetConfig(widget.id, cfg)}
          />
        )
      case 'clock':         return <ClockWidget />
      case 'greeting':      return <GreetingWidget />
      case 'fin-saldo':     return <FinSaldo />
      case 'fin-sobra':     return <FinSobra />
      case 'fin-fatura':    return <FinFatura />
      case 'email-inbox':
        return (
          <EmailWidget
            config={widgetConfigs[widget.id]}
            onConfigChange={(cfg) => updateWidgetConfig(widget.id, cfg)}
          />
        )
      case 'drive-files':
        return (
          <DriveWidget
            config={widgetConfigs[widget.id]}
            onConfigChange={(cfg) => updateWidgetConfig(widget.id, cfg)}
          />
        )
      default:              return <div className={styles.emptyState}>Widget desconhecido</div>
    }
  }

  // Some widgets are self-contained (no header needed)
  // All widgets are headerless — the ones that need headers render them internally
  const HEADERLESS = new Set(Object.keys(WIDGET_REGISTRY))

  const activeWidgetTypes = new Set(widgets.map(w => w.type))

  return (
    <div className={styles.page}>
      <ChatWidget />
      <WidgetCatalog onAdd={addWidget} activeWidgetTypes={activeWidgetTypes} />
      <div className={styles.tabBarRow}>
        <TabBar
          tabs={tabs}
          activeTabId={activeTabId}
          onSwitch={switchTab}
          onAdd={addTab}
          onRename={renameTab}
          onDelete={deleteTab}
        />
        {saveStatus && (
          <span className={`${styles.saveIndicator} ${saveStatus === 'saved' ? styles.saveIndicatorDone : ''}`}>
            {saveStatus === 'saving' ? 'Salvando...' : 'Salvo'}
          </span>
        )}
      </div>
      <DashboardGrid
        key={activeTabId}
        widgets={widgets}
        profileId={profileId}
        tabId={activeTabId}
        renderWidgetContent={renderWidgetContent}
        removeWidget={removeWidget}
        onLayoutChange={handleLayoutChange}
        headerlessTypes={HEADERLESS}
      />
    </div>
  )
}

/* ── Dashboard Grid (manages gridstack lifecycle per tab) ── */

function DashboardGrid({ widgets, profileId, tabId, renderWidgetContent, removeWidget, onLayoutChange, headerlessTypes }) {
  const gridRef = useRef(null)
  const gridInstanceRef = useRef(null)
  const onLayoutChangeRef = useRef(onLayoutChange)
  onLayoutChangeRef.current = onLayoutChange
  const widgetIdsRef = useRef(new Set())
  widgetIdsRef.current = new Set(widgets.map(w => w.id))

  useEffect(() => {
    if (!gridRef.current || gridInstanceRef.current) return

    const grid = GridStack.init({
      column: 12,
      cellHeight: 70,
      margin: 8,
      float: true,
      animate: true,
      draggable: { handle: `.${styles.widgetHeader}, .${styles.catalogDragHandle}` },
      resizable: { handles: 'se' },
    }, gridRef.current)

    // Positions come from the widgets prop (canonical source = tabs state)
    // No separate grid key needed — positions live in the tab's widgets array

    // Track user interaction — only save layout on actual drag/resize, not init
    let userInteracting = false

    const readLayout = () => {
      const validIds = widgetIdsRef.current
      return grid.getGridItems()
        .map(el => ({
          id: el.getAttribute('gs-id'),
          x: parseInt(el.getAttribute('gs-x')),
          y: parseInt(el.getAttribute('gs-y')),
          w: parseInt(el.getAttribute('gs-w')),
          h: parseInt(el.getAttribute('gs-h')),
        }))
        .filter(n => n.id && validIds.has(n.id))
    }

    grid.on('dragstart resizestart', () => {
      userInteracting = true
      gridRef.current.classList.add('gs-dragging')
    })
    grid.on('dragstop resizestop', () => {
      gridRef.current.classList.remove('gs-dragging')
    })
    grid.on('change', () => {
      if (!userInteracting) return
      userInteracting = false
      if (onLayoutChangeRef.current) onLayoutChangeRef.current(readLayout())
    })

    gridInstanceRef.current = grid

    return () => {
      grid.destroy(false)
      gridInstanceRef.current = null
    }
  }, [])

  // Sync GridStack with React widget state — add new items, remove stale
  const prevWidgetIds = useRef(new Set())

  useEffect(() => {
    if (!gridInstanceRef.current || !gridRef.current) return
    const grid = gridInstanceRef.current
    const currentIds = new Set(widgets.map(w => w.id))

    // Remove GridStack items that were deleted from React state
    const removedIds = [...prevWidgetIds.current].filter(id => !currentIds.has(id))
    if (removedIds.length > 0) {
      const items = grid.getGridItems()
      items.forEach(el => {
        const id = el.getAttribute('gs-id')
        if (removedIds.includes(id)) {
          grid.removeWidget(el, true) // true = also remove DOM
        }
      })
    }

    // Add new widgets to GridStack (delayed to let React flush DOM)
    const addedIds = [...currentIds].filter(id => !prevWidgetIds.current.has(id))
    if (addedIds.length > 0) {
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          if (!gridInstanceRef.current || !gridRef.current) return
          addedIds.forEach(id => {
            const el = gridRef.current.querySelector(`[gs-id="${id}"]`)
            if (el) {
              const w = widgets.find(w => w.id === id)
              gridInstanceRef.current.makeWidget(el)
              if (w) gridInstanceRef.current.update(el, { x: w.x, y: w.y, w: w.w, h: w.h })
            }
          })
        })
      })
    }

    prevWidgetIds.current = currentIds
  }, [widgets])

  return (
    <div ref={gridRef} className={`grid-stack ${styles.gridContainer}`}>
      {widgets.map((widget) => {
        const meta = getWidgetMeta(widget.type)
        const minW = meta?.minW || 2
        const minH = meta?.minH || 1
        const headerless = headerlessTypes.has(widget.type)

        return (
          <div
            key={widget.id}
            className="grid-stack-item"
            gs-id={widget.id}
            gs-x={widget.x}
            gs-y={widget.y}
            gs-w={widget.w}
            gs-h={widget.h}
            gs-min-w={minW}
            gs-min-h={minH}
          >
            <div className="grid-stack-item-content">
              {headerless ? (
                <div style={{ height: '100%', position: 'relative' }}>
                  <div className={styles.catalogDragHandle} />
                  <button
                    className={styles.removeBtn}
                    onClick={() => removeWidget(widget.id)}
                    title="Remover widget"
                  >
                    ×
                  </button>
                  {renderWidgetContent(widget)}
                </div>
              ) : (
                <div className={styles.widget}>
                  <div className={styles.widgetHeader}>
                    <h3 className={styles.widgetTitle}>{meta?.label || widget.type}</h3>
                    <div className={styles.widgetHeaderRight}>
                      <button
                        className={styles.removeBtnHeader}
                        onClick={() => removeWidget(widget.id)}
                        title="Remover widget"
                      >
                        ×
                      </button>
                    </div>
                  </div>
                  <div style={{ flex: 1, overflow: 'hidden', minHeight: 0 }}>
                    {renderWidgetContent(widget)}
                  </div>
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

