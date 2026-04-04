# Google Auth + Server-Side Dashboard State — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace X-Profile-ID header auth with Google Social Login + JWT, and move dashboard widget state from localStorage to server.

**Architecture:** Google Identity Services (GIS) on frontend sends ID token to Django backend, which verifies it and returns a simplejwt token pair. Profile is determined by matching the Google email. Dashboard state (tabs, widgets, configs) persisted in a new DashboardState model, loaded on login, auto-saved on change.

**Tech Stack:** Django 5.2, djangorestframework-simplejwt 5.5.0, google-auth (already installed), React 18, Google Identity Services JS library, Vite 5.

---

## File Map

### Backend (new files)
- `backend/api/auth_views.py` — Google login endpoint + JWT refresh
- `backend/api/dashboard_views.py` — DashboardState CRUD endpoint
- `backend/api/migrations/0031_profile_google_fields_dashboardstate.py` — auto-generated

### Backend (modified files)
- `backend/api/models.py` — add google fields to Profile, add DashboardState model
- `backend/api/serializers.py` — add DashboardStateSerializer
- `backend/api/middleware.py` — add JWT-based profile resolution
- `backend/api/urls.py` — add auth + dashboard-state routes
- `backend/vault_project/settings.py` — configure SIMPLE_JWT with custom claims

### Frontend (new files)
- `src/context/AuthContext.jsx` — auth state, login/logout, token management
- `src/pages/Login.jsx` — login page with Google button
- `src/pages/Login.module.css` — login page styles
- `src/hooks/useDashboardState.js` — server-side state load/save hook

### Frontend (modified files)
- `src/main.jsx` — wrap with AuthProvider, add login route
- `src/App.jsx` — add route guard
- `src/api/client.js` — add JWT auth header, refresh logic
- `src/components/Layout.jsx` — replace ProfileSwitcher with user avatar
- `src/components/PersonalOrganizer.jsx` — use useDashboardState hook
- `src/context/ProfileContext.jsx` — derive profile from AuthContext
- `index.html` — add GIS script tag

---

## Task 1: Profile Model — Add Google Fields

**Files:**
- Modify: `backend/api/models.py:20-64` (Profile model)

- [ ] **Step 1: Add google fields to Profile model**

In `backend/api/models.py`, add three fields to the `Profile` model after `setup_completed` (line 56):

```python
    google_email = models.EmailField(unique=True, null=True, blank=True,
        help_text='Google account email used for login')
    google_picture = models.URLField(max_length=500, null=True, blank=True,
        help_text='Google profile picture URL')
    google_name = models.CharField(max_length=200, null=True, blank=True,
        help_text='Google display name')
```

- [ ] **Step 2: Generate and run migration**

```bash
docker compose exec backend python manage.py makemigrations api -n profile_google_fields
docker compose exec backend python manage.py migrate
```

Expected: migration creates 3 nullable fields on Profile.

- [ ] **Step 3: Seed google_email for existing profiles**

```bash
docker compose exec backend python manage.py shell -c "
from api.models import Profile
Profile.objects.filter(name='Palmer').update(google_email='raphaelpalmer42@gmail.com')
Profile.objects.filter(name='Rafa').update(google_email='rafaellarezendegalvao@gmail.com')
print('Done:', list(Profile.objects.values_list('name', 'google_email')))
"
```

- [ ] **Step 4: Commit**

```bash
git add backend/api/models.py backend/api/migrations/
git commit -m "feat(auth): add google_email, google_picture, google_name to Profile"
```

---

## Task 2: DashboardState Model

**Files:**
- Modify: `backend/api/models.py` (add new model at end)
- Modify: `backend/api/serializers.py` (add serializer)

- [ ] **Step 1: Add DashboardState model**

Append to `backend/api/models.py`:

```python
class DashboardState(models.Model):
    """Server-side storage for dashboard widget layouts, tabs, and configs.
    Replaces localStorage for cross-device sync."""
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='dashboard_state')
    state = models.JSONField(default=dict, help_text='Full dashboard state: tabs, widgets, configs')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'DashboardState({self.profile.name})'
```

- [ ] **Step 2: Add serializer**

In `backend/api/serializers.py`, add import of `DashboardState` to the import block, then add:

```python
class DashboardStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardState
        fields = ['state', 'updated_at']
        read_only_fields = ['updated_at']
```

- [ ] **Step 3: Generate and run migration**

```bash
docker compose exec backend python manage.py makemigrations api -n dashboard_state
docker compose exec backend python manage.py migrate
```

- [ ] **Step 4: Commit**

```bash
git add backend/api/models.py backend/api/serializers.py backend/api/migrations/
git commit -m "feat(auth): add DashboardState model for server-side widget state"
```

---

## Task 3: Google Login Endpoint

**Files:**
- Create: `backend/api/auth_views.py`
- Modify: `backend/api/urls.py`
- Modify: `backend/vault_project/settings.py`

- [ ] **Step 1: Configure SIMPLE_JWT with custom claims**

