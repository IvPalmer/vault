import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useLocation } from 'react-router-dom'
import { api, setProfileId, getProfileId } from '../api/client'
import { useAuth } from './AuthContext'

const ProfileContext = createContext(null)

const SECTIONS = ['overview', 'analytics', 'settings', 'pessoal', 'financeiro']

function toSlug(name) {
  return name?.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '') || ''
}

function getSlugFromPath(pathname) {
  const parts = pathname.split('/').filter(Boolean)
  if (parts.length >= 2 && SECTIONS.includes(parts[1])) {
    return parts[0]
  }
  return null
}

export function ProfileProvider({ children }) {
  const { user, isAuthenticated } = useAuth()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const location = useLocation()
  const [profileId, setProfileIdState] = useState(() => getProfileId())

  const { data: profiles = [], isLoading } = useQuery({
    queryKey: ['profiles'],
    queryFn: () => api.get('/profiles/'),
    staleTime: 60 * 60 * 1000,
    enabled: isAuthenticated,
  })

  const profileList = profiles.results || profiles

  // When auth user changes, sync profile ID
  useEffect(() => {
    if (user?.id && user.id !== profileId) {
      setProfileIdState(user.id)
      setProfileId(user.id)
      queryClient.resetQueries({ predicate: (query) => query.queryKey[0] !== 'profiles' })
    }
  }, [user?.id])

  // URL slug resolution
  useEffect(() => {
    if (isLoading || !profileList.length) return
    if (location.pathname === '/home' || location.pathname.startsWith('/home/')) return
    if (location.pathname === '/login') return

    const urlSlug = getSlugFromPath(location.pathname)

    if (urlSlug) {
      const matchedProfile = profileList.find(p => toSlug(p.name) === urlSlug)
      if (matchedProfile && matchedProfile.id !== profileId) {
        setProfileIdState(matchedProfile.id)
        setProfileId(matchedProfile.id)
        queryClient.resetQueries({ predicate: (query) => query.queryKey[0] !== 'profiles' })
      } else if (!matchedProfile) {
        const firstProfile = profileList[0]
        if (firstProfile) {
          navigate(`/${toSlug(firstProfile.name)}/overview`, { replace: true })
        }
      }
    } else {
      const storedProfile = profileList.find(p => p.id === profileId) || profileList[0]
      if (storedProfile) {
        const slug = toSlug(storedProfile.name)
        const parts = location.pathname.split('/').filter(Boolean)
        if (parts.length === 1 && SECTIONS.includes(parts[0])) {
          navigate(`/${slug}/${parts[0]}`, { replace: true })
        } else if (parts.length === 0) {
          navigate(`/${slug}/overview`, { replace: true })
        }
      }
    }
  }, [profileList, isLoading, location.pathname])

  // Auto-select first profile if none stored
  useEffect(() => {
    if (isLoading || !profileList.length) return
    const urlSlug = getSlugFromPath(location.pathname)
    if (urlSlug && profileList.find(p => toSlug(p.name) === urlSlug)) return
    if (!profileId || !profileList.find(p => p.id === profileId)) {
      const firstId = profileList[0]?.id
      if (firstId) {
        setProfileIdState(firstId)
        setProfileId(firstId)
      }
    }
  }, [profiles, profileId, isLoading, location.pathname])

  const switchProfile = useCallback((id) => {
    const targetProfile = profileList.find(p => p.id === id)
    setProfileIdState(id)
    setProfileId(id)
    queryClient.resetQueries({ predicate: (query) => query.queryKey[0] !== 'profiles' })
    if (targetProfile) {
      const slug = toSlug(targetProfile.name)
      const parts = location.pathname.split('/').filter(Boolean)
      const section = parts.length >= 2 && SECTIONS.includes(parts[1])
        ? parts[1]
        : 'overview'
      navigate(`/${slug}/${section}`)
    }
  }, [queryClient, profileList, location.pathname, navigate])

  const currentProfile = profileList.find(p => p.id === profileId) || null

  return (
    <ProfileContext.Provider value={{
      profileId,
      profiles: profileList,
      currentProfile,
      switchProfile,
      isLoading,
      profileSlug: currentProfile ? toSlug(currentProfile.name) : (user ? toSlug(user.name) : ''),
      toSlug,
    }}>
      {children}
    </ProfileContext.Provider>
  )
}

export function useProfile() {
  const context = useContext(ProfileContext)
  if (!context) throw new Error('useProfile must be used within ProfileProvider')
  return context
}
