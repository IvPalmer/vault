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
import { useState, useMemo, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Responsive, WidthProvider } from 'react-grid-layout'
import 'react-grid-layout/css/styles.css'
import 'react-resizable/css/styles.css'
import { useProfile } from '../context/ProfileContext'
import api from '../api/client'
import styles from './PersonalOrganizer.module.css'

const ResponsiveGridLayout = WidthProvider(Responsive)

// Reminders sidecar runs on the local Mac (port 5177).
// Calling localhost directly (not through Vite proxy) means each user's
// browser hits their own Mac's sidecar → sees their own Apple Reminders.
const SIDECAR_BASE = 'http://localhost:5177'
async function sidecarGet(path) {
  const res = await fetch(`${SIDECAR_BASE}${path}`)
  if (!res.ok) throw new Error(`Sidecar ${res.status}`)
  return res.json()
}
async function sidecarPost(path, data) {
  const res = await fetch(`${SIDECAR_BASE}${path}`, {
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

/* ── Dashboard Summary Cards ────────────────────────────── */

function DashboardCards({ tasks, projects }) {
  const todayStr = new Date().toISOString().slice(0, 10)
  const allTasks = tasks || []
  const activeTasks = allTasks.filter((t) => t.status !== 'done')
  const todayTasks = activeTasks.filter((t) => t.due_date === todayStr)
  const overdueTasks = activeTasks.filter((t) => {
    if (!t.due_date) return false
    return t.due_date < todayStr
  })
  const activeProjects = (projects || []).filter((p) => p.status === 'active')

  const cards = [
    { label: 'Hoje', value: todayTasks.length, accent: false },
    { label: 'Atrasadas', value: overdueTasks.length, accent: overdueTasks.length > 0, danger: overdueTasks.length > 0 },
    { label: 'Ativas', value: activeTasks.length, accent: false },
    { label: 'Projetos', value: activeProjects.length, accent: false },
  ]

  return (
    <div className={styles.dashboardCards}>
      {cards.map((c) => (
        <div
          key={c.label}
          className={`${styles.dashCard} ${c.danger ? styles.dashCardDanger : ''}`}
        >
          <span className={styles.dashCardValue}>{c.value}</span>
          <span className={styles.dashCardLabel}>{c.label}</span>
        </div>
      ))}
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

  const formatEventDate = (iso) => {
    const d = new Date(iso.includes('T') ? iso : iso + 'T12:00:00')
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const evtDate = new Date(d)
    evtDate.setHours(0, 0, 0, 0)
    const diff = Math.floor((evtDate - today) / 86400000)
    if (diff === 0) return 'Hoje'
    if (diff === 1) return 'Amanha'
    return d.toLocaleDateString('pt-BR', { weekday: 'short', day: '2-digit', month: 'short' })
  }

  return (
    <div className={styles.widget}>
      <div className={styles.widgetHeader}>
        <h3 className={styles.widgetTitle}>PROXIMOS EVENTOS</h3>
        {events.length > 0 && <span className={styles.badge}>{events.length}</span>}
      </div>
      <div className={styles.eventsList}>
        {isLoading && <div className={styles.emptyState}>Carregando...</div>}
        {events.slice(0, 10).map((evt, i) => (
          <div key={i} className={styles.eventItem}>
            <div className={styles.eventDate}>{formatEventDate(evt.start)}</div>
            <div className={styles.eventInfo}>
              <span className={styles.eventTitle}>{evt.title}</span>
              <span className={styles.eventTime}>
                {evt.all_day ? 'Dia todo' : formatTime(evt.start)}
              </span>
            </div>
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

  const selectedEvents = selectedDate ? (eventsByDate[selectedDate] || []) : []

  const formatTime = (iso) => new Date(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })

  return (
    <div className={styles.widget}>
      <div className={styles.calHeader}>
        <button className={styles.calNavBtn} onClick={prevMonth}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6" /></svg>
        </button>
        <h3 className={styles.calTitle}>{MONTH_NAMES[viewMonth]} {viewYear}</h3>
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
          const hasEvents = !!eventsByDate[key]
          return (
            <button
              key={i}
              className={[styles.calDay, d.outside && styles.calDayOutside, isToday && styles.calDayToday, isSelected && styles.calDaySelected].filter(Boolean).join(' ')}
              onClick={() => setSelectedDate(key === selectedDate ? null : key)}
            >
              <span className={styles.calDayNum}>{d.day}</span>
              {hasEvents && <span className={styles.calDot} />}
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
                <span className={styles.calEventTitle}>{evt.title}</span>
                <span className={styles.calEventTime}>
                  {evt.all_day ? 'Dia todo' : `${formatTime(evt.start)} — ${formatTime(evt.end)}`}
                </span>
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

function PersonalReminders() {
  const queryClient = useQueryClient()
  const [activeListIdx, setActiveListIdx] = useState(0)
  const [newReminder, setNewReminder] = useState('')

  // Fetch ALL reminder lists (not just R&R)
  const { data: listsData } = useQuery({
    queryKey: ['pessoal-reminders-lists'],
    queryFn: () => sidecarGet('/api/home/reminders/lists/?all=true'),
    retry: 1,
    staleTime: 5 * 60 * 1000,
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

/* ── Layout Persistence ───────────────────────────────────── */

const STORAGE_KEY = 'vault-pessoal-layouts'

const DEFAULT_LAYOUTS = {
  lg: [
    { i: 'dashboard', x: 0, y: 0, w: 12, h: 2, static: true },
    { i: 'capture',   x: 0, y: 2, w: 12, h: 2, static: true },
    { i: 'projects',  x: 0, y: 4, w: 12, h: 2, static: true },
    { i: 'tasks',     x: 0, y: 6, w: 5, h: 10, minW: 3, minH: 4 },
    { i: 'calendar',  x: 5, y: 6, w: 4, h: 10, minW: 3, minH: 6 },
    { i: 'reminders', x: 9, y: 6, w: 3, h: 6,  minW: 2, minH: 3 },
    { i: 'events',    x: 5, y: 16, w: 4, h: 6, minW: 2, minH: 3 },
    { i: 'notes',     x: 9, y: 12, w: 3, h: 6, minW: 2, minH: 3 },
  ],
  md: [
    { i: 'dashboard', x: 0, y: 0, w: 10, h: 2, static: true },
    { i: 'capture',   x: 0, y: 2, w: 10, h: 2, static: true },
    { i: 'projects',  x: 0, y: 4, w: 10, h: 2, static: true },
    { i: 'tasks',     x: 0, y: 6, w: 5, h: 10, minW: 3, minH: 4 },
    { i: 'calendar',  x: 5, y: 6, w: 5, h: 10, minW: 3, minH: 6 },
    { i: 'reminders', x: 0, y: 16, w: 5, h: 6, minW: 2, minH: 3 },
    { i: 'events',    x: 5, y: 16, w: 5, h: 6, minW: 2, minH: 3 },
    { i: 'notes',     x: 0, y: 22, w: 10, h: 5, minW: 2, minH: 3 },
  ],
  sm: [
    { i: 'dashboard', x: 0, y: 0, w: 6, h: 2, static: true },
    { i: 'capture',   x: 0, y: 2, w: 6, h: 3, static: true },
    { i: 'projects',  x: 0, y: 5, w: 6, h: 2, static: true },
    { i: 'tasks',     x: 0, y: 7, w: 6, h: 8, minW: 3, minH: 4 },
    { i: 'calendar',  x: 0, y: 15, w: 6, h: 10, minW: 3, minH: 6 },
    { i: 'events',    x: 0, y: 25, w: 6, h: 6, minW: 2, minH: 3 },
    { i: 'reminders', x: 0, y: 31, w: 6, h: 6, minW: 2, minH: 3 },
    { i: 'notes',     x: 0, y: 37, w: 6, h: 5, minW: 2, minH: 3 },
  ],
}

function loadLayouts() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) return JSON.parse(saved)
  } catch { /* ignore */ }
  return DEFAULT_LAYOUTS
}

function saveLayouts(layouts) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(layouts))
  } catch { /* ignore */ }
}

/* ── Main Component ──────────────────────────────────────── */

export default function PersonalOrganizer() {
  const { currentProfile } = useProfile()
  const queryClient = useQueryClient()
  const [activeProject, setActiveProject] = useState(null)
  const [layouts, setLayouts] = useState(loadLayouts)

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

  const greeting = useMemo(() => {
    const h = new Date().getHours()
    if (h < 12) return 'Bom dia'
    if (h < 18) return 'Boa tarde'
    return 'Boa noite'
  }, [])

  const handleLayoutChange = useCallback((_, allLayouts) => {
    setLayouts(allLayouts)
    saveLayouts(allLayouts)
  }, [])

  const handleResetLayout = useCallback(() => {
    setLayouts(DEFAULT_LAYOUTS)
    saveLayouts(DEFAULT_LAYOUTS)
  }, [])

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <h2 className={styles.pageTitle}>{greeting}, {currentProfile?.name}</h2>
          <p className={styles.pageSubtitle}>Pessoal</p>
        </div>
        <button className={styles.resetLayoutBtn} onClick={handleResetLayout} title="Restaurar layout padrao">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 12a9 9 0 019-9 9.75 9.75 0 016.74 2.74L21 8" />
            <path d="M21 3v5h-5" />
            <path d="M21 12a9 9 0 01-9 9 9.75 9.75 0 01-6.74-2.74L3 16" />
            <path d="M8 16H3v5" />
          </svg>
        </button>
      </header>

      <ResponsiveGridLayout
        className={styles.gridLayout}
        layouts={layouts}
        breakpoints={{ lg: 1200, md: 900, sm: 0 }}
        cols={{ lg: 12, md: 10, sm: 6 }}
        rowHeight={36}
        onLayoutChange={handleLayoutChange}
        draggableHandle={`.${styles.widgetDragHandle}`}
        margin={[12, 12]}
        containerPadding={[0, 0]}
        useCSSTransforms={true}
        compactType="vertical"
      >
        <div key="dashboard">
          <DashboardCards tasks={tasks} projects={projects} />
        </div>

        <div key="capture">
          <QuickCapture
            onAddTask={(data) => addTaskMutation.mutate(data)}
            onAddNote={(data) => addNoteMutation.mutate(data)}
            projects={projects}
          />
        </div>

        <div key="projects">
          <ProjectsBar
            projects={projects}
            activeProject={activeProject}
            onSelectProject={setActiveProject}
          />
        </div>

        <div key="tasks" className={styles.gridCell}>
          <DragHandle />
          <TaskList activeProject={activeProject} />
        </div>

        <div key="calendar" className={styles.gridCell}>
          <DragHandle />
          <PersonalCalendar />
        </div>

        <div key="reminders" className={styles.gridCell}>
          <DragHandle />
          <PersonalReminders />
        </div>

        <div key="events" className={styles.gridCell}>
          <DragHandle />
          <UpcomingEvents />
        </div>

        <div key="notes" className={styles.gridCell}>
          <DragHandle />
          <NotesList activeProject={activeProject} projects={projects} />
        </div>
      </ResponsiveGridLayout>
    </div>
  )
}

/* ── Drag Handle (floating in top-left of grid cells) ────── */

function DragHandle() {
  return (
    <div className={styles.widgetDragHandle} title="Arrastar">
      <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor">
        <circle cx="5" cy="5" r="2"/><circle cx="12" cy="5" r="2"/><circle cx="19" cy="5" r="2"/>
        <circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/>
      </svg>
    </div>
  )
}