In `backend/vault_project/settings.py`, replace the existing `SIMPLE_JWT` block (lines 158-161) with:

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# Google OAuth Client ID for ID token verification
GOOGLE_CLIENT_ID = '322466188232-agarvcbekbncq69237rcrllq43mm7ejk.apps.googleusercontent.com'
```

- [ ] **Step 2: Create auth_views.py**

Create `backend/api/auth_views.py`:

```python
"""
Google Sign-In authentication views.
Verifies Google ID tokens and returns JWT token pairs.
"""
import logging

from django.conf import settings
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Profile

logger = logging.getLogger(__name__)


class GoogleLoginView(APIView):
    """POST /api/auth/google/ — verify Google ID token, return JWT pair."""
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except ValueError as e:
            logger.warning(f'Google ID token verification failed: {e}')
            return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)

        email = idinfo.get('email')
        if not email:
            return Response({'error': 'No email in token'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            profile = Profile.objects.get(google_email=email, is_active=True)
        except Profile.DoesNotExist:
            return Response(
                {'error': f'No profile found for {email}. This is a closed system.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Update profile with latest Google info
        profile.google_name = idinfo.get('name', profile.google_name)
        profile.google_picture = idinfo.get('picture', profile.google_picture)
        profile.save(update_fields=['google_name', 'google_picture'])

        # Generate JWT pair with profile info in claims
        refresh = RefreshToken()
        refresh['profile_id'] = str(profile.id)
        refresh['profile_name'] = profile.name
        refresh['email'] = email

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'profile': {
                'id': str(profile.id),
                'name': profile.name,
                'email': email,
                'picture': profile.google_picture,
                'slug': profile.name.lower().replace(' ', '-'),
            },
        })


class TokenRefreshView(APIView):
    """POST /api/auth/refresh/ — refresh JWT access token."""
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'refresh token required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(refresh_token)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),  # rotated
                'profile': {
                    'id': refresh.get('profile_id'),
                    'name': refresh.get('profile_name'),
                    'email': refresh.get('email'),
                },
            })
        except Exception:
            return Response({'error': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)


class AuthMeView(APIView):
    """GET /api/auth/me/ — return current user profile from JWT."""
    permission_classes = [AllowAny]

    def get(self, request):
        profile = getattr(request, 'profile', None)
        if not profile:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({
            'id': str(profile.id),
            'name': profile.name,
            'email': profile.google_email,
            'picture': profile.google_picture,
            'slug': profile.name.lower().replace(' ', '-'),
        })
```

- [ ] **Step 3: Add auth URL routes**

In `backend/api/urls.py`, add imports at the top:

```python
from .auth_views import GoogleLoginView, TokenRefreshView, AuthMeView
```

Add to `urlpatterns` list (before the first path entry):

```python
    # Auth
    path('auth/google/', GoogleLoginView.as_view(), name='auth-google'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    path('auth/me/', AuthMeView.as_view(), name='auth-me'),
```

- [ ] **Step 4: Add auth paths to middleware EXEMPT_PREFIXES**

In `backend/api/middleware.py`, update `EXEMPT_PREFIXES` (line 13):

```python
EXEMPT_PREFIXES = ('/api/profiles', '/api/home', '/api/calendar/oauth-callback', '/api/auth', '/admin', '/static')
```

- [ ] **Step 5: Verify endpoint works**

```bash
docker compose restart backend
curl -s http://localhost:8001/api/auth/me/ | python3 -m json.tool
```

Expected: `{"error": "Not authenticated"}` with 401 status.

- [ ] **Step 6: Commit**

```bash
git add backend/api/auth_views.py backend/api/urls.py backend/api/middleware.py backend/vault_project/settings.py
git commit -m "feat(auth): Google login endpoint + JWT token refresh + /me endpoint"
```

---

## Task 4: JWT-Aware Profile Middleware

**Files:**
- Modify: `backend/api/middleware.py`

- [ ] **Step 1: Update ProfileMiddleware to read JWT**

Replace the entire content of `backend/api/middleware.py`:

```python
"""
Profile middleware: resolves request.profile from JWT token or X-Profile-ID header.

Priority:
1. JWT token claim 'profile_id' (from Authorization: Bearer header)
2. X-Profile-ID header (fallback for dev/API testing)
3. First active profile (last resort)
"""
import logging

from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from .models import Profile

logger = logging.getLogger(__name__)

# Paths that don't require a profile
EXEMPT_PREFIXES = ('/api/profiles', '/api/home', '/api/calendar/oauth-callback', '/api/auth', '/admin', '/static')


class ProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()

    def __call__(self, request):
        # Skip profile resolution for exempt paths
        if any(request.path.startswith(p) for p in EXEMPT_PREFIXES):
            request.profile = None
            return self.get_response(request)

        profile = None

        # 1. Try JWT token
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            try:
                validated_token = self.jwt_auth.get_validated_token(
                    auth_header.split(' ', 1)[1]
                )
                profile_id = validated_token.get('profile_id')
                if profile_id:
                    try:
                        profile = Profile.objects.get(id=profile_id, is_active=True)
                    except (Profile.DoesNotExist, ValueError):
                        pass
            except (InvalidToken, TokenError):
                pass

        # 2. Fallback: X-Profile-ID header
        if not profile:
            profile_id = request.headers.get('X-Profile-ID')
            if profile_id:
                try:
                    profile = Profile.objects.get(id=profile_id, is_active=True)
                except (Profile.DoesNotExist, ValueError):
                    return JsonResponse(
                        {'error': f'Profile not found: {profile_id}'},
                        status=404,
                    )

        # 3. Last resort: first active profile
        if not profile:
            profile = Profile.objects.filter(is_active=True).first()
            if not profile:
                return JsonResponse(
                    {'error': 'No active profile found'},
                    status=400,
                )

        request.profile = profile
        return self.get_response(request)
```

- [ ] **Step 2: Restart backend and verify existing functionality**

```bash
docker compose restart backend
curl -s -H "X-Profile-ID: a29184ea-9d4d-4c65-8300-386ed5b07fca" http://localhost:8001/api/profiles/ | python3 -m json.tool
```

Expected: profiles list returns normally (backward compatible).

- [ ] **Step 3: Commit**

```bash
git add backend/api/middleware.py
git commit -m "feat(auth): JWT-aware ProfileMiddleware with X-Profile-ID fallback"
```

---

## Task 5: Dashboard State API Endpoint

**Files:**
- Create: `backend/api/dashboard_views.py`
- Modify: `backend/api/urls.py`

- [ ] **Step 1: Create dashboard_views.py**

Create `backend/api/dashboard_views.py`:

```python
"""Dashboard state CRUD — server-side widget layout persistence."""
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DashboardState
from .serializers import DashboardStateSerializer


class DashboardStateView(APIView):
    """GET/PUT /api/dashboard-state/ — read/write dashboard state for current profile."""
    permission_classes = [AllowAny]

    def get(self, request):
        profile = request.profile
        if not profile:
            return Response({'error': 'No profile'}, status=401)

        try:
            ds = DashboardState.objects.get(profile=profile)
            return Response(DashboardStateSerializer(ds).data)
        except DashboardState.DoesNotExist:
            return Response({'state': {}, 'updated_at': None})

    def put(self, request):
        profile = request.profile
        if not profile:
            return Response({'error': 'No profile'}, status=401)

        ds, created = DashboardState.objects.get_or_create(profile=profile)
        serializer = DashboardStateSerializer(ds, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
```

- [ ] **Step 2: Add URL route**

In `backend/api/urls.py`, add import:

```python
from .dashboard_views import DashboardStateView
```

Add to `urlpatterns`:

```python
    # Dashboard state
    path('dashboard-state/', DashboardStateView.as_view(), name='dashboard-state'),
```

- [ ] **Step 3: Restart and test**

```bash
docker compose restart backend
# GET (empty)
curl -s -H "X-Profile-ID: a29184ea-9d4d-4c65-8300-386ed5b07fca" http://localhost:8001/api/dashboard-state/ | python3 -m json.tool
# PUT
curl -s -X PUT -H "Content-Type: application/json" -H "X-Profile-ID: a29184ea-9d4d-4c65-8300-386ed5b07fca" -d '{"state":{"tabs":[{"id":"default","name":"Principal"}]}}' http://localhost:8001/api/dashboard-state/ | python3 -m json.tool
# GET (populated)
curl -s -H "X-Profile-ID: a29184ea-9d4d-4c65-8300-386ed5b07fca" http://localhost:8001/api/dashboard-state/ | python3 -m json.tool
```

Expected: first GET returns empty state, PUT saves, second GET returns saved state.

- [ ] **Step 4: Commit**

```bash
git add backend/api/dashboard_views.py backend/api/urls.py
git commit -m "feat(auth): dashboard state API endpoint (GET/PUT)"
```

---

## Task 6: Frontend — GIS Script + API Client Auth

**Files:**
- Modify: `index.html`
- Modify: `src/api/client.js`

- [ ] **Step 1: Add Google Identity Services script to index.html**

Read the current `index.html`, then add the GIS script tag in `<head>`:

```html
<script src="https://accounts.google.com/gsi/client" async defer></script>
```

- [ ] **Step 2: Rewrite api/client.js with JWT support**

Replace `src/api/client.js` with:

```javascript
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
  // Also clear legacy profile ID
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
  // Deduplicate concurrent refresh attempts
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
```

- [ ] **Step 3: Commit**

```bash
git add index.html src/api/client.js
git commit -m "feat(auth): JWT token management in API client + GIS script tag"
```

---

## Task 7: Frontend — AuthContext

**Files:**
- Create: `src/context/AuthContext.jsx`

- [ ] **Step 1: Create AuthContext**

Create `src/context/AuthContext.jsx`:

```jsx
import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { api, setTokens, clearTokens, getAccessToken, getRefreshToken, setProfileId } from '../api/client'

const AuthContext = createContext(null)

const GOOGLE_CLIENT_ID = '322466188232-agarvcbekbncq69237rcrllq43mm7ejk.apps.googleusercontent.com'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)        // { id, name, email, picture, slug }
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  // On mount: try to restore session from stored tokens
  useEffect(() => {
    async function restoreSession() {
      const token = getAccessToken()
      const refresh = getRefreshToken()
      if (!token && !refresh) {
        setIsLoading(false)
        return
      }

      try {
        const profile = await api.get('/auth/me/')
        setUser(profile)
        // Sync legacy profile ID for any code still using it
        setProfileId(profile.id)
      } catch (err) {
        // Token invalid/expired and refresh failed
        clearTokens()
      }
      setIsLoading(false)
    }
    restoreSession()
  }, [])

  const login = useCallback(async (googleIdToken) => {
    setError(null)
    try {
      const data = await fetch('/api/auth/google/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: googleIdToken }),
      }).then(r => {
        if (!r.ok) return r.json().then(d => { throw new Error(d.error || 'Login failed') })
        return r.json()
      })

      setTokens(data.access, data.refresh)
      setUser(data.profile)
      setProfileId(data.profile.id)
      return data.profile
    } catch (err) {
      setError(err.message)
      throw err
    }
  }, [])

  const logout = useCallback(() => {
    clearTokens()
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: !!user,
      isLoading,
      error,
      login,
      logout,
      googleClientId: GOOGLE_CLIENT_ID,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
```

- [ ] **Step 2: Commit**

```bash
git add src/context/AuthContext.jsx
git commit -m "feat(auth): AuthContext with Google login, session restore, logout"
```

---

## Task 8: Frontend — Login Page

**Files:**
- Create: `src/pages/Login.jsx`
- Create: `src/pages/Login.module.css`

- [ ] **Step 1: Create Login page**

Create `src/pages/Login.jsx`:

```jsx
import { useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import styles from './Login.module.css'

export default function Login() {
  const { login, isAuthenticated, isLoading, error, googleClientId } = useAuth()
  const navigate = useNavigate()
  const btnRef = useRef(null)
  const initialized = useRef(false)

  // If already authenticated, redirect
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      navigate('/', { replace: true })
    }
  }, [isAuthenticated, isLoading, navigate])

  const handleCredentialResponse = useCallback(async (response) => {
    try {
      const profile = await login(response.credential)
      navigate(`/${profile.slug}/overview`, { replace: true })
    } catch {
      // error is set in AuthContext
    }
  }, [login, navigate])

  // Initialize GIS
  useEffect(() => {
    if (initialized.current || !btnRef.current) return
    if (!window.google?.accounts?.id) {
      // GIS script not loaded yet — wait for it
      const checkInterval = setInterval(() => {
        if (window.google?.accounts?.id) {
          clearInterval(checkInterval)
          initGIS()
        }
      }, 100)
      const timeout = setTimeout(() => clearInterval(checkInterval), 10000)
      return () => { clearInterval(checkInterval); clearTimeout(timeout) }
    }
    initGIS()

    function initGIS() {
      if (initialized.current) return
      initialized.current = true
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: handleCredentialResponse,
      })
      window.google.accounts.id.renderButton(btnRef.current, {
        theme: 'outline',
        size: 'large',
        text: 'signin_with',
        shape: 'rectangular',
        width: 300,
      })
    }
  }, [googleClientId, handleCredentialResponse])

  if (isLoading) return null

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h1 className={styles.title}>vault</h1>
        <p className={styles.subtitle}>Finanças pessoais</p>
        <div ref={btnRef} className={styles.googleBtn} />
        {error && <p className={styles.error}>{error}</p>}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create Login styles**

