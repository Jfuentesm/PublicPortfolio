from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict, Any, Optional
import uuid
import os
import socket
from datetime import datetime, timedelta

from models.job import Job, JobStatus, ProcessingStage
from models.user import User

from core.config import settings
from core.logging_config import setup_logging, get_logger, set_correlation_id, set_user, set_job_id
from middleware.logging_middleware import RequestLoggingMiddleware, log_request_middleware

from api.auth import get_current_user, authenticate_user, create_access_token
from core.database import get_db
from core.initialize_db import initialize_database
from services.file_service import save_upload_file
from tasks.classification_tasks import process_vendor_file

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
app.mount("/static", StaticFiles(directory="/frontend/static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the frontend application."""
    logger.info("Serving index.html")
    index_path = "/frontend/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        logger.error(f"Index file not found at {index_path}", extra={"path": index_path})
        return HTMLResponse(
            content=f"<html><body><h1>Error: Frontend file not found</h1>"
                    f"<p>Could not find {index_path}</p>"
                    f"<p>Directory contents: {os.listdir('/frontend')}</p>"
                    "</body></html>"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint to verify service is running."""
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    logger.info(f"Health check called", extra={"hostname": hostname, "ip": local_ip})
    
    # Check database connectivity
    try:
        db = next(get_db())
        db_status = "connected"
        db.close()
    except Exception as e:
        logger.error(f"Database connection error", exc_info=True,
                    extra={"error_details": str(e)})
        db_status = f"error: {str(e)}"
    
    # Check if frontend files exist
    frontend_status = "found" if os.path.exists("/frontend/index.html") else "missing"
    
    return {
        "status": "healthy", 
        "hostname": hostname, 
        "ip": local_ip,
        "database": db_status,
        "frontend": frontend_status,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/upload", response_model=Dict[str, Any])
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    company_name: str = Form(...),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Upload vendor Excel file for processing."""
    # Generate job ID and set context
    job_id = str(uuid.uuid4())
    set_correlation_id(job_id)  # Use job_id as correlation_id
    set_job_id(job_id)
    set_user(current_user)
    
    logger.info(
        f"File upload initiated", 
        extra={
            "company_name": company_name,
            "filename": file.filename,
            "username": current_user.username
        }
    )
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        logger.warning(f"Invalid file format rejected", 
                      extra={"filename": file.filename, "valid_formats": [".xlsx", ".xls"]})
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")
    
    try:
        input_file_path = save_upload_file(file, job_id)
        logger.debug(f"File saved successfully", extra={"filepath": input_file_path})
        
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
        logger.info(f"Job created in database", 
                   extra={"company": company_name, "status": JobStatus.PENDING})
        
        # Schedule background task
        logger.debug(f"Scheduling background task")
        background_tasks.add_task(process_vendor_file, job_id, input_file_path)
        
        logger.info(f"File uploaded successfully, processing scheduled",
                   extra={"job_id": job_id})
        
        return {
            "job_id": job_id,
            "status": "pending",
            "message": f"File {file.filename} uploaded successfully and processing has started"
        }
    except Exception as e:
        logger.error(f"Error processing upload", exc_info=True,
                    extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")


@app.get("/api/v1/jobs/{job_id}", response_model=Dict[str, Any])
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Check job status."""
    # Set context
    set_correlation_id(job_id)
    set_job_id(job_id)
    set_user(current_user)
    
    logger.info(f"Job status requested", 
               extra={"username": current_user.username})
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.warning(f"Job not found", extra={"job_id": job_id})
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
    
    logger.info(f"Job status retrieved", 
               extra={
                   "status": job.status,
                   "progress": job.progress,
                   "stage": job.current_stage
               })
    
    return {
        "job_id": job.id,
        "status": job.status,
        "progress": job.progress,
        "current_stage": job.current_stage,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "estimated_completion": job.stats.get('estimated_completion', None)
    }


@app.get("/api/v1/jobs/{job_id}/download")
async def download_results(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Download job results."""
    # Set context
    set_correlation_id(job_id)
    set_job_id(job_id)
    set_user(current_user)
    
    logger.info(f"Results download requested", 
               extra={"username": current_user.username})
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.warning(f"Job not found", extra={"job_id": job_id})
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
    
    if job.status != JobStatus.COMPLETED:
        logger.warning(f"Job not completed", 
                      extra={"job_id": job_id, "status": job.status})
        raise HTTPException(status_code=400, detail="Job processing has not completed yet")
    
    if not job.output_file_name:
        logger.warning(f"Output file not set", extra={"job_id": job_id})
        raise HTTPException(status_code=404, detail="Output file not found")
    
    output_path = os.path.join("/data", "output", job_id, job.output_file_name)
    if not os.path.exists(output_path):
        logger.error(f"Output file not found on disk", 
                    extra={"job_id": job_id, "expected_path": output_path})
        raise HTTPException(status_code=404, detail="Output file not found")
    
    logger.info(f"Serving result file", 
               extra={"filename": job.output_file_name, "path": output_path})
    
    return FileResponse(
        output_path,
        filename=job.output_file_name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.post("/api/v1/jobs/{job_id}/notify", response_model=Dict[str, Any])
async def request_notification(
    job_id: str,
    email: Dict[str, str],
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Request email notification when job completes."""
    # Set context
    set_correlation_id(job_id)
    set_job_id(job_id)
    set_user(current_user)
    
    logger.info(f"Notification requested", 
               extra={"username": current_user.username, "email": email.get("email")})
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.warning(f"Job not found", extra={"job_id": job_id})
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
    
    job.notification_email = email.get("email")
    db.commit()
    
    logger.info(f"Notification email set", 
               extra={"email": email.get("email")})
    
    return {
        "success": True,
        "message": f"Notification will be sent to {email.get('email')} when job completes"
    }


@app.get("/api/v1/jobs/{job_id}/stats", response_model=Dict[str, Any])
async def get_job_stats(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get job processing statistics."""
    # Set context
    set_correlation_id(job_id)
    set_job_id(job_id)
    set_user(current_user)
    
    logger.info(f"Job stats requested", 
               extra={"username": current_user.username})
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.warning(f"Job not found", extra={"job_id": job_id})
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
    
    logger.info(f"Job stats retrieved")
    
    return {
        "vendors_processed": job.stats.get("total_vendors", 0),
        "unique_vendors": job.stats.get("unique_vendors", 0),
        "api_calls": job.stats.get("api_calls", 0),
        "tokens_used": job.stats.get("tokens_used", 0),
        "tavily_searches": job.stats.get("tavily_searches", 0),
        "processing_time": job.stats.get("processing_time", 0)
    }


@app.post("/token", response_model=Dict[str, Any])
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db = Depends(get_db)
):
    """
    Get an access token for authentication.
    """
    # Generate correlation ID for this request
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)
    
    logger.info(f"Login attempt", 
               extra={"username": form_data.username, "ip": request.client.host})
    
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            logger.warning(f"Login failed: invalid credentials", 
                          extra={"username": form_data.username, "ip": request.client.host})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Once authenticated, set user context
        set_user(user)
        
        # Create token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, 
            expires_delta=access_token_expires
        )
        
        logger.info(f"Login successful", 
                   extra={
                       "username": user.username, 
                       "ip": request.client.host,
                       "token_expires_in_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES
                   })
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "username": user.username
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error", exc_info=True,
                    extra={"error": str(e), "username": form_data.username})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during the login process",
        )


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    # Initialize logger
    setup_logging(log_level=None, log_to_file=True)
    logger.info("Application starting up")
    
    try:
        logger.info("Initializing database")
        initialize_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database", exc_info=True,
                    extra={"error_details": str(e)})
    
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    logger.info(f"Server running", 
               extra={"hostname": hostname, "ip": local_ip, "port": 8000})
    
    if os.path.exists("/frontend"):
        frontend_files = os.listdir("/frontend")
        logger.info(f"Frontend directory accessed", 
                   extra={"files_count": len(frontend_files)})
    else:
        logger.error("Frontend directory not found!")


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server")
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")