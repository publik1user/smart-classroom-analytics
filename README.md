# Smart Classroom Utilization & Timetable Analytics System
Full-stack college platform to monitor classroom use, find free rooms, detect timetable conflicts, recommend rooms and analyse usage.

## Tech Stack
Frontend: React + TypeScript + Vite + Tailwind CSS + Recharts | Backend: Python Flask (REST) + SQLite | Tests: Pytest + Vitest

## Features
Dashboard (real DB stats), Classroom CRUD + weekly schedule, Timetable / Courses / Faculty / Sections, Occupancy search by day & time, Conflict detection (double-booking, faculty, section, capacity), Smart recommendations with suitability score, Analytics (utilization, heatmap, underutilized, building-wise), CSV import with row validation & dry-run.

## Quick Start
### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py   # http://localhost:5000  (DB auto-created & seeded)
```
### Frontend (new terminal)
```bash
cd frontend
npm install
npm run dev     # http://localhost:5173
```
Login is not required for the demo. Sample data loads automatically on first run.

## Tests
```bash
cd backend && pytest -v
cd frontend && npm test
```

## API (main)
GET/POST /api/rooms, GET/PUT/DELETE /api/rooms/:id, GET/POST /api/faculty|courses|sections, GET/POST /api/sessions, PUT/DELETE /api/sessions/:id, GET /api/dashboard, /api/availability, /api/conflicts, /api/recommendations, /api/analytics, POST /api/import/rooms, /api/import/timetable?dry_run=true, POST /api/seed

## Structure
backend/app.py (all APIs, DB, seed, conflict & recommendation logic), backend/tests/, frontend/src/pages/ (8 pages), frontend/src/api/, sample_data/*.csv, docs/, .env.example

## Notes
Utilization = sessions per room / 35 weekly slots x 100. Conflict & recommendation logic is in backend/app.py and covered by tests.