Create `src/pages/Login.module.css`:

```css
.container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--color-bg, #0a0a0a);
}

.card {
  text-align: center;
  padding: 3rem 2.5rem;
  border-radius: 12px;
  background: var(--color-surface, #141414);
  border: 1px solid var(--color-border, #222);
}

.title {
  font-size: 2.5rem;
  font-weight: 300;
  letter-spacing: 0.15em;
  color: var(--color-text, #e0e0e0);
  margin: 0 0 0.25rem;
}

.subtitle {
  color: var(--color-text-muted, #666);
  margin: 0 0 2rem;
  font-size: 0.9rem;
}

.googleBtn {
  display: flex;
  justify-content: center;
  min-height: 44px;
}

.error {
  color: var(--color-red, #ef4444);
  margin-top: 1rem;
  font-size: 0.85rem;
}
```

- [ ] **Step 3: Commit**

```bash
mkdir -p src/pages
git add src/pages/Login.jsx src/pages/Login.module.css
git commit -m "feat(auth): login page with Google Sign-In button"
```

---

## Task 9: Frontend — Wire Auth Into App Shell

**Files:**
- Modify: `src/main.jsx`
- Modify: `src/App.jsx`
- Modify: `src/context/ProfileContext.jsx`

- [ ] **Step 1: Update main.jsx — add AuthProvider**

