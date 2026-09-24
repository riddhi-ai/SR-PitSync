"""Fills the database with the team. Run once:  python seed.py
Safe to run again: it only adds people who are missing."""
from sqlalchemy import select

import config
from auth import hash_password
from database import Base, SessionLocal, engine
from models import Member, Setting

# (name, role text, subsystems, is_coordinator)
TEAM = [
    ("Aditi", "Steering", ["steering"], False),
    ("Arpita", "Suspension member and Sponsorship and PR Lead", ["suspension"], False),
    ("Kunal", "Drivetrain member", ["drivetrain"], False),
    ("Nandan", "LV lead", ["lv"], False),
    ("Omkar", "Steering and Inventory member", ["steering"], False),
    ("Sanskruti", "Chassis and Aerodynamics Lead", ["chassis", "aero"], False),
    ("Satvik", "Brakes Lead", ["brakes"], False),
    ("Zaara", "Suspension and Media lead", ["suspension"], False),
    ("Shravani", "Drivetrain member", ["drivetrain"], False),
    ("Gaurav", "Aerodynamics", ["aero"], False),
    ("Om F", "LV member", ["lv"], False),
    ("Tanvi", "HV lead and supervisor", ["hv"], True),
    ("Taha", "Chassis lead and Vice captain", ["chassis"], True),
    ("Bhushan", "Steering lead and Captain", ["steering"], True),
]
RECRUITS = ["Sakshi", "Atul", "Rugved", "Chaitanya", "Siddhesh", "Yash", "Parth"]


def email_for(name: str) -> str:
    # PLACEHOLDER addresses. Replace with real emails (PATCH /members/{id}) so notifications arrive.
    return name.lower().replace(" ", ".") + "@example.com"


def main():
    Base.metadata.create_all(engine)
    db = SessionLocal()
    rows = TEAM + [(n, "New recruit", [], False) for n in RECRUITS]
    added = 0
    for name, role, subs, boss in rows:
        email = email_for(name)
        if db.scalar(select(Member).where(Member.email == email)):
            continue
        db.add(Member(name=name, email=email, role_text=role, subsystems=",".join(subs), is_coordinator=boss,
                      password_hash=hash_password(config.SEED_PASSWORD)))
        added += 1
    for key, value in (("workshop_start", "10:00"), ("workshop_end", "17:00")):
        if not db.get(Setting, key):
            db.add(Setting(key=key, value=value))
    db.commit()
    total = len(db.scalars(select(Member)).all())
    print(f"Added {added} members. Total members: {total}.")
    print(f"Everyone's first password: {config.SEED_PASSWORD}  (they must change it)")
    print("Coordinator logins: taha@example.com, tanvi@example.com, bhushan@example.com")
    db.close()


if __name__ == "__main__":
    main()
