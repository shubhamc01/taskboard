import os

import pymysql
from flask import Flask, jsonify, request

app = Flask(__name__)
STATUSES = ("todo", "doing", "done")
PRIORITIES = ("low", "medium", "high")
DEMO = [("Kick-off call with the client", "done", "high"), ("Write the API contract", "done", "medium"),
        ("Design the onboarding screens", "doing", "high"), ("Set up CI/CD with devops-agent", "doing", "medium"),
        ("Load-test the checkout flow", "todo", "high"), ("Draft the release notes", "todo", "low")]


class MySQLStore:
    """Tasks in MySQL. The table is created (and seeded with a demo board) on first use."""

    def __init__(self):
        self.ready = False

    def _conn(self):
        c = pymysql.connect(host=os.environ["DB_HOST"], user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"],
                            database=os.environ["DB_NAME"], autocommit=True, cursorclass=pymysql.cursors.DictCursor)
        if not self.ready:
            with c.cursor() as cur:
                cur.execute("CREATE TABLE IF NOT EXISTS tasks (id INT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(200) NOT NULL,"
                            " status VARCHAR(10) NOT NULL DEFAULT 'todo', priority VARCHAR(10) NOT NULL DEFAULT 'medium',"
                            " created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                cur.execute("SELECT COUNT(*) AS n FROM tasks")
                if cur.fetchone()["n"] == 0:
                    cur.executemany("INSERT INTO tasks (title, status, priority) VALUES (%s, %s, %s)", DEMO)
            self.ready = True
        return c

    def ping(self):
        with self._conn() as c, c.cursor() as cur:
            cur.execute("SELECT 1")

    def list(self):
        with self._conn() as c, c.cursor() as cur:
            cur.execute("SELECT id, title, status, priority, created_at FROM tasks ORDER BY id DESC LIMIT 200")
            return [{**r, "created_at": r["created_at"].isoformat()} for r in cur.fetchall()]

    def add(self, title, status, priority):
        with self._conn() as c, c.cursor() as cur:
            cur.execute("INSERT INTO tasks (title, status, priority) VALUES (%s, %s, %s)", (title, status, priority))
            return cur.lastrowid

    def update(self, task_id, fields):
        with self._conn() as c, c.cursor() as cur:
            sets = ", ".join(f"{k} = %s" for k in fields)  # keys are whitelisted by the caller
            return cur.execute(f"UPDATE tasks SET {sets} WHERE id = %s", (*fields.values(), task_id)) > 0 or self._exists(cur, task_id)

    def delete(self, task_id):
        with self._conn() as c, c.cursor() as cur:
            return cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,)) > 0

    @staticmethod
    def _exists(cur, task_id):
        cur.execute("SELECT 1 FROM tasks WHERE id = %s", (task_id,))
        return cur.fetchone() is not None


store = MySQLStore()


def _fields(body, partial):
    """The editable fields of a task, validated; (fields, error)."""
    out = {}
    if "title" in body or not partial:
        title = str(body.get("title") or "").strip()
        if not title or len(title) > 200:
            return None, "title is required (at most 200 characters)"
        out["title"] = title
    for key, allowed, default in (("status", STATUSES, "todo"), ("priority", PRIORITIES, "medium")):
        if key in body or not partial:
            value = body.get(key, default)
            if value not in allowed:
                return None, f"{key} must be one of {', '.join(allowed)}"
            out[key] = value
    return (out, None) if out else (None, "nothing to update")


@app.errorhandler(pymysql.MySQLError)
def db_down(e):
    return {"error": f"database unavailable ({type(e).__name__})"}, 503


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/api/healthz")
def api_health():
    store.ping()
    return {"ok": True}


@app.get("/api/tasks")
def list_tasks():
    return jsonify(store.list())


@app.post("/api/tasks")
def add_task():
    fields, err = _fields(request.get_json(silent=True) or {}, partial=False)
    if err:
        return {"error": err}, 400
    return {"id": store.add(**fields)}, 201


@app.patch("/api/tasks/<int:task_id>")
def update_task(task_id):
    fields, err = _fields(request.get_json(silent=True) or {}, partial=True)
    if err:
        return {"error": err}, 400
    return ({"ok": True}, 200) if store.update(task_id, fields) else ({"error": "not found"}, 404)


@app.delete("/api/tasks/<int:task_id>")
def delete_task(task_id):
    return ("", 204) if store.delete(task_id) else ({"error": "not found"}, 404)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
