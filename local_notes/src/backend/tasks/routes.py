# src/backend/tasks/routes.py
"""
routes.py

Defines FastAPI routes for task management.
Provides endpoints to create, read, update, and delete tasks.
Utilizes Pydantic models for request validation.
"""

import datetime
from typing import List, Optional, Generator  # Added Generator for proper type hints

from fastapi import APIRouter, Depends, HTTPException, Path, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.sessions import SessionLocal  # Updated import: use "sessions" (plural)
from tasks.models import Task, TaskStatus
from tasks.recurrence import get_next_due_date

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}}
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.
    
    Yields:
        Session: SQLAlchemy session object.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TaskCreate(BaseModel):
    """
    Pydantic model for creating a new task.
    """
    title: str
    description: Optional[str] = ""
    due_date: Optional[datetime.datetime] = None
    priority: Optional[int] = 2  # 1: High, 2: Medium, 3: Low
    recurrence: Optional[str] = None
    note_path: Optional[str] = None


class TaskUpdate(BaseModel):
    """
    Pydantic model for updating an existing task.
    All fields are optional to allow partial updates.
    """
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime.datetime] = None
    priority: Optional[int] = None
    status: Optional[TaskStatus] = None
    recurrence: Optional[str] = None
    note_path: Optional[str] = None


class TaskResponse(BaseModel):
    """
    Pydantic model for task responses.
    """
    id: int
    title: str
    description: Optional[str]
    due_date: Optional[datetime.datetime]
    priority: int
    status: TaskStatus
    recurrence: Optional[str]
    note_path: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        orm_mode = True


@router.post("/", response_model=TaskResponse, summary="Create a new task")
def create_task(task: TaskCreate, db: Session = Depends(get_db)) -> Task:
    """
    Create a new task with the provided details.
    
    Args:
        task (TaskCreate): Task data from the request body.
        db (Session): Database session dependency.
    
    Returns:
        Task: The created task.
    """
    new_task = Task(
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        priority=task.priority,
        recurrence=task.recurrence,
        note_path=task.note_path
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@router.get("/", response_model=List[TaskResponse], summary="Retrieve all tasks")
def read_tasks(db: Session = Depends(get_db)) -> List[Task]:
    """
    Retrieve a list of all tasks.
    
    Args:
        db (Session): Database session dependency.
    
    Returns:
        List[Task]: List of tasks.
    """
    tasks = db.query(Task).all()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse, summary="Retrieve a task by ID")
def read_task(
    task_id: int = Path(..., description="The ID of the task"),
    db: Session = Depends(get_db)
) -> Task:
    """
    Retrieve a specific task by its ID.
    
    Args:
        task_id (int): The ID of the task.
        db (Session): Database session dependency.
    
    Returns:
        Task: The requested task.
    
    Raises:
        HTTPException: If the task is not found.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskResponse, summary="Update a task")
def update_task(
    task_id: int = Path(..., description="The ID of the task to update"),
    task_update: TaskUpdate = Body(...),
    db: Session = Depends(get_db)
) -> Task:
    """
    Update an existing task.
    
    Args:
        task_id (int): The ID of the task to update.
        task_update (TaskUpdate): Updated task data.
        db (Session): Database session dependency.
    
    Returns:
        Task: The updated task.
    
    Raises:
        HTTPException: If the task is not found.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_update.dict(exclude_unset=True)
    
    # If a new due date is provided along with an existing recurrence rule,
    # compute the next due date based on the recurrence rule.
    if "due_date" in update_data and task.recurrence and update_data.get("due_date"):
        update_data["due_date"] = get_next_due_date(update_data["due_date"], task.recurrence)
    
    for key, value in update_data.items():
        setattr(task, key, value)
    
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", summary="Delete a task")
def delete_task(
    task_id: int = Path(..., description="The ID of the task to delete"),
    db: Session = Depends(get_db)
) -> dict:
    """
    Delete a task by its ID.
    
    Args:
        task_id (int): The ID of the task to delete.
        db (Session): Database session dependency.
    
    Returns:
        dict: A message confirming deletion.
    
    Raises:
        HTTPException: If the task is not found.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully"}