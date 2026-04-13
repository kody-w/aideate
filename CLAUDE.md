# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AIdeate is a local-first, privacy-safe workshop tool for identifying and prioritizing AI use cases with customers. It's an internal Microsoft tool built as static HTML — no server, no build step, no npm, no framework. All JavaScript is embedded in `<script>` tags within HTML files.

## Running Locally

```bash
./start.sh          # Serves on http://localhost:8765 via python3 http.server
./start.sh 9000     # Custom port
```

HTTP is recommended. `file://` also works for basic functionality.

## Testing

Open `tests.html` in a browser and click "Run All Tests." There are 37 tests covering JSON schema, localStorage persistence, import/export, unified app structure, PII checks, and PWA functionality. There is no CLI test runner — tests run entirely in the browser DOM.

## Architecture

### Single-page interactive presentation

- **`index.html`** — The entire app in one file. A 12-slide presentation deck with a slide-out drawer for all operator controls.
- The slide deck is the main view (full-screen, shareable via screen share).
- A **gear icon (FAB)** in the bottom-right corner opens a **380px drawer** from the right edge containing all workshop controls.
- Drawer sections are **context-aware** — they show/hide based on the current slide via `data-context` attributes.
- Keyboard: arrow keys navigate slides, `G` toggles the drawer, `Escape` closes it, `F` toggles fullscreen.

### State management

A single centralized `state` object holds all workshop data. Key fields: `sessionId`, `workshopName`, `companyName`, `phase` (ideate/vote/evaluate/prioritize), `participants` (array of `{id, name, title, initials}`), `ideas` (with votes/voters/evaluation), `timerSeconds`, `demoSlides`, `departments`. Every mutation autosaves to `localStorage` and directly calls the relevant render functions.

### Persistence

- **localStorage key**: `aideate_autosave`
- **JSON import/export**: Full workshop state round-trips through `.json` files (see `samples/` for schema examples)

### PWA / Offline

- `sw.js` — Service worker with stale-while-revalidate for HTML, cache-first for assets. Cache version: `aideate-v4`.
- `manifest.json` — PWA manifest (Microsoft Fluent theme color `#0078d4`, `standalone` display).

### AI Integration (optional)

GitHub Models API (`models.inference.ai.azure.com`) for formatting raw chat text into structured use cases and AI-powered evaluation of ideas. Requires a user-provided GitHub Personal Access Token stored in localStorage. Triggered by "Format with AI" and "Fill with AI" buttons in the drawer.

## Key Constraints

- **No build step or transpilation** — edit HTML/JS/CSS directly, changes are live on reload.
- **No dependencies** — zero npm packages, zero CDN links. Everything is vanilla JS/CSS.
- **Single-file architecture** — `index.html` is self-contained with inline `<script>` and `<style>` tags. There is no `src/` directory.
- **Privacy-first** — no PII hardcoded, no server calls except optional AI formatting, all data stays in browser localStorage.
- **License** — internal Microsoft tool, not for external distribution.
