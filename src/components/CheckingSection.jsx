import { useQuery } from '@tanstack/react-query'
import { useMonth } from '../context/MonthContext'
import api from '../api/client'
import VaultTable from './VaultTable'
import tableStyles from './VaultTable.module.css'
import styles from './CheckingSection.module.css'

function fmt(n) {
  return Math.abs(n).toLocaleString('pt-BR', { maximumFractionDigits: 2, minimumFractionDigits: 2 })
}

function AmountCell({ value }) {
  const cls = value > 0 ? tableStyles.positive : tableStyles.negative
  return <span className={cls}>R$ {fmt(value)}</span>
}

const checkingColumns = [
  {
    accessorKey: 'date',
    header: 'DATA',
    size: 100,
    cell: ({ getValue }) => {
      const d = new Date(getValue() + 'T00:00:00')
      return d.toLocaleDateString('pt-BR')
    },
  },
  {
    accessorKey: 'description',
    header: 'DESCRIÇÃO',
    minSize: 300,
  },
  {
    accessorKey: 'category',
    header: 'CATEGORIA',
    size: 160,
  },
  {
    accessorKey: 'amount',
    header: 'VALOR',
    size: 140,
    cell: ({ getValue }) => <AmountCell value={getValue()} />,
  },
]

function CheckingSection() {
  const { selectedMonth } = useMonth()

  const { data, isLoading } = useQuery({
    queryKey: ['analytics-checking', selectedMonth],
    queryFn: () => api.get(`/analytics/checking/?month_str=${selectedMonth}`),
    enabled: !!selectedMonth,
  })

  if (isLoading) {
    return <div className={styles.loading}>Carregando conta corrente...</div>
  }

  if (!data || data.count === 0) {
    return null
  }

  return (
    <div className={styles.section}>
      <h3 className={styles.title}>CONTA CORRENTE</h3>

      {/* Summary */}
      <div className={styles.summary}>
        <span>
          Entradas: <span className={tableStyles.positive}>R$ {fmt(data.total_in)}</span>
        </span>
        <span>
          Saídas: <span className={tableStyles.negative}>R$ {fmt(data.total_out)}</span>
        </span>
        <span>
          Saldo: <span className={data.net >= 0 ? tableStyles.positive : tableStyles.negative}>
            R$ {fmt(data.net)}
          </span>
        </span>
      </div>

      {/* Table */}
      <VaultTable
        columns={checkingColumns}
        data={data.transactions}
        emptyMessage="Sem transações de conta corrente neste mês."
        maxHeight={500}
      />
    </div>
  )
}

export default CheckingSection
