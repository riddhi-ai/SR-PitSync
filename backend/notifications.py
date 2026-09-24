"""Email sending. Every email is saved in the email_log table first, then sent in the background."""
import smtplib
from email.message import EmailMessage

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import Session

import config
from database import SessionLocal
from models import EmailLog, Member

SIGN_OFF = "\n\n- SR PITSYNC (STES Racing)"


def coordinator_emails(db: Session, exclude_id: int | None = None) -> list[str]:
    rows = db.scalars(select(Member).where(Member.is_coordinator, Member.is_active)).all()
    return [m.email for m in rows if m.id != exclude_id]


def all_member_emails(db: Session) -> list[str]:
    return list(db.scalars(select(Member.email).where(Member.is_active)).all())


def queue_email(db: Session, bg: BackgroundTasks, recipients: list[str], subject: str, body: str) -> None:
    ids = []
    for to in dict.fromkeys(recipients):  # removes duplicates, keeps order
        log = EmailLog(to=to, subject=subject, body=body + SIGN_OFF)
        db.add(log)
        db.flush()
        ids.append(log.id)
    db.commit()
    if ids:
        bg.add_task(_deliver, ids)  # runs AFTER the response is sent, so the app stays fast


def _send_smtp(to: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = config.MAIL_FROM, to, subject
    msg.set_content(body)
    if config.SMTP_PORT == 465:
        with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, timeout=20) as s:
            s.login(config.SMTP_USER, config.SMTP_PASSWORD)
            s.send_message(msg)
    else:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=20) as s:
            s.starttls()
            if config.SMTP_USER:
                s.login(config.SMTP_USER, config.SMTP_PASSWORD)
            s.send_message(msg)


def _deliver(ids: list[int]) -> None:
    db = SessionLocal()
    try:
        for i in ids:
            log = db.get(EmailLog, i)
            if not log:
                continue
            if not config.SMTP_HOST:
                log.error = "SMTP not configured: saved to log only"
                print(f"[EMAIL not sent] to={log.to} subject={log.subject}")
                continue
            try:
                _send_smtp(log.to, log.subject, log.body)
                log.sent = True
            except Exception as e:  # one bad address must not stop the others
                log.error = str(e)[:300]
        db.commit()
    finally:
        db.close()
