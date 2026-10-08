import app as taskboard


class MemStore:
    def __init__(self):
        self.rows, self.next = {}, 1

    def ping(self):
        pass

    def list(self):
        return sorted(self.rows.values(), key=lambda r: -r["id"])

    def add(self, title, status, priority):
        self.rows[self.next] = {"id": self.next, "title": title, "status": status, "priority": priority, "created_at": ""}
        self.next += 1
        return self.next - 1

    def update(self, task_id, fields):
        if task_id not in self.rows:
            return False
        self.rows[task_id].update(fields)
        return True

    def delete(self, task_id):
        return self.rows.pop(task_id, None) is not None


def client():
    taskboard.store = MemStore()
    return taskboard.app.test_client()


def test_health():
    c = client()
    assert c.get("/healthz").json == {"ok": True}
    assert c.get("/api/healthz").json == {"ok": True}


def test_task_lifecycle():
    c = client()
    r = c.post("/api/tasks", json={"title": "  Ship it  ", "priority": "high"})
    assert r.status_code == 201
    tid = r.json["id"]
    assert c.get("/api/tasks").json[0] == {"id": tid, "title": "Ship it", "status": "todo", "priority": "high", "created_at": ""}
    assert c.patch(f"/api/tasks/{tid}", json={"status": "done"}).status_code == 200
    assert c.get("/api/tasks").json[0]["status"] == "done"
    assert c.delete(f"/api/tasks/{tid}").status_code == 204
    assert c.delete(f"/api/tasks/{tid}").status_code == 404


def test_validation():
    c = client()
    assert c.post("/api/tasks", json={"title": ""}).status_code == 400
    assert c.post("/api/tasks", json={"title": "x", "status": "blocked"}).status_code == 400
    assert c.patch("/api/tasks/1", json={"title": "x; DROP TABLE tasks"}).status_code == 404
    assert c.patch("/api/tasks/1", json={"id": 5}).status_code == 400
