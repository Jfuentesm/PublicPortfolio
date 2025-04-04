# app/api/main.py
import socket
import sqlalchemy
import httpx
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from typing import Dict, Any, Optional, List
import uuid
import os
from datetime import datetime, timedelta
import logging

# --- Model Imports ---
from models.job import Job, JobStatus, ProcessingStage
from models.user import User

# --- Core Imports ---
from core.config import settings
from core.logging_config import setup_logging, get_logger, set_correlation_id, set_user, set_job_id, log_function_call, get_correlation_id
from middleware.logging_middleware import RequestLoggingMiddleware
from core.database import get_db, SessionLocal
from core.initialize_db import initialize_database

# --- Service Imports ---
from services.file_service import save_upload_file

# --- Task Imports ---
from tasks.celery_app import celery_app

# --- Utility Imports ---
from utils.taxonomy_loader import load_taxonomy

# --- Auth Imports ---
from fastapi.security import OAuth2PasswordRequestForm
from api.auth import (
    get_current_user,
    authenticate_user,
    create_access_token,
    get_current_active_user # Keep this if needed elsewhere, though often get_current_user is enough
)

# --- Router Imports ---
from api import jobs as jobs_router
from api import users as users_router # Import the new users router

# --- Schema Imports ---
from schemas.job import JobResponse
from schemas.user import UserResponse as UserResponseSchema # Import UserResponse schema


# --- Logging Setup ---
setup_logging_done = False
try:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    startup_logger = logging.getLogger("vendor_classification.startup")
except Exception as e:
    print(f"Initial basic logging config failed: {e}")
    startup_logger = logging.getLogger("vendor_classification.startup")

logger = get_logger("vendor_classification.api") # Get the main API logger


# --- FastAPI App Initialization ---
app = FastAPI(
    title="NAICS Vendor Classification API",
    description="API for classifying vendors according to NAICS taxonomy",
    version="1.0.0",
)

# --- Middleware ---
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Vue.js Frontend Serving Setup ---
VUE_BUILD_DIR = "/app/frontend/dist"
VUE_INDEX_FILE = os.path.join(VUE_BUILD_DIR, "index.html")
logger.info(f"Attempting to serve Vue frontend from: {VUE_BUILD_DIR}")
if not os.path.exists(VUE_BUILD_DIR):
    logger.error(f"Vue build directory NOT FOUND at {VUE_BUILD_DIR}. Frontend will not be served.")
elif not os.path.exists(VUE_INDEX_FILE):
    logger.error(f"Vue index.html NOT FOUND at {VUE_INDEX_FILE}. Frontend serving might fail.")
else:
    logger.info(f"Vue build directory and index.html found. Static files will be mounted.")
# Static files are mounted at the end of the file


