/**
 * ShoppingListCard — lista semanal de compras derivada do plano alimentar.
 * Categorias colapsáveis com itens (quantidade + uso), alertas de segurança,
 * estimativa de custo e checklist toggle.
 */
import { useState } from 'react'
import styles from './saude-widgets.module.css'

function CategoryCard({ cat }) {
  const [open, setOpen] = useState(true)
  return (
    <div className={styles.shopCategory}>
      <button
        type="button"
        className={styles.shopCategoryHeader}
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
      >
        <span className={styles.shopCategoryTitle}>{cat.titulo}</span>
        <span className={styles.shopCategoryCount}>{cat.itens.length}</span>
        <span className={styles.shopCategoryToggle}>{open ? '−' : '+'}</span>
      </button>
      {open && (
        <div className={styles.shopCategoryBody}>
          {cat.alerta && (
            <div className={cat.alerta.tipo === 'danger' ? styles.shopAlertDanger : styles.shopAlertInfo}>
              <span className={styles.shopAlertLabel}>
                {cat.alerta.tipo === 'danger' ? 'Atenção' : 'Nota'}
              </span>
              {cat.alerta.texto}
            </div>
          )}
          {cat.tip && (
            <div className={styles.shopAlertInfo}>
              <span className={styles.shopAlertLabel}>Dica</span>
              {cat.tip}
            </div>
          )}
          <ul className={styles.shopItemList}>
            {cat.itens.map((it, i) => (
              <li key={i} className={styles.shopItem}>
                <label className={styles.shopItemLabel}>
                  <input type="checkbox" className={styles.shopItemCheck} />
                  <span className={styles.shopItemName}>{it.item}</span>
                </label>
                <span className={styles.shopItemQty}>{it.qty}</span>
                <span className={styles.shopItemUse}>{it.uso}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export default function ShoppingListCard({ list }) {
  if (!list) return null
  const dataFmt = list.base_prescricao.split('-').reverse().join('/')
  return (
    <div className={styles.shopCard}>
      <div className={styles.shopHeader}>
        <div className={styles.widgetLabel}>
          Lista de compras · {list.periodo_dias} dias · base prescrição {dataFmt}
        </div>
        <div className={styles.shopCost}>
          Estimativa: R$ {list.custo_estimado_min} – {list.custo_estimado_max}/semana
        </div>
      </div>

      <div className={styles.shopGrid}>
        {list.categorias.map(c => <CategoryCard key={c.id} cat={c} />)}
      </div>

      <details className={styles.shopDetails}>
        <summary>Custo detalhado por categoria</summary>
        <table className={styles.shopCostTable}>
          <tbody>
            {list.custo_breakdown.map((c, i) => (
              <tr key={i}><td>{c.categoria}</td><td>{c.faixa}</td></tr>
            ))}
            <tr className={styles.shopCostTotal}>
              <td><strong>Total</strong></td>
              <td><strong>R$ {list.custo_estimado_min} – {list.custo_estimado_max}/semana</strong></td>
            </tr>
          </tbody>
        </table>
        <p className={styles.shopEconomyTip}>💡 {list.dica_economia}</p>
      </details>

      <details className={styles.shopDetails}>
        <summary>Reposição meio de semana</summary>
        <ul className={styles.shopReposicao}>
          {list.reposicao_meio_semana.map((r, i) => <li key={i}>{r}</li>)}
        </ul>
      </details>
    </div>
  )
}
