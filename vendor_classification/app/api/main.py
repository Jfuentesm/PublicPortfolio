# app/api/main.py
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import uuid
import os
import socket
from datetime import datetime, timedelta

from models.job import Job, JobStatus, ProcessingStage
from models.user import User

from core.config import settings
from core.logging_config import setup_logging, get_logger, set_correlation_id, set_user, set_job_id, log_function_call
from middleware.logging_middleware import RequestLoggingMiddleware, log_request_middleware

from api.auth import get_current_user, authenticate_user, create_access_token
from core.database import get_db
from core.initialize_db import initialize_database
from services.file_service import save_upload_file
# --- REMOVED direct task import ---
# from tasks.classification_tasks import process_vendor_file
# --- ADDED celery_app import ---
from tasks.celery_app import celery_app

from fastapi.security import OAuth2PasswordRequestForm

# Configure logging
logger = get_logger("vendor_classification.api")

app = FastAPI(
    title="NAICS Vendor Classification API",
    description="API for classifying vendors according to NAICS taxonomy",
    version="1.0.0",
)

# Add logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
frontend_dir = "/frontend"
static_dir = "/frontend/static"

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"Mounted static files from {static_dir}")
else:
    logger.error(f"Static directory not found at {static_dir}, cannot mount.")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the frontend application."""
    index_path = os.path.join(frontend_dir, "index.html")
    logger.info(f"Attempting to serve index.html from {index_path}")
    if os.path.exists(index_path):
        logger.info("Serving index.html")
        return FileResponse(index_path)
    else:
        logger.error(f"Index file not found at {index_path}", extra={"path": index_path})
        content = f"<html><body><h1>Error: Frontend file not found</h1><p>Could not find {index_path}</p></body></html>"
        return HTMLResponse(content=content, status_code=404)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    hostname = socket.gethostname()
    local_ip = ""
    try:
        local_ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        local_ip = "Could not resolve IP"
    logger.info(f"Health check called", extra={"hostname": hostname, "ip": local_ip})
    db_status = "unknown"
    try:
        db = next(get_db())
        db_status = "connected"
        db.close()
    except Exception as e:
        logger.error(f"Database connection error during health check", exc_info=False, extra={"error_details": str(e)})
        db_status = f"error: {str(e)[:100]}"
    frontend_status = "found" if os.path.exists(os.path.join(frontend_dir, "index.html")) else "missing"
    static_status = "found" if os.path.exists(static_dir) else "missing"
    # Check Celery broker connection (optional but good)
    celery_broker_status = "unknown"
    try:
        celery_status = celery_app.control.inspect().ping()
        if celery_status:
            celery_broker_status = "connected"
        else:
            celery_broker_status = "no response from worker(s)"
    except Exception as celery_e:
        celery_broker_status = f"error: {str(celery_e)[:100]}"

    return {
        "status": "healthy",
        "hostname": hostname,
        "ip": local_ip,
        "database": db_status,
        "celery_broker": celery_broker_status,
        "frontend_index": frontend_status,
        "frontend_static": static_status,
        "timestamp": datetime.now().isoformat()
    }

# Custom Exception Handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    correlation_id = getattr(exc, 'correlation_id', None) or uuid.uuid4()
    logger.error("Request validation failed (422)", extra={ "error_details": exc.errors(), "request_body_preview": str(await request.body())[:500], "request_headers": dict(request.headers), "correlation_id": correlation_id, "path": request.url.path })
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": exc.errors()})


# Fully Restored upload_file
@app.post("/api/v1/upload", response_model=Dict[str, Any])
async def upload_file(
    # background_tasks: BackgroundTasks, # Removed - using Celery directly
    file: UploadFile = File(...),
    company_name: str = Form(...),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Upload vendor Excel file for processing."""
    job_id = str(uuid.uuid4())
    set_correlation_id(job_id)
    set_job_id(job_id)
    set_user(current_user)

    logger.info(
        f"===> Entered upload_file endpoint",
        extra={
            "company_name": company_name,
            "uploaded_filename": file.filename, # Keep renamed key
            "content_type": file.content_type,
            "file_size": file.size,
            "username": current_user.username,
            "job_id": job_id
        }
    )

    if not file.filename:
         logger.warning("Upload rejected: File has no filename.", extra={"job_id": job_id})
         raise HTTPException(status_code=400, detail="File must have a filename.")
    if not file.filename.endswith(('.xlsx', '.xls')):
        logger.warning(f"Invalid file format rejected", extra={"filename": file.filename, "valid_formats": [".xlsx", ".xls"], "job_id": job_id})
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")
    if not company_name or not company_name.strip():
         logger.warning("Upload rejected: Company name is missing or empty.", extra={"job_id": job_id})
         raise HTTPException(status_code=400, detail="Company name cannot be empty.")

    try:
        logger.info("Attempting to save uploaded file...", extra={"job_id": job_id})
        input_file_path = save_upload_file(file, job_id)
        logger.info(f"File saved successfully", extra={"filepath": input_file_path, "job_id": job_id})

        logger.info("Creating Job record in database...", extra={"job_id": job_id})
        job = Job(
            id=job_id,
            company_name=company_name,
            input_file_name=file.filename,
            status=JobStatus.PENDING,
            current_stage=ProcessingStage.INGESTION,
            created_by=current_user.username
        )
        db.add(job)
        db.commit()
        logger.info(f"Job created successfully in database", extra={"company": company_name, "status": JobStatus.PENDING, "job_id": job_id})

        logger.info(f"Attempting to send task to Celery", extra={"job_id": job_id, "input_file_path": input_file_path})
        try:
            # --- UPDATED TASK SENDING ---
            task_name = 'tasks.classification_tasks.process_vendor_file'
            celery_app.send_task(task_name, args=[job_id, input_file_path])
            # --- END UPDATED TASK SENDING ---
            logger.info("Celery task sent successfully", extra={"job_id": job_id, "task_name": task_name})
        except Exception as task_error:
             logger.error("Failed to send Celery task!", exc_info=True, extra={"job_id": job_id})
             # Attempt to mark job as failed if task sending fails
             job.fail(f"Failed to queue processing task: {str(task_error)}")
             db.commit()
             raise HTTPException(status_code=500, detail=f"Error scheduling processing task: {str(task_error)}")

        logger.info(f"File uploaded successfully, processing scheduled via Celery", extra={"job_id": job_id})
        return { "job_id": job_id, "status": "pending", "message": f"File {file.filename} uploaded successfully and processing has started" }
    except HTTPException as http_exc:
        logger.warning(f"HTTP exception during upload", extra={"status_code": http_exc.status_code, "detail": http_exc.detail, "job_id": job_id})
        raise http_exc # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Unexpected error processing upload", exc_info=True, extra={"error": str(e), "job_id": job_id})
        try:
            # Ensure job exists before trying to fail it
            job_in_error = db.query(Job).filter(Job.id == job_id).first()
            if job_in_error and job_in_error.status != JobStatus.FAILED.value:
                job_in_error.fail(f"Upload endpoint failed: {str(e)}")
                db.commit()
                logger.info("Marked job as failed due to upload error.", extra={"job_id": job_id})
            elif not job_in_error:
                 logger.error("Could not find job to mark as failed during upload error handling.", extra={"job_id": job_id})

        except Exception as db_err:
            logger.error("Failed to mark job as failed during error handling.", exc_info=True, extra={"job_id": job_id, "db_error": str(db_err)})
            db.rollback()
        # Raise a generic 500 for unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during upload: {str(e)}")