Replace `src/main.jsx`:

```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from './context/AuthContext'
import { ProfileProvider } from './context/ProfileContext'
import { MonthProvider } from './context/MonthContext'
import App from './App'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AuthProvider>
          <ProfileProvider>
            <MonthProvider>
              <App />
            </MonthProvider>
          </ProfileProvider>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)
```

- [ ] **Step 2: Update App.jsx — add login route + auth guard**

Replace `src/App.jsx`:

```jsx
import { useState, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './components/Home'
import MonthlyOverview from './components/MonthlyOverview'
import Analytics from './components/Analytics'
import Settings from './components/Settings'
import PersonalOrganizer from './components/PersonalOrganizer'
import CategoryManager from './components/CategoryManager'
import SetupWizard from './components/SetupWizard'
import ErrorBoundary from './components/ErrorBoundary'
import Login from './pages/Login'
import { useProfile } from './context/ProfileContext'
import { useAuth } from './context/AuthContext'
import './App.css'

function AuthGuard({ children }) {
  const { isAuthenticated, isLoading } = useAuth()
  if (isLoading) return null
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return children
}

function App() {
  const { currentProfile, isLoading: profileLoading, profileSlug } = useProfile()
  const { isAuthenticated, isLoading: authLoading } = useAuth()
  const [showWizard, setShowWizard] = useState(false)
  const [wizardEditMode, setWizardEditMode] = useState(false)

  useEffect(() => {
    if (!profileLoading && currentProfile && currentProfile.setup_completed === false) {
      setWizardEditMode(false)
      setShowWizard(true)
    }
  }, [currentProfile, profileLoading])

  const handleOpenWizardFromSettings = () => {
    setWizardEditMode(true)
    setShowWizard(true)
  }

  const handleCloseWizard = () => {
    setShowWizard(false)
    setWizardEditMode(false)
  }

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/*" element={
        <AuthGuard>
          <Layout>
            <Routes>
              <Route path="/home" element={<ErrorBoundary fallbackMessage="Erro ao carregar Home"><Home /></ErrorBoundary>} />
              <Route path="/:profileSlug/pessoal" element={<ErrorBoundary fallbackMessage="Erro ao carregar Pessoal"><PersonalOrganizer /></ErrorBoundary>} />
              <Route path="/:profileSlug/overview" element={<ErrorBoundary fallbackMessage="Erro ao carregar Visão Mensal"><MonthlyOverview /></ErrorBoundary>} />
              <Route path="/:profileSlug/analytics" element={<ErrorBoundary fallbackMessage="Erro ao carregar Analytics"><Analytics /></ErrorBoundary>} />
              <Route path="/:profileSlug/settings" element={<ErrorBoundary fallbackMessage="Erro ao carregar Configurações"><Settings onOpenWizard={handleOpenWizardFromSettings} /></ErrorBoundary>} />
              <Route path="/:profileSlug/categories" element={<ErrorBoundary fallbackMessage="Erro ao carregar Categorias"><CategoryManager /></ErrorBoundary>} />
              <Route path="/overview" element={profileSlug ? <Navigate to={`/${profileSlug}/overview`} replace /> : null} />
              <Route path="/analytics" element={profileSlug ? <Navigate to={`/${profileSlug}/analytics`} replace /> : null} />
              <Route path="/settings" element={profileSlug ? <Navigate to={`/${profileSlug}/settings`} replace /> : null} />
              <Route path="/" element={<Navigate to="/home" replace />} />
            </Routes>
          </Layout>
          {showWizard && <SetupWizard onClose={handleCloseWizard} editMode={wizardEditMode} />}
        </AuthGuard>
      } />
    </Routes>
  )
}

export default App
```

