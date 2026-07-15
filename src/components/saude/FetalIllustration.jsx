/**
 * FetalIllustration — progressive SVG drawings of the embryo/fetus by week.
 *
 * Five distinct stages, each with its own anatomy. A subtle heartbeat pulse
 * runs in stages where a heart is visible (week >= 5) so the figure feels
 * alive instead of frozen. The previous single-shape illustration scaled
 * monotonously and never actually changed between weeks 4 and 9.
 *
 * Stages (clinical correspondence):
 *   - 4–5w  : blastocyst/early embryo, no recognizable form
 *   - 6–7w  : C-shaped embryo with arm/leg buds, primitive heart
 *   - 8–9w  : embryo with paddle limbs, larger head, eye spots
 *   - 10–13w: early fetus — distinct head, limbs, beginning fingers
 *   - 14–19w: classic curled fetus profile with fingers/toes
 *   - 20–27w: detailed fetus, more proportional
 *   - 28+w  : late fetus, mature proportions
 */
import styles from './saude-widgets.module.css'

function StageBlastocyst() {
  // 4–5w: tiny cluster, no recognizable shape
  return (
    <g>
      <circle cx="120" cy="105" r="9" fill="url(#fetusGrad)" stroke="rgba(120, 60, 20, 0.45)" strokeWidth="1.2" />
      <circle cx="124" cy="101" r="3.5" fill="rgba(255,255,255,0.4)" />
    </g>
  )
}

function StageEmbryoEarly() {
  // 6–7w: C-shaped embryo with limb buds + heart pulse
  return (
    <g>
      {/* Body (C-curve) */}
      <path
        d="M 105 80 Q 90 95, 95 115 Q 105 135, 128 132 Q 145 125, 142 105 Q 138 88, 120 82 Z"
        fill="url(#fetusGrad)"
        stroke="rgba(120, 60, 20, 0.5)"
        strokeWidth="1.4"
      />
      {/* Head bulge */}
      <circle cx="118" cy="92" r="11" fill="url(#fetusGrad)" stroke="rgba(120, 60, 20, 0.45)" strokeWidth="1.2" />
      {/* Tail / sacral region */}
      <path d="M 102 120 Q 96 130, 105 138" stroke="rgba(120, 60, 20, 0.5)" strokeWidth="1.3" fill="none" strokeLinecap="round" />
      {/* Arm buds */}
      <circle cx="108" cy="108" r="3" fill="url(#fetusGrad)" stroke="rgba(120, 60, 20, 0.4)" strokeWidth="1" />
      {/* Leg buds */}
      <circle cx="130" cy="125" r="3.2" fill="url(#fetusGrad)" stroke="rgba(120, 60, 20, 0.4)" strokeWidth="1" />
      {/* Heart pulse dot */}
      <circle cx="118" cy="110" r="2.5" fill="#c0392b" opacity="0.85">
        <animate attributeName="r" values="1.8;3.2;1.8" dur="1.1s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.7;1;0.7" dur="1.1s" repeatCount="indefinite" />
      </circle>
    </g>
  )
}

function StageEmbryoLate() {
  // 8–9w: more distinct shape, paddle limbs, eye spots
  return (
    <g>
      {/* Head — larger now */}
      <ellipse cx="116" cy="88" rx="20" ry="22" fill="url(#fetusGrad)" stroke="rgba(120, 60, 20, 0.5)" strokeWidth="1.4" />
      {/* Body (curled C) */}
      <path
        d="M 100 105 Q 86 125, 100 145 Q 122 158, 142 142 Q 152 122, 138 102 Q 122 96, 108 100 Z"
        fill="url(#fetusGrad)"
        stroke="rgba(120, 60, 20, 0.5)"
        strokeWidth="1.4"
      />
      {/* Eye spot */}
      <circle cx="108" cy="86" r="1.8" fill="rgba(60, 30, 10, 0.7)" />
      {/* Arm paddle */}
      <path d="M 100 115 Q 88 122, 92 135 Q 98 138, 102 130" fill="url(#fetusGrad)" stroke="rgba(120, 60, 20, 0.45)" strokeWidth="1.2" />
      {/* Leg paddle */}
      <path d="M 135 150 Q 122 162, 108 158 Q 104 152, 112 148" fill="url(#fetusGrad)" stroke="rgba(120, 60, 20, 0.45)" strokeWidth="1.2" />
      {/* Heart pulse */}
      <circle cx="118" cy="118" r="2.8" fill="#c0392b" opacity="0.7">
        <animate attributeName="r" values="2;3.5;2" dur="1s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.55;0.9;0.55" dur="1s" repeatCount="indefinite" />
      </circle>
    </g>
  )
}

