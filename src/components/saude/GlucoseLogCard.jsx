/**
 * GlucoseLogCard — gráfico da automonitorização de glicose capilar (gestação).
 *
 * Plota as três medições diárias — jejum (azul), almoço (âmbar) e jantar (teal) —
 * sobre a faixa-alvo de jejum 65–95 mg/dL e a linha de corte pós-refeição de
 * 140 mg/dL. Pontos acima do alvo ficam vermelhos. Abaixo, resumo por refeição
 * e a lista de picos (≥130) ligando cada valor à refeição que o provocou.
 */
import { useMemo } from 'react'
import {
  ResponsiveContainer, ComposedChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, ReferenceArea, ReferenceLine,
} from 'recharts'
import styles from './saude-widgets.module.css'

const C_JEJUM = '#5b8bc4'    // azul — jejum
const C_ALMOCO = '#c47e3a'   // âmbar — almoço (pós-almoço/tarde)
const C_JANTAR = '#3f8f8a'   // teal — jantar (pós-jantar/noite)
const C_BAND = '#5fa67a'     // verde — faixa-alvo jejum
const C_POSBAND = '#d9a441'  // gold — faixa pós-refeição 120–140 (2h/1h)
const C_OVER = '#b43c3c'     // vermelho — acima do limite

function ddmm(iso) {
  const [, m, d] = iso.split('-')
  return `${d}/${m}`
}

const isJejumOver = (v, ref) => v > ref.max || v < ref.min
const isPosOver = (v, max) => v >= max

// Fábrica de dots: vermelho quando acima do alvo, cor da série caso contrário.
const makeDot = (color, over) => (props) => {
  const { cx, cy, value, index } = props
  if (cx == null || cy == null || value == null) return null
  return (
    <circle
      key={index} cx={cx} cy={cy} r={4}
      fill={over(value) ? C_OVER : color} stroke="#fff" strokeWidth={1.25}
    />
  )
}

function GlucoseTooltip({ active, payload, refs }) {
  const d = active ? payload?.[0]?.payload : null
  if (!d) return null
  const row = (label, color, valor, refeicao, over) => valor == null ? null : (
    <div className={styles.glucoseTooltipPos}>
      <div className={styles.glucoseTooltipRow}>
        <span style={{ color }}>{label}</span>
        <strong style={{ color: over ? C_OVER : 'inherit' }}>{valor} mg/dL</strong>
      </div>
      {refeicao && <div className={styles.glucoseTooltipMeal}>{refeicao}</div>}
    </div>
  )
  return (
    <div className={styles.glucoseTooltip}>
      <div className={styles.glucoseTooltipDate}>{ddmm(d.data)} · {d.dia}º dia</div>
      {row('Jejum', C_JEJUM, d.jejum, null, d.jejum != null && isJejumOver(d.jejum, refs.jejum))}
      {row('Almoço', C_ALMOCO, d.almoco, d.almocoMeal, d.almoco != null && isPosOver(d.almoco, refs.pos1h.max))}
      {row('Jantar', C_JANTAR, d.jantar, d.jantarMeal, d.jantar != null && isPosOver(d.jantar, refs.pos1h.max))}
      {d.nota && <div className={styles.glucoseTooltipNote}>{d.nota}</div>}
    </div>
  )
}

function avg(nums) {
  return nums.length ? Math.round(nums.reduce((s, n) => s + n, 0) / nums.length) : null
}

