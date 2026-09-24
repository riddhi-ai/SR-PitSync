"""Tasks. Coordinators assign them. Members update their own, and each update is logged for TODAY."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

import timeutil
from auth import coordinator_only, current_member
from database import get_db
from models import Member, Task, TaskUpdate
from notifications import coordinator_emails, queue_email
from schemas import TaskCreate, TaskDiaryRow, TaskOut, TaskUpdateIn, split_subsystems

router = APIRouter(prefix="/tasks", tags=["tasks"])

LABEL = {"todo": "To do", "in_progress": "In progress", "done": "Done"}


def task_out(t: Task) -> TaskOut:
    return TaskOut(id=t.id, title=t.title, description=t.description, due_date=t.due_date, status=t.status,
                   progress=t.progress, notes=t.notes, assigned_to=t.assigned_to, assignee_name=t.assignee.name,
                   subsystems=split_subsystems(t.assignee.subsystems), created_at=t.created_at, updated_at=t.updated_at)


@router.post("", response_model=TaskOut, status_code=201)
def assign_task(data: TaskCreate, bg: BackgroundTasks, db: Session = Depends(get_db),
                boss: Member = Depends(coordinator_only)):
    person = db.get(Member, data.assigned_to)
    if not person or not person.is_active:
        raise HTTPException(404, "That member does not exist")
    task = Task(assigned_to=person.id, created_by=boss.id, title=data.title, description=data.description,
                due_date=data.due_date)
    db.add(task)
    db.commit()
    queue_email(db, bg, [person.email], f"New task: {task.title}",
                f"Hi {person.name},\n\n{boss.name} assigned you a task.\n\nTask: {task.title}\n"
                f"Due: {task.due_date}\n{task.description}")
    return task_out(task)


@router.get("", response_model=list[TaskOut])
def list_tasks(status: str | None = None, assignee_id: int | None = None, me: Member = Depends(current_member),
               db: Session = Depends(get_db)):
    q = select(Task).order_by(Task.due_date, Task.id)
    if not me.is_coordinator:
        q = q.where(Task.assigned_to == me.id)  # members only ever see their own tasks
    elif assignee_id:
        q = q.where(Task.assigned_to == assignee_id)
    if status:
        q = q.where(Task.status == status)
    return [task_out(t) for t in db.scalars(q).all()]


@router.patch("/{task_id}", response_model=TaskOut)
def update_my_task(task_id: int, data: TaskUpdateIn, bg: BackgroundTasks, me: Member = Depends(current_member),
                   db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if task.assigned_to != me.id:
        raise HTTPException(403, "You can only update your own tasks")
    if data.status:
        task.status = data.status
    if data.progress is not None:
        task.progress = data.progress
    if data.notes is not None:
        task.notes = data.notes
    # keep status and progress consistent
    if task.status == "done":
        task.progress = 100
    elif data.progress == 100 and not data.status:
        task.status = "done"
    elif task.progress > 0 and task.status == "todo":
        task.status = "in_progress"
    # today's diary entry (the server decides what today is)
    today = timeutil.today()
    diary = db.scalar(select(TaskUpdate).where(TaskUpdate.task_id == task.id, TaskUpdate.day == today))
    if not diary:
        diary = TaskUpdate(task_id=task.id, member_id=me.id, day=today, status=task.status, progress=task.progress)
        db.add(diary)
    diary.status, diary.progress, diary.notes = task.status, task.progress, task.notes
    db.commit()
    queue_email(db, bg, coordinator_emails(db, exclude_id=me.id), f"{me.name} updated: {task.title}",
                f"{me.name} updated a task.\n\nTask: {task.title}\nStatus: {LABEL[task.status]}\n"
                f"Progress: {task.progress}%\nNotes: {task.notes or '(none)'}")
    return task_out(task)


@router.get("/{task_id}/diary", response_model=list[TaskDiaryRow])
def task_diary(task_id: int, me: Member = Depends(current_member), db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if task.assigned_to != me.id and not me.is_coordinator:
        raise HTTPException(403, "Not your task")
    rows = db.scalars(select(TaskUpdate).where(TaskUpdate.task_id == task_id).order_by(TaskUpdate.day)).all()
    return [TaskDiaryRow(day=r.day, status=r.status, progress=r.progress, notes=r.notes) for r in rows]


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), _: Member = Depends(coordinator_only)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    db.query(TaskUpdate).filter(TaskUpdate.task_id == task_id).delete()
    db.delete(task)
    db.commit()
    return {"ok": True}
