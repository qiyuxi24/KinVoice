# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KinVoice (package: `com.kinvoice.app`) is a **QuickApp (快应用)** mobile app — a lightweight Android app framework native to Chinese OEMs. The app, named "Cloudie", is a parent-child emotional communication companion that uses AI to promote Nonviolent Communication (NVC).

- **Frontend**: QuickApp `.ux` single-file components (template + script + style), Less styling, Prettier formatting
- **Backend**: FastAPI + Uvicorn, async SQLite (aiosqlite + SQLAlchemy 2.0), OpenAI-compatible LLM integration (vivo API)
- **AI**: LLM service for companion chat, NVC text conversion, AI profile writing, and card summarization

## Essential Commands

### Frontend (QuickApp)

```bash
yarn build          # Build rpk package
yarn release        # Build with signature
yarn server         # Start dev server
yarn gen PageName   # Generate new page from template
yarn prettier       # Format all code
yarn prettier-watch # Watch and auto-format (recommended)
```

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env        # Edit with real LLM_API_KEY etc.
python init_db.py            # Initialize SQLite database
python start.py              # One-click startup (recommended)
# OR
uvicorn app.main:app --reload --port 8000
```

After backend starts, API docs at `http://localhost:8000/docs`.

## Architecture

### Frontend (`src/`)

- **Entry point**: `src/app.ux` — injects `$utils` and `$apis` into `global` for all pages
- **Pages**: 10 pages in `src/pages/` — `.ux` single-file components
- **Routing**: `src/manifest.json` → `router.pages`. Entry: `pages/Companion`. Navigation: `router.replace({ uri: '/pages/PageName' })`
- **API layer**: Three-tier architecture:
  - **Layer 1**: `helper/ajax.js` — Promise wrapper for `@system.fetch`, integrated error codes, 20s timeout with timer cleanup, QuickApp Studio proxy unwrapping
  - **Layer 2**: `helper/apis/` — **Manual import** in `index.js` (NOT auto-scan; QuickApp does not support `require.context`). Each module wraps one backend endpoint group
  - **Layer 3**: Global injection via `app.ux` → `$apis` accessible in all pages
- **User identity**: `helper/userIdentity.js` — UUID stored in localStorage, passed in request body (not header)
- **Styling**: Less preprocessor. Shared variables/mixins in `src/assets/styles/`

### Backend (`backend/app/`) — 9 Route Modules

| Route | Endpoint | Purpose |
|-------|----------|---------|
| `chat` | `POST /chat` | AI companion conversation (Cloudie + NVC) |
| `memory` | `CRUD /cards` | Memory cards + conversation favorites |
| `summarize` | `POST /summarize` | Conversation summary |
| `chatroom` | `GET/POST /chatroom/*` | Family chat (private/group) |
| `profile` | `CRUD /profiles` | Family member profiles |
| `profile_ai` | `POST/GET /profile/ai/*` | AI profile writing/reading |
| `family` | `POST/GET /family/*` | Family group create/join/leave |
| `tts` | `POST /tts` | TTS text-to-speech (vivo) |
| `replica` | `POST /replica` | Voice cloning (xia branch) |

**Layered architecture**: Routes (`api/`) → Services (`services/`) → Models + Schemas → DB (`db/session.py`)

**Key services**:
- `llm_service.py` — Unified LLM call (xia `call_llm/chat` + si `chat_completion` compatible), Mock mode, 3600s timeout
- `cloudie_prompt.py` — Cloudie companion system prompt
- `card_summarizer.py` — Extract cards from conversations

**Models** (7 tables): `Card`, `Conversation`, `ChatMessage`, `FamilyMember`, `User`, `FamilyGroup`, `FamilyMembership`

**DB session**: `session.py` provides both `get_session()` (FastAPI DI with auto commit/rollback) and `AsyncSessionLocal` (manual transaction)

### Key Config

- **Frontend baseUrl**: `src/helper/apis/config.js` → `http://localhost:8000` (simulator) / LAN IP (real device)
- **Backend .env**: `LLM_API_KEY`, `LLM_API_BASE`, `LLM_MODEL`, `ALLOWED_ORIGINS`, `DATABASE_URL`, `LOG_LEVEL`
- **User identity**: Frontend generates UUID → stored in localStorage → passed as `user_id` in request body

### QuickApp-Specific Quirks

1. **@system.fetch response**: Returns `{ code, headers, data: "JSON字符串" }` — needs explicit `JSON.parse`. QuickApp Studio may wrap in an additional `{ code, headers, data }` proxy layer — `ajax.js` auto-detects and unwraps this.
2. **Content-Type**: Must be set explicitly for POST/PUT; some QuickApp versions auto-convert to form-urlencoded otherwise.
3. **Timer cleanup**: `Promise.race` timeout timers must be `clearTimeout()`'d on success, or the timer pool drains and the app becomes unresponsive.
4. **require.context**: NOT supported; use manual imports in `index.js`.
5. **Line endings**: Must be CRLF; LF files may cause page load failure.

### Page Structure

| Page | Route | Purpose |
|------|-------|---------|
| Companion | `pages/Companion` (entry) | AI chatbot, Cloudie mascot, NVC responses |
| BreakIce | `pages/BreakIce` | NVC text conversion (anger → gentle expression) |
| Memory | `pages/Memory` | Memory cards by category + conversation favorites |
| ChatRoom | `pages/ChatRoom` | Family member real-time chat (private/group) |
| Family | `pages/Family` | Create/view family groups |
| FamilyJoin | `pages/FamilyJoin` | Join family by ID + password |
| Profile | `pages/Profile` | User settings, family profile list |
| ProfileDetail | `pages/ProfileDetail` | Individual family member profile detail |

### Data Flow

```
User input in page
  → $apis.chat.sendMessage({ message, history })
    → ajax.post(`${baseUrl}/chat`, { message, history, emotion_state })
      → fetchPromise → $fetch.fetch → Promise.race([fetch, timeout])
        → 2xx → resolve(parsedJson)
        → non-2xx → reject({ code, message, detail, level, raw, isError })
  → .then(data → update UI) / .catch(err → show error or fallback)
```

For family/chatroom endpoints: user_id is passed in request body (from `userIdentity.getUserId()`), not in headers.
