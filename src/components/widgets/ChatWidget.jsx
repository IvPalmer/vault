/**
 * ChatWidget — Floating chat panel that talks to Claude via the chat-sidecar.
 *
 * Features:
 * - Per-profile conversation history
 * - File/image attachment support
 * - SSE streaming responses
 * - Markdown-like rendering
 */
import { useState, useRef, useEffect, useCallback } from 'react'
import { useProfile } from '../../context/ProfileContext'
import styles from './ChatWidget.module.css'

const SIDECAR_URL = ''  // routed through Vite proxy at /sidecar
const MAX_HISTORY = 50

function storageKey(profileId) {
  return `vault-chat-history-${profileId}`
}

function loadHistory(profileId) {
  try {
    const raw = localStorage.getItem(storageKey(profileId))
    if (raw) return JSON.parse(raw).slice(-MAX_HISTORY)
  } catch {}
  return []
}

function saveHistory(profileId, messages) {
  localStorage.setItem(
    storageKey(profileId),
    JSON.stringify(messages.slice(-MAX_HISTORY))
  )
}

/** Simple markdown-ish rendering: bold, italic, code, line breaks */
function renderContent(text) {
  if (!text) return null
  // Code blocks
  let html = text.replace(/```[\s\S]*?```/g, (m) => {
    const code = m.slice(3, -3).replace(/^\w*\n/, '')
    return `<pre class="${styles.codeBlock}">${escHtml(code)}</pre>`
  })
  // Inline code
  html = html.replace(/`([^`]+)`/g, `<code class="${styles.inlineCode}">$1</code>`)
  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  // Italic
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  // Line breaks
  html = html.replace(/\n/g, '<br/>')
  return <span dangerouslySetInnerHTML={{ __html: html }} />
}

function escHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

export default function ChatWidget() {
  const { currentProfile } = useProfile()
  const profileId = currentProfile?.id || 'default'
  const profileName = currentProfile?.name || 'User'

  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState(() => loadHistory(profileId))
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [attachment, setAttachment] = useState(null) // { name, data (base64), type }
  const [listening, setListening] = useState(false)
  const [voiceMode, setVoiceMode] = useState(false) // auto-speak responses
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const fileInputRef = useRef(null)
  const recognitionRef = useRef(null)
  const lastSpokenRef = useRef('')

  // Reload history on profile switch
  useEffect(() => {
    setMessages(loadHistory(profileId))
  }, [profileId])

  // Persist messages
  useEffect(() => {
    saveHistory(profileId, messages)
  }, [profileId, messages])

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streaming])

  // Focus input when panel opens
  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  // Escape to close
  useEffect(() => {
    if (!open) return
    const handleKey = (e) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [open])

  const handleFileSelect = useCallback((e) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      const base64 = reader.result.split(',')[1]
      setAttachment({ name: file.name, data: base64, type: file.type })
    }
    reader.readAsDataURL(file)
    // Reset file input so same file can be re-selected
    e.target.value = ''
  }, [])

  const removeAttachment = useCallback(() => setAttachment(null), [])

  // ── Voice: Speech-to-Text ──
  const startListening = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) return

    if (recognitionRef.current) {
      recognitionRef.current.stop()
      recognitionRef.current = null
      setListening(false)
      return
    }

    const recognition = new SpeechRecognition()
    recognition.lang = 'pt-BR'
    recognition.continuous = false
    recognition.interimResults = true

    let finalTranscript = ''

    recognition.onresult = (event) => {
      let interim = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript
        } else {
          interim += event.results[i][0].transcript
        }
      }
      setInput(finalTranscript + interim)
    }

    recognition.onend = () => {
      setListening(false)
      recognitionRef.current = null
      // Auto-send in voice mode if we got text
      if (voiceMode && finalTranscript.trim()) {
        // Small delay to let state settle
        setTimeout(() => {
          const btn = document.querySelector('[data-voice-send]')
          if (btn) btn.click()
        }, 100)
      }
    }

    recognition.onerror = () => {
      setListening(false)
      recognitionRef.current = null
    }

    recognitionRef.current = recognition
    setListening(true)
    recognition.start()
  }, [voiceMode])

  // ── Voice: Text-to-Speech ──
  const speak = useCallback((text) => {
    if (!text || !voiceMode) return
    // Strip markdown
    const clean = text
      .replace(/```[\s\S]*?```/g, '')
      .replace(/`[^`]+`/g, '')
      .replace(/\*\*(.+?)\*\*/g, '$1')
      .replace(/\*(.+?)\*/g, '$1')
      .replace(/<[^>]+>/g, '')
      .replace(/\n/g, '. ')
      .trim()
    if (!clean || clean === lastSpokenRef.current) return
    lastSpokenRef.current = clean

    window.speechSynthesis.cancel()
    const utter = new SpeechSynthesisUtterance(clean)
    utter.lang = 'pt-BR'
    utter.rate = 1.05
    // Try to find a Portuguese voice
    const voices = window.speechSynthesis.getVoices()
    const ptVoice = voices.find(v => v.lang.startsWith('pt')) || voices.find(v => v.lang.startsWith('pt-BR'))
    if (ptVoice) utter.voice = ptVoice
    window.speechSynthesis.speak(utter)
  }, [voiceMode])

  // Auto-speak new assistant messages when voice mode is on
  useEffect(() => {
    if (!voiceMode || streaming) return
    const last = messages[messages.length - 1]
    if (last?.role === 'assistant' && last.content) {
      speak(last.content)
    }
  }, [messages, streaming, voiceMode, speak])

  // Stop speech when voice mode is toggled off
  useEffect(() => {
    if (!voiceMode) {
      window.speechSynthesis?.cancel()
      lastSpokenRef.current = ''
    }
  }, [voiceMode])

  const sendingRef = useRef(false)

  const sendMessage = useCallback(async () => {
    const text = input.trim()
    if (!text || streaming || sendingRef.current) return
    sendingRef.current = true

    const userMsg = {
      role: 'user',
      content: text,
      attachment: attachment ? attachment.name : null,
      ts: Date.now(),
    }
    setMessages((prev) => [...prev, userMsg, { role: 'assistant', content: '', ts: Date.now() }])
    setInput('')
    setStreaming(true)

    const body = {
      message: text,
      profile_id: profileId,
      profile_name: profileName,
    }
    if (attachment) {
      body.attachment_name = attachment.name
      body.attachment_data = attachment.data
      body.attachment_type = attachment.type
    }
    setAttachment(null)

    try {
      const resp = await fetch(`${SIDECAR_URL}/sidecar/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!resp.ok) throw new Error(`Sidecar ${resp.status}`)

      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let finished = false
      while (!finished) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (finished) break
          if (!line.startsWith('data: ')) continue
          const jsonStr = line.slice(6).trim()
          if (!jsonStr) continue

          try {
            const data = JSON.parse(jsonStr)
            if (data.done) {
              finished = true
              break
            }
            if (data.error) {
              setMessages((prev) => {
                const updated = [...prev]
                const last = updated[updated.length - 1]
                if (last?.role === 'assistant') last.content = `Erro: ${data.error}`
                return [...updated]
              })
              finished = true
              break
            }
            if (data.content) {
              setMessages((prev) => {
                const updated = [...prev]
                const last = updated[updated.length - 1]
                if (last?.role === 'assistant') {
                  last.content = data.content  // Replace with latest (incremental streaming)
                }
                return [...updated]
              })
            }
          } catch {}
        }
      }
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev]
        const last = updated[updated.length - 1]
        if (last?.role === 'assistant') last.content = `Erro de conexao: ${err.message}`
        return [...updated]
      })
    } finally {
      setStreaming(false)
      sendingRef.current = false
    }
  }, [input, streaming, profileId, profileName, attachment])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const clearHistory = useCallback(() => {
    setMessages([])
    // Also clear sidecar session
    fetch(`${SIDECAR_URL}/sidecar/clear?profile_id=${profileId}`, { method: 'POST' }).catch(() => {})
  }, [profileId])

  if (!open) {
    return (
      <button
        className={styles.chatBubble}
        onClick={() => setOpen(true)}
        title="Chat com assistente"
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
      </button>
    )
  }

  return (
    <>
      <button
        className={`${styles.chatBubble} ${styles.chatBubbleOpen}`}
        onClick={() => setOpen(false)}
        title="Fechar chat"
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
      </button>
      <div className={styles.panel}>
        <div className={styles.panelHeader}>
          <span className={styles.panelTitle}>Assistente</span>
          <div className={styles.headerActions}>
            <button
              className={`${styles.clearBtn} ${voiceMode ? styles.voiceActive : ''}`}
              onClick={() => setVoiceMode(!voiceMode)}
              title={voiceMode ? 'Desativar modo voz' : 'Ativar modo voz'}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill={voiceMode ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                {voiceMode && <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />}
              </svg>
            </button>
            <button
              className={styles.clearBtn}
              onClick={clearHistory}
              title="Limpar conversa"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              </svg>
            </button>
            <button className={styles.closeBtn} onClick={() => setOpen(false)}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
        </div>

        <div className={styles.messages}>
          {messages.length === 0 && (
            <div className={styles.emptyState}>
              Oi {profileName}! Como posso ajudar?
            </div>
          )}
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`${styles.msgRow} ${
                msg.role === 'user' ? styles.msgRowUser : styles.msgRowAssistant
              }`}
            >
              <div
                className={`${styles.msgBubble} ${
                  msg.role === 'user' ? styles.msgUser : styles.msgAssistant
                } ${msg.role === 'assistant' && msg.content && /confirma\??/i.test(msg.content) ? styles.confirmMessage : ''}`}
              >
                {msg.attachment && (
                  <div className={styles.attachmentTag}>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
                    </svg>
                    {msg.attachment}
                  </div>
                )}
                {msg.role === 'assistant' ? renderContent(msg.content) : msg.content}
              </div>
            </div>
          ))}
          {streaming && messages[messages.length - 1]?.content === '' && (
            <div className={styles.typing}>
              <span /><span /><span />
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className={styles.inputArea}>
          {attachment && (
            <div className={styles.attachmentPreview}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
              </svg>
              <span>{attachment.name}</span>
              <button onClick={removeAttachment} className={styles.attachmentRemove}>x</button>
            </div>
          )}
          <div className={styles.inputRow}>
            <input type="file" ref={fileInputRef} onChange={handleFileSelect} style={{ display: 'none' }} />
            <button
              className={styles.attachBtn}
              onClick={() => fileInputRef.current?.click()}
              disabled={streaming}
              title="Anexar arquivo"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
              </svg>
            </button>
            <button
              className={`${styles.attachBtn} ${listening ? styles.micActive : ''}`}
              onClick={startListening}
              disabled={streaming}
              title={listening ? 'Parar' : 'Falar'}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill={listening ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="23" />
                <line x1="8" y1="23" x2="16" y2="23" />
              </svg>
            </button>
            <input
              ref={inputRef}
              className={styles.input}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Mensagem..."
              disabled={streaming}
            />
            <button
              className={styles.sendBtn}
              onClick={sendMessage}
              disabled={streaming || !input.trim()}
              data-voice-send
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </>
  )
}
