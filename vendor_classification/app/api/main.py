
# <file path='app/api/main.py'>
# app/api/main.py
import socket
import sqlalchemy
import httpx
from fastapi import (
    FastAPI, Depends, HTTPException, UploadFile, File, Form,
    BackgroundTasks, status, Request
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel # Added for response model
from typing import Dict, Any, Optional, List
import uuid
import os
from datetime import datetime, timedelta
import logging
import time
from sqlalchemy.orm import Session

# --- Model Imports ---
from models.job import Job, JobStatus, ProcessingStage
from models.user import User

# --- Core Imports ---
from core.config import settings
# Import logger and context functions from refactored modules
from core.logging_config import setup_logging, get_logger
from core.log_context import set_correlation_id, set_user, set_job_id, get_correlation_id
# Import middleware (which now uses updated context functions)
from middleware.logging_middleware import RequestLoggingMiddleware
from core.database import get_db, SessionLocal, engine
from core.initialize_db import initialize_database

# --- Service Imports ---
# --- UPDATED: Import validate_file_header ---
from services.file_service import save_upload_file, validate_file_header
# --- END UPDATED ---

# --- Task Imports ---
from tasks.celery_app import celery_app
from tasks.classification_tasks import process_vendor_file

# --- Utility Imports ---
from utils.taxonomy_loader import load_taxonomy

# --- Auth Imports ---
from fastapi.security import OAuth2PasswordRequestForm
from api.auth import (
    get_current_user,
    authenticate_user,
    create_access_token,
    get_current_active_user
)

# --- Router Imports ---
from api import jobs as jobs_router
from api import users as users_router

# --- Schema Imports ---
from schemas.job import JobResponse
from schemas.user import UserResponse as UserResponseSchema

# --- Logging Setup ---
# Initialize logging BEFORE creating the FastAPI app instance
# This ensures loggers are ready when middleware/routers are attached
setup_logging(log_level=logging.DEBUG, log_to_file=True, log_dir=settings.TAXONOMY_DATA_DIR.replace('taxonomy', 'logs')) # Use settings for log dir
logger = get_logger("vendor_classification.api")

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
    allow_origins=["*"], # Allow all origins for now, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include Routers ---
logger.info("Including API routers...")
app.include_router(
    jobs_router.router,
    prefix="/api/v1/jobs",
    tags=["Jobs"],
    dependencies=[Depends(get_current_user)]
)
logger.info("Included jobs router with prefix /api/v1/jobs")

app.include_router(
    users_router.router,
    prefix="/api/v1/users",
    tags=["Users"],
)
logger.info("Included users router with prefix /api/v1/users")
# --- End Include Routers ---

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
                # Check if settings attributes exist before using them
                or_url = f"{settings.OPENROUTER_API_BASE}/models" if hasattr(settings, 'OPENROUTER_API_BASE') else None
                or_headers = {"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"} if hasattr(settings, 'OPENROUTER_API_KEY') else None
                if or_url and or_headers:
                    or_resp = await client.get(or_url, headers=or_headers)
                    openrouter_status = "connected" if or_resp.status_code == 200 else f"error: {or_resp.status_code}"
                else:
                    openrouter_status = "config_missing"
                    logger.warning("OpenRouter API base or key missing in settings for health check.")


                tv_url = "https://api.tavily.com/search"
                tv_payload = {"api_key": settings.TAVILY_API_KEY, "query": "test", "max_results": 1} if hasattr(settings, 'TAVILY_API_KEY') else None
                if tv_payload:
                    tv_resp = await client.post(tv_url, json=tv_payload)
                    tavily_status = "connected" if tv_resp.status_code == 200 else f"error: {tv_resp.status_code}"
                else:
                    tavily_status = "config_missing"
                    logger.warning("Tavily API key missing in settings for health check.")


    except httpx.RequestError as http_err:
            logger.warning(f"HTTPX RequestError during external API health check: {http_err}")
            openrouter_status = openrouter_status if openrouter_status != "unknown" else "connection_error"
            tavily_status = tavily_status if tavily_status != "unknown" else "connection_error"
    except Exception as api_err:
            logger.error(f"Error checking external APIs during health check: {api_err}", exc_info=True) # Log full traceback
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
@app.post("/token", response_model=Dict[str, Any])
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
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

        if not user.is_active:
                logger.warning(f"Login failed: user '{user.username}' is inactive.", extra={"ip": client_host})
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Inactive user.",
                )

        set_user(user) # Set context for logging
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        logger.info(f"Login successful, token generated", extra={ "username": user.username, "ip": client_host, "token_expires_in_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponseSchema.model_validate(user)
        }

    except HTTPException as http_exc:
        if http_exc.status_code not in [status.HTTP_401_UNAUTHORIZED, status.HTTP_400_BAD_REQUEST]:
                logger.error(f"HTTP exception during login", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected login error", exc_info=True, extra={"error": str(e), "username": form_data.username})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during the login process."
        )

# --- ADDED: File Validation Endpoint ---
class FileValidationResponse(BaseModel):
    is_valid: bool
    message: str
    detected_columns: List[str] = []
    missing_mandatory_columns: List[str] = []

@app.post("/api/v1/validate-upload", response_model=FileValidationResponse, status_code=status.HTTP_200_OK)
async def validate_uploaded_file_header(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user) # Ensure user is logged in
):
    """
    Quickly validates the header of an uploaded Excel file.
    Checks for the mandatory 'vendor_name' column (case-insensitive).
    Returns validation status and detected columns.
    """
    set_user(current_user) # Set context for logging
    validation_uuid = str(uuid.uuid4())[:8] # Short ID for this validation attempt

    log_extra = {
        "validation_id": validation_uuid,
        "uploaded_filename": file.filename, # Renamed from 'filename'
        "username": current_user.username
    }
    logger.info("File validation request received", extra=log_extra)

    if not file.filename:
        logger.warning("Validation attempt with no filename.", extra=log_extra)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided.")
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        logger.warning(f"Invalid file type for validation: {file.filename}", extra=log_extra)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Please upload an Excel file (.xlsx or .xls).")

    try:
        validation_result = validate_file_header(file)

        # --- FIX: Avoid merging 'message' key into log extra ---
        # Create a log-safe version of the validation result by renaming the 'message' key
        log_safe_validation_result = {
            "validation_is_valid": validation_result.get("is_valid"),
            "validation_message": validation_result.get("message"), # Rename 'message' key for logging
            "validation_detected_columns": validation_result.get("detected_columns"),
            "validation_missing_columns": validation_result.get("missing_mandatory_columns")
        }
        # Merge the base log_extra with the log-safe validation results
        current_log_extra = {**log_extra, **log_safe_validation_result}
        # --- END FIX ---

        # Now log using the safe dictionary that doesn't have a 'message' key
        logger.info(f"File header validation completed", extra=current_log_extra)

        status_code = status.HTTP_200_OK
        if not validation_result["is_valid"]:
            # You could use 422 here, but 200 is also fine as the *request* was processed,
            # and the validation *result* indicates failure. Let's stick with 200 for simplicity
            # and let the frontend interpret the `is_valid` flag.
            # status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            pass

        return JSONResponse(
            status_code=status_code,
            content=validation_result # Return the original validation_result to the frontend
        )

    except ValueError as ve:
        logger.warning(f"Validation failed due to parsing error: {ve}", extra=log_extra)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        # Log the error with the original log_extra, avoiding the problematic merge
        logger.error(f"Unexpected error during file header validation", exc_info=True, extra=log_extra)
        # Return a 500 error to the frontend
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error validating file: {e}")
    finally:
        # Ensure the file stream is closed, even though we only read the header
        if hasattr(file, 'close') and callable(file.close):
            try:
                # For async UploadFile, use await file.close() if needed
                # For standard sync SpooledTemporaryFile, just call close()
                 file.close()
            except Exception:
                logger.warning("Error closing file stream after validation", extra=log_extra, exc_info=False)
