# AIdeate — AI Use-Case Prioritization Workshop

A local-first, privacy-safe workshop tool for identifying and prioritizing AI use cases with customers. Built as static HTML — no server, no build step, no data leaves your device. Installable as a PWA for fully offline use.

## Quick Start

```bash
./start.sh
```

This opens two browser windows:
- **Presenter** (`index.html`) — share this screen in Teams/Zoom
- **Control Panel** (`control.html`) — operate offscreen on your second monitor

Arrow keys navigate slides. The control panel syncs live to the presenter via BroadcastChannel.

## Install & Offline Use

AIdeate works three ways:

### 1. GitHub Pages (online)
Just visit the hosted URL. Works immediately in any browser.

### 2. Install as PWA (recommended for repeat use)
From the control panel, click **📲 Install App** (when your browser supports it). The app installs to your device and works fully offline — no server needed.

### 3. Download for local use
Click **📥 Download App (.zip)** in the control panel to download the full app. Extract and run:

```bash
cd aideate-main
./start.sh
```

Or just open `control.html` and `index.html` directly in your browser.

## How It Works

### Workshop Flow (11 slides)
1. **Welcome** — workshop name + company from your config
2. **Agenda** — 4 phases overview
3. **"We Came Prepared"** — pre-loaded use cases (from your JSON import)
4-7. **Demo slides** — configurable iframe URLs (optional, skipped if empty)
8. **Let's Get Started** — instructions for facilitator-driven flow
9. **💡 Ideate** — LIVE: ideas appear as you add them from the control panel
10. **🗳️ Vote** — LIVE: votes update in real-time as participants call them out
11. **📊 Results** — LIVE: podium + ranked table

### Control Panel Features
- **Workshop Setup** — name, company (broadcasts to presenter)
- **Import/Export** — full workshop state as `.json` (participants, ideas, votes, demos)
- **Participants** — named roster with avatars (shown on presenter)
- **Timer** — countdown with start/stop/reset
- **Demo URLs** — 4 configurable iframe slides with visibility toggles
- **Ideas** — add manually or paste from Teams chat
- **AI Formatting** — paste rough chat text, AI extracts structured use case (requires GitHub token)
- **Vote Control** — +/- per idea with voter names
- **Download/Install** — PWA install + offline ZIP download

## Privacy & Security

- **Zero PII hardcoded** — all customer content comes from your JSON import
- **Local-first** — autosaves to localStorage, export as `.json` file
- **No server calls** — except optional AI formatting (GitHub Models API, your token)
- **Session-scoped** — BroadcastChannel uses unique session IDs (no cross-talk)
- **GitHub Pages ready** — static files, HTTPS, no backend
- **Offline capable** — service worker caches all files for offline use

## JSON Import/Export

Export saves everything — import restores it instantly:

```json
{
  "version": "1.0",
  "sessionId": "abc123",
  "workshopName": "AI Workshop",
  "companyName": "Contoso",
  "participants": [
    { "id": 1001, "name": "Alice", "title": "VP Engineering", "initials": "A" }
  ],
  "ideas": [
    { "id": 2001, "name": "Sales Agent", "dept": "Sales", "desc": "...", "submitter": "Alice", "votes": 3, "voters": ["Alice","Bob","Charlie"] }
  ],
  "phase": "ideate",
  "timerSeconds": 300,
  "demoSlides": [
    { "label": "Demo 1", "url": "https://example.com/demo.html", "visible": true }
  ],
  "departments": ["Sales", "Operations", "HR", "IT"],
  "createdAt": "2026-04-09T12:00:00Z"
}
```

### Pre-loading Content for a Customer

1. Create a `.json` file with their company name, pre-identified use cases, and demo URLs
2. Open the control panel → click **📥 Import**
3. Everything loads into the presenter instantly
4. After the workshop, click **📤 Export** to save results with votes

## Files

| File | Purpose |
|------|---------|
| `index.html` | Presenter view (screen share this) |
| `control.html` | Offscreen control panel |
| `tests.html` | 37 automated tests |
| `start.sh` | Local HTTP server launcher |
| `manifest.json` | PWA web app manifest |
| `sw.js` | Service worker for offline caching |
| `icon.svg` | App icon |
| `samples/` | Example workshop JSON files |

## Requirements

- Modern browser (Chrome, Edge, Firefox, Safari)
- For local use: Python 3 (for `start.sh` HTTP server) or just open the HTML files directly
- For GitHub Pages: just push and enable Pages

## Disclaimer

AIdeate is an experimental tool created by the AI Business Applications Specialist Team (AIBAST) at Microsoft. Although the underlying browser features used by AIdeate are fully supported (such as BroadcastChannel, localStorage, Service Workers, etc.), AIdeate itself represents an example implementation of these features and is **not a supported Microsoft product**. It is provided "as-is" without warranty of any kind. Microsoft makes no guarantees regarding its suitability, reliability, or availability. Use of this tool is at your own risk.

Support for this project is limited to the [GitHub Issues](https://github.com/kody-w/aideate/issues) page. For issues with underlying browser features or platform capabilities, please refer to the respective browser vendor documentation.

## License

MIT
