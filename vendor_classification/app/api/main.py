# --- file path='app/api/main.py' ---
# app/api/main.py
import socket
import sqlalchemy
import httpx
from fastapi import ( # Ensure all necessary imports are present
    FastAPI, Depends, HTTPException, UploadFile, File, Form,
    BackgroundTasks, status, Request
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from typing import Dict, Any, Optional, List
import uuid
import os
from datetime import datetime, timedelta
import logging
import time # Added for sleep
# --- ADDED: Import Session ---
from sqlalchemy.orm import Session
# --- END ADDED ---

# --- Model Imports ---
from models.job import Job, JobStatus, ProcessingStage # Import Job and enums
from models.user import User

# --- Core Imports ---
from core.config import settings
from core.logging_config import setup_logging, get_logger, set_correlation_id, set_user, set_job_id, log_function_call, get_correlation_id
from middleware.logging_middleware import RequestLoggingMiddleware
from core.database import get_db, SessionLocal, engine # Import engine
from core.initialize_db import initialize_database # Keep for potential direct call if needed

# --- Service Imports ---
from services.file_service import save_upload_file # Import file saving service

# --- Task Imports ---
from tasks.celery_app import celery_app
from tasks.classification_tasks import process_vendor_file # Import the Celery task

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
from api import jobs as jobs_router        # <--- IMPORTED jobs_router
from api import users as users_router      # <--- IMPORTED users_router

# --- Schema Imports ---
from schemas.job import JobResponse # Import JobResponse schema for upload return
from schemas.user import UserResponse as UserResponseSchema # Import UserResponse schema


# --- Logging Setup ---
# Setup logging early (assuming it's called elsewhere or handled by Docker entrypoint)
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

# --- Include Routers ---
logger.info("Including API routers...")
app.include_router(
    jobs_router.router,
    prefix="/api/v1/jobs", # <--- PREFIX for job routes
    tags=["Jobs"],         # <--- Tag for Swagger UI
    dependencies=[Depends(get_current_user)] # <--- Add auth dependency to all job routes
)
logger.info("Included jobs router with prefix /api/v1/jobs")

app.include_router(
    users_router.router,
    prefix="/api/v1/users", # <--- PREFIX for user routes
    tags=["Users"],         # <--- Tag for Swagger UI
    # Dependencies are handled within the user routes (e.g., get_current_active_superuser)
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
# Static files are mounted at the end of the file


# --- API ROUTES (Keep root routes like health, token directly under app) ---

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
    db: Session = Depends(get_db) # Use imported Session here
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

# --- UPLOAD ROUTE ---
@app.post("/api/v1/upload", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_vendor_file(
    background_tasks: BackgroundTasks,
    company_name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db), # Use imported Session here
    current_user: User = Depends(get_current_user) # Ensure user is logged in
):
    """
    Accepts vendor file upload, creates a job, and queues it for processing.
    """
    job_id = str(uuid.uuid4())
    set_job_id(job_id) # Set job ID in context for subsequent logs
    set_user(current_user) # Set user context

    # --- MODIFIED: Renamed 'filename' key to avoid conflict ---
    logger.info(f"Upload request received", extra={
        "job_id": job_id,
        "company_name": company_name,
        "uploaded_filename": file.filename, # Renamed key
        "content_type": file.content_type,
        "username": current_user.username
    })
    # --- END MODIFIED ---

    # --- File Validation (Basic) ---
    if not file.filename:
        logger.warning("Upload attempt with no filename.", extra={"job_id": job_id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided.")
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        logger.warning(f"Invalid file type uploaded: {file.filename}", extra={"job_id": job_id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Please upload an Excel file (.xlsx or .xls).")

    # --- Save File ---
    saved_file_path = None
    try:
        logger.debug(f"Attempting to save uploaded file for job {job_id}")
        saved_file_path = save_upload_file(file=file, job_id=job_id)
        logger.info(f"File saved successfully for job {job_id}", extra={"saved_path": saved_file_path})
    except IOError as e:
        logger.error(f"Failed to save uploaded file for job {job_id}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save file: {e}")
    except Exception as e: # Catch potential FastAPI upload errors too
        logger.error(f"Unexpected error during file upload/saving for job {job_id}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing upload: {e}")

    # --- Create Job Record ---
    job = None
    try:
        logger.debug(f"Creating database job record for job {job_id}")
        job = Job(
            id=job_id,
            company_name=company_name,
            input_file_name=os.path.basename(saved_file_path), # Store just the filename
            status=JobStatus.PENDING.value,
            current_stage=ProcessingStage.INGESTION.value,
            created_by=current_user.username
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        logger.info(f"Database job record created successfully for job {job_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create database job record for job {job_id}", exc_info=True)
        # Attempt to clean up saved file if DB record fails
        if saved_file_path and os.path.exists(saved_file_path):
            try: os.remove(saved_file_path)
            except OSError: logger.warning(f"Could not remove file {saved_file_path} after DB error.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create job record.")

    # --- Queue Celery Task ---
    try:
        logger.info(f"Adding Celery task 'process_vendor_file' to background tasks for job {job_id}")
        # Ensure the task is called with keyword arguments for clarity and robustness
        background_tasks.add_task(process_vendor_file.delay, job_id=job_id, file_path=saved_file_path)
        logger.info(f"Celery task queued successfully for job {job_id}")
    except Exception as e:
        logger.error(f"Failed to queue Celery task for job {job_id}", exc_info=True)
        # Update job status to failed if task queueing fails
        job.fail(f"Failed to queue processing task: {str(e)}")
        db.commit()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to queue job for processing.")

    # Return the initial job details (use JobResponse schema)
    logger.info(f"Upload request for job {job_id} processed successfully, returning 202 Accepted.")
    return JobResponse.model_validate(job) # Use Pydantic v2 validation
# --- END UPLOAD ROUTE ---


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