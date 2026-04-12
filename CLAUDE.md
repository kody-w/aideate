# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AIdeate is a local-first, privacy-safe workshop tool for identifying and prioritizing AI use cases with customers. It's an internal Microsoft tool built as static HTML — no server, no build step, no npm, no framework. All JavaScript is embedded in `<script>` tags within HTML files.

## Running Locally

```bash
./start.sh          # Serves on http://localhost:8765 via python3 http.server
./start.sh 9000     # Custom port
```

HTTP is required (not `file://`) because BroadcastChannel and iframes need same-origin context.

## Testing

Open `tests.html` in a browser and click "Run All Tests." There are 37 tests covering JSON schema, BroadcastChannel sync, localStorage, file I/O, rendering, and state updates. There is no CLI test runner — tests run entirely in the browser DOM.

## Architecture

### Two-window design

- **`index.html`** (Presenter) — 11-slide deck shown via screen share. Receives state updates and renders live data.
- **`control.html`** (Control Panel) — Operator UI on a second monitor. Manages all workshop state and broadcasts changes.

### Sync mechanism

The control panel broadcasts state to the presenter via the **BroadcastChannel API** (browser-native, same-origin). Messages are typed objects: `{ type, ...payload }`. Session IDs prevent cross-talk between concurrent workshops.

### State management

A single centralized `state` object in each HTML file holds all workshop data. Key fields: `sessionId`, `workshopName`, `companyName`, `phase` (ideate/vote/prioritize), `participants`, `ideas` (with votes/voters), `timerSeconds`, `demoSlides`, `departments`. Every mutation autosaves to `localStorage` and broadcasts to the presenter.

### Persistence

- **localStorage keys**: `aideate_autosave`, `aideate_session_id`, `aideate_presenter_state:{sessionId}`
- **JSON import/export**: Full workshop state round-trips through `.json` files (see `samples/` for schema examples)

### PWA / Offline

- `sw.js` — Service worker with stale-while-revalidate for HTML, cache-first for assets. Cache version: `aideate-v2`.
- `manifest.json` — PWA manifest (Microsoft Fluent theme color `#0078d4`, `minimal-ui` display).

### AI Integration (optional)

GitHub Models API (`models.inference.ai.azure.com`) for formatting raw chat text into structured use cases. Requires a user-provided GitHub Personal Access Token stored in localStorage. Triggered by the "Format with AI" button in the control panel.

## Key Constraints

- **No build step or transpilation** — edit HTML/JS/CSS directly, changes are live on reload.
- **No dependencies** — zero npm packages, zero CDN links. Everything is vanilla JS/CSS.
- **Single-file architecture** — each HTML file is self-contained with inline `<script>` and `<style>` tags. There is no `src/` directory.
- **Privacy-first** — no PII hardcoded, no server calls except optional AI formatting, all data stays in browser localStorage.
- **License** — internal Microsoft tool, not for external distribution.
