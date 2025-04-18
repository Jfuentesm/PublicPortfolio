# app/api/main.py
from fastapi import (
    FastAPI, Depends, HTTPException, UploadFile, File, Form,
    BackgroundTasks, status, Request
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uuid
import os
import logging
import time
from sqlalchemy.orm import Session

# --- Core Imports ---
from core.logging_config import setup_logging, get_logger
from core.log_context import set_correlation_id, set_user, set_job_id, get_correlation_id
from middleware.logging_middleware import RequestLoggingMiddleware
from core.database import get_db, SessionLocal
from core.initialize_db import initialize_database

# --- Model Imports ---
from models.job import Job, JobStatus, ProcessingStage # Keep top-level imports
from models.user import User

# --- Service Imports ---
from services.file_service import save_upload_file, validate_file_header

# --- Task Imports ---
from tasks.classification_tasks import process_vendor_file # Keep this specific import

# --- Utility Imports ---
from utils.taxonomy_loader import load_taxonomy

# --- Auth Imports ---
from fastapi.security import OAuth2PasswordRequestForm
from api.auth import (
    get_current_user,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_current_active_superuser
)

# --- Router Imports ---
from api import jobs as jobs_router
from api import users as users_router
from api import password_reset as password_reset_router
from api import admin as admin_router
from api.health_utils import health_check

# --- Schema Imports ---
from schemas.job import JobResponse
from schemas.user import UserResponse as UserResponseSchema
from core.config import settings

# --- Logging Setup ---
setup_logging(log_level=logging.DEBUG, log_to_file=True, log_dir=settings.TAXONOMY_DATA_DIR.replace('taxonomy', 'logs'))
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
    allow_origins=[settings.FRONTEND_URL, "http://localhost:8080", "http://127.0.0.1:8080", f"http://localhost:{settings.FRONTEND_URL.split(':')[-1]}"],
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

app.include_router(
    password_reset_router.router,
    prefix="/api/v1/auth",
    tags=["Password Reset"],
)
logger.info("Included password reset router with prefix /api/v1/auth")

app.include_router(
    admin_router.router,
    prefix="/api/v1/admin",
    tags=["Admin"],
    dependencies=[Depends(get_current_active_superuser)]
)
logger.info("Included admin router with prefix /api/v1/admin (superuser required)")
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

@app.get("/health", tags=["Health"])
async def get_health_status():
    """Provides the system health status."""
    return await health_check()


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
    log_level = logging.ERROR if exc.status_code >= 500 else logging.WARNING
    logger.log(log_level, f"HTTP Exception: {exc.status_code} - {exc.detail}", extra={
        "correlation_id": correlation_id,
        "request_headers": dict(request.headers),
        "path": request.url.path,
        "method": request.method,
        "status_code": exc.status_code,
        "detail": exc.detail,
    }, exc_info=(exc.status_code >= 500))

    # --- FIX: Robust header handling ---
    exc_headers = getattr(exc, "headers", None) # Get actual headers or None
    headers = exc_headers if isinstance(exc_headers, dict) else {} # Ensure headers is a dict
    headers["X-Correlation-ID"] = correlation_id # Now this should be safe
    # --- END FIX ---

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers, # Pass the modified dict
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

        set_user(user)
        access_token = create_access_token(subject=user.username)

        logger.info(f"Login successful, token generated", extra={ "username": user.username, "ip": client_host, "token_expires_in_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponseSchema.model_validate(user)
        }

    except HTTPException as http_exc:
        # Log unexpected HTTP exceptions, but re-raise all HTTP exceptions
        if http_exc.status_code not in [status.HTTP_401_UNAUTHORIZED, status.HTTP_400_BAD_REQUEST]:
                logger.error(f"Unexpected HTTP exception during login for {form_data.username}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected login error", exc_info=True, extra={"error": str(e), "username": form_data.username})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during the login process."
        )

# --- File Validation Endpoint ---
class FileValidationResponse(BaseModel):
    is_valid: bool
    message: str
    detected_columns: List[str] = []
    missing_mandatory_columns: List[str] = []

@app.post("/api/v1/validate-upload", response_model=FileValidationResponse, status_code=status.HTTP_200_OK, tags=["File Operations"])
async def validate_uploaded_file_header(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Quickly validates the header of an uploaded Excel file.
    Checks for the mandatory 'vendor_name' column (case-insensitive).
    Returns validation status and detected columns.
    """
    set_user(current_user)
    validation_uuid = str(uuid.uuid4())[:8]

    log_extra = {
        "validation_id": validation_uuid,
        "uploaded_filename": file.filename,
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

        log_safe_validation_result = {
            "validation_is_valid": validation_result.get("is_valid"),
            "validation_message": validation_result.get("message"),
            "validation_detected_columns": validation_result.get("detected_columns"),
            "validation_missing_columns": validation_result.get("missing_mandatory_columns")
        }
        current_log_extra = {**log_extra, **log_safe_validation_result}
        logger.info(f"File header validation completed", extra=current_log_extra)

        status_code = status.HTTP_200_OK
        # No need to change status code based on validation result

        return JSONResponse(
            status_code=status_code,
            content=validation_result
        )

    except ValueError as ve:
        logger.warning(f"Validation failed due to parsing error: {ve}", extra=log_extra)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error during file header validation", exc_info=True, extra=log_extra)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error validating file: {e}")
    finally:
        # Ensure file is closed even if validation fails early
        if hasattr(file, 'close') and callable(file.close):
            try:
                 file.close()
            except Exception:
                logger.warning("Error closing file stream after validation", extra=log_extra, exc_info=False)


# --- UPLOAD ROUTE ---
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
        "uploaded_filename": file.filename,
        "content_type": file.content_type,
        "username": current_user.username
    })

    if not file.filename:
        logger.warning("Upload attempt with no filename.", extra={"job_id": job_id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided.")
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        logger.warning(f"Invalid file type uploaded: {file.filename}", extra={"job_id": job_id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Please upload an Excel file (.xlsx or .xls).")

    saved_file_path = None
    try:
        logger.debug(f"Attempting to save uploaded file for job {job_id}")
        saved_file_path = save_upload_file(file=file, job_id=job_id)
        logger.info(f"File saved successfully for job {job_id}", extra={"saved_path": saved_file_path})
    except IOError as e:
        logger.error(f"Failed to save uploaded file for job {job_id}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save file: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during file upload/saving for job {job_id}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing upload: {e}")

    job = None
    try:
        logger.debug(f"Creating database job record for job {job_id}")
        # --- FIX: Explicitly import JobStatus and ProcessingStage here ---
        from models.job import Job, JobStatus, ProcessingStage
        # --- END FIX ---
        job = Job(
            id=job_id,
            company_name=company_name,
            input_file_name=os.path.basename(saved_file_path),
            status=JobStatus.PENDING.value,
            current_stage=ProcessingStage.INGESTION.value,
            created_by=current_user.username,
            target_level=target_level
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
        # process_vendor_file is already imported at the top level
        background_tasks.add_task(process_vendor_file.delay, job_id=job_id, file_path=saved_file_path, target_level=target_level)
        logger.info(f"Celery task queued successfully for job {job_id}")
    except Exception as e:
        logger.error(f"Failed to queue Celery task for job {job_id}", exc_info=True)
        if job:
            # Need to import JobStatus if not already available locally (it is now due to the fix above)
            job.status = JobStatus.FAILED.value # Manually update status if fail method isn't easily usable
            job.error_message = f"Failed to queue processing task: {str(e)}"
            db.commit()
        else:
             logger.error(f"Job object was None when trying to mark as failed due to Celery queue error.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to queue job for processing.")

    logger.info(f"Upload request for job {job_id} processed successfully, returning 202 Accepted.")
    return JobResponse.model_validate(job)


# --- Mount Static Files (Vue App) ---
if os.path.exists(VUE_BUILD_DIR) and os.path.exists(VUE_INDEX_FILE):
    logger.info(f"Mounting Vue app from directory: {VUE_BUILD_DIR}")
    app.mount("/assets", StaticFiles(directory=os.path.join(VUE_BUILD_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_vue_app(request: Request, full_path: str):
        potential_file_path = os.path.join(VUE_BUILD_DIR, full_path.lstrip('/'))
        # Prevent serving API routes via the static file server
        if full_path.startswith("api/") or full_path.startswith("/api/"):
             logger.warning(f"Request for API path '{full_path}' reached static file fallback. Letting FastAPI handle.")
             # Let FastAPI handle 404s for actual API routes
             return None

        if os.path.isfile(potential_file_path) and os.path.basename(potential_file_path) != 'index.html':
             logger.debug(f"Serving static file directly: {full_path}")
             return FileResponse(potential_file_path)
        else:
            logger.debug(f"Serving index.html for SPA route or missing file: {full_path}")
            if os.path.exists(VUE_INDEX_FILE):
                return FileResponse(VUE_INDEX_FILE)
            else:
                logger.error(f"Vue index.html not found at {VUE_INDEX_FILE} when trying to serve fallback route.")
                return JSONResponse(status_code=500, content={"detail": "Frontend index file missing."})

else:
    logger.error(f"Cannot mount Vue app: Directory {VUE_BUILD_DIR} or index file {VUE_INDEX_FILE} not found.")
    @app.get("/", include_in_schema=False)
    async def missing_frontend():
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": f"Frontend not found. Expected build files in {VUE_BUILD_DIR}"}
        )
# --- END VUE.JS FRONTEND SERVING SETUP ---

# --- Initialize Database on Startup ---
@app.on_event("startup")
async def startup_event():
    logger.info("Application startup: Initializing database...")
    try:
        initialize_database()
        logger.info("Database initialization check complete.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
# --- END Initialize Database ---