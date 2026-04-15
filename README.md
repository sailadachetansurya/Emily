# 🌟 Emily: The Emotive Intelligence Ecosystem

> **Bridging the gap between human affect and machine logic.**

Emily is a state-of-the-art framework for building emotionally intelligent systems. This repository integrates deep emotional analysis, longitudinal memory tracking, and a premium wellness interface designed to foster empathy and self-awareness.

---

## 🏗️ Architecture: The Monorepo Breakdown

To maintain production-grade scalability and clarity, the ecosystem is organized into two primary pillars:

### 🧠 [Core Engine](./core)
The "Brain" of Emily. This directory contains the NLP models, training pipelines, and the emotional policy system.
- **Emotion Extraction**: Multi-dimensional valence/arousal/stability detection.
- **Dataset Management**: Specialized pipelines for emotional ground-truth processing.
- **Policy Engine**: Deterministic rules for safe and empathetic AI interactions.

### 🌐 [ECHO Platform](./web)
The "Heart" of Emily. A high-fidelity Next.js web application for users to journal, track, and visualize their emotional journey.
- **Emotional Timeline**: Interactive temporal analysis using Recharts.
- **Trigger Mapping**: Discovery of environmental and social emotional triggers.
- **Recovery Dashboard**: Metric-driven progress tracking for wellness.

---

## 🚀 Quick Start

### 1. Requirements
- **Node.js**: 18.x or higher
- **Python**: 3.10+ (for core engine)
- **Git**: Professional workflow enabled

### 2. Spinning up the Web Platform
```bash
cd web
npm install
npm run dev
```

### 3. Running Core AI Tasks
```bash
cd core
pip install -r requirements-api.txt
python run_prepare_emotion_dataset.py
```

---

## 📊 Documentation & Research

We provide comprehensive guides and scholarly synthesis for deep exploration:

- 📑 **[NotebookLM Master Prompt](./docs/NOTEBOOKLM_MASTER_PROMPT_EMOTIONAL_INTELLIGENCE.md)**: Paste this into Google NotebookLM for a 10/10 research experience.
- 🔬 **[NLP Training Essentials](./docs/NLP%20Emotion%20Model%20Training%20Essentials.md)**: Deep dive into the model architecture.
- 🛡️ **[Safety & Policy Guide](./docs/Basic%20Emotive%20AI%20Implementation%20Guide.md)**: How we ensure responsible emotive AI.

---

## 🛠️ Contribution Workflow

1. **Branching**: Always branch from `main` using `feature/` or `fix/` prefixes.
2. **Structure**: Keep logic in `core/` and UI in `web/`.
3. **Commit Messages**: Use conventional commits (e.g., `feat(web): add recovery charts`).

---

## 📡 Deployment (Netlify/Vercel)

This repo is optimized for **Netlify**.
- **Base directory**: `web`
- **Build command**: `npm run build`
- **Publish directory**: `.next`

---

*Made with ❤️ by the Emily Contributors.*
