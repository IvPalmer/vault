/**
 * HipModel3D — interactive 3D viewer of Palmer's segmented hip CT.
 * Ported from health/visualizations/viewer_3d_quadril.html (Three.js r169)
 * into a contained React component. STL meshes live in /public/models/hip/.
 */
import { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js'
import styles from './HipModel3D.module.css'

const MODEL_DEFS = [
  { key: 'femur_esquerdo',          label: 'Fêmur Esquerdo',          color: 0xffd700, opacity: 0.6,  group: 'bones' },
  { key: 'femur_direito',           label: 'Fêmur Direito',           color: 0x87ceeb, opacity: 0.6,  group: 'bones' },
  { key: 'pelve_esquerda',          label: 'Pelve Esquerda',          color: 0xf08080, opacity: 0.2,  group: 'bones' },
  { key: 'pelve_direita',           label: 'Pelve Direita',           color: 0xadd8e6, opacity: 0.2,  group: 'bones' },
  { key: 'sacro',                   label: 'Sacro',                   color: 0xdeb887, opacity: 0.2,  group: 'bones' },
  { key: 'cabeca_femoral_esquerda', label: 'Cabeça Femoral Esq. (CAM)', color: 0xff4444, opacity: 0.55, group: 'bones' },
  { key: 'cabeca_femoral_direita',  label: 'Cabeça Femoral Dir.',     color: 0x4444ff, opacity: 0.55, group: 'bones' },
  { key: 'gluteo_minimo_esquerdo',  label: 'Glúteo Mínimo Esq.',      color: 0xff69b4, opacity: 0.5,  group: 'muscles' },
  { key: 'gluteo_medio_esquerdo',   label: 'Glúteo Médio Esq.',       color: 0xfa8072, opacity: 0.5,  group: 'muscles' },
]

const VIEWS = [
  { id: 'anterior', label: 'Anterior' },
  { id: 'posterior', label: 'Posterior' },
  { id: 'left', label: 'Lat. Esq.' },
  { id: 'right', label: 'Lat. Dir.' },
  { id: 'superior', label: 'Superior' },
  { id: 'reset', label: 'Reset' },
]

const hex = (c) => '#' + c.toString(16).padStart(6, '0')

export default function HipModel3D() {
  const mountRef = useRef(null)
  // mutable engine state kept off React to survive re-renders
  const eng = useRef({
    scene: null, camera: null, renderer: null, controls: null,
    meshes: {}, base: {}, center: new THREE.Vector3(), radius: 200,
    scales: { bones: 1, muscles: 1 }, frame: 0, viewFrame: 0, observer: null,
    vis: Object.fromEntries(MODEL_DEFS.map((d) => [d.key, true])),
  })
  const [visible, setVisible] = useState(() =>
    Object.fromEntries(MODEL_DEFS.map((d) => [d.key, true])))
  const [opacity, setOpacity] = useState({ bones: 100, muscles: 100 })
  const [loaded, setLoaded] = useState(0)

  useEffect(() => {
    const mount = mountRef.current
    if (!mount) return
    const e = eng.current
    let alive = true
    const w = mount.clientWidth || 600
    const h = mount.clientHeight || 520

    const scene = new THREE.Scene()
    scene.background = new THREE.Color(0x0a0a0f)
    scene.fog = new THREE.FogExp2(0x0a0a0f, 0.0008)

    const camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 5000)
    camera.position.set(0, 0, 500)

    const renderer = new THREE.WebGLRenderer({ antialias: true })
    renderer.setSize(w, h)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure = 1.1
    mount.appendChild(renderer.domElement)

    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = 0.06
    controls.rotateSpeed = 0.7
    controls.minDistance = 50
    controls.maxDistance = 2000

    scene.add(new THREE.AmbientLight(0x404060, 1.2))
    scene.add(new THREE.HemisphereLight(0x8899bb, 0x223344, 0.8))
    const d1 = new THREE.DirectionalLight(0xffffff, 1.5); d1.position.set(200, 300, 200); scene.add(d1)
    const d2 = new THREE.DirectionalLight(0x8899cc, 0.6); d2.position.set(-200, 100, -100); scene.add(d2)
    const d3 = new THREE.DirectionalLight(0x445566, 0.4); d3.position.set(0, -200, 150); scene.add(d3)
    const rim = new THREE.DirectionalLight(0x334466, 0.3); rim.position.set(0, 0, -300); scene.add(rim)

    Object.assign(e, { scene, camera, renderer, controls, meshes: {}, base: {} })

    const loader = new STLLoader()
    let settled = 0
    const frameModel = () => {
      const box = new THREE.Box3()
      Object.values(e.meshes).forEach((m) => {
        m.geometry.computeBoundingBox()
        box.union(m.geometry.boundingBox.clone().applyMatrix4(m.matrixWorld))
      })
      if (box.isEmpty()) return
      const center = new THREE.Vector3(); box.getCenter(center)
      const size = new THREE.Vector3(); box.getSize(size)
      e.radius = size.length() / 2
      e.center.copy(center)
      controls.target.copy(center)
      camera.position.set(center.x, center.y, center.z + e.radius * 2.5)
      camera.lookAt(center)
      controls.update()
      d1.position.set(center.x + e.radius, center.y + e.radius * 1.5, center.z + e.radius)
      d1.target.position.copy(center); scene.add(d1.target)
    }

    const settle = () => {
      settled += 1
      setLoaded(settled)
      if (settled === MODEL_DEFS.length && alive) frameModel()
    }

    MODEL_DEFS.forEach((def) => {
      loader.load(
        `/models/hip/${def.key}.stl`,
        (geometry) => {
          if (!alive) { geometry.dispose(); return }
          geometry.computeVertexNormals()
          const op = Math.min(1, Math.max(0.02, def.opacity * (e.scales[def.group] ?? 1)))
          const material = new THREE.MeshPhysicalMaterial({
            color: def.color, transparent: true, opacity: op,
            roughness: 0.45, metalness: 0.05, clearcoat: 0.15, clearcoatRoughness: 0.4,
            side: THREE.DoubleSide, depthWrite: op > 0.4,
            polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1,
          })
          const mesh = new THREE.Mesh(geometry, material)
          mesh.visible = e.vis[def.key] !== false
          e.meshes[def.key] = mesh
          e.base[def.key] = def.opacity
          scene.add(mesh)
          settle()
        },
        undefined,
        (err) => { if (!alive) return; console.warn(`hip model ${def.key} failed`, err); settle() },
      )
    })

    const render = () => { e.frame = requestAnimationFrame(render); controls.update(); renderer.render(scene, camera) }
    render()

    const ro = new ResizeObserver(() => {
      const nw = mount.clientWidth, nh = mount.clientHeight
      if (!nw || !nh) return
      camera.aspect = nw / nh; camera.updateProjectionMatrix(); renderer.setSize(nw, nh)
    })
    ro.observe(mount)
    e.observer = ro

    return () => {
      alive = false
      cancelAnimationFrame(e.frame)
      if (e.viewFrame) cancelAnimationFrame(e.viewFrame)
      ro.disconnect()
      controls.dispose()
      Object.values(e.meshes).forEach((m) => { m.geometry.dispose(); m.material.dispose() })
      e.meshes = {}
      renderer.dispose()
      if (renderer.domElement.parentNode === mount) mount.removeChild(renderer.domElement)
    }
  }, [])

  const toggle = (key) => {
    setVisible((v) => {
      const next = !v[key]
      eng.current.vis[key] = next
      const m = eng.current.meshes[key]
      if (m) m.visible = next
      return { ...v, [key]: next }
    })
  }

  const setGroupOpacity = (group, value) => {
    const v = Number(value)
    setOpacity((o) => ({ ...o, [group]: v }))
    const e = eng.current
    e.scales[group] = v / 100
    MODEL_DEFS.forEach((def) => {
      if (def.group !== group) return
      const m = e.meshes[def.key]
      if (!m) return
      const final = e.base[def.key] * (v / 100)
      m.material.opacity = Math.min(1, Math.max(0.02, final))
      m.material.depthWrite = final > 0.4
    })
  }

  const setView = (view) => {
    const e = eng.current
    if (!e.camera) return
    const c = e.center
    const d = e.radius * 2.5
    const targets = {
      anterior: [c.x, c.y, c.z + d],
      posterior: [c.x, c.y, c.z - d],
      left: [c.x + d, c.y, c.z],
      right: [c.x - d, c.y, c.z],
      superior: [c.x, c.y + d, c.z + 0.01],
      reset: [c.x, c.y, c.z + d],
    }
    const dest = new THREE.Vector3(...(targets[view] || targets.reset))
    const startPos = e.camera.position.clone()
    const startTgt = e.controls.target.clone()
    const t0 = performance.now()
    const dur = 600
    if (e.viewFrame) cancelAnimationFrame(e.viewFrame)
    const step = (now) => {
      const t = Math.min((now - t0) / dur, 1)
      const k = 1 - Math.pow(1 - t, 3)
      e.camera.position.lerpVectors(startPos, dest, k)
      e.controls.target.lerpVectors(startTgt, c, k)
      e.controls.update()
      e.viewFrame = t < 1 ? requestAnimationFrame(step) : 0
    }
    e.viewFrame = requestAnimationFrame(step)
  }

  const total = MODEL_DEFS.length
  const done = loaded >= total

  return (
    <div className={styles.wrap}>
      <div className={styles.canvas} ref={mountRef} />

      <div className={styles.panel}>
        <div className={styles.section}>
          <div className={styles.sectionTitle}>Estruturas</div>
          {MODEL_DEFS.map((d) => (
            <div key={d.key} className={styles.toggle} onClick={() => toggle(d.key)}>
              <span className={styles.dot} style={{ background: hex(d.color) }} />
              <span className={`${styles.check} ${visible[d.key] ? styles.checkOn : ''}`} />
              <span className={styles.toggleLabel}>{d.label}</span>
            </div>
          ))}
        </div>
        <div className={styles.section}>
          <div className={styles.sectionTitle}>Transparência Global</div>
          <div className={styles.opacity}>
            <label>Ossos</label>
            <input type="range" min="5" max="100" value={opacity.bones}
              onChange={(ev) => setGroupOpacity('bones', ev.target.value)} />
          </div>
          <div className={styles.opacity}>
            <label>Músculos</label>
            <input type="range" min="5" max="100" value={opacity.muscles}
              onChange={(ev) => setGroupOpacity('muscles', ev.target.value)} />
          </div>
        </div>
      </div>

      <div className={styles.views}>
        {VIEWS.map((v) => (
          <button key={v.id} className={styles.viewBtn} onClick={() => setView(v.id)}>{v.label}</button>
        ))}
      </div>

      <div className={styles.caption}>TC segmentada · STL · Three.js</div>

      <div className={`${styles.loading} ${done ? styles.loadingHidden : ''}`}>
        <div className={styles.spinner} />
        <div className={styles.loadingText}>Carregando modelo 3D… ({loaded}/{total})</div>
        <div className={styles.bar}><div className={styles.barFill} style={{ width: `${(loaded / total) * 100}%` }} /></div>
      </div>
    </div>
  )
}
