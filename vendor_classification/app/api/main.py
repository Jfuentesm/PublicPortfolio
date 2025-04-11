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
from fastapi.responses import JSONResponse, FileResponse # Added FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel # Added for response model
from typing import Dict, Any, Optional, List
import uuid
import os
from datetime import datetime, timedelta, timezone # Added timezone
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
from api import password_reset as password_reset_router # ADDED: Password Reset Router

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
    # Allow specific origins in production
    allow_origins=[settings.FRONTEND_URL, "http://localhost:8080", "http://127.0.0.1:8080", f"http://localhost:{settings.FRONTEND_URL.split(':')[-1]}"], # Allow dev frontend dynamically
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
    dependencies=[Depends(get_current_user)] # Secure job routes
)
logger.info("Included jobs router with prefix /api/v1/jobs")

app.include_router(
    users_router.router,
    prefix="/api/v1/users",
    tags=["Users"],
    # Dependencies applied per-route in users.py
)
logger.info("Included users router with prefix /api/v1/users")

# --- ADDED: Include Password Reset Router ---
app.include_router(
    password_reset_router.router,
    prefix="/api/v1/auth", # Group under auth path
    tags=["Password Reset"],
    # No global dependency, endpoints handle auth/no auth as needed
)
logger.info("Included password reset router with prefix /api/v1/auth")
# --- END ADDED ---

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
                or_headers = {"Authorization": f"Bearer {settings.OPENROUTER_API_KEYS[0]}"} if hasattr(settings, 'OPENROUTER_API_KEYS') and settings.OPENROUTER_API_KEYS else None # Use first key for check
                if or_url and or_headers:
                    or_resp = await client.get(or_url, headers=or_headers)
                    openrouter_status = "connected" if or_resp.status_code == 200 else f"error: {or_resp.status_code}"
                else:
                    openrouter_status = "config_missing_or_empty"
                    logger.warning("OpenRouter API base or key missing/empty in settings for health check.")


                tv_url = "https://api.tavily.com/search"
                tv_payload = {"api_key": settings.TAVILY_API_KEYS[0], "query": "test", "max_results": 1} if hasattr(settings, 'TAVILY_API_KEYS') and settings.TAVILY_API_KEYS else None # Use first key for check
                if tv_payload:
                    tv_resp = await client.post(tv_url, json=tv_payload)
                    tavily_status = "connected" if tv_resp.status_code == 200 else f"error: {tv_resp.status_code}"
                else:
                    tavily_status = "config_missing_or_empty"
                    logger.warning("Tavily API key missing/empty in settings for health check.")


    except httpx.RequestError as http_err:
            logger.warning(f"HTTPX RequestError during external API health check: {http_err}")
            openrouter_status = openrouter_status if openrouter_status != "unknown" else "connection_error"
            tavily_status = tavily_status if tavily_status != "unknown" else "connection_error"
    except Exception as api_err:
            logger.error(f"Error checking external APIs during health check: {api_err}", exc_info=True) # Log full traceback
            openrouter_status = openrouter_status if openrouter_status != "unknown" else "check_error"
            tavily_status = tavily_status if tavily_status != "unknown" else "check_error"

    email_status = "configured" if settings.SMTP_HOST and settings.SMTP_USER and settings.EMAIL_FROM else "not_configured"

    return {
        "status": "healthy",
        "hostname": hostname,
        "ip": local_ip,
        "database": db_status,
        "celery_broker": celery_broker_status,
        "vue_frontend_index": vue_frontend_status,
        "email_service": email_status, # Added email status
        "external_api_openrouter": openrouter_status,
        "external_api_tavily": tavily_status,
        "timestamp": datetime.now(timezone.utc).isoformat() # Use timezone aware
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

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    correlation_id = get_correlation_id() or str(uuid.uuid4())
    # Log HTTP exceptions (like 401, 403, 404, 422 from manual raises)
    # Avoid logging stack traces for common HTTP errors unless it's a 500
    log_level = logging.ERROR if exc.status_code >= 500 else logging.WARNING
    logger.log(log_level, f"HTTP Exception: {exc.status_code} - {exc.detail}", extra={
        "correlation_id": correlation_id,
        "request_headers": dict(request.headers),
        "path": request.url.path,
        "method": request.method,
        "status_code": exc.status_code,
        "detail": exc.detail,
    }, exc_info=(exc.status_code >= 500)) # Include stack trace only for 5xx errors

    headers = getattr(exc, "headers", {})
    headers["X-Correlation-ID"] = correlation_id # Ensure correlation ID is in response

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers,
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
# Note: This is the endpoint for exchanging username/password for a token
@app.post("/token", response_model=Dict[str, Any], tags=["Authentication"])
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
        # Use the updated function, passing username (or user.id if preferred for subject)
        access_token = create_access_token(subject=user.username)

        logger.info(f"Login successful, token generated", extra={ "username": user.username, "ip": client_host, "token_expires_in_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES})

        # Return user details along with the token
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponseSchema.model_validate(user) # Use Pydantic v2 method
        }

    except HTTPException as http_exc:
        # Log only unexpected HTTP exceptions during login
        if http_exc.status_code not in [status.HTTP_401_UNAUTHORIZED, status.HTTP_400_BAD_REQUEST]:
                logger.error(f"Unexpected HTTP exception during login for {form_data.username}", exc_info=True)
        raise # Re-raise the exception to be handled by the exception handler
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

@app.post("/api/v1/validate-upload", response_model=FileValidationResponse, status_code=status.HTTP_200_OK, tags=["File Operations"])
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
@app.post("/api/v1/upload", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED, tags=["File Operations"])
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
    # Serve static files from 'assets', etc.
    app.mount("/assets", StaticFiles(directory=os.path.join(VUE_BUILD_DIR, "assets")), name="assets")

    # --- REMOVED FAVICONS MOUNT ---
    # Check if the favicons directory *actually* exists in the build output before mounting
    # favicons_dir_path = os.path.join(VUE_BUILD_DIR, "favicons")
    # if os.path.isdir(favicons_dir_path):
    #     logger.info(f"Mounting /favicons from {favicons_dir_path}")
    #     app.mount("/favicons", StaticFiles(directory=favicons_dir_path), name="favicons")
    # else:
    #     logger.warning(f"Directory {favicons_dir_path} not found. Skipping /favicons mount.")
    # --- END REMOVED FAVICONS MOUNT ---

    # Serve index.html for all other routes (SPA handling)
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_vue_app(request: Request, full_path: str):
        # Check if the path looks like a file request that wasn't caught by static mounts
        # This is a basic check, might need refinement
        potential_file_path = os.path.join(VUE_BUILD_DIR, full_path.lstrip('/'))

        # If it's not an API route and the path doesn't correspond to an existing file in dist
        # (other than index.html itself), serve index.html
        if not full_path.startswith("api"):
            if os.path.isfile(potential_file_path) and os.path.basename(potential_file_path) != 'index.html':
                 # It's likely a static file request that should be served directly
                 # (e.g., /favicon.ico if it exists in dist root)
                 logger.debug(f"Serving static file directly: {full_path}")
                 return FileResponse(potential_file_path)
            else:
                # Serve index.html for SPA routing or if file not found
                logger.debug(f"Serving index.html for SPA route or missing file: {full_path}")
                return FileResponse(VUE_INDEX_FILE)
        else:
            # This case should ideally be handled by FastAPI routing before getting here
            logger.error(f"Request starting with 'api' reached fallback route: {full_path}")
            return JSONResponse(status_code=404, content={"detail": "API route not found"})

else:
    logger.error(f"Cannot mount Vue app: Directory {VUE_BUILD_DIR} or index file {VUE_INDEX_FILE} not found.")
    @app.get("/", include_in_schema=False)
    async def missing_frontend():
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": f"Frontend not found. Expected build files in {VUE_BUILD_DIR}"}
        )
# --- END VUE.JS FRONTEND SERVING SETUP ---

# --- Initialize Database on Startup (Optional) ---
@app.on_event("startup")
async def startup_event():
    logger.info("Application startup: Initializing database...")
    try:
        initialize_database()
        logger.info("Database initialization check complete.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        # Depending on severity, you might want to prevent startup

# --- END Initialize Database ---

#</file>