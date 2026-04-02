/**
 * PersonalOrganizer.jsx — Pessoal (personal organizer) page.
 *
 * Profile-scoped dashboard with:
 *   - Personal tasks (with project grouping)
 *   - Personal notes
 *   - Calendar (personal context — profile's selected calendars)
 *   - Quick capture input
 */
import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useProfile } from '../context/ProfileContext'
import api from '../api/client'
import styles from './PersonalOrganizer.module.css'

// Reminders sidecar runs on the local Mac (port 5176).
// Calling localhost directly (not through Vite proxy) means each user's
// browser hits their own Mac's sidecar → sees their own Apple Reminders.
const SIDECAR_BASE = 'http://localhost:5176'
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
const PRIORITY_COLORS = { 0: '', 1: 'var(--color-text-secondary)', 2: 'var(--color-accent)', 3: 'var(--color-red)' }

/* ── Quick Capture ───────────────────────────────────────── */

function QuickCapture({ onAddTask, onAddNote }) {
  const [value, setValue] = useState('')
  const [mode, setMode] = useState('task') // 'task' or 'note'

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!value.trim()) return
    if (mode === 'task') {
      onAddTask(value.trim())
    } else {
      onAddNote(value.trim())
    }
    setValue('')
  }

  return (
    <form onSubmit={handleSubmit} className={styles.quickCapture}>
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
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={mode === 'task' ? 'Nova tarefa...' : 'Nova nota...'}
        className={styles.captureInput}
      />
      <button type="submit" className={styles.captureBtn} disabled={!value.trim()}>
        +
      </button>
    </form>
  )
}

/* ── Task List ───────────────────────────────────────────── */

