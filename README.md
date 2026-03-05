# 🔍 VeriGraph

> **MLOps-driven fact-checking system** with automated model lifecycle management, multi-stage deployments, and distributed ML inference.

An end-to-end production-ready application demonstrating core MLOps principles: version control, CI/CD pipelines, model registry, staged deployments, and monitoring.

---

## 🎯 MLOps Features Implemented

✅ **Model Versioning & Registry** - DagHub/MLflow tracking with staging ↔ production promotions  
✅ **Multi-Stage Deployments** - Separate staging and production environments  
✅ **CI/CD Pipeline** - Automated testing, building, and deployment to Fly.io  
✅ **Distributed Architecture** - Lightweight API layer + dedicated ML inference server  
✅ **Quality Gates** - Model promotion with validation checks  
✅ **Experiment Tracking** - Complete ML experiment logging and artifact management  

---

## 🏗️ Architecture

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Frontend   │─────▶│  FastAPI     │─────▶│  MacMini ML  │
│  React/Vite  │      │  Backend     │      │  Server      │
└──────────────┘      └──────┬───────┘      └──────────────┘
                             │
                      ┌──────▼───────┐
                      │  PostgreSQL  │
                      │  (Neon)      │
                      └──────────────┘
```

**3-Tier Design:**
- **Frontend** - React + Tailwind CSS (Staging & Production)
- **Backend** - FastAPI with SQLAlchemy (Lightweight API layer)
- **ML Server** - Local MacMini M1 with GAN models (Cost-optimized inference)

---

## 🚀 Quick Start

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install && npm run dev
```

**Endpoints:**
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

---

## 📊 Model Lifecycle

```
Training → DagHub/MLflow → Staging → Quality Gate → Production
```

**Promotion Scripts:**
- `backend/promote_model.py` - Promote models between stages
- `backend/scripts/promote_with_quality_gate.py` - Quality-gated promotions
- Model artifacts automatically synced to inference server

---

## 🛠️ Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React, Vite, Tailwind CSS |
| **Backend** | FastAPI, SQLAlchemy, Pydantic |
| **ML** | PyTorch, MLflow, DagHub |
| **Database** | PostgreSQL (Neon) |
| **Deploy** | Fly.io, Docker |
| **CI/CD** | GitHub Actions |

---

## 📚 Documentation

- [CICD-ARCHITECTURE.md](CICD-ARCHITECTURE.md) - Complete CI/CD and architecture details
- [backend/docs/](backend/docs/) - Model integration and production workflows
- [backend/scripts/README.md](backend/scripts/README.md) - MLOps utility scripts

---

**Built for MLOps Course** - Demonstrating production-grade ML system design and deployment
