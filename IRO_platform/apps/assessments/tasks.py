# apps/assessments/tasks.py
from celery import shared_task

@shared_task
def example_task(assessment_id):
    # your asynchronous logic, e.g., sending an email after an assessment is created
    pass