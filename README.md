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
Create a virtual environment and install dependencies:
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
```powershell
cp Backend/.env.example Backend/.env
```
*Edit `Backend/.env` to set your `SECRET_KEY` and admin credentials.*

---

## 🛠️ Running the Project

### Phase A: Start the Backend
From the root directory:
```powershell
cd Backend
..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend runs at: `http://127.0.0.1:8000`*

### Phase B: Start the Frontend
Open a new terminal and run a simple HTTP server:
```powershell
cd Frontend
python -m http.server 5500
```
*Frontend runs at: `http://127.0.0.1:5500`*

### Phase C: Initial Setup (Admin)
If this is your first time running KavachG, create the admin user:
```powershell
cd Backend
..\.venv\Scripts\python.exe create_admin_user.py
```

---

## 📂 Repository Layout
- `/Backend` - FastAPI logic & API endpoints.
- `/Frontend` - UI/UX assets and scripts.
- `/Models` - YOLOv8 weights (.pt) and evaluation scripts.
- `/Database` - SQLite storage and incident media.

---

## 🔒 Security
- Use strong admin passwords.
- Do not commit your `.env` file (protected by `.gitignore`).
- Restrict `ALLOWED_ORIGINS` in production settings.
