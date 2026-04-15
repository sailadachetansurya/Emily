# ECHO — Emotional Chronicle

> **Your mind, decoded.** A Gen Z mental health companion powered by AI.

![Status](https://img.shields.io/badge/status-alpha-orange)
![License](https://img.shields.io/badge/license-MIT-blue)
![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)
![Tailwind](https://img.shields.io/badge/Tailwind-CSS-38B2AC?logo=tailwind-css)

---

## 🎨 Design System: "Gen Z Pulse"

| Element | Choice |
|---------|--------|
| **Style** | Neubrutalism + OLED Dark |
| **Palette** | "The Neon Remedy" |
| **Primary** | Electric Violet `#8B5CF6` (Empathy) |
| **Secondary** | Acid Green `#A3E635` (Recovery) |
| **Accent** | Blaze Orange `#F97316` (Triggers) |
| **Background** | OLED Black `#050505` |
| **Typography** | Orbitron • Inter • JetBrains Mono |
| **Shadows** | Hard, flat — NO blur |
| **Animations** | 150ms snap transitions |

---

## 🚀 Quick Start

```bash
cd D:\dheer@j\Emily\ECHO_website
npm install
npm run dev
```

Open → **http://localhost:3000**

---

## 📦 Tech Stack

| Layer | Technology |
|-------|------------|
| **Framework** | Next.js 14 (App Router) |
| **Styling** | Tailwind CSS + Custom |
| **Animations** | Framer Motion |
| **3D Background** | Three.js + R3F + Drei |
| **Language** | TypeScript (Strict) |
| **Backend** | Emily (Python FastAPI) |

---

## 📁 Project Structure

```
ECHO_website/
│
├── 📄 package.json           # Dependencies & scripts
├── 📄 tailwind.config.ts     # Design tokens
├── 📄 tsconfig.json          # TypeScript config
├── 📄 next.config.mjs        # Next.js config
├── 📄 postcss.config.js      # PostCSS plugins
│
├── 📂 src/
│   ├── 📂 app/
│   │   ├── layout.tsx        # Root layout + fonts
│   │   ├── page.tsx          # Main dashboard
│   │   └── api/              # API routes (TODO)
│   │
│   ├── 📂 components/
│   │   ├── Card.tsx          # Neubrutalism card
│   │   ├── Button.tsx        # Bold button
│   │   ├── Input.tsx         # Form input
│   │   └── BentoGrid.tsx     # Grid layout
│   │
│   ├── 📂 lib/
│   │   └── emily-api.ts      # Emily backend client
│   │
│   └── 📂 styles/
│       └── globals.css       # Tailwind + custom
│
├── 📂 public/                # Static assets
│
└── 📄 README.md              # You are here
```

---

## 🎯 Features

### Dashboard Components

| Component | Description |
|-----------|-------------|
| **Journal Card** | 2-column textarea for entries + action buttons |
| **Mood Check** | 5 emoji-based quick mood selector |
| **Week Summary** | Stats: entries, avg mood, streak counter |
| **Recent Insights** | AI-generated patterns & observations |
| **Triggers Map** | Tagged triggers with visual indicators |

### Coming Soon

- [ ] Real-time emotion analysis
- [ ] Emotional memory timeline
- [ ] Personalized coping strategies
- [ ] Export data (PDF/JSON)
- [ ] Dark/Light theme toggle
- [ ] Mobile responsive layout

---

## 🔌 Emily Backend Integration

The Python emotive pipeline lives at `D:\dheer@j\Emily`.

### Integration Steps

1. **Expose Emily as FastAPI server**
2. **Create API routes** in `src/app/api/`
3. **Connect** journal input → emotion analysis → insights

### Configuration

```ts
// src/lib/emily-api.ts
const EMILY_BASE_URL = process.env.EMILY_API_URL || "http://localhost:8000";
```

---

## 🎨 Design Tokens

All design tokens are defined in [`tailwind.config.ts`](./tailwind.config.ts):

```ts
colors: {
  background: "#050505",
  electric: {
    violet: "#8B5CF6",  // Empathy
    green: "#A3E635",   // Recovery
    orange: "#F97316",  // Triggers
  }
}
boxShadow: {
  hard: "6px 6px 0px 0px #000000",
  glow: "0 0 20px rgba(139, 92, 246, 0.5)"
}
```

---

## 📚 Documentation

| Doc | Purpose |
|-----|---------|
| [QUICKSTART.md](./QUICKSTART.md) | Get running in 5 minutes |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | System design & data flow |

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Submit a PR

---

## 📝 License

MIT — Built with 💜 for Gen Z mental wellness.

---

<div align="center">

**ECHO v0.1.0** • [Report Issue](https://github.com/echo/issues) • [View Docs](https://echo/docs)

</div>
