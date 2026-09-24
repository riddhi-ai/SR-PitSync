# SR PITSYNC Backend (FastAPI)

The server behind the SR PITSYNC workshop app. It stores members, attendance and tasks, checks who is allowed to do what, and sends the emails.

## 1. Run it on your computer

You need **Python 3.10 or newer** (`python --version`).

```bash
cd backend
python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # Mac / Linux
pip install -r requirements.txt
copy .env.example .env           # Mac/Linux: cp .env.example .env
python seed.py                   # creates the database and the 21 members
uvicorn main:app --reload
```

Now open **http://127.0.0.1:8000/docs**. FastAPI builds a page there where you can try every endpoint.

**First login test:** in `/docs` click `POST /auth/login`, then "Try it out", and use
`{"email": "taha@example.com", "password": "ChangeMe123!"}`.
Copy the `access_token`, click the green **Authorize** button at the top, and paste it. Now every endpoint works as Taha.

## 2. Before real use (important)

1. In `.env`, set `SECRET_KEY` to a long random string (run `python -c "import secrets; print(secrets.token_urlsafe(48))"`).
2. The seeded emails are **placeholders** (`aditi@example.com`). Set the real ones with `PATCH /members/{id}` as a coordinator. Without real emails nobody receives notifications.
3. Everyone starts with `SEED_PASSWORD` and the app flags `must_change_password`. Ask people to change it (`POST /auth/change-password`).

## 3. Email setup

Leave `SMTP_HOST` empty while testing. Emails are then only saved in the `email_log` table (see `GET /notifications/log`).
For real emails fill in `SMTP_*` in `.env`. Gmail needs an **App Password** (Google Account > Security > 2-Step Verification > App passwords). Brevo, Resend and Mailgun also offer SMTP details.
Emails sent from a personal address may land in spam, so tell members to check.

## 4. How your rules are enforced (in the server, not the browser)

| Rule | Where |
|---|---|
| Only today's attendance can be edited, for everyone including coordinators | `require_today()` in `routers/attendance.py`, using the SERVER clock in `timeutil.py` |
| Members edit only their own attendance and tasks | `current_member` + ownership checks |
| Only Taha, Tanvi, Bhushan add/remove members, assign tasks, change timing | `coordinator_only` in `auth.py` |
| Coordinators cannot be removed | `remove_member` in `routers/members.py` |
| Task assigned, task updated, marked absent, timing changed: emails | `notifications.py` |
| Passwords | Hashed with Argon2, never stored as plain text |

## 5. Endpoints

| Method and path | Who | What |
|---|---|---|
| POST `/auth/login` | anyone | Get a token |
| POST `/auth/change-password` | member | Change password |
| GET / PATCH `/members/me` | member | My profile |
| POST `/members/me/photo` | member | Upload photo (JPG/PNG/WEBP, max 2 MB) |
| GET `/members` | member | Team list |
| GET `/members/admin` | coordinator | Full list with emails and removed members |
| POST `/members` | coordinator | Add member (returns a temporary password) |
| PATCH / DELETE `/members/{id}` | coordinator | Edit / remove |
| GET `/attendance/{day}/whos-in` | member | Everyone with status. `day` = `today` or `2026-09-24` |
| PUT `/attendance/{day}` | member | Set present/coming/absent and ETA (today only) |
| POST `/attendance/{day}/time-in` and `/time-out` | member | Time in/out (today only) |
| POST / GET `/tasks` | coordinator / all | Assign / list (members see only their own) |
| PATCH `/tasks/{id}` | assignee | Update status, progress, notes |
| GET `/tasks/{id}/diary` | assignee, coordinator | Day-by-day progress |
| DELETE `/tasks/{id}` | coordinator | Delete |
| GET / PUT `/workshop` | member / coordinator | Timing and server clock |
| GET `/notifications/log` | coordinator | Email outbox |

Subsystem keys: `chassis, steering, suspension, brakes, lv, hv, drivetrain, aero`.

## 6. Run the tests

```bash
pip install -r requirements-dev.txt
pytest
```

## 7. Connecting the website

Serve the frontend from a local server (for example the VS Code "Live Server" extension on port 5500). Opening the HTML file by double-click will be blocked by the browser. The website sends the token in a header: `Authorization: Bearer <token>`.
When the site moves to a real address, add it to `CORS_ORIGINS` in `.env`.

## 8. Going live

- Host on Render, Railway or a small VPS. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
- Switch `DATABASE_URL` to PostgreSQL (`postgresql+psycopg://user:pass@host/db`) and `pip install "psycopg[binary]"`. Free hosts often erase local files, and SQLite and `uploads/` live in local files.
- Always use HTTPS, and keep `.env` out of GitHub.

## Folder guide

```
main.py          starts the app        models.py     database tables
config.py        settings from .env    schemas.py    data rules in/out
database.py      database connection   auth.py       passwords, tokens, permissions
timeutil.py      server date and time  notifications.py  emails
seed.py          loads the 21 members  routers/      the endpoints
tests/           automatic checks
```
