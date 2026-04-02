/**
 * CalendarSettings.jsx — Manage Google Calendar accounts and calendar selections.
 *
 * Used inside Settings page. Profile-scoped: each profile connects their own
 * Google accounts and selects which calendars to show in Home vs Pessoal.
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../api/client'
import { useProfile } from '../context/ProfileContext'
import styles from './CalendarSettings.module.css'

export default function CalendarSettings() {
  const { currentProfile } = useProfile()
  const queryClient = useQueryClient()
  const [expandedAccount, setExpandedAccount] = useState(null)

  // Fetch connected accounts
  const { data: accountsData, isLoading: loadingAccounts } = useQuery({
    queryKey: ['calendar-accounts'],
    queryFn: () => api.get('/calendar/accounts/'),
  })
  const accounts = accountsData?.accounts || []

  // Fetch current selections
  const { data: selectionsData } = useQuery({
    queryKey: ['calendar-selections'],
    queryFn: () => api.get('/calendar/selections/'),
  })
  const selections = selectionsData?.selections || []

  // Fetch available calendars for expanded account
  const { data: availableData, isLoading: loadingAvailable } = useQuery({
    queryKey: ['calendar-available', expandedAccount],
    queryFn: () => api.get(`/calendar/available/${expandedAccount}/`),
    enabled: !!expandedAccount,
  })
  const availableCalendars = availableData?.calendars || []

  // Connect new account
  const connectMutation = useMutation({
    mutationFn: () => api.post('/calendar/connect/'),
    onSuccess: (data) => {
      if (data.auth_url) {
        window.location.href = data.auth_url
      }
    },
  })

  // Disconnect account
  const disconnectMutation = useMutation({
    mutationFn: (accountId) => api.delete(`/calendar/accounts/${accountId}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar-accounts'] })
      queryClient.invalidateQueries({ queryKey: ['calendar-selections'] })
      setExpandedAccount(null)
    },
  })

  // Save selections
  const saveMutation = useMutation({
    mutationFn: (sels) => api.put('/calendar/selections/', { selections: sels }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar-selections'] })
      queryClient.invalidateQueries({ queryKey: ['calendar-events'] })
    },
  })

  // Build selection lookup: key = `${accountId}:${calendarId}`
  const selectionMap = {}
  for (const sel of selections) {
    selectionMap[`${sel.account}:${sel.calendar_id}`] = sel
  }

  const toggleSelection = (accountId, cal, field) => {
    const key = `${accountId}:${cal.calendar_id}`
    const existing = selectionMap[key]

    let newSelections
    if (!existing && field) {
      // Add new selection
      newSelections = [
        ...selections.map((s) => ({
          account_id: s.account,
          calendar_id: s.calendar_id,
          calendar_name: s.calendar_name,
          color: s.color,
          show_in_home: s.show_in_home,
          show_in_personal: s.show_in_personal,
        })),
        {
          account_id: accountId,
          calendar_id: cal.calendar_id,
          calendar_name: cal.name,
          color: cal.color || '',
          show_in_home: field === 'show_in_home',
          show_in_personal: field === 'show_in_personal',
        },
      ]
    } else if (existing) {
      const updated = { ...existing, [field]: !existing[field] }
      // If both are now false, remove the selection
      if (!updated.show_in_home && !updated.show_in_personal) {
        newSelections = selections
          .filter((s) => !(s.account === accountId && s.calendar_id === cal.calendar_id))
          .map((s) => ({
            account_id: s.account,
            calendar_id: s.calendar_id,
            calendar_name: s.calendar_name,
            color: s.color,
            show_in_home: s.show_in_home,
            show_in_personal: s.show_in_personal,
          }))
      } else {
        newSelections = selections.map((s) => {
          const mapped = {
            account_id: s.account,
            calendar_id: s.calendar_id,
            calendar_name: s.calendar_name,
            color: s.color,
            show_in_home: s.show_in_home,
            show_in_personal: s.show_in_personal,
          }
          if (s.account === accountId && s.calendar_id === cal.calendar_id) {
            mapped[field] = !s[field]
          }
          return mapped
        })
      }
    } else {
      return
    }

    saveMutation.mutate(newSelections)
  }

  return (
    <div className={styles.section}>
      <h2 className={styles.title}>Calendarios</h2>

      {/* Connected accounts */}
      <div className={styles.accounts}>
        {loadingAccounts && <p className={styles.muted}>Carregando...</p>}
        {accounts.map((acc) => (
          <div key={acc.id} className={styles.accountCard}>
            <div className={styles.accountHeader}>
              <div className={styles.accountInfo}>
                <span className={styles.accountEmail}>{acc.email}</span>
                {!acc.connected && (
                  <span className={styles.accountWarning}>Token expirado</span>
                )}
              </div>
              <div className={styles.accountActions}>
                <button
                  className={styles.btnSmall}
                  onClick={() =>
                    setExpandedAccount(expandedAccount === acc.id ? null : acc.id)
                  }
                >
                  {expandedAccount === acc.id ? 'Fechar' : 'Calendarios'}
                </button>
                <button
                  className={styles.btnDanger}
                  onClick={() => {
                    if (confirm(`Desconectar ${acc.email}?`)) {
                      disconnectMutation.mutate(acc.id)
                    }
                  }}
                >
                  Desconectar
                </button>
              </div>
            </div>

            {/* Calendar list for this account */}
            {expandedAccount === acc.id && (
              <div className={styles.calendarList}>
                {loadingAvailable && <p className={styles.muted}>Carregando calendarios...</p>}
                {availableCalendars.map((cal) => {
                  const key = `${acc.id}:${cal.calendar_id}`
                  const sel = selectionMap[key]
                  return (
                    <div key={cal.calendar_id} className={styles.calendarRow}>
                      <div
                        className={styles.calendarDot}
                        style={{ backgroundColor: cal.color || '#666' }}
                      />
                      <span className={styles.calendarName}>{cal.name}</span>
                      <label className={styles.checkLabel}>
                        <input
                          type="checkbox"
                          checked={sel?.show_in_home || false}
                          onChange={() => toggleSelection(acc.id, cal, 'show_in_home')}
                        />
                        Home
                      </label>
                      <label className={styles.checkLabel}>
                        <input
                          type="checkbox"
                          checked={sel?.show_in_personal || false}
                          onChange={() => toggleSelection(acc.id, cal, 'show_in_personal')}
                        />
                        Pessoal
                      </label>
                    </div>
                  )
                })}
                {availableCalendars.length === 0 && !loadingAvailable && (
                  <p className={styles.muted}>Nenhum calendario encontrado</p>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Connect button */}
      <button
        className={styles.btnConnect}
        onClick={() => connectMutation.mutate()}
        disabled={connectMutation.isPending}
      >
        {connectMutation.isPending ? 'Conectando...' : '+ Conectar conta Google'}
      </button>
    </div>
  )
}