- [ ] **Step 3: Update ProfileContext — derive from AuthContext**

Replace `src/context/ProfileContext.jsx`:

```jsx
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

  // URL slug resolution (same logic as before)
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
```

- [ ] **Step 4: Commit**

```bash
git add src/main.jsx src/App.jsx src/context/ProfileContext.jsx
git commit -m "feat(auth): wire AuthContext into app shell with login route + auth guard"
```

---

## Task 10: Frontend — Header with Avatar + Logout

**Files:**
- Modify: `src/components/Layout.jsx`

- [ ] **Step 1: Replace ProfileSwitcher with user avatar in Layout**

Replace `src/components/Layout.jsx`:

```jsx
import { useState, useRef, useEffect } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { useNavigate } from 'react-router-dom'
import MonthPicker from './MonthPicker'
import { useProfile } from '../context/ProfileContext'
import { useAuth } from '../context/AuthContext'
import styles from './Layout.module.css'

function UserMenu() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    if (!open) return
    const handleClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [open])

  if (!user) return null

  const handleLogout = () => {
    setOpen(false)
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div ref={ref} className={styles.userMenu}>
      <button className={styles.userBtn} onClick={() => setOpen(!open)}>
        {user.picture ? (
          <img src={user.picture} alt="" className={styles.avatar} referrerPolicy="no-referrer" />
        ) : (
          <span className={styles.avatarFallback}>{user.name?.[0] || '?'}</span>
        )}
        <span className={styles.userName}>{user.name}</span>
      </button>
      {open && (
        <div className={styles.userDropdown}>
          <div className={styles.userInfo}>
            <span className={styles.userEmail}>{user.email}</span>
          </div>
          <button className={styles.logoutBtn} onClick={handleLogout}>
            Sair
          </button>
        </div>
      )}
    </div>
  )
}

function Layout({ children }) {
  const { pathname } = useLocation()
  const { profileSlug } = useProfile()

  const isHome = pathname === '/home' || pathname.startsWith('/home/')
  const isPessoal = pathname.endsWith('/pessoal')
  const isSettings = pathname.endsWith('/settings') || pathname.endsWith('/categories')
  const isAnalytics = pathname.endsWith('/analytics')
  const showMonthPicker = !isHome && !isPessoal && !isSettings && !isAnalytics

  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <div className={styles.topRow}>
          <h1 className={styles.title}>vault</h1>
          <nav className={styles.nav}>
            <NavLink to="/home" className={({ isActive }) => isActive ? styles.activeTab : styles.navTab}>Home</NavLink>
            <NavLink to={`/${profileSlug}/pessoal`} className={({ isActive }) => isActive ? styles.activeTab : styles.navTab}>Pessoal</NavLink>
            <NavLink to={`/${profileSlug}/overview`} className={({ isActive }) => isActive ? styles.activeTab : styles.navTab}>Financeiro</NavLink>
            <NavLink to={`/${profileSlug}/analytics`} className={({ isActive }) => isActive ? styles.activeTab : styles.navTab}>Analytics</NavLink>
            <NavLink to={`/${profileSlug}/settings`} className={({ isActive }) => isActive ? styles.activeTab : styles.navTab}>Config</NavLink>
          </nav>
          <UserMenu />
        </div>
        {showMonthPicker && <MonthPicker />}
      </header>
      <main className={(isHome || isPessoal || isAnalytics) ? styles.mainWide : styles.main}>
        {children}
      </main>
    </div>
  )
}

export default Layout
```

