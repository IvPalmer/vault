/**
 * MealPlanCard — Plano alimentar prescrito (gestação).
 * Lista refeições em ordem cronológica, com itens + substituições colapsáveis.
 */
import { useState } from 'react'
import styles from './saude-widgets.module.css'

function MealItem({ item }) {
  const [open, setOpen] = useState(false)
  const hasSubs = item.substituicoes && item.substituicoes.length > 0
  return (
    <li className={styles.mealItem}>
      <div className={styles.mealItemMain}>
        <span className={styles.mealFood}>{item.alimento}</span>
        <span className={styles.mealQty}>{item.quantidade}</span>
        {hasSubs && (
          <button
            type="button"
            className={styles.mealSubToggle}
            onClick={() => setOpen(o => !o)}
            aria-expanded={open}
          >
            {open ? '−' : '+'} {item.substituicoes.length} subs
          </button>
        )}
      </div>
      {open && hasSubs && (
        <ul className={styles.mealSubList}>
          {item.substituicoes.map((s, i) => <li key={i}>{s}</li>)}
        </ul>
      )}
    </li>
  )
}

export default function MealPlanCard({ plan }) {
  if (!plan) return null
  const dataFmt = plan.data_prescricao.split('-').reverse().join('/')

  return (
    <div className={styles.mealPlanCard}>
      <div className={styles.mealPlanHeader}>
        <div>
          <div className={styles.widgetLabel}>Plano alimentar · prescrito {dataFmt} · IG {plan.ig_na_prescricao}</div>
          <div className={styles.mealPlanNutri}>
            {plan.profissional.nome} · {plan.profissional.conselho} · {plan.profissional.instituto}
          </div>
          <div className={styles.mealPlanNutriContact}>
            {plan.profissional.endereco} · {plan.profissional.telefone} · convênio: {plan.profissional.convenio}
          </div>
        </div>
      </div>

      {plan.observacoes && plan.observacoes.length > 0 && (
        <ul className={styles.mealPlanObs}>
          {plan.observacoes.map((o, i) => <li key={i}>{o}</li>)}
        </ul>
      )}

      <div className={styles.mealGrid}>
        {plan.refeicoes.map(r => (
          <div key={r.id} className={styles.mealCard}>
            <div className={styles.mealHeader}>
              <span className={styles.mealTime}>{r.horario}</span>
              <span className={styles.mealTitle}>{r.titulo}</span>
            </div>
            <ul className={styles.mealList}>
              {r.itens.map((item, i) => <MealItem key={i} item={item} />)}
            </ul>
          </div>
        ))}
      </div>
    </div>
  )
}
