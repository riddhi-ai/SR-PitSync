"""Workshop timing, the server clock, and the email outbox."""
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

import config
import timeutil
from auth import coordinator_only, current_member
from database import get_db
from models import EmailLog, Member, Setting
from notifications import all_member_emails, queue_email
from schemas import WorkshopIn

router = APIRouter(tags=["workshop"])


def get_times(db: Session) -> tuple[str, str]:
    rows = {s.key: s.value for s in db.scalars(select(Setting)).all()}
    return rows.get("workshop_start", "10:00"), rows.get("workshop_end", "17:00")


def _put(db: Session, key: str, value: str) -> None:
    row = db.get(Setting, key)
    if row:
        row.value = value
    else:
        db.add(Setting(key=key, value=value))


@router.get("/workshop")
def workshop(_: Member = Depends(current_member), db: Session = Depends(get_db)):
    start, end = get_times(db)
    now = timeutil.hhmm()
    state = "not_started" if now < start else "live" if now < end else "closed"
    return {"date": timeutil.today(), "server_time": timeutil.now().isoformat(), "timezone": config.TIMEZONE,
            "start": start, "end": end, "state": state}


@router.put("/workshop")
def change_timing(data: WorkshopIn, bg: BackgroundTasks, db: Session = Depends(get_db),
                  boss: Member = Depends(coordinator_only)):
    old_start, old_end = get_times(db)
    if (old_start, old_end) == (data.start, data.end):
        return {"start": data.start, "end": data.end, "changed": False}
    _put(db, "workshop_start", data.start)
    _put(db, "workshop_end", data.end)
    db.commit()
    queue_email(db, bg, all_member_emails(db), "Workshop timing changed",
                f"{boss.name} changed the workshop timing.\n\nNew: {data.start} to {data.end}\n"
                f"Old: {old_start} to {old_end}")
    return {"start": data.start, "end": data.end, "changed": True}


@router.get("/notifications/log")
def email_log(limit: int = 50, _: Member = Depends(coordinator_only), db: Session = Depends(get_db)):
    rows = db.scalars(select(EmailLog).order_by(EmailLog.id.desc()).limit(min(limit, 200))).all()
    return [{"id": r.id, "to": r.to, "subject": r.subject, "sent": r.sent, "error": r.error,
             "created_at": r.created_at} for r in rows]
