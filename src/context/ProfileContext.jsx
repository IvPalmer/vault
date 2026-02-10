import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api, setProfileId, getProfileId } from '../api/client'

const ProfileContext = createContext(null)

export function ProfileProvider({ children }) {
  const queryClient = useQueryClient()
  const [profileId, setProfileIdState] = useState(() => getProfileId())

  const { data: profiles = [], isLoading } = useQuery({
    queryKey: ['profiles'],
    queryFn: () => api.get('/profiles/'),
    staleTime: 60 * 60 * 1000, // 1 hour — profiles rarely change
  })

  // Auto-select first profile if none stored or stored one is invalid
  useEffect(() => {
    if (isLoading || !profiles.length) return

    // Check if profiles is paginated (has .results) or plain array
    const profileList = profiles.results || profiles

    if (!profileId || !profileList.find(p => p.id === profileId)) {
      const firstId = profileList[0]?.id
      if (firstId) {
        setProfileIdState(firstId)
        setProfileId(firstId)
      }
    }
  }, [profiles, profileId, isLoading])

  const switchProfile = useCallback((id) => {
    setProfileIdState(id)
    setProfileId(id)
    // Nuclear: reset all cached data so active queries refetch for new profile
    // resetQueries (vs removeQueries) triggers immediate refetch on mounted components
    queryClient.resetQueries({ predicate: (query) => query.queryKey[0] !== 'profiles' })
  }, [queryClient])

  const currentProfile = (profiles.results || profiles).find(p => p.id === profileId) || null

  return (
    <ProfileContext.Provider value={{
      profileId,
      profiles: profiles.results || profiles,
      currentProfile,
      switchProfile,
      isLoading,
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
