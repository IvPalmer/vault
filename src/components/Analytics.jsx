import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useMonth } from '../context/MonthContext'
import api from '../api/client'
import {
  SpendingTrendsChart,
  CategoryBreakdownChart,
  CardAnalysisChart,
  AnalyticsFilters,
  AnalyticsKpiCards,
  SavingsRateChart,
  CategoryTrendsChart,
  ExpenseCompositionChart,
  TopExpensesTable,
  MonthlyCategoryChart,
  CategoryDescBreakdownChart,
  SpendingInsights,
} from './charts'
import Skeleton from './Skeleton'
import styles from './Analytics.module.css'

function Analytics() {
  const { months } = useMonth()
  const [filters, setFilters] = useState({
    startMonth: '2025-12',
    endMonth: null,
    categories: [],
    accounts: '',
  })

  const queryParams = useMemo(() => {
    const p = new URLSearchParams()
    if (filters.startMonth) p.set('start_month', filters.startMonth)
    if (filters.endMonth) p.set('end_month', filters.endMonth)
    if (filters.categories.length) p.set('categories', filters.categories.join(','))
    if (filters.accounts) p.set('accounts', filters.accounts)
    return p.toString()
  }, [filters])

  const { data, isLoading, error } = useQuery({
    queryKey: ['analytics-trends', queryParams],
    queryFn: () => api.get(`/analytics/trends/${queryParams ? `?${queryParams}` : ''}`),
  })

  return (
    <div className={styles.container}>
      {/* KPI Summary Cards */}
      {isLoading ? (
        <div className={styles.kpiRow}>
          {[...Array(5)].map((_, i) => (
            <div key={i} className={styles.card} style={{ padding: 'var(--space-md)' }}>
              <Skeleton variant="text" width="60%" />
              <Skeleton variant="text" width="80%" height="24px" />
              <Skeleton variant="text" width="50%" />
            </div>
          ))}
        </div>
      ) : data?.summary_kpis && (
        <AnalyticsKpiCards data={data.summary_kpis} />
      )}

      {/* Filter Bar */}
      <AnalyticsFilters
        filters={filters}
        setFilters={setFilters}
        months={months}
        availableCategories={data?.available_categories}
      />

      {/* Spending Insights */}
      <SpendingInsights />

      {error && (
        <div className={styles.error}>Erro ao carregar dados de analytics</div>
      )}

      {/* Charts Grid */}
      {isLoading ? (
        <div className={styles.grid}>
          <div className={`${styles.card} ${styles.spanFull}`}>
            <h3 className={styles.cardTitle}>TENDÊNCIA DE GASTOS</h3>
            <Skeleton variant="chart" height="380px" />
          </div>
          <div className={`${styles.card} ${styles.spanFour}`}>
            <h3 className={styles.cardTitle}>TAXA DE POUPANÇA</h3>
            <Skeleton variant="chart" height="380px" />
          </div>
          <div className={`${styles.card} ${styles.spanTwo}`}>
            <h3 className={styles.cardTitle}>GASTOS POR CATEGORIA</h3>
            <Skeleton variant="chart" height="280px" />
          </div>
          <div className={`${styles.card} ${styles.spanFull}`}>
            <h3 className={styles.cardTitle}>CONSUMO POR MÊS E CATEGORIA</h3>
            <Skeleton variant="chart" height="420px" />
          </div>
          <div className={`${styles.card} ${styles.spanFull}`}>
            <h3 className={styles.cardTitle}>EVOLUÇÃO POR CATEGORIA</h3>
            <Skeleton variant="chart" height="380px" />
          </div>
          <div className={`${styles.card} ${styles.spanThree}`}>
            <h3 className={styles.cardTitle}>COMPOSIÇÃO DE GASTOS</h3>
            <Skeleton variant="chart" height="350px" />
          </div>
          <div className={`${styles.card} ${styles.spanThree}`}>
            <h3 className={styles.cardTitle}>ANÁLISE POR CARTÃO</h3>
            <Skeleton variant="chart" height="350px" />
          </div>
          <div className={`${styles.card} ${styles.spanFull}`}>
            <h3 className={styles.cardTitle}>CONSUMO POR CATEGORIA E ITEM RECORRENTE</h3>
            <Skeleton variant="chart" height="420px" />
          </div>
          <div className={`${styles.card} ${styles.spanFull}`}>
            <h3 className={styles.cardTitle}>MAIORES GASTOS DO PERÍODO</h3>
            <Skeleton variant="chart" height="300px" />
          </div>
        </div>
      ) : data && (
        <div className={styles.grid}>
          {/* Row 1: Spending Trends — full width */}
          <div className={`${styles.card} ${styles.spanFull}`}>
            <h3 className={styles.cardTitle}>TENDÊNCIA DE GASTOS</h3>
            <SpendingTrendsChart data={data.spending_trends} />
          </div>

          {/* Row 2: Savings Rate (4/6) + Category Donut (2/6) */}
          <div className={`${styles.card} ${styles.spanFour}`}>
            <h3 className={styles.cardTitle}>TAXA DE POUPANÇA</h3>
            <SavingsRateChart data={data.savings_rate} savingsTarget={data.savings_target_pct} />
          </div>
          <div className={`${styles.card} ${styles.spanTwo}`}>
            <h3 className={styles.cardTitle}>GASTOS POR CATEGORIA</h3>
            <CategoryBreakdownChart data={data.category_breakdown} />
          </div>

          {/* Row 3: Monthly by Category — full width (like old Excel chart) */}
          <div className={`${styles.card} ${styles.spanFull}`}>
            <h3 className={styles.cardTitle}>CONSUMO POR MÊS E CATEGORIA</h3>
            <MonthlyCategoryChart data={data.monthly_category_stacked} />
          </div>

          {/* Row 4: Category Trends — full width */}
          <div className={`${styles.card} ${styles.spanFull}`}>
            <h3 className={styles.cardTitle}>EVOLUÇÃO POR CATEGORIA</h3>
            <CategoryTrendsChart data={data.category_trends} />
          </div>

          {/* Row 5: Expense Composition (3/6) + Card Analysis (3/6) */}
          <div className={`${styles.card} ${styles.spanThree}`}>
            <h3 className={styles.cardTitle}>COMPOSIÇÃO DE GASTOS</h3>
            <ExpenseCompositionChart data={data.expense_composition} />
          </div>
          <div className={`${styles.card} ${styles.spanThree}`}>
            <h3 className={styles.cardTitle}>ANÁLISE POR CARTÃO</h3>
            <CardAnalysisChart data={data.card_analysis} />
          </div>

          {/* Row 6: Category × Recurring Item breakdown — full width */}
          <div className={`${styles.card} ${styles.spanFull}`}>
            <h3 className={styles.cardTitle}>CONSUMO POR CATEGORIA E ITEM RECORRENTE</h3>
            <CategoryDescBreakdownChart data={data.category_desc_breakdown} />
          </div>

          {/* Row 7: Top Expenses Table — full width */}
          <div className={`${styles.card} ${styles.spanFull}`}>
            <h3 className={styles.cardTitle}>MAIORES GASTOS DO PERÍODO</h3>
            <TopExpensesTable data={data.top_expenses} />
          </div>
        </div>
      )}
    </div>
  )
}

export default Analytics