# --- API ROUTES ---

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    hostname = socket.gethostname()
    local_ip = ""
    try:
        local_ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
             local_ip = "Could not resolve IP"

    logger.info(f"Health check called", extra={"hostname": hostname, "ip": local_ip})
    db_status = "unknown"
    db = None
    try:
        db = SessionLocal()
        db.execute(sqlalchemy.text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Health Check: Database connection error", exc_info=True, extra={"error_details": str(e)})
        db_status = f"error: {str(e)[:100]}"
    finally:
        if db:
            db.close()

    vue_frontend_status = "found" if os.path.exists(VUE_INDEX_FILE) else "missing"

    celery_broker_status = "unknown"
    celery_connection = None
    try:
        celery_connection = celery_app.connection(heartbeat=2.0)
        celery_connection.ensure_connection(max_retries=1, timeout=2)
        celery_broker_status = "connected"
    except Exception as celery_e:
        logger.error(f"Celery broker connection error during health check: {str(celery_e)}", exc_info=False)
        celery_broker_status = f"error: {str(celery_e)[:100]}"
    finally:
         if celery_connection:
              try: celery_connection.close()
              except Exception as close_err: logger.warning(f"Error closing celery connection in health check: {close_err}")

    openrouter_status = "unknown"
    tavily_status = "unknown"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
             or_url = f"{settings.OPENROUTER_API_BASE}/models"
             or_headers = {"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"}
             or_resp = await client.get(or_url, headers=or_headers)
             openrouter_status = "connected" if or_resp.status_code == 200 else f"error: {or_resp.status_code}"

             tv_url = "https://api.tavily.com/search"
             tv_payload = {"api_key": settings.TAVILY_API_KEY, "query": "test", "max_results": 1}
             tv_resp = await client.post(tv_url, json=tv_payload)
             tavily_status = "connected" if tv_resp.status_code == 200 else f"error: {tv_resp.status_code}"

    except httpx.RequestError as http_err:
         logger.warning(f"HTTPX RequestError during external API health check: {http_err}")
         openrouter_status = openrouter_status if openrouter_status != "unknown" else "connection_error"
         tavily_status = tavily_status if tavily_status != "unknown" else "connection_error"
    except Exception as api_err:
         logger.error(f"Error checking external APIs during health check: {api_err}")
         openrouter_status = openrouter_status if openrouter_status != "unknown" else "check_error"
         tavily_status = tavily_status if tavily_status != "unknown" else "check_error"

    return {
        "status": "healthy",
        "hostname": hostname,
        "ip": local_ip,
        "database": db_status,
        "celery_broker": celery_broker_status,
        "vue_frontend_index": vue_frontend_status,
        "external_api_openrouter": openrouter_status,
        "external_api_tavily": tavily_status,
        "timestamp": datetime.now().isoformat()
    }


# --- Exception Handlers ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    correlation_id = get_correlation_id() or str(uuid.uuid4())
    try: body_preview = str(await request.body())[:500]
    except Exception: body_preview = "[Could not read request body]"
    logger.error("Request validation failed (422)", extra={
        "error_details": exc.errors(), "request_body_preview": body_preview,
        "request_headers": dict(request.headers), "correlation_id": correlation_id,
        "path": request.url.path
    })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
        headers={"X-Correlation-ID": correlation_id}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    correlation_id = get_correlation_id() or str(uuid.uuid4())
    logger.error(f"Unhandled exception during request to {request.url.path}", exc_info=True, extra={
        "correlation_id": correlation_id, "request_headers": dict(request.headers),
        "path": request.url.path, "method": request.method,
    })
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred.", "correlation_id": correlation_id},
        headers={"X-Correlation-ID": correlation_id}
    )


# --- Authentication Endpoint ---
@app.post("/token", response_model=Dict[str, Any]) # Keep response model generic Dict or create specific AuthResponse schema
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db = Depends(get_db)
):
    """Handles user login and returns JWT token and user details."""
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

        # Check if user is active *after* authentication
        if not user.is_active:
             logger.warning(f"Login failed: user '{user.username}' is inactive.", extra={"ip": client_host})
             raise HTTPException(
                 status_code=status.HTTP_400_BAD_REQUEST, # Use 400 for inactive user
                 detail="Inactive user.",
             )

        set_user(user) # Set context for logging
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        logger.info(f"Login successful, token generated", extra={ "username": user.username, "ip": client_host, "token_expires_in_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES})

        # Return user details along with token using the UserResponseSchema
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponseSchema.model_validate(user) # Validate and structure user data
        }

    except HTTPException as http_exc:
        # Avoid logging expected 401/400 errors as exceptions unless debugging needed
        if http_exc.status_code not in [status.HTTP_401_UNAUTHORIZED, status.HTTP_400_BAD_REQUEST]:
             logger.error(f"HTTP exception during login", exc_info=True)
        raise # Re-raise the exception
    except Exception as e:
        logger.error(f"Unexpected login error", exc_info=True, extra={"error": str(e), "username": form_data.username})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during the login process."
        )


# --- Job Related API Endpoints ---

