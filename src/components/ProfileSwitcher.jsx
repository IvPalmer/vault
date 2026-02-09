import { useState, useRef, useEffect } from 'react'
import { useProfile } from '../context/ProfileContext'
import styles from './ProfileSwitcher.module.css'

function ProfileSwitcher() {
  const { currentProfile, profiles, switchProfile, isLoading } = useProfile()
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  if (isLoading || !profiles.length) return null
  // If only one profile, show name but no dropdown
  if (profiles.length === 1) {
    return (
      <div className={styles.wrapper}>
        <span className={styles.singleName}>{currentProfile?.name}</span>
      </div>
    )
  }

  return (
    <div className={styles.wrapper} ref={ref}>
      <button
        className={styles.trigger}
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        <span className={styles.name}>{currentProfile?.name || '...'}</span>
        <svg className={styles.chevron} width="10" height="6" viewBox="0 0 10 6" fill="none">
          <path d="M1 1L5 5L9 1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
      {open && (
        <div className={styles.dropdown}>
          {profiles.map(p => (
            <button
              key={p.id}
              className={`${styles.option} ${p.id === currentProfile?.id ? styles.active : ''}`}
              onClick={() => {
                switchProfile(p.id)
                setOpen(false)
              }}
            >
              {p.name}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default ProfileSwitcher