function StageFetusEarly() {
  // 10–13w: recognizable fetus, distinct limbs
  return (
    <g>
      {/* Head */}
      <ellipse cx="120" cy="80" rx="28" ry="30" fill="url(#fetusGrad)" stroke="rgba(120, 60, 20, 0.5)" strokeWidth="1.5" />
      {/* Body */}
      <path
        d="M 102 105 Q 86 130, 100 152 Q 125 168, 148 150 Q 158 128, 144 105 Q 124 96, 108 100 Z"
        fill="url(#fetusGrad)"
        stroke="rgba(120, 60, 20, 0.5)"
        strokeWidth="1.5"
      />
      {/* Eye */}
      <circle cx="110" cy="76" r="2.2" fill="rgba(60, 30, 10, 0.75)" />
      {/* Arm */}
      <path d="M 100 118 Q 84 128, 88 145 Q 94 152, 102 140 Q 105 130, 102 122 Z" fill="url(#fetusGrad)" stroke="rgba(120, 60, 20, 0.45)" strokeWidth="1.2" />
      {/* Finger hint */}
      <path d="M 87 144 L 84 148 M 90 146 L 88 150 M 93 147 L 91 152" stroke="rgba(120, 60, 20, 0.5)" strokeWidth="1" strokeLinecap="round" />
      {/* Leg curled */}
      <path d="M 140 155 Q 125 172, 105 162 Q 100 155, 110 152 Q 128 148, 138 152 Z" fill="url(#fetusGrad)" stroke="rgba(120, 60, 20, 0.45)" strokeWidth="1.2" />
      {/* Heart */}
      <circle cx="122" cy="118" r="3" fill="#c0392b" opacity="0.6">
        <animate attributeName="r" values="2.3;3.8;2.3" dur="0.95s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.4;0.8;0.4" dur="0.95s" repeatCount="indefinite" />
      </circle>
    </g>
  )
}

function StageFetusMid() {
  // 14–19w: classic profile, proportional, more detail
  return (
    <g>
      {/* Head */}
      <ellipse cx="120" cy="76" rx="32" ry="34" fill="url(#fetusGrad)" stroke="rgba(120, 60, 20, 0.5)" strokeWidth="1.5" />
      {/* Body */}
      <path
        d="M 102 100 Q 82 132, 102 156 Q 130 172, 152 154 Q 162 128, 146 102 Q 124 92, 108 96 Z"
        fill="url(#fetusGrad)"
        stroke="rgba(120, 60, 20, 0.5)"
        strokeWidth="1.5"
      />
      {/* Closed eye */}
      <path d="M 106 75 Q 112 73, 115 76" stroke="rgba(60, 30, 10, 0.75)" strokeWidth="1.4" fill="none" strokeLinecap="round" />
      {/* Nose hint */}
      <path d="M 100 82 Q 96 86, 100 90" stroke="rgba(120, 60, 20, 0.5)" strokeWidth="1" fill="none" strokeLinecap="round" />
      {/* Mouth */}
      <path d="M 100 95 Q 104 97, 108 95" stroke="rgba(120, 60, 20, 0.5)" strokeWidth="1" fill="none" strokeLinecap="round" />
      {/* Arm with fingers */}
      <path d="M 100 116 Q 82 128, 86 146 Q 94 154, 104 142" fill="url(#fetusGrad)" stroke="rgba(120, 60, 20, 0.45)" strokeWidth="1.3" />
      <path d="M 85 145 L 80 150 M 88 148 L 84 153 M 91 150 L 87 156 M 94 151 L 91 157" stroke="rgba(120, 60, 20, 0.55)" strokeWidth="1" strokeLinecap="round" />
      {/* Leg with toes */}
      <path d="M 142 158 Q 125 176, 100 168 Q 95 158, 110 155 Q 130 152, 140 154 Z" fill="url(#fetusGrad)" stroke="rgba(120, 60, 20, 0.45)" strokeWidth="1.3" />
      <path d="M 100 168 L 96 172 M 102 170 L 99 175 M 105 171 L 103 176" stroke="rgba(120, 60, 20, 0.55)" strokeWidth="1" strokeLinecap="round" />
      {/* Umbilical */}
      <path d="M 130 110 Q 145 96, 140 80" stroke="rgba(180, 90, 40, 0.5)" strokeWidth="2" fill="none" strokeLinecap="round" strokeDasharray="2 3" />
      {/* Heart */}
      <circle cx="124" cy="116" r="3.2" fill="#c0392b" opacity="0.55">
        <animate attributeName="r" values="2.6;4;2.6" dur="0.85s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.35;0.7;0.35" dur="0.85s" repeatCount="indefinite" />
      </circle>
    </g>
  )
}

