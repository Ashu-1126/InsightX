# 🛡️ KavachG - AI Safety Command Center

KavachG is a state-of-the-art industrial safety monitoring and incident response platform. It leverages advanced YOLO-based AI models to provide real-time monitoring, PPE detection, fire/smoke alerts, and fall detection.

---

## 🏗️ Project Architecture

The project is structured into three primary components:

### 1. **🧠 Models**
Contains pre-trained YOLO weights and detection scripts specialized for industrial safety:
- **PPE Detection**: Monitors for Helmets, Vests, etc.
- **Fire & Smoke**: Real-time detection of fire and smoke hazards.
- **Fall Detection**: Identifies falls and unsafe postures.
- **Pose Detection**: Analyzes worker movements and ergonomic safety.

### 2. **⚙️ Backend**
A high-performance API built with **FastAPI** that orchestrates:
- Live camera stream processing.
- AI model inference on-demand.
- Incident logging and Database management (SQLite).
- JWT Authentication and Role-Based Access Control (RBAC).

### 3. **🖥️ Frontend**
A modern, responsive Command Center interface built with:
- **Vanilla JavaScript & CSS**: Lightweight and high-performance.
- **Live Video Streaming**: Multi-pane monitoring views.
- **Incident Dashboard**: Tracking, reporting, and exporting (CSV).

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- A modern web browser
- Webcam/Camera for live monitoring

### 1️⃣ Environment Setup
Create a virtual environment and install dependencies.

**🍎 macOS / Linux (bash/zsh):**
```bash
# Create venv (use python3 on macOS)
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Install Backend requirements
pip install -r Backend/requirements.txt
```

**🪟 Windows (PowerShell):**
```powershell
# Create venv
python -m venv .venv

# Activate venv
.\.venv\Scripts\Activate.ps1

# Install Backend requirements
pip install -r Backend/requirements.txt
```

### 2️⃣ Configuration
Copy the sample environment file and configure your credentials:

**🍎 macOS / Linux:**
```bash
cp Backend/.env.example Backend/.env
```

**🪟 Windows (PowerShell):**
```powershell
cp Backend/.env.example Backend/.env
```
*Edit `Backend/.env` to set your `SECRET_KEY` and admin credentials.*

---

## 🛠️ Running the Project

### Phase A: Start the Backend
From the root directory (`InsightX`):

**🍎 macOS / Linux:**
```bash
cd Backend
../.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**🪟 Windows (PowerShell):**
```powershell
cd Backend
..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend runs at: `http://127.0.0.1:8000`  •  API docs at `http://127.0.0.1:8000/docs`*

### Phase B: Start the Frontend (Next.js — SENTINEL AI)
The primary UI is a **Next.js** app in `sentinel-frontend/`. Open a **new terminal**.
Requires **Node.js 18+** (tested on Node 22). The first run needs `npm install`.

**🍎 macOS / Linux & 🪟 Windows (same commands):**
```bash
cd sentinel-frontend
npm install        # first time only
npm run dev        # runs on http://localhost:3000
```
*Frontend runs at: `http://localhost:3000`. The API URL is set in `sentinel-frontend/.env.local` (`NEXT_PUBLIC_API_URL=http://localhost:8000`).*

> ⚠️ **Note:** `sentinel-frontend/` is a Next.js app — it will **not** work with `python -m http.server`
> (you'll get 404s). That static-server approach only applies to the legacy `Frontend/` directory.

<details>
<summary>Legacy vanilla-JS frontend (<code>Frontend/</code>)</summary>

The older static frontend can be served with Python's built-in HTTP server:

**🍎 macOS / Linux:**
```bash
cd Frontend
python3 -m http.server 5500
```

**🪟 Windows (PowerShell):**
```powershell
cd Frontend
python -m http.server 5500
```
*Runs at: `http://127.0.0.1:5500`*
</details>

### Phase C: Initial Setup (Admin)
If this is your first time running KavachG, create the admin user.
This reads `ADMIN_EMAIL` / `ADMIN_PASSWORD` from `Backend/.env`:

**🍎 macOS / Linux:**
```bash
cd Backend
../.venv/bin/python create_admin_user.py
```

**🪟 Windows (PowerShell):**
```powershell
cd Backend
..\.venv\Scripts\python.exe create_admin_user.py
```

---

## 📂 Repository Layout
- `/Backend` - FastAPI logic & API endpoints.
- `/sentinel-frontend` - **Primary** Next.js + TypeScript UI (SENTINEL AI), runs on port 3000.
- `/Frontend` - Legacy vanilla JS/HTML UI (served via `http.server`).
- `/Models` - YOLOv8 weights (.pt) and evaluation scripts.
- `/Database` - SQLite storage and incident media.

---

## 🔒 Security
- Use strong admin passwords.
- Do not commit your `.env` file (protected by `.gitignore`).
- Restrict `ALLOWED_ORIGINS` in production settings.
