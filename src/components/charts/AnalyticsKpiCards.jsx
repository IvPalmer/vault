import styles from './AnalyticsKpiCards.module.css'

function fmt(n) {
  return Math.abs(n).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
}

const MONTH_LABELS = {
  '01': 'Jan', '02': 'Fev', '03': 'Mar', '04': 'Abr',
  '05': 'Mai', '06': 'Jun', '07': 'Jul', '08': 'Ago',
  '09': 'Set', '10': 'Out', '11': 'Nov', '12': 'Dez',
}

function shortMonth(monthStr) {
  if (!monthStr) return '—'
  const [y, m] = monthStr.split('-')
  return `${MONTH_LABELS[m]} ${y.slice(2)}`
}

function AnalyticsKpiCards({ data }) {
  if (!data) return null

  const cards = [
    {
      label: 'Renda Média',
      value: `R$ ${fmt(data.avg_monthly_income)}`,
      sub: 'por mês',
      color: 'var(--color-green)',
    },
    {
      label: 'Gasto Médio',
      value: `R$ ${fmt(data.avg_monthly_expenses)}`,
      sub: 'por mês',
      color: 'var(--color-red)',
    },
    {
      label: 'Taxa de Poupança',
      value: `${data.avg_savings_rate.toFixed(1)}%`,
      sub: `melhor: ${shortMonth(data.best_month)}`,
      color: data.avg_savings_rate >= 20 ? 'var(--color-green)' : 'var(--color-orange)',
    },
    {
      label: 'Saldo Total',
      value: `R$ ${fmt(data.total_net)}`,
      sub: `${data.num_months} meses`,
      color: data.total_net >= 0 ? 'var(--color-green)' : 'var(--color-red)',
    },
    {
      label: 'Pior Mês',
      value: shortMonth(data.worst_month),
      sub: 'menor poupança',
      color: 'var(--color-text-secondary)',
    },
  ]

  return (
    <div className={styles.row}>
      {cards.map((card, i) => (
        <div key={i} className={styles.card}>
          <span className={styles.label}>{card.label}</span>
          <span className={styles.value} style={{ color: card.color }}>{card.value}</span>
          <span className={styles.sub}>{card.sub}</span>
        </div>
      ))}
    </div>
  )
}

export default AnalyticsKpiCards
