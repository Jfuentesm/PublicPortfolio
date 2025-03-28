# app/api/main.py
import socket # Ensure socket is imported
import sqlalchemy # Ensure sqlalchemy is imported
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import uuid
import os
from datetime import datetime, timedelta

from models.job import Job, JobStatus, ProcessingStage
from models.user import User

from core.config import settings
# --- MODIFIED IMPORT: Added get_correlation_id ---
from core.logging_config import setup_logging, get_logger, set_correlation_id, set_user, set_job_id, log_function_call, get_correlation_id
# --- END MODIFIED IMPORT ---
from middleware.logging_middleware import RequestLoggingMiddleware # Removed log_request_middleware as it's not used directly here

from api.auth import get_current_user, authenticate_user, create_access_token
from core.database import get_db
from core.initialize_db import initialize_database
from services.file_service import save_upload_file
from tasks.celery_app import celery_app # Use celery_app directly

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
    try:
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        logger.info(f"Mounted static files from {static_dir}")
    except RuntimeError as e:
         logger.warning(f"Could not mount static files (possibly already mounted): {e}")
    except Exception as e:
        logger.error(f"Failed to mount static files from {static_dir}", exc_info=True)
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
        # Try getting IP associated with hostname, might fail in some container setups
        local_ip = socket.gethostbyname(hostname)
    except socket.gaierror:
         # Fallback: Try getting IP from a common interface (like eth0)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80)) # Connect to external IP to find local outbound IP
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
             local_ip = "Could not resolve IP"

    logger.info(f"Health check called", extra={"hostname": hostname, "ip": local_ip})
    db_status = "unknown"
    try:
        db = next(get_db())
        # Perform a simple query to test connection
        db.execute(sqlalchemy.text("SELECT 1")) # <--- sqlalchemy used here
        db_status = "connected"
        db.close()
    except Exception as e:
        logger.error(f"Database connection error during health check", exc_info=False, extra={"error_details": str(e)})
        db_status = f"error: {str(e)[:100]}"

    frontend_status = "found" if os.path.exists(os.path.join(frontend_dir, "index.html")) else "missing"
    static_status = "found" if os.path.exists(static_dir) else "missing"

    # Check Celery broker connection
    celery_broker_status = "unknown"
    try:
        # Use connection test which is more reliable than ping
        with celery_app.connection() as connection:
            connection.ensure_connection(max_retries=1, timeout=2)
            celery_broker_status = "connected"
            logger.debug("Celery broker connection successful during health check.")
    except Exception as celery_e:
        logger.error(f"Celery broker connection error during health check: {str(celery_e)}", exc_info=False)
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

# Custom Exception Handler for Validation Errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    correlation_id = get_correlation_id() or str(uuid.uuid4()) # <--- get_correlation_id used here
    try:
        body_preview = str(await request.body())[:500]
    except Exception:
        body_preview = "[Could not read request body]"
    logger.error("Request validation failed (422)", extra={
        "error_details": exc.errors(),
        "request_body_preview": body_preview,
        "request_headers": dict(request.headers),
        "correlation_id": correlation_id,
        "path": request.url.path
    })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
        headers={"X-Correlation-ID": correlation_id} # Include correlation ID in response
    )

# General Exception Handler
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    correlation_id = get_correlation_id() or str(uuid.uuid4()) # <--- get_correlation_id used here
    logger.error(f"Unhandled exception during request to {request.url.path}", exc_info=True, extra={
        "correlation_id": correlation_id,
        "request_headers": dict(request.headers),
        "path": request.url.path,
        "method": request.method,
    })
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred.", "correlation_id": correlation_id},
        headers={"X-Correlation-ID": correlation_id}
    )


