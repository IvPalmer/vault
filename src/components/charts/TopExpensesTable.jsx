import { useMemo } from 'react'
import styles from './TopExpensesTable.module.css'

const MONTH_LABELS = {
  '01': 'Jan', '02': 'Fev', '03': 'Mar', '04': 'Abr',
  '05': 'Mai', '06': 'Jun', '07': 'Jul', '08': 'Ago',
  '09': 'Set', '10': 'Out', '11': 'Nov', '12': 'Dez',
}

function shortDate(dateStr) {
  if (!dateStr) return '—'
  const [y, m, d] = dateStr.split('-')
  return `${d} ${MONTH_LABELS[m]} ${y.slice(2)}`
}

function fmt(n) {
  return Math.abs(n).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function TopExpensesTable({ data }) {
  const { rows, maxAmount } = useMemo(() => {
    if (!data?.length) return { rows: [], maxAmount: 0 }
    const maxAmount = Math.max(...data.map(r => Math.abs(r.amount)))
    return { rows: data, maxAmount }
  }, [data])

  if (!rows.length) return null

  return (
    <div className={styles.wrap}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th className={styles.thRank}>#</th>
            <th className={styles.thDesc}>Descrição</th>
            <th className={styles.thCat}>Categoria</th>
            <th className={styles.thDate}>Data</th>
            <th className={styles.thAmount}>Valor</th>
            <th className={styles.thBar}></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => {
            const pct = maxAmount ? (Math.abs(row.amount) / maxAmount) * 100 : 0
            return (
              <tr key={i} className={styles.row}>
                <td className={styles.rank}>{i + 1}</td>
                <td className={styles.desc} title={row.description}>
                  {row.description.length > 32 ? row.description.slice(0, 32) + '...' : row.description}
                </td>
                <td className={styles.cat}>
                  <span className={styles.tag}>{row.category || '—'}</span>
                </td>
                <td className={styles.date}>{shortDate(row.date)}</td>
                <td className={styles.amount}>R$ {fmt(row.amount)}</td>
                <td className={styles.barCell}>
                  <div className={styles.barTrack}>
                    <div
                      className={styles.barFill}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export default TopExpensesTable