@app.get("/api/v1/jobs/{job_id}", response_model=Dict[str, Any])
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Check job status."""
    set_correlation_id(job_id)
    set_job_id(job_id)
    set_user(current_user)
    logger.info(f"Job status requested", extra={"username": current_user.username, "job_id": job_id})
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.warning(f"Job not found", extra={"job_id": job_id})
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
    logger.info(f"Job status retrieved", extra={ "status": job.status, "progress": job.progress, "stage": job.current_stage, "job_id": job_id })
    job_stats = job.stats if isinstance(job.stats, dict) else {}
    return { "job_id": job.id, "status": job.status, "progress": job.progress, "current_stage": job.current_stage, "created_at": job.created_at, "updated_at": job.updated_at, "estimated_completion": job_stats.get('estimated_completion', None), "error_message": job.error_message }

# --- UPDATED download_results (Fixed logging key) ---
@app.get("/api/v1/jobs/{job_id}/download")
async def download_results(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Download job results."""
    set_correlation_id(job_id)
    set_job_id(job_id)
    set_user(current_user)
    logger.info(f"Results download requested", extra={"username": current_user.username, "job_id": job_id})

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.warning(f"Job not found", extra={"job_id": job_id})
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")

    if job.status == JobStatus.FAILED.value:
        logger.warning(f"Attempt to download results for failed job", extra={"job_id": job_id, "status": job.status})
        raise HTTPException(status_code=400, detail=f"Job failed: {job.error_message}")

    if job.status != JobStatus.COMPLETED.value:
        logger.warning(f"Job not completed", extra={"job_id": job_id, "status": job.status})
        raise HTTPException(status_code=400, detail="Job processing has not completed yet")

    if not job.output_file_name:
        logger.error(f"Job completed but output file name is missing", extra={"job_id": job_id})
        raise HTTPException(status_code=404, detail="Output file name not recorded for this job.")

    output_path = os.path.join(settings.OUTPUT_DATA_DIR, job_id, job.output_file_name)
    if not os.path.exists(output_path):
        logger.error(f"Output file not found on disk", extra={"job_id": job_id, "expected_path": output_path})
        raise HTTPException(status_code=404, detail="Output file not found on server.")

    # --- FIXED LOGGING KEY ---
    logger.info(f"Serving result file",
               extra={"output_filename": job.output_file_name, "path": output_path, "job_id": job_id})
    # --- END FIXED LOGGING KEY ---

    return FileResponse(
        output_path,
        filename=job.output_file_name, # This filename is sent to the browser
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
# --- END UPDATED download_results ---


@app.post("/api/v1/jobs/{job_id}/notify", response_model=Dict[str, Any])
async def request_notification(
    job_id: str,
    email_payload: Dict[str, str],
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Request email notification when job completes."""
    set_correlation_id(job_id)
    set_job_id(job_id)
    set_user(current_user)
    email = email_payload.get("email")
    if not email:
         logger.warning("Notification request missing email.", extra={"job_id": job_id})
         raise HTTPException(status_code=400, detail="Email address is required in the request body.")
    logger.info(f"Notification requested", extra={"username": current_user.username, "email": email, "job_id": job_id})
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.warning(f"Job not found", extra={"job_id": job_id})
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
    job.notification_email = email
    db.commit()
    logger.info(f"Notification email set", extra={"email": email, "job_id": job_id})
    return { "success": True, "message": f"Notification will be sent to {email} when job completes" }

@app.get("/api/v1/jobs/{job_id}/stats", response_model=Dict[str, Any])
async def get_job_stats(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get job processing statistics."""
    set_correlation_id(job_id)
    set_job_id(job_id)
    set_user(current_user)
    logger.info(f"Job stats requested", extra={"username": current_user.username, "job_id": job_id})
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.warning(f"Job not found", extra={"job_id": job_id})
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
    logger.info(f"Job stats retrieved", extra={"job_id": job_id})

    # Safely access nested stats
    job_stats = job.stats if isinstance(job.stats, dict) else {}
    api_usage = job_stats.get("api_usage", {}) if isinstance(job_stats.get("api_usage"), dict) else {}

    return {
        "vendors_processed": job_stats.get("total_vendors", 0),
        "unique_vendors": job_stats.get("unique_vendors", 0),
        # Use the updated key names from classification_tasks.py
        "api_calls": api_usage.get("openrouter_calls", 0),
        "tokens_used": api_usage.get("openrouter_total_tokens", 0),
        "tavily_searches": api_usage.get("tavily_search_calls", 0),
        "processing_time": job_stats.get("processing_duration_seconds", 0)
    }


@app.post("/token", response_model=Dict[str, Any])
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db = Depends(get_db)
):
    """Get an access token for authentication."""
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)
    client_host = request.client.host if request.client else "Unknown"
    logger.info(f"Login attempt", extra={"username": form_data.username, "ip": client_host, "correlation_id": correlation_id})
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            logger.warning(f"Login failed: invalid credentials", extra={"username": form_data.username, "ip": client_host, "correlation_id": correlation_id})
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
        set_user(user)
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
        logger.info(f"Login successful", extra={ "username": user.username, "ip": client_host, "token_expires_in_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES, "correlation_id": correlation_id })
        return { "access_token": access_token, "token_type": "bearer", "username": user.username }
    except HTTPException as http_exc:
        if http_exc.status_code != status.HTTP_401_UNAUTHORIZED:
             logger.error(f"HTTP exception during login", exc_info=True, extra={"correlation_id": correlation_id})
        raise
    except Exception as e:
        logger.error(f"Unexpected login error", exc_info=True, extra={"error": str(e), "username": form_data.username, "correlation_id": correlation_id})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred during the login process")

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    setup_logging(log_level=None, log_to_file=True)
    logger.info("Application starting up...")
    try:
        logger.info("Initializing database...")
        initialize_database()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.critical(f"CRITICAL: Error initializing database during startup.", exc_info=True, extra={"error_details": str(e)})
    hostname = socket.gethostname()
    local_ip = ""
    try:
         local_ip = socket.gethostbyname(hostname)
    except socket.gaierror:
         local_ip = "Could not resolve IP"
    logger.info(f"Server running", extra={"hostname": hostname, "ip": local_ip, "port": 8000})
    if os.path.exists(frontend_dir):
        try:
            frontend_files = os.listdir(frontend_dir)
            logger.info(f"Frontend directory found at {frontend_dir}", extra={"files_count": len(frontend_files)})
            if not os.path.exists(os.path.join(frontend_dir, "index.html")):
                 logger.warning(f"index.html not found inside {frontend_dir}")
            if not os.path.exists(static_dir):
                 logger.warning(f"Static directory not found at {static_dir}")
        except Exception as list_err:
             logger.error(f"Error listing frontend directory contents", exc_info=True)
    else:
        logger.error(f"Frontend directory not found at {frontend_dir}!")

if __name__ == "__main__":
    import uvicorn
    setup_logging(log_level="DEBUG", log_to_file=False)
    logger.info("Starting uvicorn server directly (likely for debugging)")
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")