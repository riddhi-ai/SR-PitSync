"""Passwords, login tokens, and 'who is asking?' checks."""
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

import config
from database import get_db
from models import Member

_hasher = PasswordHasher()
_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def make_token(member: Member) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=config.TOKEN_HOURS)
    return jwt.encode({"sub": str(member.id), "exp": exp}, config.SECRET_KEY, algorithm="HS256")


def current_member(creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
                   db: Session = Depends(get_db)) -> Member:
    """Use as a dependency on any route that needs a logged-in member."""
    if not creds:
        raise HTTPException(401, "Please log in first")
    try:
        data = jwt.decode(creds.credentials, config.SECRET_KEY, algorithms=["HS256"])
        member = db.get(Member, int(data["sub"]))
    except (jwt.PyJWTError, ValueError, KeyError):
        raise HTTPException(401, "Your login has expired. Please log in again")
    if not member or not member.is_active:
        raise HTTPException(401, "This account is not active")
    return member


def coordinator_only(member: Member = Depends(current_member)) -> Member:
    """Use as a dependency on routes only Taha, Tanvi and Bhushan may call."""
    if not member.is_coordinator:
        raise HTTPException(403, "Only coordinators can do this")
    return member
