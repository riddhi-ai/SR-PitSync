"""Member profiles, and coordinator tools to add or remove members."""
import os
import secrets
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

import config
from auth import coordinator_only, current_member, hash_password
from database import get_db
from models import Member
from notifications import queue_email
from schemas import (MemberAdminUpdate, MemberCreate, MemberCreated, MemberOut, MemberPublic, ProfileUpdate,
                     member_out, member_public)

router = APIRouter(prefix="/members", tags=["members"])
MAX_PHOTO = 2 * 1024 * 1024


@router.get("/me", response_model=MemberOut)
def my_profile(me: Member = Depends(current_member)):
    return member_out(me)


@router.patch("/me", response_model=MemberOut)
def update_my_profile(data: ProfileUpdate, me: Member = Depends(current_member), db: Session = Depends(get_db)):
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(me, field, value)
    db.commit()
    return member_out(me)


def _photo_ext(data: bytes) -> str | None:
    """Checks the real file bytes, not just what the browser claims."""
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


@router.post("/me/photo", response_model=MemberOut)
async def upload_photo(file: UploadFile, me: Member = Depends(current_member), db: Session = Depends(get_db)):
    data = await file.read(MAX_PHOTO + 1)
    if len(data) > MAX_PHOTO:
        raise HTTPException(413, "Photo must be under 2 MB")
    ext = _photo_ext(data)
    if not ext:
        raise HTTPException(400, "Photo must be a JPG, PNG or WEBP image")
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    name = f"{me.id}-{uuid4().hex[:8]}{ext}"
    with open(os.path.join(config.UPLOAD_DIR, name), "wb") as f:
        f.write(data)
    if me.photo_url:  # delete the old photo
        old = os.path.join(config.UPLOAD_DIR, os.path.basename(me.photo_url))
        if os.path.exists(old):
            os.remove(old)
    me.photo_url = f"/uploads/{name}"
    db.commit()
    return member_out(me)


@router.get("", response_model=list[MemberPublic])
def list_members(_: Member = Depends(current_member), db: Session = Depends(get_db)):
    rows = db.scalars(select(Member).where(Member.is_active).order_by(Member.name)).all()
    return [member_public(m) for m in rows]


@router.get("/admin", response_model=list[MemberOut])
def list_members_admin(_: Member = Depends(coordinator_only), db: Session = Depends(get_db)):
    """Coordinator view: includes emails and inactive (removed) members."""
    return [member_out(m) for m in db.scalars(select(Member).order_by(Member.name)).all()]


@router.post("", response_model=MemberCreated, status_code=201)
def add_member(data: MemberCreate, bg: BackgroundTasks, db: Session = Depends(get_db),
               boss: Member = Depends(coordinator_only)):
    email = data.email.lower()
    temp = secrets.token_urlsafe(9)
    existing = db.scalar(select(Member).where(Member.email == email))
    if existing and existing.is_active:
        raise HTTPException(409, "A member with this email already exists")
    if existing:  # bring back a removed member
        member = existing
        member.is_active = True
        member.name, member.role_text = data.name, data.role_text
        member.subsystems = ",".join(data.subsystems)
    else:
        member = Member(name=data.name, email=email, role_text=data.role_text, subsystems=",".join(data.subsystems))
        db.add(member)
    member.password_hash = hash_password(temp)
    member.must_change_password = True
    db.commit()
    queue_email(db, bg, [email], "Welcome to SR PITSYNC",
                f"Hi {member.name},\n\n{boss.name} added you to the STES Racing workshop app.\n"
                f"Login email: {email}\nTemporary password: {temp}\n\n"
                "Please log in, change your password and complete your profile.")
    return MemberCreated(member=member_out(member), temporary_password=temp)


@router.patch("/{member_id}", response_model=MemberOut)
def edit_member(member_id: int, data: MemberAdminUpdate, db: Session = Depends(get_db),
                _: Member = Depends(coordinator_only)):
    member = db.get(Member, member_id)
    if not member:
        raise HTTPException(404, "Member not found")
    changes = data.model_dump(exclude_none=True)
    if "email" in changes:
        changes["email"] = changes["email"].lower()
        clash = db.scalar(select(Member).where(Member.email == changes["email"], Member.id != member_id))
        if clash:
            raise HTTPException(409, "Another member already uses this email")
    if "subsystems" in changes:
        changes["subsystems"] = ",".join(changes["subsystems"])
    for field, value in changes.items():
        setattr(member, field, value)
    db.commit()
    return member_out(member)


@router.delete("/{member_id}")
def remove_member(member_id: int, db: Session = Depends(get_db), boss: Member = Depends(coordinator_only)):
    """Soft delete: the member can no longer log in, but old attendance and tasks stay intact."""
    member = db.get(Member, member_id)
    if not member:
        raise HTTPException(404, "Member not found")
    if member.is_coordinator:
        raise HTTPException(400, "Coordinators cannot be removed")
    member.is_active = False
    db.commit()
    return {"ok": True, "removed": member.name}
