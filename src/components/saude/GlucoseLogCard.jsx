/**
 * GlucoseLogCard — gráfico da automonitorização de glicose capilar (gestação).
 *
 * Plota o jejum diário (linha azul) sobre a faixa-alvo 65–95 mg/dL e o maior
 * valor pós-refeição do dia (linha âmbar), com a linha de corte de 140 mg/dL.
 * Abaixo, resumo de estatísticas e a lista de picos pós-refeição (≥130) ligando
 * cada pico à refeição que o provocou.
 */
import { useMemo } from 'react'
import {
  ResponsiveContainer, ComposedChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, ReferenceArea, ReferenceLine,
} from 'recharts'
import styles from './saude-widgets.module.css'

const C_JEJUM = '#5b8bc4'   // azul — jejum
const C_POS = '#c47e3a'     // âmbar — pós-refeição
const C_BAND = '#5fa67a'    // verde — faixa-alvo jejum
const C_OVER = '#b43c3c'    // vermelho — acima do limite

function ddmm(iso) {
  const [, m, d] = iso.split('-')
  return `${d}/${m}`
}

function GlucoseTooltip({ active, payload }) {
  const d = active ? payload?.[0]?.payload : null
  if (!d) return null
  const pos = d.pos ?? []
  return (
    <div className={styles.glucoseTooltip}>
      <div className={styles.glucoseTooltipDate}>{ddmm(d.data)} · {d.dia}º dia</div>
      {d.jejum != null && (
        <div className={styles.glucoseTooltipRow}>
          <span style={{ color: C_JEJUM }}>Jejum</span>
          <strong style={{ color: d.jejumOver ? C_OVER : 'inherit' }}>{d.jejum} mg/dL</strong>
        </div>
      )}
      {pos.map((p, i) => (
        <div key={i} className={styles.glucoseTooltipPos}>
          <div className={styles.glucoseTooltipRow}>
            <span style={{ color: C_POS }}>Pós-refeição</span>
            <strong style={{ color: p.valor >= 140 ? C_OVER : 'inherit' }}>{p.valor} mg/dL</strong>
          </div>
          <div className={styles.glucoseTooltipMeal}>{p.refeicao}</div>
        </div>
      ))}
      {d.nota && <div className={styles.glucoseTooltipNote}>{d.nota}</div>}
    </div>
  )
}

function JejumDot({ cx, cy, payload }) {
  if (cx == null || cy == null || payload.jejum == null) return null
  const over = payload.jejumOver
  return <circle cx={cx} cy={cy} r={3.5} fill={over ? C_OVER : C_JEJUM} stroke="#fff" strokeWidth={1} />
}

function PosDot({ cx, cy, payload }) {
  if (cx == null || cy == null || payload.posMax == null) return null
  const over = payload.posMax >= 140
  return <circle cx={cx} cy={cy} r={3.5} fill={over ? C_OVER : C_POS} stroke="#fff" strokeWidth={1} />
}

