# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Quick Commands

```bash
npm install          # Install dependencies
npm run dev          # Start dev server (http://localhost:3000)
npm run build        # Production build
npm run start        # Start production server
npm run lint         # ESLint check
```

## High-Level Architecture

### System Overview

ECHO is a Gen Z-focused mental health dashboard with a "Neubrutalism + OLED Dark" design aesthetic. It consists of:

```
┌─────────────────────────────────────────┐
│  ECHO Frontend (Next.js 14 + Tailwind)  │
│  - Animated Three.js background         │
│  - Framer Motion interactions           │
│  - Bento grid dashboard layout          │
└─────────────────────────────────────────┘
              │ HTTP/REST
              ▼
┌─────────────────────────────────────────┐
│  Emily Backend (Python FastAPI)         │
│  Location: D:\dheer@j\Emily             │
│  - Emotion classification pipeline      │
│  - LLM-powered response generation      │
│  - Safety processing                    │
└─────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript (strict mode) |
| Styling | Tailwind CSS with custom design tokens |
| Animations | Framer Motion (150ms snap transitions) |
| 3D Background | Three.js + @react-three/fiber + @react-three/drei |
| Backend | Emily (Python FastAPI at `D:\dheer@j\Emily`) |

### Design System: "Gen Z Pulse"

Defined in `tailwind.config.ts`:

- **Colors**: OLED Black `#050505` background with Electric Violet (empathy), Acid Green (recovery), Blaze Orange (triggers)
- **Shadows**: Hard, flat shadows (NO blur) - `shadow-hard`, `shadow-glow-*` variants
- **Typography**: Orbitron (display), Inter (body), JetBrains Mono (data)
- **Animations**: 150-200ms snap transitions, spring easing

### Component Architecture

```
src/
├── app/
│   ├── layout.tsx        # Root layout, font imports, ParticleBackground
│   └── page.tsx          # Dashboard with BentoGrid layout
├── components/
│   ├── Card.tsx          # Animated card with hover/tap states
│   ├── Button.tsx        # Neubrutalism button variants
│   ├── Input.tsx         # Form input with focus glow
│   ├── BentoGrid.tsx     # Grid + Item components (responsive)
│   └── ParticleBackground.tsx  # Three.js animated background
└── lib/
    └── emily-api.ts      # Emily API client with fallback mode
```

### Key Integration Points

**Emily API Client** (`src/lib/emily-api.ts`):
- Connects to `http://localhost:8000` (configurable via `EMILY_API_URL` env var)
- Has built-in fallback responses when backend is unavailable
- Main endpoints: `/api/pipeline/analyze` (journal → emotion analysis)

**To start Emily backend**:
```bash
cd D:\dheer@j\Emily
.venv\Scripts\python -m uvicorn src.pipeline.api:app --reload
```

### Data Flow

1. User types journal entry → stored in local component state
2. "Analyze" button → `EmilyAPIClient.analyzeJournal()` → POST to Emily
3. Emily processes through: Input Gateway → Emotion Engine → Memory Manager → Policy Engine → Prompt Builder → LLM → Safety Processor
4. Response displayed in UI with emotion-based color mapping

### Current State

- ✅ Frontend dashboard fully functional with mock/fallback data
- ✅ All core components implemented (Card, Button, Input, BentoGrid)
- ✅ Three.js particle background animated
- ⏳ Emily backend integration ready but requires backend to be running
- ⏳ API routes in `src/app/api/` are TODO

### Common Tasks

**Run dev server**:
```bash
npm run dev
```

**If port 3000 is in use**:
```bash
npm run dev -- -p 3001
```

**Troubleshoot install issues**:
```bash
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```
