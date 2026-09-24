"""Schemas describe what data is allowed IN and what we send OUT. Pydantic checks it for you."""
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

SUBSYSTEMS = {"chassis", "steering", "suspension", "brakes", "lv", "hv", "drivetrain", "aero"}
HHMM = r"^([01]\d|2[0-3]):[0-5]\d$"
EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def _check_subsystems(v):
    if v is None:
        return v
    bad = [x for x in v if x not in SUBSYSTEMS]
    if bad:
        raise ValueError(f"Unknown subsystem(s): {bad}. Allowed: {sorted(SUBSYSTEMS)}")
    return list(dict.fromkeys(v))


# ---------- auth ----------
class LoginIn(BaseModel):
    email: str = Field(pattern=EMAIL)
    password: str


class PasswordChangeIn(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=100)

class EmailChangeIn(BaseModel):
    current_password: str
    new_email: str = Field(pattern=EMAIL, max_length=120)


# ---------- members ----------
class MemberPublic(BaseModel):
    """What every logged-in member may see about a teammate (no email)."""
    id: int
    name: str
    role_text: str
    subsystems: list[str]
    is_coordinator: bool
    phone: str
    branch: str
    year: str
    blood_group: str
    photo_url: str


class MemberOut(MemberPublic):
    """Full details: for the owner and for coordinators."""
    email: str
    is_active: bool
    profile_complete: bool
    must_change_password: bool


class MemberCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: str = Field(pattern=EMAIL, max_length=120)
    role_text: str = Field(default="Member", max_length=120)
    subsystems: list[str] = []
    @field_validator("subsystems")
    @classmethod
    def check_subsystems(cls, v):
        return _check_subsystems(v)


class MemberAdminUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    email: Optional[str] = Field(default=None, pattern=EMAIL, max_length=120)
    role_text: Optional[str] = Field(default=None, max_length=120)
    subsystems: Optional[list[str]] = None
    @field_validator("subsystems")
    @classmethod
    def check_subsystems(cls, v):
        return _check_subsystems(v)


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    phone: Optional[str] = Field(default=None, pattern=r"^\+?\d{7,15}$")
    branch: Optional[str] = Field(default=None, max_length=60)
    year: Optional[Literal["FE", "SE", "TE", "BE"]] = None
    blood_group: Optional[Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]] = None


class MemberCreated(BaseModel):
    member: MemberOut
    temporary_password: str


# ---------- attendance ----------
class AttendanceIn(BaseModel):
    status: Optional[Literal["present", "coming", "absent"]] = None
    eta: Optional[str] = Field(default=None, pattern=HHMM)


class WhoIsInRow(MemberPublic):
    status: Literal["present", "coming", "absent", "not_updated"]
    eta: str = ""
    time_in: str = ""
    time_out: str = ""


class WhoIsInOut(BaseModel):
    day: date
    editable: bool  # True only for today
    counts: dict[str, int]
    members: list[WhoIsInRow]


# ---------- tasks ----------
class TaskCreate(BaseModel):
    assigned_to: int
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    due_date: date


class TaskUpdateIn(BaseModel):
    status: Optional[Literal["todo", "in_progress", "done"]] = None
    progress: Optional[int] = Field(default=None, ge=0, le=100)
    notes: Optional[str] = Field(default=None, max_length=500)


class TaskOut(BaseModel):
    id: int
    title: str
    description: str
    due_date: date
    status: str
    progress: int
    notes: str
    assigned_to: int
    assignee_name: str
    subsystems: list[str]
    created_at: datetime
    updated_at: datetime


class TaskDiaryRow(BaseModel):
    day: date
    status: str
    progress: int
    notes: str


# ---------- workshop ----------
class WorkshopIn(BaseModel):
    start: str = Field(pattern=HHMM)
    end: str = Field(pattern=HHMM)

    @model_validator(mode="after")
    def order_ok(self):
        if self.start >= self.end:
            raise ValueError("Start time must be earlier than end time")
        return self


# ---------- helpers ----------
def split_subsystems(text: str) -> list[str]:
    return [s for s in (text or "").split(",") if s]


def member_public(m) -> MemberPublic:
    return MemberPublic(id=m.id, name=m.name, role_text=m.role_text, subsystems=split_subsystems(m.subsystems),
                        is_coordinator=m.is_coordinator, phone=m.phone, branch=m.branch, year=m.year,
                        blood_group=m.blood_group, photo_url=m.photo_url)


def member_out(m) -> MemberOut:
    return MemberOut(**member_public(m).model_dump(), email=m.email, is_active=m.is_active,
                     profile_complete=all([m.phone, m.branch, m.year, m.blood_group]),
                     must_change_password=m.must_change_password)
