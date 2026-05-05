/**
 * useLabPanel — fetch lab markers for a profile from DB and assemble
 * a panel structure compatible with LabPanelDashboard.
 *
 * Returns the same shape as the hardcoded panels (palmerHealthData /
 * rafaHealthData) so the dashboard component can render either.
 *
 * Falls back to the provided fallbackPanel if the DB query returns
 * empty or errors.
 */
import { useQuery } from '@tanstack/react-query'
import api from '../../api/client'

function assemblePanel(markers, fallback) {
  if (!markers || markers.length === 0) return fallback

  // Group by category, keep most recent value per (category, key) using exam_data desc.
  // Older values become history entries.
  const byCategory = new Map() // slug -> { meta, latestByKey: Map(key -> marker), historyByKey: Map(key -> [olders]) }

  for (const m of markers) {
    if (!byCategory.has(m.category_slug)) {
      byCategory.set(m.category_slug, {
        slug: m.category_slug,
        label: m.category_label,
        order: m.category_order,
        latestByKey: new Map(),
        historyByKey: new Map(),
        latestExamDate: m.exam_data,
        latestExamLab: m.exam_lab,
      })
    }
    const cat = byCategory.get(m.category_slug)

    if (!cat.latestByKey.has(m.key)) {
      cat.latestByKey.set(m.key, m)
      // first time seeing this key — set as latest
      if (m.exam_data > cat.latestExamDate) {
        cat.latestExamDate = m.exam_data
        cat.latestExamLab = m.exam_lab
      }
    } else {
      // already have a value for this key — current m is older (because queryset is sorted by -exam.data)
      if (!cat.historyByKey.has(m.key)) cat.historyByKey.set(m.key, [])
      cat.historyByKey.get(m.key).push({
        data: m.exam_data,
        value: parseFloat(m.value) || m.value_text,
        status: m.status,
      })
    }
  }

  // Compute panel-level metadata: most recent overall exam_date + lab
  let panelDate = null
  let panelLab = ''
  for (const m of markers) {
    if (!panelDate || m.exam_data > panelDate) {
      panelDate = m.exam_data
      panelLab = m.exam_lab
    }
  }

  // Build categorias array sorted by order
  const sorted = Array.from(byCategory.values()).sort((a, b) => a.order - b.order)
  const categorias = sorted.map(cat => {
    const markers = Array.from(cat.latestByKey.values()).map(m => {
      const out = {
        key: m.key,
        label: m.label,
        value: m.value !== null && m.value !== undefined ? parseFloat(m.value) : (m.value_text || null),
        unit: m.unit || '',
        status: m.status,
      }
      if (m.ref_min !== null && m.ref_min !== undefined) out.ref_min = parseFloat(m.ref_min)
      if (m.ref_max !== null && m.ref_max !== undefined) out.ref_max = parseFloat(m.ref_max)
      if (m.ref_text) out.ref_text = m.ref_text
      if (m.obs) out.obs = m.obs
      const hist = cat.historyByKey.get(m.key)
      if (hist && hist.length > 0) out.history = hist
      return out
    })

    const out = {
      id: cat.slug,
      nome: cat.label,
      markers,
    }
    // Override category date if it differs from panel baseline
    if (cat.latestExamDate !== panelDate) {
      out.data_atualizacao = cat.latestExamDate
      out.lab_atualizacao = cat.latestExamLab
    }
    return out
  })

  return {
    data_coleta: panelDate || (fallback?.data_coleta || ''),
    laboratorio: panelLab || (fallback?.laboratorio || ''),
    contexto: fallback?.contexto || '',
    categorias,
  }
}

export function useLabPanel(profileId, fallbackPanel) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['lab-markers', profileId],
    queryFn: async () => {
      if (!profileId) return []
      // api.get() returns parsed JSON directly (no .data wrapper)
      return (await api.get(`/saude/lab-markers/?profile_id=${profileId}`)) || []
    },
    enabled: !!profileId,
  })

  if (isLoading) return { panel: fallbackPanel, isLoading: true, source: 'fallback' }
  if (error) return { panel: fallbackPanel, isLoading: false, source: 'fallback', error }

  const assembled = assemblePanel(data, fallbackPanel)
  const source = data && data.length > 0 ? 'db' : 'fallback'
  return { panel: assembled, isLoading: false, source }
}
