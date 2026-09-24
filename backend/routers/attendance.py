"""Attendance. READING any date is allowed. EDITING is only allowed for today, for everyone."""
from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

import timeutil
from auth import current_member
from database import get_db
from models import Attendance, Member
from notifications import coordinator_emails, queue_email
from schemas import AttendanceIn, WhoIsInOut, WhoIsInRow, member_public

router = APIRouter(prefix="/attendance", tags=["attendance"])


def resolve_day(day: str) -> date:
    if day == "today":
        return timeutil.today()
    try:
        return date.fromisoformat(day)
    except ValueError:
        raise HTTPException(422, "Use a date like 2026-09-24, or the word 'today'")


def require_today(day: str) -> date:
    """THE DATE LOCK. Past and future dates are refused, for every user, including coordinators."""
    d = resolve_day(day)
    if d != timeutil.today():
        raise HTTPException(403, f"{d} is locked. Only today ({timeutil.today()}) can be edited")
    return d


def _my_row(db: Session, member_id: int, d: date) -> Attendance:
    row = db.scalar(select(Attendance).where(Attendance.member_id == member_id, Attendance.day == d))
    if not row:
        row = Attendance(member_id=member_id, day=d, status="present")
        db.add(row)
    return row


@router.get("/{day}/whos-in", response_model=WhoIsInOut)
def whos_in(day: str, _: Member = Depends(current_member), db: Session = Depends(get_db)):
    d = resolve_day(day)
    rows = {a.member_id: a for a in db.scalars(select(Attendance).where(Attendance.day == d)).all()}
    members = db.scalars(select(Member).where(Member.is_active).order_by(Member.name)).all()
    out, counts = [], {"present": 0, "coming": 0, "absent": 0, "not_updated": 0}
    for m in members:
        a = rows.get(m.id)
        status = a.status if a else "not_updated"
        counts[status] += 1
        out.append(WhoIsInRow(**member_public(m).model_dump(), status=status,
                              eta=a.eta if a else "", time_in=a.time_in if a else "", time_out=a.time_out if a else ""))
    return WhoIsInOut(day=d, editable=(d == timeutil.today()), counts=counts, members=out)


@router.put("/{day}")
def set_my_status(day: str, data: AttendanceIn, bg: BackgroundTasks, me: Member = Depends(current_member),
                  db: Session = Depends(get_db)):
    d = require_today(day)
    row = _my_row(db, me.id, d)
    was_absent = row.status == "absent" and row.id is not None
    if data.status:
        row.status = data.status
    if row.status == "absent":
        row.eta = row.time_in = row.time_out = ""
    else:
        if data.eta is not None:
            row.eta = data.eta
        if row.status == "present" and not row.time_in:
            row.time_in = timeutil.hhmm()
        if row.status == "coming":
            row.time_in = row.time_out = ""
    db.commit()
    if row.status == "absent" and not was_absent:
        queue_email(db, bg, coordinator_emails(db, exclude_id=me.id), f"{me.name} is absent today",
                    f"{me.name} ({me.role_text}) marked themselves ABSENT for {d} at {timeutil.hhmm()}.")
    return {"day": d, "status": row.status, "eta": row.eta, "time_in": row.time_in, "time_out": row.time_out}


@router.post("/{day}/time-in")
def time_in(day: str, me: Member = Depends(current_member), db: Session = Depends(get_db)):
    d = require_today(day)
    row = _my_row(db, me.id, d)
    row.status, row.eta = "present", ""
    row.time_in = row.time_in or timeutil.hhmm()
    db.commit()
    return {"day": d, "status": row.status, "time_in": row.time_in, "time_out": row.time_out}


@router.post("/{day}/time-out")
def time_out(day: str, me: Member = Depends(current_member), db: Session = Depends(get_db)):
    d = require_today(day)
    row = _my_row(db, me.id, d)
    if row.status != "present" or not row.time_in:
        raise HTTPException(400, "Mark yourself present (time in) before timing out")
    row.time_out = timeutil.hhmm()
    db.commit()
    return {"day": d, "status": row.status, "time_in": row.time_in, "time_out": row.time_out}
