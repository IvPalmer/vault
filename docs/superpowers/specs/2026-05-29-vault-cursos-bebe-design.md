# Cursos sub-view under Família (Saúde) — design

**Date:** 2026-05-29
**Status:** implemented
**Scope:** Surface the archived baby-prep courses (Brunna's Hotmart purchases, saved to Google Drive) inside Vault as an in-app, browse-and-watch course view.

## Goal

Under the **Família** tab of the Saúde module, add a tab-like view that lets Palmer/Rafa browse and watch the three archived courses without leaving the app: **5 Aulas para a Maternidade**, **Enxoval Inteligente** (8 modules + aulas bônus + oficina de carrinhos), and the **O Ano de Ouro** e-book (PDF).

## Decisions (from brainstorming)

- **Interactivity:** browse + watch only. No progress tracking, no notes, no backend. (Can grow later.)
- **Content:** all three courses.
- **Approach:** curated static catalog + Google Drive preview embeds (vs. a live Drive folder listing). Curated gives real module names/order and a polished course feel for ~the same effort; the live-listing route would expose raw filenames and reverse-engineered grouping.

## Architecture (frontend-only)

- **`src/components/saude/babyCourses.js`** — static catalog. `course → modules → lessons`; each `lesson = { title, type: 'video'|'pdf', driveId, duration? }`. IDs are the Google Drive file IDs from the archive. Adding content later = edit this file.
- **`src/components/saude/CursosView.jsx`** — two-pane component: left rail (course → module → lesson, click to select) + main pane that embeds the active lesson via `https://drive.google.com/file/d/<driveId>/preview` (16:9 box for video, tall box for PDF) plus an "Abrir no Google Drive" fallback link. Selection held in local `useState` (defaults to first lesson). No data fetching.
- **`src/components/saude/cursos.module.css`** — styles, palette mirrors `Saude.module.css`.
- **`src/components/Saude.jsx`** — `FamiliaView` gains a sub-tab bar (reusing existing `styles.subTabs/subTab/subTabActive`): **Acompanhamento** (existing pregnancy dashboard, default) | **Cursos** (new). The existing dashboard's `isLoading`/`!ativa` guards moved inside the Acompanhamento branch so Cursos renders independently of pregnancy state. Hooks stay unconditional at the top of the component.

## Data flow

Static module import → `CursosView` renders rail from `BABY_COURSES` → user clicks a lesson → `activeId` state updates → main pane re-points the `<iframe>` (keyed on `driveId`) at the Drive preview URL.

## Dependencies & assumptions

- Playback relies on the Drive folder `Curso Bebê - Brunna (Hotmart)` being shared **"anyone with the link"** (already enabled). If sharing is revoked, embeds break and the "Abrir no Drive" link is the fallback.
- No new packages, no backend models/endpoints, no migrations.

## Non-goals

Progress/resume, watched-state, notes/checklists, in-app editing of the catalog, dynamic Drive sync. Out of scope by decision.

## Verification

`npm run build` (vite) compiles clean. Visual check on the deployed app (vault.grooveops.dev → Saúde → Família → Cursos): rail lists all courses/modules/lessons; selecting a video plays the embedded Drive player; selecting the e-book renders the PDF; "Abrir no Drive" opens the file. Mac is edit-only — ship via commit + push (Dokploy auto-redeploy).