- [ ] **Step 2: Add user menu styles to Layout.module.css**

Read `src/components/Layout.module.css`, then append these styles:

```css
/* User menu */
.userMenu {
  position: relative;
  margin-left: auto;
}

.userBtn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  color: var(--color-text);
}

.userBtn:hover {
  background: var(--color-surface-hover, rgba(255,255,255,0.06));
}

.avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
}

.avatarFallback {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
}

.userName {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.userDropdown {
  position: absolute;
  right: 0;
  top: 100%;
  margin-top: 4px;
  background: var(--color-surface, #1a1a1a);
  border: 1px solid var(--color-border, #333);
  border-radius: 8px;
  min-width: 180px;
  padding: 0.5rem 0;
  z-index: 100;
}

.userInfo {
  padding: 0.5rem 1rem;
  border-bottom: 1px solid var(--color-border, #333);
}

.userEmail {
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.logoutBtn {
  display: block;
  width: 100%;
  text-align: left;
  padding: 0.5rem 1rem;
  background: none;
  border: none;
  color: var(--color-red, #ef4444);
  cursor: pointer;
  font-size: 0.85rem;
}

.logoutBtn:hover {
  background: rgba(255,255,255,0.04);
}
```

- [ ] **Step 3: Commit**

```bash
git add src/components/Layout.jsx src/components/Layout.module.css
git commit -m "feat(auth): header user avatar with logout dropdown, remove ProfileSwitcher"
```

---

## Task 11: Frontend — Dashboard State Hook + PersonalOrganizer Migration

**Files:**
- Create: `src/hooks/useDashboardState.js`
- Modify: `src/components/PersonalOrganizer.jsx`

- [ ] **Step 1: Create useDashboardState hook**

Create `src/hooks/useDashboardState.js`:

