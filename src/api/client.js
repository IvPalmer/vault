const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

// Token management
let accessToken = localStorage.getItem('vaultAccessToken')
let refreshToken = localStorage.getItem('vaultRefreshToken')
let refreshPromise = null

export function setTokens(access, refresh) {
  accessToken = access
  refreshToken = refresh
  if (access) localStorage.setItem('vaultAccessToken', access)
  else localStorage.removeItem('vaultAccessToken')
  if (refresh) localStorage.setItem('vaultRefreshToken', refresh)
  else localStorage.removeItem('vaultRefreshToken')
}

export function clearTokens() {
  accessToken = null
  refreshToken = null
  localStorage.removeItem('vaultAccessToken')
  localStorage.removeItem('vaultRefreshToken')
  localStorage.removeItem('vaultProfileId')
}

export function getAccessToken() { return accessToken }
export function getRefreshToken() { return refreshToken }

// Legacy profile ID — fallback when no JWT
let currentProfileId = localStorage.getItem('vaultProfileId')
export function setProfileId(id) {
  currentProfileId = id
  if (id) localStorage.setItem('vaultProfileId', id)
  else localStorage.removeItem('vaultProfileId')
}
export function getProfileId() { return currentProfileId }

async function attemptRefresh() {
  if (!refreshToken) return false
  if (refreshPromise) return refreshPromise

  refreshPromise = (async () => {
    try {
      const resp = await fetch(`${API_BASE_URL}/auth/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: refreshToken }),
      })
      if (!resp.ok) return false
      const data = await resp.json()
      setTokens(data.access, data.refresh)
      return true
    } catch {
      return false
    } finally {
      refreshPromise = null
    }
  })()
  return refreshPromise
}

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`
  const { headers: optionHeaders, ...restOptions } = options

  const buildHeaders = () => {
    const h = {
      'Content-Type': 'application/json',
      ...optionHeaders,
    }
    if (accessToken) {
      h['Authorization'] = `Bearer ${accessToken}`
    } else if (currentProfileId) {
      h['X-Profile-ID'] = currentProfileId
    }
    return h
  }

  let response = await fetch(url, { ...restOptions, headers: buildHeaders() })

  // On 401, try refresh once
  if (response.status === 401 && refreshToken) {
    const refreshed = await attemptRefresh()
    if (refreshed) {
      response = await fetch(url, { ...restOptions, headers: buildHeaders() })
    }
  }

  if (!response.ok) {
    const error = new Error(`API Error: ${response.status} ${response.statusText}`)
    error.status = response.status
    try { error.data = await response.json() } catch { error.data = null }
    throw error
  }

  if (response.status === 204) return null
  return response.json()
}

export const api = {
  get: (endpoint) => request(endpoint),
  post: (endpoint, data) => request(endpoint, { method: 'POST', body: JSON.stringify(data) }),
  put: (endpoint, data) => request(endpoint, { method: 'PUT', body: JSON.stringify(data) }),
  patch: (endpoint, data) => request(endpoint, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (endpoint, data) => request(endpoint, { method: 'DELETE', body: data ? JSON.stringify(data) : undefined }),
}

export default api