# --- END ADDED: File Validation Endpoint ---


# --- UPLOAD ROUTE (No changes needed here for validation, but keep previous updates) ---
@app.post("/api/v1/upload", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_vendor_file(
    background_tasks: BackgroundTasks,
    company_name: str = Form(...),
    target_level: int = Form(..., ge=1, le=5, description="Target classification level (1-5)"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Accepts vendor file upload, creates a job, and queues it for processing.
    Allows specifying the target classification level.
    **Assumes frontend performs pre-validation using /validate-upload.**
    """
    job_id = str(uuid.uuid4())
    set_job_id(job_id)
    set_user(current_user)

    logger.info(f"Upload request received", extra={
        "job_id": job_id,
        "company_name": company_name,
        "target_level": target_level,
        "uploaded_filename": file.filename, # Use consistent naming
        "content_type": file.content_type,
        "username": current_user.username
    })

    # Basic checks still useful as a fallback, though frontend should prevent this
    if not file.filename:
        logger.warning("Upload attempt with no filename.", extra={"job_id": job_id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided.")
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        logger.warning(f"Invalid file type uploaded: {file.filename}", extra={"job_id": job_id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Please upload an Excel file (.xlsx or .xls).")

    # --- Pre-validation Check (Optional but recommended server-side redundancy) ---
    # You *could* re-run the validation here before saving, but it adds overhead.
    # Relying on the frontend pre-validation is the primary goal.
    # try:
    #     # Need to reset stream position if reading again
    #     await file.seek(0)
    #     validation_result = validate_file_header(file)
    #     if not validation_result["is_valid"]:
    #         logger.warning(f"Server-side validation failed for upload job {job_id}", extra=validation_result)
    #         raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=validation_result["message"])
    #     # Reset stream position again for saving
    #     await file.seek(0)
    # except Exception as e:
    #      logger.error(f"Error during server-side pre-validation for job {job_id}", exc_info=True)
    #      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed during server-side file pre-check.")
    # --- End Pre-validation Check ---


    saved_file_path = None
    try:
        logger.debug(f"Attempting to save uploaded file for job {job_id}")
        saved_file_path = save_upload_file(file=file, job_id=job_id) # file object might be used here
        logger.info(f"File saved successfully for job {job_id}", extra={"saved_path": saved_file_path})
    except IOError as e:
        logger.error(f"Failed to save uploaded file for job {job_id}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save file: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during file upload/saving for job {job_id}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing upload: {e}")
    # finally: # file is closed by save_upload_file now
    #     if hasattr(file, 'close') and callable(file.close):
    #         file.close()

    job = None
    try:
        logger.debug(f"Creating database job record for job {job_id}")
        job = Job(
            id=job_id,
            company_name=company_name,
            input_file_name=os.path.basename(saved_file_path),
            status=JobStatus.PENDING.value,
            current_stage=ProcessingStage.INGESTION.value,
            created_by=current_user.username,
            target_level=target_level # Save the target level
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        logger.info(f"Database job record created successfully for job {job_id}", extra={"target_level": job.target_level})
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create database job record for job {job_id}", exc_info=True)
        if saved_file_path and os.path.exists(saved_file_path):
            try: os.remove(saved_file_path)
            except OSError: logger.warning(f"Could not remove file {saved_file_path} after DB error.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create job record.")

    try:
        logger.info(f"Adding Celery task 'process_vendor_file' to background tasks for job {job_id}")
        background_tasks.add_task(process_vendor_file.delay, job_id=job_id, file_path=saved_file_path, target_level=target_level)
        logger.info(f"Celery task queued successfully for job {job_id}")
    except Exception as e:
        logger.error(f"Failed to queue Celery task for job {job_id}", exc_info=True)
        if job:
            job.fail(f"Failed to queue processing task: {str(e)}")
            db.commit()
        else:
             logger.error(f"Job object was None when trying to mark as failed due to Celery queue error.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to queue job for processing.")

    logger.info(f"Upload request for job {job_id} processed successfully, returning 202 Accepted.")
    return JobResponse.model_validate(job)
# --- END UPLOAD ROUTE ---


# --- Mount Static Files (Vue App) ---
if os.path.exists(VUE_BUILD_DIR) and os.path.exists(VUE_INDEX_FILE):
    logger.info(f"Mounting Vue app from directory: {VUE_BUILD_DIR}")
    app.mount("/", StaticFiles(directory=VUE_BUILD_DIR, html=True), name="app")
else:
    logger.error(f"Cannot mount Vue app: Directory {VUE_BUILD_DIR} or index file {VUE_INDEX_FILE} not found.")
    @app.get("/")
    async def missing_frontend():
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": f"Frontend not found. Expected build files in {VUE_BUILD_DIR}"}
        )
# --- END VUE.JS FRONTEND SERVING SETUP ---
