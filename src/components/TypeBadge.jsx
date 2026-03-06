import styles from './TypeBadge.module.css'

const TYPE_MAP = {
  Fixo: { label: 'Fixo', cls: styles.fixo },
  Entrada: { label: 'Entrada', cls: styles.entrada },
  Investimento: { label: 'Invest.', cls: styles.invest },
  Variavel: { label: 'Variavel', cls: styles.variavel },
}

function TypeBadge({ value }) {
  const t = TYPE_MAP[value] || { label: value || '—', cls: '' }
  return <span className={`${styles.badge} ${t.cls}`}>{t.label}</span>
}

export default TypeBadge
