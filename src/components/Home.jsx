/**
 * Home.jsx — Family Hub home screen.
 *
 * Shared dashboard (not profile-scoped) with:
 *   - Greeting + date
 *   - Module cards (Financeiro active, others "Em breve")
 *   - Apple Reminders widget (3 lists: R&R Tarefas, R&R Casa, R&R Compras)
 *   - Family notes bulletin board
 */
import { useState } from 'react'
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

      {/* Two-column: Reminders + Notes */}
      <div className={styles.grid}>
        <RemindersWidget />
        <NotesBoard />
      </div>
    </div>
  )
}