export default function GlucoseLogCard({ log }) {
  const { chartData, stats, picos } = useMemo(() => {
    if (!log?.dias?.length) return { chartData: [], stats: null, picos: [] }
    const { jejum: refJejum, pos1h } = log.referencias

    const chartData = log.dias.map(d => ({
      dia: d.dia,
      data: d.data,
      label: ddmm(d.data),
      jejum: d.jejum,
      almoco: d.almoco?.valor ?? null,
      almocoMeal: d.almoco?.refeicao ?? null,
      jantar: d.jantar?.valor ?? null,
      jantarMeal: d.jantar?.refeicao ?? null,
      nota: d.nota ?? null,
    }))

    const jejuns = chartData.filter(d => d.jejum != null).map(d => d.jejum)
    const almocos = chartData.filter(d => d.almoco != null).map(d => d.almoco)
    const jantares = chartData.filter(d => d.jantar != null).map(d => d.jantar)
    const inTarget = jejuns.filter(v => v >= refJejum.min && v <= refJejum.max).length
    const allPos = [
      ...log.dias.filter(d => d.almoco).map(d => ({ ...d.almoco, data: d.data, meal: 'Almoço' })),
      ...log.dias.filter(d => d.jantar).map(d => ({ ...d.jantar, data: d.data, meal: 'Jantar' })),
    ]

    const stats = {
      nReg: log.dias.filter(d => d.jejum != null || d.almoco || d.jantar).length,
      jejumMedia: avg(jejuns),
      jejumPctTarget: jejuns.length ? Math.round((inTarget / jejuns.length) * 100) : null,
      almocoMedia: avg(almocos),
      jantarMedia: avg(jantares),
      nPosOver: allPos.filter(p => p.valor >= pos1h.max).length,
    }

    const picos = allPos
      .filter(p => p.valor >= 130)
      .sort((a, b) => b.valor - a.valor)

    return { chartData, stats, picos }
  }, [log])

  if (!log || !chartData.length) return null
  const { jejum: refJejum, pos1h, pos2h } = log.referencias
  const periodo = `${ddmm(log.periodo.inicio)} – ${ddmm(log.periodo.fim)}`

  return (
    <div className={styles.glucoseCard}>
      <div className={styles.mealPlanHeader}>
        <div>
          <div className={styles.widgetLabel}>Glicose capilar · {periodo} · {stats.nReg} dias com registro</div>
          <div className={styles.glucoseSub}>{log.fonte}</div>
        </div>
      </div>

      <div className={styles.glucoseStats}>
        <div className={styles.glucoseStat}>
          <span className={styles.glucoseStatNum} style={{ color: C_JEJUM }}>{stats.jejumMedia ?? '—'}</span>
          <span className={styles.glucoseStatLabel}>jejum médio</span>
        </div>
        <div className={styles.glucoseStat}>
          <span className={styles.glucoseStatNum}>{stats.jejumPctTarget != null ? `${stats.jejumPctTarget}%` : '—'}</span>
          <span className={styles.glucoseStatLabel}>jejum no alvo</span>
        </div>
        <div className={styles.glucoseStat}>
          <span className={styles.glucoseStatNum} style={{ color: C_ALMOCO }}>{stats.almocoMedia ?? '—'}</span>
          <span className={styles.glucoseStatLabel}>almoço médio</span>
        </div>
        <div className={styles.glucoseStat}>
          <span className={styles.glucoseStatNum} style={{ color: C_JANTAR }}>{stats.jantarMedia ?? '—'}</span>
          <span className={styles.glucoseStatLabel}>jantar médio</span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={chartData} margin={{ top: 12, right: 12, bottom: 4, left: -12 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border, #e3e3e3)" vertical={false} />
          {/* faixa-alvo de jejum 65–95 */}
          <ReferenceArea y1={refJejum.min} y2={refJejum.max} fill={C_BAND} fillOpacity={0.12} />
          <ReferenceLine y={refJejum.max} stroke={C_BAND} strokeDasharray="4 4" strokeOpacity={0.7} />
          {/* faixa pós-refeição: 2h < 120, 1h < 140 (hora nem sempre registrada) */}
          <ReferenceArea y1={pos2h.max} y2={pos1h.max} fill={C_POSBAND} fillOpacity={0.12} />
          <ReferenceLine
            y={pos2h.max} stroke={C_POSBAND} strokeDasharray="4 4" strokeOpacity={0.8}
            label={{ value: '120 · 2h', position: 'right', fill: C_POSBAND, fontSize: 9 }}
          />
          <ReferenceLine
            y={pos1h.max} stroke={C_OVER} strokeDasharray="4 4" strokeOpacity={0.6}
            label={{ value: '140 · 1h', position: 'right', fill: C_OVER, fontSize: 9 }}
          />
          <XAxis
            dataKey="label"
            tick={{ fill: 'var(--text-secondary, #6b6660)', fontSize: 10 }}
            axisLine={{ stroke: 'var(--border, #e3e3e3)' }}
            tickLine={false}
            interval="preserveStartEnd"
            minTickGap={12}
          />
          <YAxis
            domain={[60, 180]}
            ticks={[60, 80, 100, 120, 140, 160, 180]}
            tick={{ fill: 'var(--text-secondary, #6b6660)', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            width={36}
          />
          <Tooltip content={<GlucoseTooltip refs={log.referencias} />} />
          <Line
            type="monotone" dataKey="jejum" name="Jejum" stroke={C_JEJUM} strokeWidth={2.5}
            dot={makeDot(C_JEJUM, v => isJejumOver(v, refJejum))} activeDot={{ r: 5 }} connectNulls
          />
          <Line
            type="monotone" dataKey="almoco" name="Almoço" stroke={C_ALMOCO} strokeWidth={2}
            dot={makeDot(C_ALMOCO, v => isPosOver(v, pos1h.max))} activeDot={{ r: 5 }} connectNulls
          />
          <Line
            type="monotone" dataKey="jantar" name="Jantar" stroke={C_JANTAR} strokeWidth={2}
            dot={makeDot(C_JANTAR, v => isPosOver(v, pos1h.max))} activeDot={{ r: 5 }} connectNulls
          />
        </ComposedChart>
      </ResponsiveContainer>

      <div className={styles.glucoseLegend}>
        <span><i style={{ background: C_JEJUM }} /> Jejum</span>
        <span><i style={{ background: C_ALMOCO }} /> Almoço</span>
        <span><i style={{ background: C_JANTAR }} /> Jantar</span>
        <span><i style={{ background: C_BAND, opacity: 0.5 }} /> Alvo jejum {refJejum.min}–{refJejum.max}</span>
        <span><i style={{ background: C_POSBAND, opacity: 0.6 }} /> Faixa pós-refeição {pos2h.max}–{pos1h.max} (2h &lt; {pos2h.max} · 1h &lt; {pos1h.max})</span>
      </div>

      {picos.length > 0 && (
        <div className={styles.glucosePicos}>
          <div className={styles.widgetLabel}>Picos pós-refeição (≥ 130 mg/dL)</div>
          <ul className={styles.glucosePicosList}>
            {picos.map((p, i) => (
              <li key={i} className={styles.glucosePicosItem}>
                <span
                  className={styles.glucosePicosVal}
                  style={{ color: p.valor >= pos1h.max ? C_OVER : C_ALMOCO }}
                >
                  {p.valor}
                </span>
                <span className={styles.glucosePicosDate}>{ddmm(p.data)}</span>
                <span className={styles.glucosePicosMeal}>
                  <strong style={{ color: p.meal === 'Jantar' ? C_JANTAR : C_ALMOCO }}>{p.meal}</strong> · {p.refeicao}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {log.observacoes?.length > 0 && (
        <ul className={styles.mealPlanObs}>
          {log.observacoes.map((o, i) => <li key={i}>{o}</li>)}
        </ul>
      )}
    </div>
  )
}
