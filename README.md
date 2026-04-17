---
title: ECHO Emily Backend
emoji: 🧠
colorFrom: indigo
colorTo: pink
sdk: docker
app_port: 7860
pinned: false
---

# 🌟 Emily: The Emotive Intelligence Ecosystem

> **Bridging the gap between human affect and machine logic.**

Emily is a high-performance framework for building emotionally intelligent systems. This repository contains the **Core AI Engine** and the **ECHO Platform** (Next.js OS-style interface).

---

## 🏗️ Project Structure

This is a **monorepo** split into two primary pillars:

| Component | Location | Responsibility |
| :--- | :--- | :--- |
| **🧠 Core Engine** | `core/` | FastAPI Backend, NLP Models, SQLite Persistence |
| **🌐 ECHO Platform** | `web/` | Next.js Frontend (Neubrutalist OS UI) |

---

## 🚀 For Contributors (Local Setup)

If you are a collaborator, follow these steps to run the full stack locally.

### 1. Requirements
- **Node.js**: 18.x or higher
- **Python**: 3.10 or 3.11 (Recommended)

### 2. Backend Setup (`core`)
1.  **Navigate & Virtual Env**:
    ```powershell
    cd core
    python -m venv .venv
    .venv\Scripts\activate # On Windows
    ```
2.  **Install Dependencies**:
    ```powershell
    pip install -r requirements.txt
    pip install -e . # Install as editable package
    ```
3.  **Run the API**:
    On Windows (PowerShell):
    ```powershell
    $env:PYTHONPATH="src"
    python -m uvicorn pipeline.api.main:app --reload --port 8000
    ```
    *(The backend will run at http://localhost:8000)*

### 3. Frontend Setup (`web`)
1.  **Navigate & Install**:
    ```powershell
    cd web
    npm install
    ```
2.  **Environment Config**:
    Create a `.env.local` file inside the `web/` directory:
    ```env
    NEXT_PUBLIC_API_URL=http://localhost:8000
    ```
3.  **Launch Dashboard**:
    ```powershell
    npm run dev
    ```
    *(The UI will be visible at http://localhost:3000)*

---

## 📡 Deployment Guide

### Frontend (Netlify)
- **Base directory**: `web`
- **Build command**: `npm run build`
- **Publish directory**: `.next`
- **Environment Variables**: Set `NEXT_PUBLIC_API_URL` to your live backend URL.

### Backend (Hugging Face Spaces / Docker)
The project includes a `Dockerfile` optimized for **Hugging Face Spaces** (Docker SDK).

1.  Create a new **Docker Space** on Hugging Face.
2.  **Sync Code**: Use the GitHub Action provided in `.github/workflows/sync_to_hf_space.yml`.
    - You MUST add your `HF_TOKEN` as a Secret in your GitHub Repo settings for this to work.
3.  **Hugging Face Environment Variables**:
    - `ECHO_ALLOWED_ORIGINS`: Set this to your Netlify URL (e.g., `https://emilysecho.netlify.app`) to fix CORS issues.

---

## 🛠️ Troubleshooting

### "Request failed: 500" on Login
This usually happens if the backend cannot write to its database or if CORS is blocking the request.
1.  **Check CORS**: Ensure `ECHO_ALLOWED_ORIGINS` on your backend host includes your Netlify address.
2.  **Check Database Permissions**: The backend tries to save data to `/data/echo_app.db`. Ensure your hosting provider allows writing to that path.

### Sync issues
The GitHub Action only runs on the repository where the `HF_TOKEN` secret is defined. If you are a collaborator, the sync will only happen if you set up your own Hugging Face Space and add your own token to your fork.

---

*Made with ❤️ by the Emily Contributors.*
