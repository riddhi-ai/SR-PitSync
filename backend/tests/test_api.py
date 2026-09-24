"""Run with:  pytest   (from the backend folder). Uses a throw-away test database."""
import os
import pathlib

os.environ["DATABASE_URL"] = "sqlite:///./test_pitsync.db"
os.environ["UPLOAD_DIR"] = "test_uploads"
os.environ["SEED_PASSWORD"] = "TestPass123!"
pathlib.Path("test_pitsync.db").unlink(missing_ok=True)

from datetime import timedelta  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

import seed  # noqa: E402
import timeutil  # noqa: E402
from main import app  # noqa: E402

seed.main()
client = TestClient(app)
PW = "TestPass123!"


def login(email):
    r = client.post("/auth/login", json={"email": email, "password": PW})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def member_id(headers, name):
    return next(m["id"] for m in client.get("/members", headers=headers).json() if m["name"] == name)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_wrong_password_and_no_token():
    assert client.post("/auth/login", json={"email": "aditi@example.com", "password": "nope"}).status_code == 401
    assert client.get("/members").status_code == 401


def test_team_has_21_members():
    h = login("aditi@example.com")
    r = client.get("/attendance/today/whos-in", headers=h).json()
    assert len(r["members"]) == 21 and r["editable"] is True


def test_date_lock_for_member_and_coordinator():
    for email in ("aditi@example.com", "taha@example.com"):
        h = login(email)
        for delta in (-1, 1):
            day = (timeutil.today() + timedelta(days=delta)).isoformat()
            r = client.put(f"/attendance/{day}", json={"status": "present"}, headers=h)
            assert r.status_code == 403, (email, day, r.text)
    day = (timeutil.today() - timedelta(days=1)).isoformat()
    assert client.get(f"/attendance/{day}/whos-in", headers=h).json()["editable"] is False


def test_absent_emails_coordinators():
    h = login("kunal@example.com")
    assert client.put("/attendance/today", json={"status": "absent"}, headers=h).status_code == 200
    log = client.get("/notifications/log", headers=login("taha@example.com")).json()
    assert any("Kunal is absent today" in row["subject"] for row in log)


def test_time_in_and_out():
    h = login("satvik@example.com")
    assert client.post("/attendance/today/time-out", headers=h).status_code == 400
    assert client.post("/attendance/today/time-in", headers=h).status_code == 200
    r = client.post("/attendance/today/time-out", headers=h).json()
    assert r["time_in"] and r["time_out"]


def test_only_coordinators_assign_tasks():
    h = login("gaurav@example.com")
    body = {"assigned_to": member_id(h, "Aditi"), "title": "x", "due_date": "2030-01-01"}
    assert client.post("/tasks", json=body, headers=h).status_code == 403


def test_task_flow_and_emails():
    boss, worker, other = login("taha@example.com"), login("omkar@example.com"), login("yash@example.com")
    body = {"assigned_to": member_id(boss, "Omkar"), "title": "Align steering rack", "due_date": "2030-01-01"}
    t = client.post("/tasks", json=body, headers=boss)
    assert t.status_code == 201
    tid = t.json()["id"]
    assert client.patch(f"/tasks/{tid}", json={"progress": 40}, headers=other).status_code == 403
    r = client.patch(f"/tasks/{tid}", json={"progress": 40, "notes": "halfway"}, headers=worker).json()
    assert r["status"] == "in_progress" and r["progress"] == 40
    assert len(client.get(f"/tasks/{tid}/diary", headers=boss).json()) == 1
    log = client.get("/notifications/log", headers=boss).json()
    subjects = [row["subject"] for row in log]
    assert any("New task: Align steering rack" in s for s in subjects)
    assert any("Omkar updated" in s for s in subjects)


def test_workshop_timing():
    boss, member = login("tanvi@example.com"), login("parth@example.com")
    assert client.put("/workshop", json={"start": "09:00", "end": "16:00"}, headers=member).status_code == 403
    assert client.put("/workshop", json={"start": "16:00", "end": "09:00"}, headers=boss).status_code == 422
    assert client.put("/workshop", json={"start": "09:00", "end": "16:00"}, headers=boss).json()["changed"] is True
    assert client.get("/workshop", headers=member).json()["start"] == "09:00"


def test_add_and_remove_member():
    boss = login("bhushan@example.com")
    r = client.post("/members", json={"name": "Neha", "email": "neha@example.com", "subsystems": ["brakes"]}, headers=boss)
    assert r.status_code == 201 and r.json()["temporary_password"]
    nid = r.json()["member"]["id"]
    assert client.delete(f"/members/{nid}", headers=boss).status_code == 200
    assert client.delete(f"/members/{member_id(boss, 'Taha')}", headers=boss).status_code == 400
