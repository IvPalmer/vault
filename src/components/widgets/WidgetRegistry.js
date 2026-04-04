// Widget type metadata registry
// Components are resolved in PersonalOrganizer.jsx — this file only holds metadata

const WIDGET_REGISTRY = {
  // ── Pessoal (existing) ──
  'kpi-hoje':      { label: 'Tarefas Hoje', category: 'Pessoal', defaultW: 3, defaultH: 2, minW: 2, minH: 1 },
  'kpi-atrasadas': { label: 'Atrasadas', category: 'Pessoal', defaultW: 3, defaultH: 2, minW: 2, minH: 1 },
  'kpi-ativas':    { label: 'Tarefas Ativas', category: 'Pessoal', defaultW: 3, defaultH: 2, minW: 2, minH: 1 },
  'kpi-projetos':  { label: 'Projetos', category: 'Pessoal', defaultW: 3, defaultH: 2, minW: 2, minH: 1 },
  'capture':       { label: 'Quick Capture', category: 'Pessoal', defaultW: 8, defaultH: 1, minW: 3, minH: 1 },
  'projects':      { label: 'Projetos Bar', category: 'Pessoal', defaultW: 4, defaultH: 1, minW: 2, minH: 1 },
  'tasks':         { label: 'Tarefas', category: 'Pessoal', defaultW: 4, defaultH: 6, minW: 2, minH: 3 },
  'reminders':     { label: 'Lembretes', category: 'Pessoal', defaultW: 5, defaultH: 6, minW: 2, minH: 3 },
  'calendar':      { label: 'Calendario', category: 'Pessoal', defaultW: 3, defaultH: 8, minW: 2, minH: 4 },
  'events':        { label: 'Eventos', category: 'Pessoal', defaultW: 4, defaultH: 5, minW: 2, minH: 3 },
  'notes':         { label: 'Notas', category: 'Pessoal', defaultW: 5, defaultH: 5, minW: 2, minH: 3 },

  // ── Display (new) ──
  'text-block':    { label: 'Texto', category: 'Display', defaultW: 4, defaultH: 2, minW: 2, minH: 1 },
  'clock':         { label: 'Relogio', category: 'Display', defaultW: 2, defaultH: 2, minW: 2, minH: 2 },
  'greeting':      { label: 'Saudacao', category: 'Display', defaultW: 4, defaultH: 1, minW: 3, minH: 1 },

  // ── Financeiro (new) ──
  'fin-saldo':     { label: 'Saldo Projetado', category: 'Financeiro', defaultW: 3, defaultH: 2, minW: 2, minH: 2 },
  'fin-sobra':     { label: 'Sobra do Mes', category: 'Financeiro', defaultW: 3, defaultH: 2, minW: 2, minH: 2 },
  'fin-fatura':    { label: 'Fatura CC', category: 'Financeiro', defaultW: 3, defaultH: 2, minW: 2, minH: 2 },
}

// Get categories grouped for the catalog UI
export function getWidgetCategories() {
  const cats = {}
  for (const [type, meta] of Object.entries(WIDGET_REGISTRY)) {
    if (!cats[meta.category]) cats[meta.category] = []
    cats[meta.category].push({ type, ...meta })
  }
  return cats
}

// Get metadata for a widget type
export function getWidgetMeta(type) {
  return WIDGET_REGISTRY[type] || null
}

// Generate unique widget ID
export function generateWidgetId(type) {
  return `${type}-${Math.random().toString(36).slice(2, 8)}`
}

// Find next available position in a 12-column grid
export function findNextPosition(existingWidgets, newW, newH) {
  // Build occupancy map
  const occupied = new Set()
  for (const w of existingWidgets) {
    for (let row = w.y; row < w.y + w.h; row++) {
      for (let col = w.x; col < w.x + w.w; col++) {
        occupied.add(`${col},${row}`)
      }
    }
  }
  // Scan rows then cols for a fit
  for (let y = 0; y < 100; y++) {
    for (let x = 0; x <= 12 - newW; x++) {
      let fits = true
      for (let dy = 0; dy < newH && fits; dy++) {
        for (let dx = 0; dx < newW && fits; dx++) {
          if (occupied.has(`${x + dx},${y + dy}`)) fits = false
        }
      }
      if (fits) return { x, y }
    }
  }
  return { x: 0, y: 0 }
}

export default WIDGET_REGISTRY