```javascript
import { useState, useEffect, useCallback, useRef } from 'react'
import api from '../api/client'

const DEBOUNCE_MS = 2000

/**
 * Server-side dashboard state with localStorage migration.
 * Returns [state, updateState, isLoading]
 *
 * State shape: { tabs, configs }
 * - tabs: [{ id, name, widgets: [{ id, type, x, y, w, h }] }]
 * - configs: { widgetId: { ...config } }
 */
export default function useDashboardState(profileId) {
  const [state, setState] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const saveTimer = useRef(null)
  const latestState = useRef(null)

  // Load state from server (or migrate from localStorage)
  useEffect(() => {
    if (!profileId) return
    let cancelled = false

    async function load() {
      try {
        const data = await api.get('/dashboard-state/')
        if (cancelled) return

        if (data.state && Object.keys(data.state).length > 0) {
          setState(data.state)
        } else {
          // Migrate from localStorage
          const migrated = migrateFromLocalStorage(profileId)
          setState(migrated)
          // Save to server
          try {
            await api.put('/dashboard-state/', { state: migrated })
          } catch {}
        }
      } catch {
        // Offline or error — fall back to localStorage
        const local = migrateFromLocalStorage(profileId)
        if (!cancelled) setState(local)
      }
      if (!cancelled) setIsLoading(false)
    }

    load()
    return () => { cancelled = true }
  }, [profileId])

  // Debounced save to server
  const saveToServer = useCallback((newState) => {
    latestState.current = newState
    if (saveTimer.current) clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(async () => {
      try {
        await api.put('/dashboard-state/', { state: latestState.current })
      } catch (err) {
        console.warn('Failed to save dashboard state:', err)
      }
    }, DEBOUNCE_MS)
  }, [])

  const updateState = useCallback((partial) => {
    setState(prev => {
      const next = { ...prev, ...partial }
      saveToServer(next)
      return next
    })
  }, [saveToServer])

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (saveTimer.current) {
        clearTimeout(saveTimer.current)
        // Flush pending save
        if (latestState.current) {
          api.put('/dashboard-state/', { state: latestState.current }).catch(() => {})
        }
      }
    }
  }, [])

  return [state, updateState, isLoading]
}

// ── localStorage migration ──

const DEFAULT_WIDGETS = [
  { id: 'kpi-hoje',      type: 'kpi-hoje',      x: 0,  y: 0, w: 3, h: 2 },
  { id: 'kpi-atrasadas', type: 'kpi-atrasadas', x: 3,  y: 0, w: 3, h: 2 },
  { id: 'kpi-ativas',    type: 'kpi-ativas',    x: 6,  y: 0, w: 3, h: 2 },
  { id: 'kpi-projetos',  type: 'kpi-projetos',  x: 9,  y: 0, w: 3, h: 2 },
  { id: 'capture',       type: 'capture',       x: 0,  y: 2, w: 8, h: 1 },
  { id: 'projects',      type: 'projects',      x: 8,  y: 2, w: 4, h: 1 },
  { id: 'tasks',         type: 'tasks',         x: 0,  y: 3, w: 4, h: 6 },
  { id: 'reminders',     type: 'reminders',     x: 4,  y: 3, w: 5, h: 6 },
  { id: 'calendar',      type: 'calendar',      x: 9,  y: 3, w: 3, h: 8 },
  { id: 'events',        type: 'events',        x: 0,  y: 9, w: 4, h: 5 },
  { id: 'notes',         type: 'notes',         x: 4,  y: 9, w: 5, h: 5 },
]

function safeJsonParse(key) {
  try {
    const v = localStorage.getItem(key)
    return v ? JSON.parse(v) : null
  } catch { return null }
}

function migrateFromLocalStorage(profileId) {
  // Try profile-scoped tabs key first
  const tabsKey = `vault-pessoal-tabs-v1-${profileId}`
  const tabs = safeJsonParse(tabsKey)
  if (tabs && tabs.length) {
    const configKey = `vault-pessoal-widget-config-v1-${profileId}`
    const configs = safeJsonParse(configKey) || {}
    return { tabs, configs }
  }

  // Try profile-scoped widgets key
  const widgetsKey = `vault-pessoal-widgets-v1-${profileId}`
  const widgets = safeJsonParse(widgetsKey)
  if (widgets && widgets.length) {
    const configKey = `vault-pessoal-widget-config-v1-${profileId}`
    const configs = safeJsonParse(configKey) || {}
    return { tabs: [{ id: 'default', name: 'Principal', widgets }], configs }
  }

  // Try old unscoped keys
  const oldWidgets = safeJsonParse('vault-pessoal-widgets-v1')
  if (oldWidgets && oldWidgets.length) {
    const configs = safeJsonParse('vault-pessoal-widget-config-v1') || {}
    const items = oldWidgets.map(item => ({ ...item, type: item.type || item.id }))
    return { tabs: [{ id: 'default', name: 'Principal', widgets: items }], configs }
  }

  // Defaults
  return { tabs: [{ id: 'default', name: 'Principal', widgets: DEFAULT_WIDGETS }], configs: {} }
}
```

- [ ] **Step 2: Update PersonalOrganizer to use the hook**

In `src/components/PersonalOrganizer.jsx`, make these changes:

**Add import** (after other imports around line 20):
```javascript
import useDashboardState from '../hooks/useDashboardState'
```

**Replace the localStorage helper functions and constants** (lines 1234-1357 — `widgetsKey` through `saveTabs`). Delete all of these:
- `widgetsKey`, `configKey`, `tabsKey`, `gridKey` functions
- `DEFAULT_WIDGETS` array
- `loadWidgets`, `saveWidgets`, `loadWidgetConfigs`, `saveWidgetConfigs`, `loadTabs`, `saveTabs` functions

**Replace `PersonalOrganizerInner`** state initialization (lines 1522-1545). Change from:

```javascript
function PersonalOrganizerInner({ profileId }) {
  const queryClient = useQueryClient()
  const [activeProject, setActiveProject] = useState(null)
  const [tabs, setTabs] = useState(() => loadTabs(profileId))
  const [activeTabId, setActiveTabId] = useState(() => {
    const t = loadTabs(profileId)
    return t[0]?.id || 'default'
  })
  const [widgetConfigs, setWidgetConfigs] = useState(() => {
    const configs = loadWidgetConfigs(profileId)
    if (profileId === PALMER_ID && !configs.reminders) {
      configs.reminders = { enabled: true }
    }
    return configs
  })

  // Derive active tab and widgets
  const activeTab = tabs.find(t => t.id === activeTabId) || tabs[0]
  const widgets = activeTab?.widgets || []

  // Persist tabs and configs
  useEffect(() => { saveTabs(profileId, tabs) }, [profileId, tabs])
  useEffect(() => { saveWidgetConfigs(profileId, widgetConfigs) }, [profileId, widgetConfigs])
```

