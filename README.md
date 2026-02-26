# VeriGraph

A modern web application built with React, Tailwind CSS, and FastAPI.

## Project Structure

```
verigraph/
├── frontend/          # React + Tailwind CSS frontend
│   ├── src/
│   ├── public/
│   └── package.json
├── backend/           # FastAPI Python backend
│   ├── main.py
│   └── requirements.txt
└── README.md
```

## Getting Started

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the FastAPI server:
```bash
uvicorn main:app --reload --port 8000
```

The API will be available at http://localhost:8000
API Documentation: http://localhost:8000/docs

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies (if not already done):
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

The app will be available at http://localhost:5173

## Tech Stack

### Frontend
- **React** - UI framework
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework

### Backend
- **FastAPI** - Modern Python web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation

## Development

- Frontend dev server: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
