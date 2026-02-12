/**
 * Home.jsx — Family Hub home screen.
 *
 * Shared dashboard (not profile-scoped) with:
 *   - Greeting + date
 *   - Module cards (Financeiro active, others "Em breve")
 *   - Apple Reminders widget (3 lists via host sidecar + EventKit)
 *   - Family notes bulletin board (Django backend)
 *   - Google Calendar month view (R&R shared calendar via Google Calendar API)
 */
import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useProfile } from '../context/ProfileContext'
import api from '../api/client'
import styles from './Home.module.css'

/* ── Helpers ─────────────────────────────────────────────── */

function getGreeting() {
  const h = new Date().getHours()
  if (h < 12) return 'Bom dia'
  if (h < 18) return 'Boa tarde'
  return 'Boa noite'
}

function getVisitorName() {
  const host = window.location.hostname
  // Accessing from the server itself → Palmer
  if (host === 'localhost' || host === '127.0.0.1') return 'Palmer'
  // Accessing from another device on the network → Rafaella
  return 'Rafaella'
}

function formatDate() {
  return new Date().toLocaleDateString('pt-BR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

function timeAgo(dateStr) {
  const d = new Date(dateStr)
  const now = new Date()
  const diffMs = now - d
  const mins = Math.floor(diffMs / 60000)
  if (mins < 1) return 'agora'
  if (mins < 60) return `${mins}min`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h`
  const days = Math.floor(hrs / 24)
  if (days < 7) return `${days}d`
  return d.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })
}

/* ── Module Cards ────────────────────────────────────────── */

const MODULES = [
  {
    key: 'financeiro',
    label: 'Financeiro',
    desc: 'Controle mensal, cartoes, orcamento',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M2 17L12 22L22 17" /><path d="M2 12L12 17L22 12" /><path d="M12 2L2 7L12 12L22 7L12 2Z" />
      </svg>
    ),
    active: true,
  },
  {
    key: 'compras',
    label: 'Compras',
    desc: 'Lista de compras compartilhada',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="9" cy="21" r="1" /><circle cx="20" cy="21" r="1" /><path d="M1 1H5L7.68 14.39A2 2 0 002 16H16A2 2 0 0019.63 13.13L21 5H6" />
      </svg>
    ),
    active: false,
  },
  {
    key: 'viagens',
    label: 'Viagens',
    desc: 'Planejamento de viagens',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17.8 19.2L16 11L12 2L8 11L6.2 19.2" /><path d="M1 16L12 22L23 16" /><path d="M12 22V12" />
      </svg>
    ),
    active: false,
  },
  {
    key: 'documentos',
    label: 'Documentos',
    desc: 'Documentos importantes',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6A2 2 0 004 4V20A2 2 0 006 22H18A2 2 0 0020 20V8Z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /><polyline points="10 9 9 9 8 9" />
      </svg>
    ),
    active: false,
  },
]

function ModuleCards({ profileSlug }) {
  return (
    <section className={styles.modules}>
      {MODULES.map((m) =>
        m.active ? (
          <Link key={m.key} to={`/${profileSlug}/overview`} className={styles.moduleCard}>
            <div className={styles.moduleIconWrap}>{m.icon}</div>
            <div className={styles.moduleInfo}>
              <span className={styles.moduleLabel}>{m.label}</span>
              <span className={styles.moduleDesc}>{m.desc}</span>
            </div>
            <svg className={styles.moduleArrow} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </Link>
        ) : (
          <div key={m.key} className={`${styles.moduleCard} ${styles.moduleDisabled}`}>
            <div className={styles.moduleIconWrap}>{m.icon}</div>
            <div className={styles.moduleInfo}>
              <span className={styles.moduleLabel}>{m.label}</span>
              <span className={styles.moduleDesc}>Em breve</span>
            </div>
          </div>
        )
      )}
    </section>
  )
}

/* ── Reminders Widget ────────────────────────────────────── */

function RemindersWidget() {
  const queryClient = useQueryClient()
  const [activeListIdx, setActiveListIdx] = useState(0)
  const [newReminder, setNewReminder] = useState('')

  // Dynamically fetch available lists from Apple Reminders
  const { data: listsData } = useQuery({
    queryKey: ['home-reminders-lists'],
    queryFn: () => api.get('/home/reminders/lists/'),
    staleTime: 5 * 60 * 1000,
  })

  const availableLists = listsData?.lists || []
  const listName = availableLists[activeListIdx] || availableLists[0] || ''

  const { data, isLoading, error } = useQuery({
    queryKey: ['home-reminders', listName],
    queryFn: () => api.get(`/home/reminders/?list=${encodeURIComponent(listName)}`),
    enabled: !!listName,
    refetchInterval: 30000,
  })

  const completeMutation = useMutation({
    mutationFn: (name) =>
      api.post('/home/reminders/complete/', { name, list: listName }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['home-reminders', listName] }),
  })

  const addMutation = useMutation({
    mutationFn: (name) => api.post('/home/reminders/add/', { name, list: listName }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['home-reminders', listName] })
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

      {/* List tabs */}
      <div className={styles.listTabs}>
        {availableLists.map((name, idx) => (
          <button
            key={name}
            className={`${styles.listTab} ${activeListIdx === idx ? styles.listTabActive : ''}`}
            onClick={() => setActiveListIdx(idx)}
          >
            {name}
          </button>
        ))}
      </div>

      {/* Add form */}
      <form onSubmit={handleAdd} className={styles.addRow}>
        <input
          type="text"
          value={newReminder}
          onChange={(e) => setNewReminder(e.target.value)}
          placeholder="Novo lembrete..."
          className={styles.addInput}
        />
        <button
          type="submit"
          className={styles.addBtn}
          disabled={!newReminder.trim() || addMutation.isPending}
        >
          +
        </button>
      </form>

      {/* Reminders list */}
      <div className={styles.remindersList}>
        {isLoading && (
          <div className={styles.emptyState}>
            <span className={styles.spinner} />
            Carregando...
          </div>
        )}
        {error && (
          <div className={styles.emptyState}>
            <span style={{ color: 'var(--color-red)' }}>Erro ao conectar com Lembretes</span>
          </div>
        )}
        {data?.reminders?.map((r, i) => (
          <div key={`${r.name}-${i}`} className={styles.reminderItem}>
            <button
              className={styles.checkBtn}
              onClick={() => completeMutation.mutate(r.name)}
              disabled={completeMutation.isPending}
              title="Concluir"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
              </svg>
            </button>
            <div className={styles.reminderContent}>
              <span className={styles.reminderName}>{r.name}</span>
              {r.due_date && (
                <span className={styles.reminderDue}>{r.due_date}</span>
              )}
              {r.notes && (
                <span className={styles.reminderNotes}>{r.notes}</span>
              )}
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

/* ── Notes Board ─────────────────────────────────────────── */

function NotesBoard() {
  const queryClient = useQueryClient()
  const { currentProfile } = useProfile()
  const [showForm, setShowForm] = useState(false)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [editId, setEditId] = useState(null)
  const [editContent, setEditContent] = useState('')

  const { data: notes = [], isLoading } = useQuery({
    queryKey: ['home-notes'],
    queryFn: () => api.get('/home/notes/'),
  })

  const notesList = notes.results || notes

  const createMutation = useMutation({
    mutationFn: (d) => api.post('/home/notes/', d),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['home-notes'] })
      setShowForm(false)
      setTitle('')
      setContent('')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, ...d }) => api.patch(`/home/notes/${id}/`, d),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['home-notes'] })
      setEditId(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => api.delete(`/home/notes/${id}/`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['home-notes'] }),
  })

  const togglePinMutation = useMutation({
    mutationFn: ({ id, pinned }) => api.patch(`/home/notes/${id}/`, { pinned: !pinned }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['home-notes'] }),
  })

  const handleCreate = (e) => {
    e.preventDefault()
    if (!content.trim()) return
    createMutation.mutate({
      title: title.trim(),
      content: content.trim(),
      author_name: currentProfile?.name || 'Familia',
    })
  }

  return (
    <div className={styles.widget}>
      <div className={styles.widgetHeader}>
        <h3 className={styles.widgetTitle}>MURAL</h3>
        <button
          className={styles.widgetHeaderBtn}
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? 'Cancelar' : '+ Nota'}
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <form onSubmit={handleCreate} className={styles.noteForm}>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Titulo (opcional)"
            className={styles.noteInput}
          />
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Escreva sua nota..."
            className={styles.noteTextarea}
            rows={3}
            autoFocus
          />
          <button
            type="submit"
            className={styles.noteSaveBtn}
            disabled={!content.trim() || createMutation.isPending}
          >
            Salvar
          </button>
        </form>
      )}

      {/* Notes list */}
      <div className={styles.notesList}>
        {isLoading && <div className={styles.emptyState}>Carregando...</div>}
        {notesList.map((note) => (
          <div
            key={note.id}
            className={`${styles.noteCard} ${note.pinned ? styles.notePinned : ''}`}
          >
            <div className={styles.noteTop}>
              <div className={styles.noteAuthorRow}>
                <span className={styles.noteAuthor}>{note.author_name}</span>
                <span className={styles.noteTime}>{timeAgo(note.updated_at)}</span>
              </div>
              <div className={styles.noteActions}>
                <button
                  className={styles.noteActionBtn}
                  onClick={() => togglePinMutation.mutate({ id: note.id, pinned: note.pinned })}
                  title={note.pinned ? 'Desafixar' : 'Fixar'}
                >
                  {note.pinned ? (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="1">
                      <path d="M16 2L21 7L15 13L19 17H5L9 13L3 7L8 2L12 6L16 2Z" />
                    </svg>
                  ) : (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M16 2L21 7L15 13L19 17H5L9 13L3 7L8 2L12 6L16 2Z" />
                    </svg>
                  )}
                </button>
                <button
                  className={styles.noteActionBtn}
                  onClick={() => {
                    if (editId === note.id) {
                      setEditId(null)
                    } else {
                      setEditId(note.id)
                      setEditContent(note.content)
                    }
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
                    <path d="M10 11v6" /><path d="M14 11v6" />
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
                  onClick={() =>
                    updateMutation.mutate({ id: note.id, content: editContent })
                  }
                >
                  Salvar
                </button>
              </div>
            ) : (
              <p className={styles.noteBody}>{note.content}</p>
            )}
          </div>
        ))}
        {notesList.length === 0 && !isLoading && (
          <div className={styles.emptyState}>
            <p>Nenhuma nota ainda</p>
            <button
              className={styles.emptyAction}
              onClick={() => setShowForm(true)}
            >
              Criar primeira nota
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

/* ── Calendar Widget (Month View) ────────────────────────── */

const WEEKDAYS = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab']
const MONTH_NAMES = [
  'Janeiro', 'Fevereiro', 'Marco', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
]

function buildCalendarDays(year, month) {
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const startDow = firstDay.getDay()       // 0=Sun
  const daysInMonth = lastDay.getDate()

  const days = []

  // Leading days from previous month
  const prevLast = new Date(year, month, 0).getDate()
  for (let i = startDow - 1; i >= 0; i--) {
    days.push({ day: prevLast - i, month: month - 1, outside: true })
  }

  // Current month days
  for (let d = 1; d <= daysInMonth; d++) {
    days.push({ day: d, month, outside: false })
  }

  // Trailing days to fill 6 rows (42 cells) or at least complete last row
  const trailing = days.length <= 35 ? 35 - days.length : 42 - days.length
  for (let d = 1; d <= trailing; d++) {
    days.push({ day: d, month: month + 1, outside: true })
  }

  return days
}

function CalendarWidget() {
  const queryClient = useQueryClient()
  const now = new Date()
  const [viewYear, setViewYear] = useState(now.getFullYear())
  const [viewMonth, setViewMonth] = useState(now.getMonth())
  const [selectedDate, setSelectedDate] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [title, setTitle] = useState('')
  const [startTime, setStartTime] = useState('')
  const [endTime, setEndTime] = useState('')

  // ── Check Google Calendar auth status ──
  const { data: authStatus, isLoading: authLoading } = useQuery({
    queryKey: ['home-calendar-status'],
    queryFn: () => api.get('/home/calendar/status/'),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  })

  const isAuthenticated = authStatus?.authenticated === true
  const calendarId = authStatus?.calendar_id || null

  // ── Fetch events for current month view (with buffer) ──
  const timeMin = `${viewYear}-${String(viewMonth + 1).padStart(2, '0')}-01`
  const lastDay = new Date(viewYear, viewMonth + 2, 0).getDate()
  const nextM = viewMonth + 2 > 12 ? 1 : viewMonth + 2
  const nextY = viewMonth + 2 > 12 ? viewYear + 1 : viewYear
  const timeMax = `${nextY}-${String(nextM).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`

  const { data, isLoading } = useQuery({
    queryKey: ['home-calendar-events', viewYear, viewMonth, calendarId],
    queryFn: () => {
      const params = new URLSearchParams()
      if (calendarId) params.set('calendar_id', calendarId)
      params.set('time_min', timeMin)
      params.set('time_max', timeMax)
      return api.get(`/home/calendar/events/?${params}`)
    },
    enabled: isAuthenticated,
    refetchInterval: 60000,
  })

  const addMutation = useMutation({
    mutationFn: (evt) => api.post('/home/calendar/add-event/', evt),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['home-calendar-events'] })
      setShowForm(false)
      setTitle('')
      setStartTime('')
      setEndTime('')
    },
  })

  // Build event lookup by YYYY-MM-DD
  const eventsByDate = useMemo(() => {
    const map = {}
    ;(data?.events || []).forEach((evt) => {
      // Handle both dateTime and date-only formats
      const startStr = evt.start
      const key = startStr.includes('T')
        ? startStr.slice(0, 10)
        : startStr
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

  const prevMonth = () => {
    if (viewMonth === 0) { setViewYear(viewYear - 1); setViewMonth(11) }
    else setViewMonth(viewMonth - 1)
    setSelectedDate(null)
  }
  const nextMonth = () => {
    if (viewMonth === 11) { setViewYear(viewYear + 1); setViewMonth(0) }
    else setViewMonth(viewMonth + 1)
    setSelectedDate(null)
  }
  const goToday = () => {
    setViewYear(now.getFullYear())
    setViewMonth(now.getMonth())
    setSelectedDate(todayKey)
  }

  const selectedEvents = selectedDate ? (eventsByDate[selectedDate] || []) : []

  const formatTime = (iso) => {
    const d = new Date(iso)
    return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  }

  const handleAdd = (e) => {
    e.preventDefault()
    if (!title.trim() || !selectedDate || !startTime) return
    const start = `${selectedDate}T${startTime}:00`
    const end = endTime ? `${selectedDate}T${endTime}:00` : `${selectedDate}T${startTime}:00`
    addMutation.mutate({
      calendar_id: calendarId,
      title: title.trim(),
      start,
      end,
    })
  }

  const selectedDateLabel = selectedDate
    ? new Date(selectedDate + 'T12:00:00').toLocaleDateString('pt-BR', {
        weekday: 'long', day: 'numeric', month: 'long',
      })
    : null

  // ── Not authenticated: show connect prompt ──
  if (!authLoading && !isAuthenticated) {
    return (
      <div className={styles.calWidget}>
        <div className={styles.calHeader}>
          <h3 className={styles.calTitle}>Calendario</h3>
        </div>
        <div className={styles.calAuthPrompt}>
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-secondary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
            <line x1="16" y1="2" x2="16" y2="6" />
            <line x1="8" y1="2" x2="8" y2="6" />
            <line x1="3" y1="10" x2="21" y2="10" />
          </svg>
          {authStatus?.error ? (
            <>
              <p className={styles.calAuthText}>{authStatus.error}</p>
              <p className={styles.calAuthHint}>
                Baixe as credenciais OAuth do Google Cloud Console e salve como
                <code> backend/credentials.json</code>
              </p>
            </>
          ) : authStatus?.auth_url ? (
            <>
              <p className={styles.calAuthText}>Conecte seu Google Calendar para ver seus eventos</p>
              <a
                href={authStatus.auth_url}
                className={styles.calAuthBtn}
              >
                Conectar Google Calendar
              </a>
            </>
          ) : (
            <p className={styles.calAuthText}>Carregando...</p>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className={styles.calWidget}>
      {/* ── Header: nav + month/year ── */}
      <div className={styles.calHeader}>
        <div className={styles.calNav}>
          <button className={styles.calNavBtn} onClick={prevMonth} title="Mes anterior">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6" /></svg>
          </button>
          <h3 className={styles.calTitle}>
            {MONTH_NAMES[viewMonth]} {viewYear}
          </h3>
          <button className={styles.calNavBtn} onClick={nextMonth} title="Proximo mes">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6" /></svg>
          </button>
        </div>
        <button className={styles.calTodayBtn} onClick={goToday}>Hoje</button>
      </div>

      {/* ── Weekday headers ── */}
      <div className={styles.calGrid}>
        {WEEKDAYS.map((wd) => (
          <div key={wd} className={styles.calWeekday}>{wd}</div>
        ))}

        {/* ── Day cells ── */}
        {days.map((d, i) => {
          const key = dateKey(d)
          const isToday = key === todayKey
          const isSelected = key === selectedDate
          const hasEvents = !!eventsByDate[key]
          return (
            <button
              key={i}
              className={[
                styles.calDay,
                d.outside ? styles.calDayOutside : '',
                isToday ? styles.calDayToday : '',
                isSelected ? styles.calDaySelected : '',
              ].filter(Boolean).join(' ')}
              onClick={() => setSelectedDate(key === selectedDate ? null : key)}
            >
              <span className={styles.calDayNum}>{d.day}</span>
              {hasEvents && <span className={styles.calDot} />}
            </button>
          )
        })}
      </div>

      {/* ── Loading indicator ── */}
      {isLoading && (
        <div className={styles.calEmpty} style={{ padding: '8px 0' }}>
          <span className={styles.spinner} /> Carregando eventos...
        </div>
      )}

      {/* ── Selected day detail panel ── */}
      {selectedDate && (
        <div className={styles.calDetail}>
          <div className={styles.calDetailHeader}>
            <span className={styles.calDetailDate}>{selectedDateLabel}</span>
            <button
              className={styles.widgetHeaderBtn}
              onClick={() => setShowForm(!showForm)}
            >
              {showForm ? 'Cancelar' : '+ Evento'}
            </button>
          </div>

          {showForm && (
            <form onSubmit={handleAdd} className={styles.calForm}>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Nome do evento"
                className={styles.noteInput}
                autoFocus
              />
              <div className={styles.calFormRow}>
                <div className={styles.calFormGroup}>
                  <label className={styles.calFormLabel}>Inicio</label>
                  <input type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} className={styles.calFormInput} />
                </div>
                <div className={styles.calFormGroup}>
                  <label className={styles.calFormLabel}>Fim</label>
                  <input type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} className={styles.calFormInput} />
                </div>
              </div>
              <button type="submit" className={styles.noteSaveBtn} disabled={!title.trim() || !startTime || addMutation.isPending}>
                Salvar
              </button>
            </form>
          )}

          {selectedEvents.length > 0 ? (
            <div className={styles.calEventsList}>
              {selectedEvents.map((evt, i) => (
                <div key={i} className={styles.calEvent}>
                  <div className={styles.calEventDot} />
                  <div className={styles.calEventInfo}>
                    <span className={styles.calEventTitle}>{evt.title}</span>
                    <span className={styles.calEventTime}>
                      {evt.all_day ? 'Dia todo' : `${formatTime(evt.start)} — ${formatTime(evt.end)}`}
                    </span>
                    {evt.location && <span className={styles.calEventLoc}>{evt.location}</span>}
                  </div>
                </div>
              ))}
            </div>
          ) : !showForm ? (
            <div className={styles.calEmpty}>Sem eventos neste dia</div>
          ) : null}
        </div>
      )}
    </div>
  )
}

/* ── Main Home Component ─────────────────────────────────── */

export default function Home() {
  const { currentProfile, profileSlug } = useProfile()

  return (
    <div className={styles.home}>
      {/* Greeting */}
      <header className={styles.greeting}>
        <h2 className={styles.greetingTitle}>
          {getGreeting()}, {getVisitorName()}
        </h2>
        <p className={styles.greetingDate}>{formatDate()}</p>
      </header>

      {/* Quick-access module cards */}
      <ModuleCards profileSlug={profileSlug} />

      {/* Widgets: Reminders + Notes side by side */}
      <div className={styles.grid}>
        <RemindersWidget />
        <NotesBoard />
      </div>

      {/* Full-width calendar below */}
      <CalendarWidget />
    </div>
  )
}
