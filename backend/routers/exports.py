"""Coordinator-only CSV data exports."""

import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth import coordinator_only
from database import get_db
from models import Member

router = APIRouter(prefix="/export", tags=["exports"])


def csv_response(filename: str, rows: list[dict]):
    output = io.StringIO()

    if not rows:
        output.write("No data available\n")
    else:
        writer = csv.DictWriter(
            output,
            fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/members.csv")
def export_members(
    _: Member = Depends(coordinator_only),
    db: Session = Depends(get_db)
):
    members = db.scalars(
        select(Member).order_by(Member.name)
    ).all()

    rows = []

    for member in members:
        rows.append({
            "ID": member.id,
            "Name": member.name,
            "Email": member.email,
            "Role": member.role_text,
            "Coordinator": member.is_coordinator,
            "Active": member.is_active,
            "Subsystems": member.subsystems or "",
            "Must Change Password": member.must_change_password,
        })

    return csv_response("pitsync_members.csv", rows)