function StageFetusLate() {
  // 20–27w: bigger, fingernails, hair hint
  return (
    <g>
      {/* Head */}
      <ellipse cx="118" cy="74" rx="36" ry="38" fill="url(#fetusGrad)" stroke="rgba(120, 60, 20, 0.5)" strokeWidth="1.5" />
      {/* Hair lanugo */}
      <path d="M 86 60 Q 110 48, 145 56" stroke="rgba(80, 40, 15, 0.4)" strokeWidth="1" fill="none" strokeDasharray="1 2" />
      {/* Body */}
      <path
        d="M 96 100 Q 76 134, 100 162 Q 132 178, 158 160 Q 168 132, 150 102 Q 124 90, 108 94 Z"
        fill="url(#fetusGrad)"
        stroke="rgba(120, 60, 20, 0.5)"
        strokeWidth="1.5"
      />
      {/* Eye (closed lid) */}
      <path d="M 103 72 Q 110 70, 115 73" stroke="rgba(60, 30, 10, 0.75)" strokeWidth="1.5" fill="none" strokeLinecap="round" />
      {/* Eyelash hint */}
      <path d="M 106 70 L 105 68 M 109 69 L 108 67 M 112 70 L 112 68" stroke="rgba(80, 40, 15, 0.5)" strokeWidth="0.8" />
      {/* Nose */}
      <path d="M 97 82 Q 92 88, 97 94" stroke="rgba(120, 60, 20, 0.55)" strokeWidth="1.2" fill="none" strokeLinecap="round" />
      {/* Mouth */}
      <path d="M 98 99 Q 104 102, 110 99" stroke="rgba(120, 60, 20, 0.55)" strokeWidth="1.2" fill="none" strokeLinecap="round" />
      {/* Arm with fingers */}
      <path d="M 96 118 Q 76 132, 82 152 Q 92 158, 104 144" fill="url(#fetusGrad)" stroke="rgba(120, 60, 20, 0.45)" strokeWidth="1.3" />
      {/* Leg with toes */}
      <path d="M 146 162 Q 128 180, 98 172 Q 92 160, 110 158 Q 132 154, 144 156 Z" fill="url(#fetusGrad)" stroke="rgba(120, 60, 20, 0.45)" strokeWidth="1.3" />
      {/* Umbilical */}
      <path d="M 128 112 Q 148 96, 145 78" stroke="rgba(180, 90, 40, 0.5)" strokeWidth="2.2" fill="none" strokeLinecap="round" strokeDasharray="2 3" />
      {/* Heart */}
      <circle cx="124" cy="116" r="3.4" fill="#c0392b" opacity="0.5">
        <animate attributeName="r" values="2.8;4.2;2.8" dur="0.75s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.3;0.65;0.3" dur="0.75s" repeatCount="indefinite" />
      </circle>
    </g>
  )
}