@app.post("/api/v1/upload", response_model=Dict[str, Any])
async def upload_file(
    file: UploadFile = File(...),
    company_name: str = Form(...),
    current_user: User = Depends(get_current_user), # Use get_current_user for basic auth check
    db = Depends(get_db)
):
    """Handles file upload and initiates the classification job."""
    job_id = str(uuid.uuid4())
    set_correlation_id(job_id); set_job_id(job_id)
    if current_user: set_user(current_user)
    logger.info(f"===> Entered upload_file endpoint", extra={ "company_name": company_name, "uploaded_filename": file.filename, "content_type": file.content_type, "file_size": getattr(file, 'size', 'unknown'), "username": current_user.username if current_user else "unknown" })

    if not file.filename: raise HTTPException(status_code=400, detail="File must have a filename.")
    if not file.filename.lower().endswith(('.xlsx', '.xls')): raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")
    if not company_name or not company_name.strip(): raise HTTPException(status_code=400, detail="Company name cannot be empty.")

    job = None
    try:
        input_file_path = save_upload_file(file, job_id)
        logger.info(f"File saved successfully", extra={"filepath": input_file_path})

        logger.info("Creating Job record in database...")
        job = Job( id=job_id, company_name=company_name, input_file_name=file.filename, status=JobStatus.PENDING, current_stage=ProcessingStage.INGESTION, created_by=current_user.username )
        db.add(job); db.commit()
        logger.info(f"Job created successfully in database", extra={"company": company_name, "status": JobStatus.PENDING})

        logger.info(f"Attempting to send task to Celery", extra={"input_file_path": input_file_path})
        try:
            task_name = 'tasks.classification_tasks.process_vendor_file'
            celery_app.send_task(task_name, args=[job_id, input_file_path])
            logger.info("Celery task sent successfully", extra={"task_name": task_name})
        except Exception as task_error:
             logger.error("Failed to send Celery task!", exc_info=True)
             if job: job.fail(f"Failed to queue processing task: {str(task_error)}"); db.commit()
             else: logger.error("Job object was None when trying to mark as failed due to Celery task send error.")
             raise HTTPException(status_code=500, detail=f"Error scheduling processing task: {str(task_error)}")

        logger.info(f"File uploaded successfully, processing scheduled via Celery")
        return { "job_id": job_id, "status": job.status, "current_stage": job.current_stage, "progress": job.progress, "created_at": job.created_at.isoformat() if job.created_at else None, "message": f"File '{file.filename}' uploaded. Processing started." }

    except HTTPException as http_exc:
        logger.warning(f"HTTP exception during upload", extra={"status_code": http_exc.status_code, "detail": http_exc.detail})
        raise http_exc
    except IOError as io_err:
        logger.error(f"File saving error during upload", exc_info=True, extra={"error": str(io_err)})
        error_db = None
        try:
            error_db = SessionLocal()
            job_in_error = error_db.query(Job).filter(Job.id == job_id).first()
            if job_in_error and job_in_error.status != JobStatus.FAILED.value:
                 job_in_error.fail(f"Upload endpoint failed (file save): {str(io_err)}"); error_db.commit()
                 logger.info("Upload IOError: Marked job as failed due to file save error.")
            elif not job_in_error: logger.error("Upload IOError: Could not find job to mark as failed during file save error handling.")
        except Exception as db_err:
             logger.error("Upload IOError: Error updating job status during file save error handling", exc_info=True, extra={"db_error": str(db_err)})
             if error_db: error_db.rollback()
        finally:
             if error_db: error_db.close()
        raise HTTPException(status_code=500, detail=f"Could not save uploaded file: {str(io_err)}")
    except Exception as e:
        logger.error(f"Unexpected error processing upload", exc_info=True, extra={"error": str(e)})
        error_db_unexpected = None
        try:
            error_db_unexpected = SessionLocal()
            job_in_error = error_db_unexpected.query(Job).filter(Job.id == job_id).first()
            if job_in_error and job_in_error.status != JobStatus.FAILED.value:
                job_in_error.fail(f"Upload endpoint failed (unexpected): {str(e)}"); error_db_unexpected.commit()
                logger.info("Upload Unexpected Error: Marked job as failed due to upload error.")
            elif not job_in_error: logger.error("Upload Unexpected Error: Could not find job to mark as failed during upload error handling.")
        except Exception as db_err_unexpected:
             logger.error("Upload Unexpected Error: Error updating job status during unexpected error handling", exc_info=True, extra={"db_error": str(db_err_unexpected)})
             if error_db_unexpected: error_db_unexpected.rollback()
        finally:
             if error_db_unexpected: error_db_unexpected.close()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during upload.")


