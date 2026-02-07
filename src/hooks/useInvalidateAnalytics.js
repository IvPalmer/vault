import { useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'

/**
 * Centralized query invalidation for analytics data.
 *
 * Call invalidateAll() after mutations that affect multiple sections
 * (e.g., mapping a transaction updates recurring, metricas, and projections).
 *
 * Call specific invalidators for targeted updates.
 */
export function useInvalidateAnalytics() {
  const queryClient = useQueryClient()

  const invalidateMetricas = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['analytics-metricas'] })
  }, [queryClient])

  const invalidateMetricasOrder = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['metricas-order'] })
  }, [queryClient])

  const invalidateRecurring = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['analytics-recurring'] })
  }, [queryClient])

  const invalidateCards = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['analytics-cards'] })
  }, [queryClient])

  const invalidateProjection = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['analytics-projection'] })
  }, [queryClient])

  const invalidateOrcamento = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['analytics-orcamento'] })
  }, [queryClient])

  const invalidateAll = useCallback(() => {
    invalidateMetricas()
    invalidateMetricasOrder()
    invalidateRecurring()
    invalidateCards()
    invalidateProjection()
    invalidateOrcamento()
  }, [
    invalidateMetricas, invalidateMetricasOrder, invalidateRecurring,
    invalidateCards, invalidateProjection, invalidateOrcamento,
  ])

  return {
    invalidateMetricas,
    invalidateMetricasOrder,
    invalidateRecurring,
    invalidateCards,
    invalidateProjection,
    invalidateOrcamento,
    invalidateAll,
  }
}

export default useInvalidateAnalytics
