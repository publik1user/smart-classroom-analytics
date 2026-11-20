# Architecture
React SPA (Vite) -> REST JSON -> Flask API -> SQLite (rooms, faculty, courses, sections, sessions).
Conflict engine compares overlapping sessions on same day. Recommender filters available rooms by capacity, scores capacity-fit + type match - existing utilization.