@app.get("/api/v1/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str, current_user: User = Depends(get_current_user), db = Depends(get_db)):
    """Get status and details for a specific job."""
    set_correlation_id(job_id); set_job_id(job_id)
    if current_user: set_user(current_user)
    logger.info(f"Job status requested", extra={"username": current_user.username if current_user else "unknown"})
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job: raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")

    # Check ownership or admin status
    if job.created_by != current_user.username and not current_user.is_superuser:
        logger.warning("User attempted to access job they do not own", extra={"job_owner": job.created_by})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this job")

    logger.info(f"Job status retrieved", extra={ "status": job.status, "progress": job.progress, "stage": job.current_stage})
    response_data = JobResponse.model_validate(job) # Pydantic v2
    return response_data


@app.get("/api/v1/jobs/{job_id}/download")
async def download_results(job_id: str, current_user: User = Depends(get_current_user), db = Depends(get_db)):
    """Download the results file for a completed job."""
    set_correlation_id(job_id); set_job_id(job_id)
    if current_user: set_user(current_user)
    logger.info(f"Results download requested", extra={"username": current_user.username if current_user else "unknown"})
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job: raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")

    # Check ownership or admin status
    if job.created_by != current_user.username and not current_user.is_superuser:
        logger.warning("User attempted to download results for job they do not own", extra={"job_owner": job.created_by})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to download results for this job")

    if job.status == JobStatus.FAILED.value: raise HTTPException(status_code=400, detail=f"Job failed: {job.error_message}")
    if job.status != JobStatus.COMPLETED.value: raise HTTPException(status_code=400, detail="Job processing has not completed yet")
    if not job.output_file_name: raise HTTPException(status_code=404, detail="Output file name not recorded for this job.")

    output_path = os.path.join(settings.OUTPUT_DATA_DIR, job_id, job.output_file_name)
    if not os.path.exists(output_path): raise HTTPException(status_code=404, detail="Output file not found on server.")

    logger.info(f"Serving result file", extra={"output_filename": job.output_file_name, "path": output_path})
    base_name = "results";
    if job.input_file_name: base_name, _ = os.path.splitext(job.input_file_name)
    download_filename = f"{base_name}_results.xlsx"
    from fastapi.responses import FileResponse
    return FileResponse( output_path, filename=download_filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename=\"{download_filename}\""} )


