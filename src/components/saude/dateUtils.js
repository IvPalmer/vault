/**
 * Local-timezone date helpers for saúde widgets.
 *
 * Important: `new Date('2026-05-28')` parses as UTC midnight, which in
 * America/Sao_Paulo (-03:00) renders as 2026-05-27 21:00 — the previous
 * local day. Use parseLocalDate for ISO date strings to keep gestational
 * day arithmetic stable in BRT.
 */

export function parseLocalDate(iso) {
  if (!iso) return null
  if (iso instanceof Date) return iso
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d)
}

export function addDays(date, days) {
  const r = new Date(date)
  r.setDate(r.getDate() + days)
  return r
}

export function diffDays(a, b) {
  // Whole-day difference, sign preserved
  const ms = a.getTime() - b.getTime()
  return Math.round(ms / 86_400_000)
}

export function fmtDateShort(d) {
  if (!d) return ''
  return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`
}

export function fmtDate(d) {
  if (!d) return ''
  return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`
}

export function todayLocal() {
  const t = new Date()
  t.setHours(0, 0, 0, 0)
  return t
}
