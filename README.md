# taskboard

A team Kanban board: Node frontend (`web/`, own Dockerfile) + Flask API (root) + MySQL, in one compose. Path routing: `/` → web, `/api` → api. Drag cards between To do / In progress / Done; a demo board is seeded on first use.

API: `GET/POST /api/tasks`, `PATCH/DELETE /api/tasks/<id>`, `GET /api/healthz` (checks MySQL), `GET /healthz`. Config: `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`.

Run: `docker compose up --build` → http://localhost:3000 (the UI calls `/api`, so put a proxy in front, as the deployed host does). Tests: `pip install -r requirements-dev.txt && pytest`. No root Dockerfile: the agent writes it. Demo target: EC2 + Docker Compose — tests MySQL detection and path routing.
