import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useLocation } from 'react-router-dom'
import { api, setProfileId, getProfileId } from '../api/client'

const ProfileContext = createContext(null)

/** Known page sections — used to distinguish profile slugs from pages */
const SECTIONS = ['overview', 'analytics', 'settings']

/**
 * Derive a URL-friendly slug from profile name.
 * "Palmer" → "palmer", "Rafa" → "rafa"
 */
function toSlug(name) {
  return name?.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '') || ''
}

/**
 * Extract profile slug from pathname.
 * "/palmer/overview" → "palmer"
 * "/overview" → null (legacy route)
 * "/" → null
 */
function getSlugFromPath(pathname) {
  const parts = pathname.split('/').filter(Boolean)
  if (parts.length >= 2 && SECTIONS.includes(parts[1])) {
    return parts[0]
  }
  return null
}

export function ProfileProvider({ children }) {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const location = useLocation()
  const [profileId, setProfileIdState] = useState(() => getProfileId())

  const { data: profiles = [], isLoading } = useQuery({
    queryKey: ['profiles'],
    queryFn: () => api.get('/profiles/'),
    staleTime: 60 * 60 * 1000, // 1 hour — profiles rarely change
  })

  const profileList = profiles.results || profiles

  // Resolve profile from URL slug
  useEffect(() => {
    if (isLoading || !profileList.length) return

    // /home is shared (not profile-scoped) — skip redirect logic
    if (location.pathname === '/home' || location.pathname.startsWith('/home/')) return

    const urlSlug = getSlugFromPath(location.pathname)

    if (urlSlug) {
      // Find profile matching the URL slug
      const matchedProfile = profileList.find(p => toSlug(p.name) === urlSlug)
      if (matchedProfile && matchedProfile.id !== profileId) {
        // URL slug points to a different profile — switch to it
        setProfileIdState(matchedProfile.id)
        setProfileId(matchedProfile.id)
        queryClient.resetQueries({ predicate: (query) => query.queryKey[0] !== 'profiles' })
      } else if (!matchedProfile) {
        // Invalid slug — redirect to first profile
        const firstProfile = profileList[0]
        if (firstProfile) {
          navigate(`/${toSlug(firstProfile.name)}/overview`, { replace: true })
        }
      }
    } else {
      // No slug in URL (root or legacy route) — redirect to stored/first profile
      const storedProfile = profileList.find(p => p.id === profileId) || profileList[0]
      if (storedProfile) {
        const slug = toSlug(storedProfile.name)
        const parts = location.pathname.split('/').filter(Boolean)
        // Check if it's a legacy route like /overview
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
    if (!profileId || !profileList.find(p => p.id === profileId)) {
      const firstId = profileList[0]?.id
      if (firstId) {
        setProfileIdState(firstId)
        setProfileId(firstId)
      }
    }
  }, [profiles, profileId, isLoading])

  const switchProfile = useCallback((id) => {
    const targetProfile = profileList.find(p => p.id === id)
    setProfileIdState(id)
    setProfileId(id)
    // Nuclear: reset all cached data so active queries refetch for new profile
    queryClient.resetQueries({ predicate: (query) => query.queryKey[0] !== 'profiles' })

    // Navigate to new profile's URL, keeping the current page section
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
      profileSlug: currentProfile ? toSlug(currentProfile.name) : '',
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
