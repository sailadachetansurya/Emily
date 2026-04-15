# ⚡ ECHO Quick Start Guide

> Get the ECHO dashboard running in **5 minutes**.

---

## 🎯 What You'll Build

A **Gen Z-focused mental health dashboard** featuring:

✅ **Neubrutalism OLED Dark** design system  
✅ **Neon accent colors** (Violet, Green, Orange)  
✅ **Hard shadows** & bold borders  
✅ **Orbitron** display font + **JetBrains Mono** for data  
✅ **Bento grid** responsive layout  
✅ **4 core components**: Card, Button, Input, BentoGrid  

---

## 📦 Step 1: Install Dependencies

```bash
cd D:\dheer@j\Emily\ECHO_website
npm install
```

<details>
<summary><strong>⚠️ Troubleshooting install errors</strong></summary>

```bash
# Clear cache
npm cache clean --force

# Delete node_modules
rm -rf node_modules package-lock.json

# Reinstall
npm install
```
</details>

---

## 🚀 Step 2: Start Dev Server

```bash
npm run dev
```

Expected output:
```
> echo-website@0.1.0 dev
> next dev

  ▲ Next.js 14.2.3
  - Local:        http://localhost:3000
  - Ready in:     2.5s
```

---

## 🎨 Step 3: Open in Browser

Navigate to **http://localhost:3000**

### What You'll See

```
┌─────────────────────────────────────────────────────────┐
│  ECHO                    [OLED Dark Background]         │
│  Emotional Chronicle                                    │
│                                                         │
│  ┌─────────────────────────┐ ┌─────────┐ ┌───────────┐ │
│  │ 📝 New Entry            │ │ 😊 Mood │ │ 📊 Week   │ │
│  │ [Textarea...]           │ │ Check   │ │ Summary   │ │
│  │ [Analyze] [Save]        │ │ [Buttons│ │ [Stats]   │ │
│  └─────────────────────────┘ └─────────┘ └───────────┘ │
│  ┌─────────────────────────┐ ┌───────────────────────┐ │
│  │ 💡 Recent Insights      │ │ ⚠️ Triggers Map       │ │
│  │ [AI Patterns...]        │ │ [Tag Cloud...]        │ │
│  └─────────────────────────┘ └───────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 🧪 Step 4: Test Interactions

### Hover Effects
- Cards should **slide up-left** on hover
- Shadow increases from `4px` → `8px`

### Click Effects
- Cards should **press down-right** when clicked
- Buttons have **snappy 150ms** transitions

### Focus States
- Input fields glow **Electric Violet** when focused
```ts
shadow-[0_0_15px_rgba(139,92,246,0.3)]
```

---

## 📁 Files Created

| File | Purpose |
|------|---------|
| `package.json` | Dependencies (Next.js, Tailwind, Framer Motion) |
| `tailwind.config.ts` | Design tokens (colors, shadows, fonts) |
| `tsconfig.json` | TypeScript configuration |
| `next.config.mjs` | Next.js build config |
| `postcss.config.js` | Tailwind plugin |
| `.gitignore` | Git exclusions |
| `src/styles/globals.css` | Global styles + Tailwind |
| `src/app/layout.tsx` | Root layout with fonts |
| `src/app/page.tsx` | Main dashboard page |
| `src/components/Card.tsx` | Animated card component |
| `src/components/Button.tsx` | Neubrutalism button |
| `src/components/Input.tsx` | Form input component |
| `src/components/BentoGrid.tsx` | Grid layout system |
| `src/lib/emily-api.ts` | Emily API client |

---

## 🎨 Design System Reference

### Colors

```ts
// tailwind.config.ts
background: "#050505"      // OLED black
electric.violet: "#8B5CF6" // Empathy
electric.green: "#A3E635"  // Recovery  
electric.orange: "#F97316" // Triggers
```

### Shadows (HARD — No Blur)

```ts
shadow-hard: "6px 6px 0px 0px #000000"
shadow-glow-violet: "0 0 20px rgba(139, 92, 246, 0.5)"
```

### Animations (SNAPPY — Not Slow)

```ts
duration-150: "150ms"
ease-snap: "cubic-bezier(0.5, 0, 1, 1)"
```

---

## 🔌 Emily Integration Status

| Status | Component |
|--------|-----------|
| ✅ | Frontend dashboard |
| ✅ | Mock/fallback responses |
| ⏳ | FastAPI backend |
| ⏳ | Real emotion analysis |

### TODO: Connect Emily

1. Start Emily pipeline as FastAPI server
2. Update `EMILY_API_URL` in `src/lib/emily-api.ts`
3. Connect journal input → `/api/pipeline/analyze`

---

## 📋 Next Steps Checklist

### Immediate (30 min)
- [ ] Run `npm install && npm run dev`
- [ ] Verify dashboard renders
- [ ] Test hover/click animations

### Short-term (2-4 hours)
- [ ] Set up Emily FastAPI server
- [ ] Connect journal analysis endpoint
- [ ] Add Three.js animated background

### Medium-term (1-2 days)
- [ ] User sessions (localStorage)
- [ ] Emotional memory persistence
- [ ] Insights visualization
- [ ] Responsive mobile layout

---

## 🆘 Troubleshooting

| Error | Solution |
|-------|----------|
| `Module not found` | Run `npm install` |
| Styles not loading | Check `layout.tsx` imports `globals.css` |
| Emily API not responding | Fallback mode activates automatically |
| Port 3000 in use | Run `npm run dev -- -p 3001` |

---

<div align="center">

**⚡ Done!** Ready to iterate.

[View Architecture](./ARCHITECTURE.md) • [Report Issue](#)

</div>
