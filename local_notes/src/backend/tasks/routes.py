# src/backend/tasks/routes.py
"""
routes.py

Defines FastAPI routes for task management.
Provides endpoints to create, read, update, and delete tasks, plus a custom endpoint for
completing recurring tasks.

Wave 2 Enhancements:
- Added a 'complete_task' endpoint to handle recurring tasks more gracefully.
  If a task has a recurrence rule, this endpoint will complete the current task
  and create a new task instance with the next due date.
"""

import datetime
from typing import List, Optional, Generator

from fastapi import APIRouter, Depends, HTTPException, Path, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.sessions import SessionLocal
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
        from_attributes = True  # Allows Pydantic to read from SQLAlchemy model attributes


@router.post("/", response_model=TaskResponse, summary="Create a new task")
def create_task(task: TaskCreate, db: Session = Depends(get_db)) -> Task:
    """
    Create a new task with the provided details.
    
    Args:
        task (TaskCreate): Task data from the request body.
        db (Session): Database session dependency.

    Returns:
        Task: The newly created SQLAlchemy Task object.
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
    Retrieve a list of all tasks from the database.

    Args:
        db (Session): Database session dependency.

    Returns:
        List[Task]: A list of SQLAlchemy Task objects.
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
        task_id (int): The ID of the task to retrieve.
        db (Session): Database session dependency.
    
    Returns:
        Task: The requested SQLAlchemy Task object.
    
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
    Update an existing task with new data.

    - If a new 'due_date' is provided and the existing or updated task has a recurrence rule,
      we calculate the next due date based on that recurrence.
    - Otherwise, we simply update the provided fields.

    Args:
        task_id (int): The ID of the task to update.
        task_update (TaskUpdate): Updated task data.
        db (Session): Database session dependency.

    Returns:
        Task: The updated SQLAlchemy Task object.

    Raises:
        HTTPException: If the task is not found.
    """
    existing_task = db.query(Task).filter(Task.id == task_id).first()
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_update.dict(exclude_unset=True)

    # Update existing fields with new values.
    for key, value in update_data.items():
        setattr(existing_task, key, value)

    db.commit()
    db.refresh(existing_task)
    return existing_task


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
        dict: A message confirming the task deletion.

    Raises:
        HTTPException: If the task is not found.
    """
    task_obj = db.query(Task).filter(Task.id == task_id).first()
    if not task_obj:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task_obj)
    db.commit()
    return {"message": "Task deleted successfully"}


class CompleteTaskResponse(BaseModel):
    """
    Pydantic model for the response of completing a task.
    """
    completed_task: TaskResponse
    new_task: Optional[TaskResponse] = None


@router.post("/{task_id}/complete", response_model=CompleteTaskResponse, summary="Complete a task")
def complete_task(
    task_id: int = Path(..., description="The ID of the task to complete"),
    db: Session = Depends(get_db)
) -> CompleteTaskResponse:
    """
    Mark a task as completed. If the task has a recurrence rule, this endpoint will:
     - Complete the current task by setting its status to 'COMPLETED'.
     - Create a new task with the same title, description, priority, and recurrence,
       but with a due date shifted according to the recurrence rule.

    Args:
        task_id (int): The ID of the task to complete.
        db (Session): Database session.

    Returns:
        CompleteTaskResponse: A Pydantic model containing the completed task and the new task
                              (if recurrence is applied).

    Raises:
        HTTPException: If the task is not found.
    """
    existing_task = db.query(Task).filter(Task.id == task_id).first()
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Mark current task as completed
    existing_task.status = TaskStatus.COMPLETED
    db.commit()
    db.refresh(existing_task)

    new_task_obj = None

    # If the task has a recurrence rule, create a new task for the next due date
    if existing_task.recurrence and existing_task.due_date:
        next_due = get_next_due_date(existing_task.due_date, existing_task.recurrence)
        # Build a new task using the existing task's data
        new_task_obj = Task(
            title=existing_task.title,
            description=existing_task.description,
            due_date=next_due,
            priority=existing_task.priority,
            status=TaskStatus.TODO,  # New cycle starts in TODO status
            recurrence=existing_task.recurrence,
            note_path=existing_task.note_path
        )
        db.add(new_task_obj)
        db.commit()
        db.refresh(new_task_obj)

    return CompleteTaskResponse(
        completed_task=existing_task,
        new_task=new_task_obj
    )