/**
 * CursosView — in-app browser for the archived baby-prep courses.
 *
 * Two-pane: left rail (course → module → lesson) + main pane that embeds the
 * selected lesson via the Google Drive preview iframe (video or PDF). No
 * backend, no progress tracking — pure browse + watch over the static
 * BABY_COURSES catalog. Playback depends on the Drive folder's
 * "anyone with the link" sharing.
 */
import { useState, useMemo } from 'react'
import { BABY_COURSES } from './babyCourses'
import styles from './cursos.module.css'

const previewUrl = (id) => `https://drive.google.com/file/d/${id}/preview`
const viewUrl = (id) => `https://drive.google.com/file/d/${id}/view`

export default function CursosView() {
  // Flatten lessons once so we can resolve the active selection and a sane
  // default (first lesson of the first course) without re-walking the tree.
  const flat = useMemo(() => {
    const out = []
    for (const course of BABY_COURSES) {
      for (const module of course.modules) {
        for (const lesson of module.lessons) {
          out.push({ ...lesson, courseTitle: course.title, moduleTitle: module.title })
        }
      }
    }
    return out
  }, [])

  const [activeId, setActiveId] = useState(flat[0]?.driveId ?? null)
  const active = useMemo(
    () => flat.find((l) => l.driveId === activeId) ?? flat[0],
    [flat, activeId],
  )

  if (!active) {
    return <div className={styles.empty}>Nenhum curso disponível.</div>
  }

  return (
    <div className={styles.layout}>
      {/* ── Left rail ───────────────────────────────── */}
      <nav className={styles.rail} aria-label="Aulas dos cursos">
        {BABY_COURSES.map((course) => (
          <div key={course.id} className={styles.courseBlock}>
            <div className={styles.courseHead}>
              <div className={styles.courseTitle}>{course.title}</div>
              {course.subtitle && (
                <div className={styles.courseSubtitle}>{course.subtitle}</div>
              )}
            </div>
            {course.modules.map((module) => (
              <div key={module.title} className={styles.moduleBlock}>
                <div className={styles.moduleTitle}>{module.title}</div>
                <ul className={styles.lessonList}>
                  {module.lessons.map((lesson) => {
                    const isActive = lesson.driveId === active.driveId
                    return (
                      <li key={lesson.driveId}>
                        <button
                          type="button"
                          className={isActive ? styles.lessonActive : styles.lesson}
                          aria-current={isActive ? 'true' : undefined}
                          onClick={() => setActiveId(lesson.driveId)}
                        >
                          <span className={styles.lessonIcon} aria-hidden="true">
                            {lesson.type === 'pdf' ? '📄' : '▶'}
                          </span>
                          <span className={styles.lessonName}>{lesson.title}</span>
                          {lesson.duration && (
                            <span className={styles.lessonDur}>{lesson.duration}</span>
                          )}
                        </button>
                      </li>
                    )
                  })}
                </ul>
              </div>
            ))}
          </div>
        ))}
      </nav>

      {/* ── Main pane ───────────────────────────────── */}
      <div className={styles.main}>
        <div className={styles.playerHead}>
          <div className={styles.breadcrumb}>
            {active.courseTitle} · {active.moduleTitle}
          </div>
          <h3 className={styles.playerTitle}>{active.title}</h3>
        </div>

        <div className={active.type === 'pdf' ? styles.embedPdf : styles.embedVideo}>
          <iframe
            key={active.driveId}
            src={previewUrl(active.driveId)}
            title={active.title}
            allow="autoplay; encrypted-media"
            referrerPolicy="no-referrer"
            allowFullScreen
          />
        </div>

        <a
          className={styles.openDrive}
          href={viewUrl(active.driveId)}
          target="_blank"
          rel="noreferrer"
        >
          Abrir no Google Drive ↗
        </a>
      </div>
    </div>
  )
}
