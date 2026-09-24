"""Login and password change."""
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import current_member, hash_password, make_token, verify_password
from database import get_db
from models import Member
from schemas import LoginIn, PasswordChangeIn, EmailChangeIn, member_out

router = APIRouter(prefix="/auth", tags=["auth"])

_fails: dict[str, list[float]] = {}  # tiny brute-force guard: 5 wrong tries = 5 minute pause
LIMIT, WINDOW = 5, 300


@router.post("/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    key = data.email.lower()
    recent = [t for t in _fails.get(key, []) if time.time() - t < WINDOW]
    if len(recent) >= LIMIT:
        raise HTTPException(429, "Too many wrong attempts. Try again in a few minutes")
    member = db.scalar(select(Member).where(Member.email == key))
    if not member or not member.is_active or not verify_password(data.password, member.password_hash):
        _fails[key] = recent + [time.time()]
        raise HTTPException(401, "Wrong email or password")
    _fails.pop(key, None)
    return {"access_token": make_token(member), "token_type": "bearer", "member": member_out(member)}


@router.post("/change-password")
def change_password(data: PasswordChangeIn, me: Member = Depends(current_member), db: Session = Depends(get_db)):
    if not verify_password(data.old_password, me.password_hash):
        raise HTTPException(400, "Old password is wrong")
    me.password_hash = hash_password(data.new_password)
    me.must_change_password = False
    db.commit()
    return {"ok": True}

@router.post("/change-email")
def change_email(
    data: EmailChangeIn,
    me: Member = Depends(current_member),
    db: Session = Depends(get_db)
):
    new_email = data.new_email.strip().lower()

    # Check current password
    if not verify_password(data.current_password, me.password_hash):
        raise HTTPException(400, "Current password is wrong")

    # Check whether the email is already being used
    existing = db.scalar(
        select(Member).where(
            Member.email == new_email,
            Member.id != me.id
        )
    )

    if existing:
        raise HTTPException(409, "This email is already registered")

    me.email = new_email
    db.commit()

    return {
        "ok": True,
        "email": me.email
    }