function TaskList() {
  const queryClient = useQueryClient()
  const [filter, setFilter] = useState('active') // 'active' | 'done' | 'all'
  const [editingId, setEditingId] = useState(null)
  const [editTitle, setEditTitle] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['pessoal-tasks'],
    queryFn: () => api.get('/pessoal/tasks/'),
  })

  const tasks = useMemo(() => {
    const list = data?.results || data || []
    if (filter === 'active') return list.filter((t) => t.status !== 'done')
    if (filter === 'done') return list.filter((t) => t.status === 'done')
    return list
  }, [data, filter])

  const toggleMutation = useMutation({
    mutationFn: ({ id, status }) =>
      api.patch(`/pessoal/tasks/${id}/`, { status: status === 'done' ? 'todo' : 'done' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pessoal-tasks'] }),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, ...data }) => api.patch(`/pessoal/tasks/${id}/`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pessoal-tasks'] })
      setEditingId(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/pessoal/tasks/${id}/`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pessoal-tasks'] }),
  })

  const activeCount = (data?.results || data || []).filter((t) => t.status !== 'done').length
  const doneCount = (data?.results || data || []).filter((t) => t.status === 'done').length

  return (
    <div className={styles.widget}>
      <div className={styles.widgetHeader}>
        <h3 className={styles.widgetTitle}>TAREFAS</h3>
        {activeCount > 0 && <span className={styles.badge}>{activeCount}</span>}
      </div>

      <div className={styles.filterTabs}>
        <button
          className={`${styles.filterTab} ${filter === 'active' ? styles.filterTabActive : ''}`}
          onClick={() => setFilter('active')}
        >
          Ativas {activeCount > 0 && `(${activeCount})`}
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
        {tasks.map((task) => {
          const due = formatDueDate(task.due_date)
          return (
            <div key={task.id} className={`${styles.taskItem} ${task.status === 'done' ? styles.taskDone : ''}`}>
              <button
                className={styles.checkBtn}
                onClick={() => toggleMutation.mutate({ id: task.id, status: task.status })}
                title={task.status === 'done' ? 'Reabrir' : 'Concluir'}
              >
                {task.status === 'done' ? (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="var(--color-accent)" stroke="var(--color-accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <polyline points="16 8 10 16 7 13" stroke="white" />
                  </svg>
                ) : (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                  </svg>
                )}
              </button>

              <div className={styles.taskContent}>
                {editingId === task.id ? (
                  <input
                    className={styles.taskEditInput}
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    onBlur={() => {
                      if (editTitle.trim() && editTitle !== task.title) {
                        updateMutation.mutate({ id: task.id, title: editTitle.trim() })
                      } else {
                        setEditingId(null)
                      }
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') e.target.blur()
                      if (e.key === 'Escape') setEditingId(null)
                    }}
                    autoFocus
                  />
                ) : (
                  <span
                    className={styles.taskTitle}
                    onClick={() => {
                      setEditingId(task.id)
                      setEditTitle(task.title)
                    }}
                  >
                    {task.title}
                  </span>
                )}

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
                  {task.project_name && (
                    <span className={styles.taskProject}>{task.project_name}</span>
                  )}
                </div>
              </div>

              <button
                className={styles.taskDeleteBtn}
                onClick={() => deleteMutation.mutate(task.id)}
                title="Excluir"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
          )
        })}
        {tasks.length === 0 && !isLoading && (
          <div className={styles.emptyState}>
            {filter === 'done' ? 'Nenhuma tarefa concluida' : 'Nenhuma tarefa pendente'}
          </div>
        )}
      </div>
    </div>
  )
}

/* ── Notes List ──────────────────────────────────────────── */

function NotesList() {
  const queryClient = useQueryClient()
  const [editId, setEditId] = useState(null)
  const [editContent, setEditContent] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['pessoal-notes'],
    queryFn: () => api.get('/pessoal/notes/'),
  })

  const notes = data?.results || data || []

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

  return (
    <div className={styles.widget}>
      <div className={styles.widgetHeader}>
        <h3 className={styles.widgetTitle}>NOTAS</h3>
        {notes.length > 0 && <span className={styles.badge}>{notes.length}</span>}
      </div>

      <div className={styles.notesList}>
        {isLoading && <div className={styles.emptyState}>Carregando...</div>}
        {notes.map((note) => (
          <div key={note.id} className={`${styles.noteCard} ${note.pinned ? styles.notePinned : ''}`}>
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
                    else { setEditId(note.id); setEditContent(note.content) }
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
                <textarea
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  className={styles.noteTextarea}
                  rows={3}
                  autoFocus
                />
                <button
                  className={styles.noteSaveBtn}
                  onClick={() => updateMutation.mutate({ id: note.id, content: editContent })}
                >
                  Salvar
                </button>
              </div>
            ) : (
              <p className={styles.noteBody}>{note.content}</p>
            )}

            {note.project_name && (
              <span className={styles.noteProject}>{note.project_name}</span>
            )}
          </div>
        ))}
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
  const [selectedDate, setSelectedDate] = useState(null)

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
  const todayKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`

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

export default function PersonalOrganizer() {
  const { currentProfile } = useProfile()
  const queryClient = useQueryClient()

  const addTaskMutation = useMutation({
    mutationFn: (title) => api.post('/pessoal/tasks/', { title }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pessoal-tasks'] }),
  })

  const addNoteMutation = useMutation({
    mutationFn: (content) => api.post('/pessoal/notes/', { content }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pessoal-notes'] }),
  })

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h2 className={styles.pageTitle}>Pessoal</h2>
        <p className={styles.pageSubtitle}>{currentProfile?.name}</p>
      </header>

      <QuickCapture
        onAddTask={(title) => addTaskMutation.mutate(title)}
        onAddNote={(content) => addNoteMutation.mutate(content)}
      />

      <div className={styles.grid}>
        <div className={styles.colMain}>
          <TaskList />
          <PersonalCalendar />
        </div>
        <div className={styles.colSide}>
          <UpcomingEvents />
          <PersonalReminders />
          <NotesList />
        </div>
      </div>
    </div>
  )
}