export default function GlucoseLogCard({ log }) {
  const { chartData, stats, picos } = useMemo(() => {
    if (!log?.dias?.length) return { chartData: [], stats: null, picos: [] }
    const { jejum: refJejum } = log.referencias

    const chartData = log.dias.map(d => {
      const posMax = d.pos.length ? Math.max(...d.pos.map(p => p.valor)) : null
      return {
        ...d,
        label: ddmm(d.data),
        posMax,
        jejumOver: d.jejum != null && (d.jejum > refJejum.max || d.jejum < refJejum.min),
      }
    })

    const jejuns = chartData.filter(d => d.jejum != null)
    const hasJejum = jejuns.length > 0
    const inTarget = jejuns.filter(d => d.jejum >= refJejum.min && d.jejum <= refJejum.max).length
    const allPos = log.dias.flatMap(d => d.pos.map(p => ({ ...p, data: d.data })))
    const stats = {
      nReg: log.dias.filter(d => d.jejum != null || d.pos.length > 0).length,
      jejumMedia: hasJejum ? Math.round(jejuns.reduce((s, d) => s + d.jejum, 0) / jejuns.length) : null,
      jejumMin: hasJejum ? Math.min(...jejuns.map(d => d.jejum)) : null,
      jejumMax: hasJejum ? Math.max(...jejuns.map(d => d.jejum)) : null,
      jejumPctTarget: hasJejum ? Math.round((inTarget / jejuns.length) * 100) : null,
      nPos: allPos.length,
      nPosOver: allPos.filter(p => p.valor >= log.referencias.pos1h.max).length,
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
          <span className={styles.glucoseStatNum}>{stats.jejumMedia ?? '—'}</span>
          <span className={styles.glucoseStatLabel}>jejum médio</span>
        </div>
        <div className={styles.glucoseStat}>
          <span className={styles.glucoseStatNum}>
            {stats.jejumMin != null ? `${stats.jejumMin}–${stats.jejumMax}` : '—'}
          </span>
          <span className={styles.glucoseStatLabel}>faixa jejum</span>
        </div>
        <div className={styles.glucoseStat}>
          <span className={styles.glucoseStatNum}>{stats.jejumPctTarget != null ? `${stats.jejumPctTarget}%` : '—'}</span>
          <span className={styles.glucoseStatLabel}>jejum no alvo</span>
        </div>
        <div className={styles.glucoseStat}>
          <span className={styles.glucoseStatNum} style={stats.nPosOver ? { color: C_OVER } : undefined}>
            {stats.nPosOver}
          </span>
          <span className={styles.glucoseStatLabel}>pós ≥ 140 ({stats.nPos} medições)</span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={chartData} margin={{ top: 12, right: 12, bottom: 4, left: -12 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border, #e3e3e3)" vertical={false} />
          {/* faixa-alvo de jejum 65–95 */}
          <ReferenceArea y1={refJejum.min} y2={refJejum.max} fill={C_BAND} fillOpacity={0.12} />
          <ReferenceLine y={refJejum.max} stroke={C_BAND} strokeDasharray="4 4" strokeOpacity={0.7} />
          {/* limite pós-refeição 1h */}
          <ReferenceLine
            y={pos1h.max} stroke={C_OVER} strokeDasharray="4 4" strokeOpacity={0.6}
            label={{ value: '140', position: 'right', fill: C_OVER, fontSize: 10 }}
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
          <Tooltip content={<GlucoseTooltip />} />
          <Line
            type="monotone" dataKey="jejum" name="Jejum" stroke={C_JEJUM} strokeWidth={2}
            dot={<JejumDot />} activeDot={{ r: 5 }}
          />
          <Line
            type="monotone" dataKey="posMax" name="Pós-refeição (maior do dia)" stroke={C_POS}
            strokeWidth={1.5} strokeDasharray="2 3" dot={<PosDot />} activeDot={{ r: 5 }}
          />
        </ComposedChart>
      </ResponsiveContainer>

      <div className={styles.glucoseLegend}>
        <span><i style={{ background: C_JEJUM }} /> Jejum</span>
        <span><i style={{ background: C_POS }} /> Pós-refeição (maior do dia)</span>
        <span><i style={{ background: C_BAND, opacity: 0.5 }} /> {refJejum.label}</span>
        <span><i style={{ background: C_OVER, opacity: 0.6 }} /> Limite pós: &lt; {pos1h.max} (1h) / &lt; {pos2h.max} (2h)</span>
      </div>

      {picos.length > 0 && (
        <div className={styles.glucosePicos}>
          <div className={styles.widgetLabel}>Picos pós-refeição (≥ 130 mg/dL)</div>
          <ul className={styles.glucosePicosList}>
            {picos.map((p, i) => (
              <li key={i} className={styles.glucosePicosItem}>
                <span
                  className={styles.glucosePicosVal}
                  style={{ color: p.valor >= pos1h.max ? C_OVER : C_POS }}
                >
                  {p.valor}
                </span>
                <span className={styles.glucosePicosDate}>{ddmm(p.data)}</span>
                <span className={styles.glucosePicosMeal}>{p.refeicao}</span>
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