@app.post("/api/v1/upload", response_model=Dict[str, Any])
async def upload_file(
    file: UploadFile = File(...),
    company_name: str = Form(...),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Upload vendor Excel file for processing."""
    job_id = str(uuid.uuid4())
    # Set context early
    set_correlation_id(job_id)
    set_job_id(job_id)
    if current_user: set_user(current_user)

    logger.info(
        f"===> Entered upload_file endpoint",
        extra={
            "company_name": company_name,
            "uploaded_filename": file.filename,
            "content_type": file.content_type,
            "file_size": getattr(file, 'size', 'unknown'), # Use getattr for safety
            "username": current_user.username if current_user else "unknown",
        }
    )

    # --- Input Validations ---
    if not file.filename:
         logger.warning("Upload rejected: File has no filename.")
         raise HTTPException(status_code=400, detail="File must have a filename.")
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        logger.warning(f"Invalid file format rejected", extra={"filename": file.filename, "valid_formats": [".xlsx", ".xls"]})
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")
    if not company_name or not company_name.strip():
         logger.warning("Upload rejected: Company name is missing or empty.")
         raise HTTPException(status_code=400, detail="Company name cannot be empty.")
    # --- End Validations ---

    try:
        logger.info("Attempting to save uploaded file...")
        input_file_path = save_upload_file(file, job_id) # Can raise IOError
        logger.info(f"File saved successfully", extra={"filepath": input_file_path})

        logger.info("Creating Job record in database...")
        job = Job(
            id=job_id,
            company_name=company_name,
            input_file_name=file.filename, # Store original filename
            status=JobStatus.PENDING,
            current_stage=ProcessingStage.INGESTION,
            created_by=current_user.username # Store username of creator
        )
        db.add(job)
        db.commit()
        logger.info(f"Job created successfully in database", extra={"company": company_name, "status": JobStatus.PENDING})

        logger.info(f"Attempting to send task to Celery", extra={"input_file_path": input_file_path})
        try:
            task_name = 'tasks.classification_tasks.process_vendor_file'
            # Send task with job_id and file_path
            celery_app.send_task(task_name, args=[job_id, input_file_path])
            logger.info("Celery task sent successfully", extra={"task_name": task_name})
        except Exception as task_error:
             logger.error("Failed to send Celery task!", exc_info=True)
             # Attempt to mark job as failed if task sending fails
             job.fail(f"Failed to queue processing task: {str(task_error)}")
             db.commit()
             # Raise HTTP 500 - crucial step failed
             raise HTTPException(status_code=500, detail=f"Error scheduling processing task: {str(task_error)}")

        logger.info(f"File uploaded successfully, processing scheduled via Celery")
        # Return essential info needed by frontend
        return {
             "job_id": job_id,
             "status": job.status,
             "current_stage": job.current_stage,
             "progress": job.progress,
             "created_at": job.created_at.isoformat() if job.created_at else None,
             "message": f"File '{file.filename}' uploaded. Processing started."
         }

    except HTTPException as http_exc:
        logger.warning(f"HTTP exception during upload", extra={"status_code": http_exc.status_code, "detail": http_exc.detail})
        raise http_exc # Re-raise HTTP exceptions directly

    except IOError as io_err:
        logger.error(f"File saving error during upload", exc_info=True, extra={"error": str(io_err)})
        # Try to fail the job if it exists
        job_in_error = db.query(Job).filter(Job.id == job_id).first()
        if job_in_error and job_in_error.status != JobStatus.FAILED.value:
             job_in_error.fail(f"Upload endpoint failed (file save): {str(io_err)}")
             db.commit()
        raise HTTPException(status_code=500, detail=f"Could not save uploaded file: {str(io_err)}")

    except Exception as e:
        logger.error(f"Unexpected error processing upload", exc_info=True, extra={"error": str(e)})
        # Try to fail the job if it exists
        job_in_error = db.query(Job).filter(Job.id == job_id).first()
        if job_in_error and job_in_error.status != JobStatus.FAILED.value:
            job_in_error.fail(f"Upload endpoint failed (unexpected): {str(e)}")
            db.commit()
            logger.info("Marked job as failed due to upload error.")
        elif not job_in_error:
            # Job might not have been created if error happened before db.add/commit
            logger.error("Could not find job to mark as failed during upload error handling.")
        else:
             db.rollback() # Rollback potential partial changes if job exists but failed state couldn't be set

        # Raise a generic 500 for unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during upload.")


@app.get("/api/v1/jobs/{job_id}", response_model=Dict[str, Any])
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user), # Ensure user is logged in
    db = Depends(get_db)
):
    """Check job status."""
    set_correlation_id(job_id)
    set_job_id(job_id)
    if current_user: set_user(current_user)
    logger.info(f"Job status requested", extra={"username": current_user.username if current_user else "unknown"})

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.warning(f"Job not found")
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")

    # --- Calculate Estimated Completion Time (Simplified Example) ---
    estimated_completion_iso = None
    if job.status == JobStatus.PROCESSING.value and job.progress > 0 and job.progress < 1.0:
        try:
            elapsed_time = (datetime.now(job.created_at.tzinfo) - job.created_at).total_seconds()
            if elapsed_time > 10: # Avoid division by zero or tiny progress
                total_estimated_time = elapsed_time / job.progress
                remaining_time = total_estimated_time - elapsed_time
                if remaining_time > 0:
                    estimated_completion_dt = datetime.now(job.created_at.tzinfo) + timedelta(seconds=remaining_time)
                    estimated_completion_iso = estimated_completion_dt.isoformat()
        except Exception as calc_err:
            logger.warning(f"Could not calculate estimated completion time: {calc_err}", exc_info=False)
    elif job.status == JobStatus.COMPLETED.value and job.completed_at:
         estimated_completion_iso = job.completed_at.isoformat()
    # --- End Estimated Completion ---

    logger.info(f"Job status retrieved", extra={ "status": job.status, "progress": job.progress, "stage": job.current_stage})

    return {
        "job_id": job.id,
        "status": job.status,
        "progress": job.progress,
        "current_stage": job.current_stage,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        "estimated_completion": estimated_completion_iso,
        "error_message": job.error_message
    }


@app.get("/api/v1/jobs/{job_id}/download")
async def download_results(
    job_id: str,
    current_user: User = Depends(get_current_user), # Ensure user is logged in
    db = Depends(get_db)
):
    """Download job results."""
    set_correlation_id(job_id)
    set_job_id(job_id)
    if current_user: set_user(current_user)
    logger.info(f"Results download requested", extra={"username": current_user.username if current_user else "unknown"})

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.warning(f"Job not found")
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")

    if job.status == JobStatus.FAILED.value:
        logger.warning(f"Attempt to download results for failed job", extra={"status": job.status})
        raise HTTPException(status_code=400, detail=f"Job failed: {job.error_message}")

    if job.status != JobStatus.COMPLETED.value:
        logger.warning(f"Job not completed, download rejected", extra={"status": job.status})
        raise HTTPException(status_code=400, detail="Job processing has not completed yet")

    if not job.output_file_name:
        logger.error(f"Job completed but output file name is missing")
        raise HTTPException(status_code=404, detail="Output file name not recorded for this job.")

    output_path = os.path.join(settings.OUTPUT_DATA_DIR, job_id, job.output_file_name)
    if not os.path.exists(output_path):
        logger.error(f"Output file not found on disk", extra={"expected_path": output_path})
        raise HTTPException(status_code=404, detail="Output file not found on server.")

    # --- FIXED LOGGING KEY ---
    logger.info(f"Serving result file",
               extra={"output_filename": job.output_file_name, "path": output_path})
    # --- END FIXED LOGGING KEY ---

    # Use original input filename stem + _results suffix for browser download name
    base_name, _ = os.path.splitext(job.input_file_name)
    download_filename = f"{base_name}_results.xlsx"

    return FileResponse(
        output_path,
        filename=download_filename, # Suggest a user-friendly download name
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=\"{download_filename}\""} # Ensure download behavior
    )


@app.post("/api/v1/jobs/{job_id}/notify", response_model=Dict[str, Any])
async def request_notification(
    job_id: str,
    email_payload: Dict[str, str],
    current_user: User = Depends(get_current_user), # Ensure user is logged in
    db = Depends(get_db)
):
    """Request email notification when job completes."""
    set_correlation_id(job_id)
    set_job_id(job_id)
    if current_user: set_user(current_user)

    email = email_payload.get("email")
    if not email:
         logger.warning("Notification request missing email.")
         raise HTTPException(status_code=400, detail="Email address is required in the request body.")

    logger.info(f"Notification requested", extra={"username": current_user.username if current_user else "unknown", "email": email})

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.warning(f"Job not found")
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")

    # Simple email format validation (basic check)
    if "@" not in email or "." not in email.split('@')[-1]:
        logger.warning(f"Invalid email format provided for notification: {email}")
        raise HTTPException(status_code=400, detail="Invalid email address format provided.")

    job.notification_email = email
    try:
        db.commit()
        logger.info(f"Notification email set successfully", extra={"email": email})
        return { "success": True, "message": f"Notification will be sent to {email} when job completes" }
    except Exception as e:
        db.rollback()
        logger.error("Failed to save notification email to database", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update notification preferences.")


@app.get("/api/v1/jobs/{job_id}/stats", response_model=Dict[str, Any])
async def get_job_stats(
    job_id: str,
    current_user: User = Depends(get_current_user), # Ensure user is logged in
    db = Depends(get_db)
):
    """Get job processing statistics."""
    set_correlation_id(job_id)
    set_job_id(job_id)
    if current_user: set_user(current_user)
    logger.info(f"Job stats requested", extra={"username": current_user.username if current_user else "unknown"})

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.warning(f"Job not found")
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")

    if not isinstance(job.stats, dict):
         logger.warning(f"Job stats data is not a dictionary or is missing", extra={"stats_type": type(job.stats)})
         # Return default/empty stats instead of erroring? Or raise 500?
         # Let's return defaults for robustness
         return {
             "vendors_processed": 0,
             "unique_vendors": 0,
             "api_calls": 0,
             "tokens_used": 0,
             "tavily_searches": 0,
             "processing_time": 0
         }

    logger.info(f"Job stats retrieved")

    # Safely access nested stats using .get() with defaults
    job_stats = job.stats
    api_usage = job_stats.get("api_usage", {}) # Default to empty dict if api_usage is missing

    # --- USE CORRECT KEYS FROM classification_tasks.py ---
    return {
        "vendors_processed": job_stats.get("total_vendors", 0),
        "unique_vendors": job_stats.get("unique_vendors", 0),
        "api_calls": api_usage.get("openrouter_calls", 0), # Updated key
        "tokens_used": api_usage.get("openrouter_total_tokens", 0), # Updated key
        "tavily_searches": api_usage.get("tavily_search_calls", 0),
        "processing_time": job_stats.get("processing_duration_seconds", 0)
    }
    # --- END USE CORRECT KEYS ---


@app.post("/token", response_model=Dict[str, Any])
async def login_for_access_token(
    request: Request, # Inject Request for client info
    form_data: OAuth2PasswordRequestForm = Depends(),
    db = Depends(get_db)
):
    """Get an access token for authentication."""
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)
    client_host = request.client.host if request.client else "Unknown"
    logger.info(f"Login attempt", extra={"username": form_data.username, "ip": client_host})

    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            logger.warning(f"Login failed: invalid credentials", extra={"username": form_data.username, "ip": client_host})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Set user context *after* successful authentication
        set_user(user)

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        logger.info(f"Login successful", extra={ "username": user.username, "ip": client_host, "token_expires_in_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES})

        return { "access_token": access_token, "token_type": "bearer", "username": user.username }

    except HTTPException as http_exc:
        # Don't log expected 401s as errors, but log other HTTP exceptions
        if http_exc.status_code != status.HTTP_401_UNAUTHORIZED:
             logger.error(f"HTTP exception during login", exc_info=True)
        raise # Re-raise the HTTPException
    except Exception as e:
        logger.error(f"Unexpected login error", exc_info=True, extra={"error": str(e), "username": form_data.username})
        # Raise a generic 500 for unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during the login process."
        )


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    # Setup logging first
    log_dir = "/data/logs" if os.path.exists("/data") else "./logs" # Use local dir if /data absent
    # --- MODIFIED: Pass llm_trace_log_file name ---
    setup_logging(
        log_level=None,
        log_to_file=True,
        log_dir=log_dir,
        async_logging=True,
        llm_trace_log_file="llm_api_trace.log" # Specify the trace log filename
    )
    # --- END MODIFIED ---
    logger.info("*********************************************")
    logger.info("          Application starting up...         ")
    logger.info("*********************************************")

    try:
        logger.info("Initializing database...")
        initialize_database() # Creates tables and admin user
        logger.info("Database initialization completed.")
    except Exception as e:
        logger.critical(f"CRITICAL: Error initializing database during startup.", exc_info=True, extra={"error_details": str(e)})
        # Decide if the app should exit or try to continue without DB
        # For now, we log critical and continue, but health check will fail.
        # raise SystemExit("Database initialization failed.") # Option to exit

    hostname = socket.gethostname()
    local_ip = "unknown"
    try:
         s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
         s.connect(("8.8.8.8", 80))
         local_ip = s.getsockname()[0]
         s.close()
    except Exception:
         try:
             local_ip = socket.gethostbyname(hostname)
         except socket.gaierror:
              local_ip = "Could not resolve IP"

    logger.info(f"Server starting", extra={"hostname": hostname, "ip": local_ip, "port": 8000}) # Default port
    logger.info(f"Input Dir: {settings.INPUT_DATA_DIR}, Output Dir: {settings.OUTPUT_DATA_DIR}, Taxonomy Dir: {settings.TAXONOMY_DATA_DIR}")
    logger.info(f"OpenRouter Model: {settings.OPENROUTER_MODEL}")
    logger.info(f"Redis URL: {settings.REDIS_URL}")
    logger.info(f"DB URL Host: {settings.DATABASE_URL.split('@')[-1].split('/')[0]}") # Log host, not full URL

    # Check frontend/static again after logging is set up
    if not os.path.exists(frontend_dir):
         logger.error(f"Frontend directory not found at {frontend_dir}")
    elif not os.path.exists(os.path.join(frontend_dir, "index.html")):
         logger.warning(f"index.html not found inside {frontend_dir}")

    if not os.path.exists(static_dir):
         logger.error(f"Static directory not found at {static_dir}")


# --- Optional: Add shutdown event ---
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("*********************************************")
    logger.info("          Application shutting down...       ")
    logger.info("*********************************************")
    # Add any cleanup tasks here if needed
# --- End Optional Shutdown ---