@app.post("/api/v1/jobs/{job_id}/notify", response_model=Dict[str, Any])
async def request_notification(job_id: str, email_payload: Dict[str, str], current_user: User = Depends(get_current_user), db = Depends(get_db)):
    """Request email notification upon job completion."""
    set_correlation_id(job_id); set_job_id(job_id)
    if current_user: set_user(current_user)
    email = email_payload.get("email")
    if not email: raise HTTPException(status_code=400, detail="Email address is required in the request body.")
    logger.info(f"Notification requested", extra={"username": current_user.username if current_user else "unknown", "email": email})
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job: raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")

    # Check ownership or admin status
    if job.created_by != current_user.username and not current_user.is_superuser:
        logger.warning("User attempted to set notification for job they do not own", extra={"job_owner": job.created_by})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to set notification for this job")

    if "@" not in email or "." not in email.split('@')[-1]: raise HTTPException(status_code=400, detail="Invalid email address format provided.")
    job.notification_email = email
    try:
        db.commit(); logger.info(f"Notification email set successfully", extra={"email": email})
        return { "success": True, "message": f"Notification will be sent to {email} when job completes" }
    except Exception as e:
        db.rollback(); logger.error("Failed to save notification email to database", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update notification preferences.")


@app.get("/api/v1/jobs/{job_id}/stats", response_model=Dict[str, Any])
async def get_job_stats(job_id: str, current_user: User = Depends(get_current_user), db = Depends(get_db)):
    """Get processing statistics for a specific job."""
    set_correlation_id(job_id); set_job_id(job_id)
    if current_user: set_user(current_user)
    logger.info(f"Job stats requested", extra={"username": current_user.username if current_user else "unknown"})
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job: raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")

    # Check ownership or admin status
    if job.created_by != current_user.username and not current_user.is_superuser:
        logger.warning("User attempted to get stats for job they do not own", extra={"job_owner": job.created_by})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access stats for this job")

    if not isinstance(job.stats, dict):
         logger.warning(f"Job stats data is not a dictionary or is missing", extra={"stats_type": type(job.stats)})
         return { "vendors_processed": 0, "unique_vendors": 0, "api_calls": 0, "tokens_used": 0, "tavily_searches": 0, "processing_time": 0, "invalid_category_errors": 0, "successfully_classified_l4": 0, "search_successful_classifications": 0 }
    logger.info(f"Job stats retrieved")
    job_stats = job.stats; api_usage = job_stats.get("api_usage", {})
    return { "vendors_processed": job_stats.get("total_vendors", 0), "unique_vendors": job_stats.get("unique_vendors", 0), "api_calls": api_usage.get("openrouter_calls", 0), "tokens_used": api_usage.get("openrouter_total_tokens", 0), "tavily_searches": api_usage.get("tavily_search_calls", 0), "processing_time": job_stats.get("processing_duration_seconds", 0), "invalid_category_errors": job_stats.get("invalid_category_errors", 0), "successfully_classified_l4": job_stats.get("successfully_classified_l4", 0), "search_successful_classifications": job_stats.get("search_successful_classifications", 0) }


# --- Include Routers ---
# Include Job History Router (requires authentication)
app.include_router(
    jobs_router.router,
    prefix=settings.API_V1_STR + "/jobs",
    tags=["Job History"], # Changed tag for clarity
    dependencies=[Depends(get_current_user)] # Apply auth dependency
)

# Include User Management Router (authentication handled within endpoints)
app.include_router(
    users_router.router,
    prefix=settings.API_V1_STR + "/users",
    tags=["User Management"], # Changed tag for clarity
    # Dependencies are applied per-endpoint in users.py
)
# --- End Include Routers ---


# --- Startup Event ---
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    global setup_logging_done
    if setup_logging_done:
        startup_logger.info("Startup event triggered again, skipping full setup.")
        return
    log_dir = "/data/logs" if os.path.exists("/data") else "./logs"
    try:
        os.makedirs(log_dir, exist_ok=True)
        startup_logger.info(f"Log directory ensured: {log_dir}")
    except OSError as e:
        startup_logger.error(f"ERROR: Could not create logging directory {log_dir}: {e}. Logging to file may fail.")
        log_dir = "./logs"
        try: os.makedirs(log_dir, exist_ok=True)
        except OSError as e2: startup_logger.error(f"ERROR: Could not create fallback logging directory {log_dir}: {e2}. Disabling file logging."); log_dir = None

    setup_logging( log_level=None, log_to_file=bool(log_dir), log_dir=log_dir, async_logging=True, llm_trace_log_file="llm_api_trace.log" )
    setup_logging_done = True
    logger.info("*********************************************")
    logger.info("          Application starting up...         ")
    logger.info("*********************************************")

    try:
        os.makedirs(settings.INPUT_DATA_DIR, exist_ok=True)
        os.makedirs(settings.OUTPUT_DATA_DIR, exist_ok=True)
        os.makedirs(settings.TAXONOMY_DATA_DIR, exist_ok=True)
        logger.info("Ensured input, output, and taxonomy data directories exist.")
    except OSError as e: logger.error(f"Failed to create one or more data directories: {e}")

    try:
        logger.info("Initializing database...")
        initialize_database()
        logger.info("Database initialization completed.")
    except Exception as e:
        logger.critical(f"CRITICAL: Error initializing database during startup.", exc_info=True, extra={"error_details": str(e)})

    try:
        logger.info("Pre-loading taxonomy into cache...")
        load_taxonomy(force_reload=True)
        logger.info("Taxonomy pre-loading completed.")
    except Exception as e:
        logger.error("Failed to pre-load taxonomy during startup.", exc_info=True)


# --- Mount Static Files (Vue App) ---
# This should be the LAST app configuration step
if os.path.exists(VUE_BUILD_DIR) and os.path.exists(VUE_INDEX_FILE):
    logger.info(f"Mounting Vue app from directory: {VUE_BUILD_DIR}")
    app.mount("/", StaticFiles(directory=VUE_BUILD_DIR, html=True), name="app")
else:
    logger.error(f"Cannot mount Vue app: Directory {VUE_BUILD_DIR} or index file {VUE_INDEX_FILE} not found.")
    # Add a fallback route to show an error if the frontend isn't mounted
    @app.get("/")
    async def missing_frontend():
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": f"Frontend not found. Expected build files in {VUE_BUILD_DIR}"}
        )
# --- END VUE.JS FRONTEND SERVING SETUP ---