import { useState, useRef, useEffect } from 'react'

const s = {
  wrap: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    background: 'var(--color-surface)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    boxShadow: 'var(--shadow-sm)',
    overflow: 'hidden',
  },
  display: {
    flex: 1,
    padding: '12px 16px',
    fontSize: '0.88rem',
    lineHeight: 1.6,
    color: 'var(--color-text)',
    whiteSpace: 'pre-wrap',
    cursor: 'text',
    overflow: 'auto',
    minHeight: 0,
  },
  placeholder: {
    color: 'var(--color-text-secondary)',
    fontStyle: 'italic',
  },
  textarea: {
    flex: 1,
    padding: '12px 16px',
    fontSize: '0.88rem',
    lineHeight: 1.6,
    color: 'var(--color-text)',
    background: 'var(--color-bg)',
    border: 'none',
    outline: 'none',
    resize: 'none',
    fontFamily: 'var(--font-sans)',
    minHeight: 0,
  },
}

export default function TextBlock({ config, onConfigChange }) {
  const [editing, setEditing] = useState(false)
  const [text, setText] = useState(config?.content || '')
  const textareaRef = useRef(null)

  useEffect(() => {
    setText(config?.content || '')
  }, [config?.content])

  useEffect(() => {
    if (editing && textareaRef.current) {
      textareaRef.current.focus()
      textareaRef.current.selectionStart = textareaRef.current.value.length
    }
  }, [editing])

  const save = () => {
    setEditing(false)
    if (text !== (config?.content || '')) {
      onConfigChange({ ...config, content: text })
    }
  }

  if (editing) {
    return (
      <div style={s.wrap}>
        <textarea
          ref={textareaRef}
          style={s.textarea}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onBlur={save}
          onKeyDown={(e) => {
            if (e.key === 'Escape') save()
          }}
        />
      </div>
    )
  }

  return (
    <div style={s.wrap} onDoubleClick={() => setEditing(true)}>
      <div style={s.display}>
        {text || <span style={s.placeholder}>Clique duplo para editar...</span>}
      </div>
    </div>
  )
}
