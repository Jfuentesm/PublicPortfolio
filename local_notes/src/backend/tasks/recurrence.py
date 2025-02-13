# src/backend/tasks/recurrence.py
"""
recurrence.py

Provides simple recurrence logic for tasks.
Contains functions to calculate the next due date based on a given recurrence rule.
"""

import datetime


def get_next_due_date(current_due_date: datetime.datetime, recurrence: str) -> datetime.datetime:
    """
    Calculate the next due date based on the current due date and recurrence rule.

    Args:
        current_due_date (datetime.datetime): The current due date.
        recurrence (str): The recurrence rule ("daily", "weekly", "monthly").

    Returns:
        datetime.datetime: The computed next due date.
    """
    recurrence_lower = recurrence.lower()
    if recurrence_lower == "daily":
        return current_due_date + datetime.timedelta(days=1)
    elif recurrence_lower == "weekly":
        return current_due_date + datetime.timedelta(weeks=1)
    elif recurrence_lower == "monthly":
        # For simplicity, approximate a month as 30 days.
        return current_due_date + datetime.timedelta(days=30)
    else:
        # Return the unchanged due date if the recurrence rule is unrecognized.
        return current_due_date
