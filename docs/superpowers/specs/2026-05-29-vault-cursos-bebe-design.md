# Cursos sub-view under Família (Saúde) — design

**Date:** 2026-05-29
**Status:** implemented & deployed (working in production)
**Scope:** Surface the archived baby-prep courses (Brunna's Hotmart purchases, saved to Google Drive) inside Vault as an in-app, browse-and-watch course view.

## Goal

Under the **Família** tab of the Saúde module, add a tab-like view that lets Palmer/Rafa browse and watch the three archived courses without leaving the app: **5 Aulas para a Maternidade**, **Enxoval Inteligente** (8 modules + aulas bônus + oficina de carrinhos), and the **O Ano de Ouro** e-book (PDF).

## Decisions (from brainstorming)

- **Interactivity:** browse + watch only. No progress tracking, no notes. (Can grow later.)
- **Content:** all three courses.
- **Catalog:** curated static catalog (`babyCourses.js`) vs. a live Drive folder listing. Curated gives real module names/order and a polished course feel; the live-listing route would expose raw filenames and reverse-engineered grouping.
- **Playback (evolved during implementation):** the original plan embedded Google Drive's `/preview` iframe for video. **That proved unreliable** — Drive shows "still processing this video for playback" for un-transcoded files, intermittently. So **video now streams through a same-origin backend proxy** and plays in a native `<video>`. **PDFs keep the Drive `/preview` iframe** (works fine for documents).

## Architecture

### Frontend
- **`src/components/saude/babyCourses.js`** — static catalog. `course → modules → lessons`; each `lesson = { title, type: 'video'|'pdf', driveId, duration? }`. `driveId` = the Google Drive file ID. Adding content later = edit this file.
- **`src/components/saude/CursosView.jsx`** — two-pane: left rail (course → module → lesson, click to select) + main pane. **Video** → native `<video>` whose `src` is the backend stream proxy (`${API_BASE_URL}/google/drive/stream/<driveId>/`). **PDF** → Drive `/preview` iframe. Plus an "Abrir no Google Drive" fallback link. Selection in local `useState` (defaults to first lesson). Element is keyed on `driveId` so switching lessons remounts cleanly.
- **`src/components/saude/cursos.module.css`** — styles, palette mirrors `Saude.module.css`.
- **`src/components/Saude.jsx`** — `FamiliaView` gains a sub-tab bar (reusing `styles.subTabs/subTab/subTabActive`): **Acompanhamento** (existing pregnancy dashboard, default) | **Cursos**. The dashboard's `isLoading`/`!ativa` guards moved inside the Acompanhamento branch (wrapped in a `role="tabpanel"`) so Cursos renders independently of pregnancy state; hooks stay unconditional at the top.
- **`src/api/client.js`** — exports `API_BASE_URL` (was a private const) so CursosView builds the absolute stream URL.

### Backend (Google Drive streaming proxy)
- **`backend/api/google_views.py` → `CursoStreamView`** (`GET /api/google/drive/stream/<file_id>/`): range-streams a Drive file's original bytes so the native player works regardless of Drive's preview transcoding.
  - **Scope guard:** only serves files nested under the course root folder `CURSO_BEBE_ROOT_FOLDER` (`1NMFkq3Uh3A2ZTQhpQH3w6S0BP5MDhr8z`) via `google_drive.is_descendant_of(...)` (walks the parent chain, cached). Never an open proxy for arbitrary Drive files.
  - **Auth to Drive:** uses the connected `GoogleAccount` (raphaelpalmer42@gmail.com) via a cached `AuthorizedSession` (auto-refreshes the OAuth token — a raw `creds.token` came back stale → 401). No app-level auth on the endpoint itself (the files are already public "anyone with link"; the folder scope is the real guard), so a plain `<video src>` works without a token.
  - **Range handling:** parses the inbound `Range`, caps each response to **8 MiB** (`_STREAM_CHUNK`), forwards `Range: bytes=start-end` to Drive's `files/<id>?alt=media`, and returns a **fully-buffered `206`** with `Content-Range`/`Content-Length`/`Accept-Ranges`. Buffered (not streamed) because browsers stalled on the proxied *streaming* body over HTTP/2; an 8 MiB bounded buffer is bulletproof and keeps each request short (proxy/worker friendly, no long-held connections, no gunicorn timeout).
- **`backend/api/google_drive.py`** — `CURSO_BEBE_ROOT_FOLDER` constant + `get_file_meta(...)` (size/mimeType/parents) + `is_descendant_of(...)`.
- **`backend/api/urls.py`** — registers the `curso-stream` route next to the other Drive routes.
- **`backend/entrypoint.sh`** — gunicorn workers 2 → 4 (headroom for concurrent streaming).

## Data flow

- **Video:** `<video src=/api/google/drive/stream/<id>/>` → browser issues `Range` requests → `CursoStreamView` scope-checks (cached) → fetches the capped range from Drive via `AuthorizedSession` → returns buffered `206`. Browser requests successive 8 MiB ranges as it plays/seeks.
- **PDF:** main pane iframe → `https://drive.google.com/file/d/<id>/preview`.

## Dependencies & assumptions

- Requires the Drive folder `Curso Bebê - Brunna (Hotmart)` shared **"anyone with the link"** (already enabled) AND the connected `GoogleAccount` having Drive scope.
- The MP4s are faststart (moov at front), ideal for progressive range playback.
- No new Python packages (`google-api-python-client`, `requests`, `google-auth` already present). No DB models/migrations.

## Non-goals

Progress/resume, watched-state, notes/checklists, in-app editing of the catalog, dynamic Drive sync.

## Verification

- `npm run build` (vite) compiles clean; backend `py_compile` clean.
- **Server proven correct** independent of any player: `curl`/in-page `fetch` of the stream endpoint return `206`, `content-type: video/mp4`, correct `Content-Range` (e.g. `bytes 0-8388607/9743793`), full 8 MiB body, faststart `moov` in the first chunk.
- **Note on visual verification:** the claude-in-chrome automation tab cannot play *any* `<video>` (a known-good external sample MP4 stalls identically — `readyState 0`, no error), so in-app playback can't be confirmed from automation. Confirmed working in a real browser by the operator.
- Mac is edit-only — ship via commit + push to `vps-deploy` (Dokploy auto-redeploy). Backend container: `compose-hack-1080p-array-fcyr5i-backend-1`.

## Commits (branch `vps-deploy`)

`3fc4561` feature (sub-tab + catalog + Drive-preview embeds) · `746f471` a11y/referrerPolicy · `7645ee9` streaming proxy + native `<video>` · `6c797df` AuthorizedSession (401 fix) · `6775315` buffered 206 (Chrome spinner fix).