function StageFetusTerm() {
  // 28+w: mature, plump, ready
  return (
    <g>
      {/* Head */}
      <ellipse cx="116" cy="72" rx="40" ry="42" fill="url(#fetusGrad)" stroke="rgba(120, 60, 20, 0.5)" strokeWidth="1.5" />
      {/* Hair */}
      <path d="M 80 55 Q 110 38, 152 50 Q 148 45, 130 42 Q 110 40, 95 45 Q 82 50, 80 55 Z" fill="rgba(80, 40, 15, 0.35)" />
      {/* Body */}
      <path
        d="M 92 100 Q 70 138, 98 170 Q 134 188, 164 168 Q 176 134, 154 102 Q 124 88, 106 92 Z"
        fill="url(#fetusGrad)"
        stroke="rgba(120, 60, 20, 0.5)"
        strokeWidth="1.5"
      />
      {/* Eye */}
      <path d="M 100 70 Q 108 67, 116 70" stroke="rgba(60, 30, 10, 0.75)" strokeWidth="1.6" fill="none" strokeLinecap="round" />
      {/* Nose */}
      <path d="M 94 80 Q 88 88, 94 94" stroke="rgba(120, 60, 20, 0.55)" strokeWidth="1.4" fill="none" strokeLinecap="round" />
      {/* Mouth */}
      <path d="M 95 100 Q 102 104, 110 100" stroke="rgba(120, 60, 20, 0.55)" strokeWidth="1.4" fill="none" strokeLinecap="round" />
      {/* Ear hint */}
      <path d="M 78 75 Q 74 80, 78 88" stroke="rgba(120, 60, 20, 0.5)" strokeWidth="1.3" fill="none" strokeLinecap="round" />
      {/* Arm */}
      <path d="M 92 120 Q 72 134, 78 156 Q 90 162, 102 146" fill="url(#fetusGrad)" stroke="rgba(120, 60, 20, 0.45)" strokeWidth="1.4" />
      {/* Leg */}
      <path d="M 152 170 Q 132 190, 96 180 Q 88 164, 108 162 Q 134 158, 148 160 Z" fill="url(#fetusGrad)" stroke="rgba(120, 60, 20, 0.45)" strokeWidth="1.4" />
      {/* Umbilical */}
      <path d="M 130 114 Q 152 96, 150 76" stroke="rgba(180, 90, 40, 0.5)" strokeWidth="2.4" fill="none" strokeLinecap="round" strokeDasharray="2 3" />
      {/* Heart */}
      <circle cx="124" cy="118" r="3.6" fill="#c0392b" opacity="0.45">
        <animate attributeName="r" values="3;4.4;3" dur="0.65s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.25;0.6;0.25" dur="0.65s" repeatCount="indefinite" />
      </circle>
    </g>
  )
}

export default function FetalIllustration({ week }) {
  let Stage = StageBlastocyst
  if (week >= 28) Stage = StageFetusTerm
  else if (week >= 20) Stage = StageFetusLate
  else if (week >= 14) Stage = StageFetusMid
  else if (week >= 10) Stage = StageFetusEarly
  else if (week >= 8) Stage = StageEmbryoLate
  else if (week >= 6) Stage = StageEmbryoEarly

  // Subtle micro-scale tied to decimal week so the illustration responds to
  // changes inside a stage (e.g. 8s+3d vs 8s+5d won't be visually identical).
  const microScale = 0.92 + Math.min(0.16, (week % 2) * 0.08)

  return (
    <svg viewBox="0 0 240 200" className={styles.fetalSvg} aria-label={`Feto em aproximadamente ${Math.floor(week)} semanas`}>
      <defs>
        <radialGradient id="amnioGrad" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="rgba(196,126,58,0.05)" />
          <stop offset="100%" stopColor="rgba(196,126,58,0.18)" />
        </radialGradient>
        <linearGradient id="fetusGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#e8b48a" />
          <stop offset="100%" stopColor="#c47e3a" />
        </linearGradient>
      </defs>

      {/* Amniotic sac */}
      <ellipse cx="120" cy="100" rx="105" ry="88" fill="url(#amnioGrad)" stroke="rgba(196,126,58,0.3)" strokeWidth="1" strokeDasharray="3 4" />

      {/* Umbilical cord — kept for all stages where the embryo is large enough */}
      {week >= 6 && week < 10 && (
        <path d="M 120 12 Q 100 50, 115 80 T 118 100" stroke="rgba(180, 90, 40, 0.4)" strokeWidth="2" fill="none" strokeLinecap="round" />
      )}

      <g transform={`translate(120, 105) scale(${microScale}) translate(-120, -105)`}>
        <Stage />
      </g>
    </svg>
  )
}
