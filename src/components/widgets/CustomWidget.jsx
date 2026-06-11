/**
 * CustomWidget — renders agent-generated HTML/CSS/JS in a sandboxed iframe.
 *
 * The chat agent can create any widget: Pinterest boards, interactive checklists,
 * weather displays, embedded feeds, countdown timers, habit trackers, etc.
 *
 * Config shape: { html: '<full HTML document>', title: 'Widget Name' }
 */
import { useRef, useEffect, useState } from 'react'
import { useProfile } from '../../context/ProfileContext'

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
    position: 'relative',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '6px 28px 6px 12px',
    borderBottom: '1px solid var(--color-border)',
    minHeight: 30,
    cursor: 'grab',
  },
  title: {
    fontSize: '0.72rem',
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: '1px',
    color: 'var(--color-text-secondary)',
    margin: 0,
  },
  iframe: {
    flex: 1,
    border: 'none',
    width: '100%',
    minHeight: 0,
    background: 'white',
  },
  empty: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'var(--color-text-secondary)',
    fontSize: '0.82rem',
    fontStyle: 'italic',
    padding: 20,
    textAlign: 'center',
  },
}

// Base styles injected into every custom widget for consistent look
const BASE_STYLES = `
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
    font-size: 14px;
    line-height: 1.5;
    color: #2c2c2c;
    padding: 12px;
    overflow-x: hidden;
  }
  a { color: #b86530; }
  h1, h2, h3, h4 { font-weight: 700; margin-bottom: 8px; }
  h3 { font-size: 0.9rem; }
  ul, ol { padding-left: 20px; margin-bottom: 8px; }
  li { margin-bottom: 4px; }
  img { max-width: 100%; border-radius: 6px; }
  .card { background: #f8f6f4; border-radius: 8px; padding: 12px; margin-bottom: 8px; }
  button {
    padding: 6px 14px; border: 1px solid #ddd; border-radius: 6px;
    background: white; cursor: pointer; font-size: 0.85rem;
    transition: all 0.15s;
  }
  button:hover { border-color: #b86530; color: #b86530; }
  input, select {
    padding: 6px 10px; border: 1px solid #ddd; border-radius: 6px;
    font-size: 0.85rem; width: 100%; outline: none;
  }
  input:focus, select:focus { border-color: #b86530; }
  .grid { display: grid; gap: 8px; }
  .flex { display: flex; gap: 8px; align-items: center; }
  .text-muted { color: #888; font-size: 0.82rem; }
  .accent { color: #b86530; }
  .badge {
    display: inline-block; padding: 2px 8px; border-radius: 10px;
    font-size: 0.75rem; font-weight: 600; background: #f0e6de; color: #b86530;
  }
</style>
`

export default function CustomWidget({ config }) {
  const iframeRef = useRef(null)
  const { currentProfile } = useProfile()
  const html = config?.html || ''
  const title = config?.title || 'Custom'

  useEffect(() => {
    if (!iframeRef.current || !html) return

    const iframe = iframeRef.current

    // The iframe is sandboxed WITHOUT allow-same-origin, so its script can't
    // touch the parent (no parent.localStorage / JWT access). The Vault API and
    // widget-local state are served via a postMessage bridge: the parent holds
    // the profile id + token context, performs the work, and posts results back.
    const VAULT_API = `${window.location.origin}/api`
    const PROFILE_ID = currentProfile?.id || ''
    const WIDGET_KEY = `custom-widget-${config?.widgetId || 'default'}`
    // Parent holds the JWT; the sandboxed iframe never sees it. Attach auth here
    // so backend requests are authenticated (X-Profile-ID alone is no longer
    // trusted by the backend).
    const authHeaders = (extra = {}) => {
      const token = localStorage.getItem('vaultAccessToken')
      return {
        ...(PROFILE_ID && { 'X-Profile-ID': PROFILE_ID }),
        ...(token && { Authorization: `Bearer ${token}` }),
        ...extra,
      }
    }

    const handleMessage = async (event) => {
      if (event.source !== iframe.contentWindow) return
      const msg = event.data
      if (!msg || msg.__vault !== 'req') return
      const reply = (result, error) =>
        iframe.contentWindow?.postMessage({ __vault: 'res', id: msg.id, result, error }, '*')
      try {
        if (msg.op === 'get') {
          const url = new URL(VAULT_API + msg.path, window.location.origin)
          Object.entries(msg.params || {}).forEach(([k, v]) => url.searchParams.set(k, v))
          const resp = await fetch(url, { headers: authHeaders() })
          reply(await resp.json())
        } else if (msg.op === 'post') {
          const resp = await fetch(VAULT_API + msg.path, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(msg.data || {}),
          })
          reply(await resp.json())
        } else if (msg.op === 'saveState') {
          try { localStorage.setItem(WIDGET_KEY, JSON.stringify(msg.state)) } catch {}
          reply(true)
        } else if (msg.op === 'loadState') {
          let result = msg.fallback
          try {
            const raw = localStorage.getItem(WIDGET_KEY)
            if (raw) result = JSON.parse(raw)
          } catch {}
          reply(result)
        }
      } catch (err) {
        reply(undefined, String(err))
      }
    }
    window.addEventListener('message', handleMessage)

    // Inject the HTML with base styles and the iframe-side bridge API
    const fullHtml = `<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
${BASE_STYLES}
<script>
  // Vault API + state bridge — requests go to the parent over postMessage.
  const __vaultPending = {};
  let __vaultSeq = 0;
  window.addEventListener('message', (e) => {
    const m = e.data;
    if (!m || m.__vault !== 'res') return;
    const p = __vaultPending[m.id];
    if (!p) return;
    delete __vaultPending[m.id];
    if (m.error) p.reject(new Error(m.error)); else p.resolve(m.result);
  });
  function __vaultCall(req) {
    return new Promise((resolve, reject) => {
      const id = ++__vaultSeq;
      __vaultPending[id] = { resolve, reject };
      parent.postMessage({ __vault: 'req', id, ...req }, '*');
    });
  }

  function vaultGet(path, params = {}) { return __vaultCall({ op: 'get', path, params }); }
  function vaultPost(path, data = {}) { return __vaultCall({ op: 'post', path, data }); }
  function saveState(state) { return __vaultCall({ op: 'saveState', state }); }
  function loadState(fallback = {}) { return __vaultCall({ op: 'loadState', fallback }); }
</script>
</head>
<body>${html}</body></html>`

    iframe.srcdoc = fullHtml

    return () => window.removeEventListener('message', handleMessage)
  }, [html, currentProfile?.id])

  if (!html) {
    return (
      <div style={s.wrap}>
        <div style={s.header}>
          <span style={s.title}>{title}</span>
        </div>
        <div style={s.empty}>Widget personalizado — aguardando conteudo do assistente</div>
      </div>
    )
  }

  return (
    <div style={s.wrap}>
      <div style={s.header}>
        <span style={s.title}>{title}</span>
      </div>
      <iframe
        ref={iframeRef}
        style={s.iframe}
        sandbox="allow-scripts allow-popups allow-forms"
        title={title}
      />
    </div>
  )
}