To:

```javascript
function PersonalOrganizerInner({ profileId }) {
  const queryClient = useQueryClient()
  const [activeProject, setActiveProject] = useState(null)
  const [dashState, updateDashState, dashLoading] = useDashboardState(profileId)

  const tabs = dashState?.tabs || [{ id: 'default', name: 'Principal', widgets: [] }]
  const widgetConfigs = dashState?.configs || {}
  const [activeTabId, setActiveTabId] = useState(null)

  // Set initial active tab when state loads
  useEffect(() => {
    if (dashState && !activeTabId) {
      setActiveTabId(dashState.tabs?.[0]?.id || 'default')
    }
  }, [dashState, activeTabId])

  // Auto-enable reminders for Palmer
  useEffect(() => {
    if (dashState && profileId === PALMER_ID && !widgetConfigs.reminders) {
      updateDashState({ configs: { ...widgetConfigs, reminders: { enabled: true } } })
    }
  }, [dashState, profileId])

  const activeTab = tabs.find(t => t.id === activeTabId) || tabs[0]
  const widgets = activeTab?.widgets || []

  const setTabs = useCallback((updater) => {
    const newTabs = typeof updater === 'function' ? updater(tabs) : updater
    updateDashState({ tabs: newTabs })
  }, [tabs, updateDashState])

  const setWidgetConfigs = useCallback((updater) => {
    const newConfigs = typeof updater === 'function' ? updater(widgetConfigs) : updater
    updateDashState({ configs: newConfigs })
  }, [widgetConfigs, updateDashState])

  if (dashLoading) return <div className={styles.loading}>Carregando dashboard...</div>
```

**Update `deleteTab`** — replace `localStorage.removeItem(gridKey(profileId, tabId))` (line 1574) with nothing (just remove that line — grid state is now in the tabs array).

- [ ] **Step 3: Commit**

```bash
git add src/hooks/useDashboardState.js src/components/PersonalOrganizer.jsx
git commit -m "feat(auth): server-side dashboard state hook + PersonalOrganizer migration"
```

---

## Task 12: Update Home.jsx — Use Auth User Name

**Files:**
- Modify: `src/components/Home.jsx`

- [ ] **Step 1: Read Home.jsx to understand current userName logic**

Read `src/components/Home.jsx` and find the `localStorage.getItem('vaultUserName')` usage (around line 28-29).

- [ ] **Step 2: Update to use AuthContext**

Add import at the top:
```javascript
import { useAuth } from '../context/AuthContext'
```

Replace the userName resolution logic with:
```javascript
const { user } = useAuth()
const userName = user?.name?.split(' ')[0] || localStorage.getItem('vaultUserName') || 'Visitante'
```

- [ ] **Step 3: Commit**

```bash
git add src/components/Home.jsx
git commit -m "feat(auth): Home page uses auth user name"
```

---

## Task 13: Smoke Test Full Flow

- [ ] **Step 1: Rebuild and restart**

```bash
docker compose restart backend
```

Wait for Vite hot-reload to pick up all frontend changes.

- [ ] **Step 2: Manual smoke test checklist**

Open `http://localhost:5175` in browser:

1. Should redirect to `/login`
2. "Entrar com Google" button should render
3. Click Google Sign-In → select `raphaelpalmer42@gmail.com`
4. Should redirect to `/palmer/overview`
5. Header shows Google avatar + name (not profile switcher)
6. Navigate to `/palmer/pessoal` → dashboard loads widgets
7. Move a widget → wait 2s → refresh page → widget position persisted (server-side)
8. Click avatar → "Sair" → returns to login page
9. Login again → dashboard state preserved

- [ ] **Step 3: Test fallback (X-Profile-ID still works)**

```bash
curl -s -H "X-Profile-ID: a29184ea-9d4d-4c65-8300-386ed5b07fca" http://localhost:8001/api/analytics/metricas/?month_str=2026-04 | python3 -m json.tool | head -5
```

Expected: metricas data returns normally.

- [ ] **Step 4: Final commit**

```bash
git add -A
git status  # check nothing unexpected
git commit -m "feat(auth): Google Social Login + server-side dashboard state

Complete auth system replacing X-Profile-ID with Google Sign-In + JWT.
Dashboard widget state now stored server-side for cross-device sync."
```

---

## Summary of Changes

| Area | Before | After |
|------|--------|-------|
| Auth | None (X-Profile-ID header) | Google Sign-In → JWT |
| Profile selection | Dropdown switcher | Determined by Google account |
| Dashboard state | localStorage per device | Server-side DashboardState model |
| Token storage | N/A | Access in memory/localStorage, refresh in localStorage |
| Header | ProfileSwitcher component | Google avatar + logout menu |
| Middleware | X-Profile-ID only | JWT → X-Profile-ID fallback |
