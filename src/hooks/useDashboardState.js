import { useState, useEffect, useCallback, useRef } from 'react'
import api from '../api/client'

const DEBOUNCE_MS = 800

/**
 * Server-side dashboard state with localStorage migration.
 * Returns [state, updateState, isLoading]
 *
 * State shape: { tabs, configs }
 * - tabs: [{ id, name, widgets: [{ id, type, x, y, w, h }] }]
 * - configs: { widgetId: { ...config } }
 */
export default function useDashboardState(profileId) {
  const [state, setState] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [saveStatus, setSaveStatus] = useState(null) // null | 'saving' | 'saved'
  const saveTimer = useRef(null)
  const latestState = useRef(null)
  const serverLoaded = useRef(false)
  const profileIdRef = useRef(profileId)
  profileIdRef.current = profileId
  const savedTimer = useRef(null)

  // Load state from server (or migrate from localStorage)
  useEffect(() => {
    if (!profileId) return
    let cancelled = false

    async function load() {
      try {
        const data = await api.get(`/dashboard-state/?profile_id=${profileId}`)
        if (cancelled) return

        if (data.state && data.state.tabs) {
          // Server has state — check if tabs have widgets
          const hasWidgets = data.state.tabs.some(t => t.widgets && t.widgets.length > 0)
          if (hasWidgets) {
            setState(data.state)
            // Delay enabling saves to let GridStack settle without overwriting
            serverLoaded.current = true

          } else {
            // Server tabs exist but no widgets — try localStorage migration
            const migrated = migrateFromLocalStorage(profileId)
            const migratedHasWidgets = migrated.tabs.some(t => t.widgets && t.widgets.length > 0)
            if (migratedHasWidgets) {
              setState(migrated)
              serverLoaded.current = true
              try { await api.put(`/dashboard-state/?profile_id=${profileIdRef.current}`, { state: migrated }) } catch {}
            } else {
              // Both empty — use server state as-is (don't overwrite with defaults)
              setState(data.state)
              serverLoaded.current = true
            }
          }
        } else {
          // No server state — migrate from localStorage
          const migrated = migrateFromLocalStorage(profileId)
          setState(migrated)
          settleTimer.current = setTimeout(() => { serverLoaded.current = true }, 3000)
          try { await api.put(`/dashboard-state/?profile_id=${profileIdRef.current}`, { state: migrated }) } catch {}
        }
      } catch {
        // Offline or error — fall back to localStorage
        const local = migrateFromLocalStorage(profileId)
        if (!cancelled) setState(local)
      }
      if (!cancelled) setIsLoading(false)
    }

    load()
    return () => { cancelled = true }
  }, [profileId])

  // Debounced save to server
  const saveToServer = useCallback((newState) => {
    if (!serverLoaded.current) return
    latestState.current = newState
    setSaveStatus('saving')
    if (savedTimer.current) clearTimeout(savedTimer.current)
    if (saveTimer.current) clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(async () => {
      try {
        await api.put(`/dashboard-state/?profile_id=${profileIdRef.current}`, { state: latestState.current })
        setSaveStatus('saved')
        savedTimer.current = setTimeout(() => setSaveStatus(null), 1500)
      } catch (err) {
        console.warn('Failed to save dashboard state:', err)
        setSaveStatus(null)
      }
    }, DEBOUNCE_MS)
  }, [])

  const updateState = useCallback((partialOrFn) => {
    setState(prev => {
      // Support functional updater: partialOrFn(prev) => partial
      const partial = typeof partialOrFn === 'function' ? partialOrFn(prev) : partialOrFn
      const next = { ...prev, ...partial }
      saveToServer(next)
      return next
    })
  }, [saveToServer])

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (saveTimer.current) {
        clearTimeout(saveTimer.current)
        // Flush pending save
        if (latestState.current && serverLoaded.current) {
          api.put(`/dashboard-state/?profile_id=${profileIdRef.current}`, { state: latestState.current }).catch(() => {})
        }
      }
    }
  }, [])

  return [state, updateState, isLoading, saveStatus]
}

// ── localStorage migration ──

const DEFAULT_WIDGETS = [
  { id: 'kpi-hoje',      type: 'kpi-hoje',      x: 0,  y: 0, w: 3, h: 2 },
  { id: 'kpi-atrasadas', type: 'kpi-atrasadas', x: 3,  y: 0, w: 3, h: 2 },
  { id: 'kpi-ativas',    type: 'kpi-ativas',    x: 6,  y: 0, w: 3, h: 2 },
  { id: 'kpi-projetos',  type: 'kpi-projetos',  x: 9,  y: 0, w: 3, h: 2 },
  { id: 'capture',       type: 'capture',       x: 0,  y: 2, w: 8, h: 1 },
  { id: 'projects',      type: 'projects',      x: 8,  y: 2, w: 4, h: 1 },
  { id: 'tasks',         type: 'tasks',         x: 0,  y: 3, w: 4, h: 6 },
  { id: 'reminders',     type: 'reminders',     x: 4,  y: 3, w: 5, h: 6 },
  { id: 'calendar',      type: 'calendar',      x: 9,  y: 3, w: 3, h: 8 },
  { id: 'events',        type: 'events',        x: 0,  y: 9, w: 4, h: 5 },
  { id: 'notes',         type: 'notes',         x: 4,  y: 9, w: 5, h: 5 },
]

function safeJsonParse(key) {
  try {
    const v = localStorage.getItem(key)
    return v ? JSON.parse(v) : null
  } catch { return null }
}

function migrateFromLocalStorage(profileId) {
  // Try profile-scoped tabs key first
  const tabsKey = `vault-pessoal-tabs-v1-${profileId}`
  const tabs = safeJsonParse(tabsKey)
  if (tabs && tabs.length) {
    const configKey = `vault-pessoal-widget-config-v1-${profileId}`
    const configs = safeJsonParse(configKey) || {}
    return { tabs, configs }
  }

  // Try profile-scoped widgets key
  const widgetsKey = `vault-pessoal-widgets-v1-${profileId}`
  const widgets = safeJsonParse(widgetsKey)
  if (widgets && widgets.length) {
    const configKey = `vault-pessoal-widget-config-v1-${profileId}`
    const configs = safeJsonParse(configKey) || {}
    return { tabs: [{ id: 'default', name: 'Principal', widgets }], configs }
  }

  // Try old unscoped keys
  const oldWidgets = safeJsonParse('vault-pessoal-widgets-v1')
  if (oldWidgets && oldWidgets.length) {
    const configs = safeJsonParse('vault-pessoal-widget-config-v1') || {}
    const items = oldWidgets.map(item => ({ ...item, type: item.type || item.id }))
    return { tabs: [{ id: 'default', name: 'Principal', widgets: items }], configs }
  }

  // Defaults
  return { tabs: [{ id: 'default', name: 'Principal', widgets: DEFAULT_WIDGETS }], configs: {} }
}
