from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict, Any, Optional
import uuid
import os
import logging
from datetime import datetime, timedelta
import socket

from models.job import Job, JobStatus, ProcessingStage
from models.user import User
from api.auth import get_current_user, authenticate_user, create_access_token  # Added missing imports
from core.database import get_db
from core.initialize_db import initialize_database
from services.file_service import save_upload_file
from tasks.classification_tasks import process_vendor_file

from fastapi.security import OAuth2PasswordRequestForm

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("vendor_classification.api")

app = FastAPI(
    title="NAICS Vendor Classification API",
    description="API for classifying vendors according to NAICS taxonomy",
    version="1.0.0",
)

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
        logger.error(f"Index file not found at {index_path}")
        return HTMLResponse(content=f"<html><body><h1>Error: Frontend file not found</h1><p>Could not find {index_path}</p><p>Directory contents: {os.listdir('/frontend')}</p></body></html>")

@app.get("/health")
async def health_check():
    """Health check endpoint to verify service is running."""
    # Log server information
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    logger.info(f"Health check called. Server running on {hostname}, IP: {local_ip}")
    
    # Check database connectivity
    try:
        db = next(get_db())
        db_status = "connected"
        db.close()
    except Exception as e:
        logger.error(f"Database connection error: {e}")
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

# Re-adding missing API endpoints
@app.post("/api/v1/upload", response_model=Dict[str, Any])
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    company_name: str = Form(...),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Upload vendor Excel file for processing."""
    # Log the upload attempt with authentication information
    logger.info(f"File upload attempt by user: {current_user.username}, filename: {file.filename}")
    
    # Validate file
    if not file.filename.endswith(('.xlsx', '.xls')):
        logger.warning(f"Invalid file format: {file.filename}")
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    try:
        # Save file
        input_file_path = save_upload_file(file, job_id)
        logger.debug(f"File saved at: {input_file_path}")
        
        # Create job record
        job = Job(
            id=job_id,
            company_name=company_name,
            input_file_name=file.filename,
            status=JobStatus.PENDING,
            current_stage=ProcessingStage.INGESTION,
            created_by=current_user.username
        )
        
        # Save job to database
        db.add(job)
        db.commit()
        logger.info(f"Job created: {job_id} for company: {company_name}")
        
        # Start processing in background
        background_tasks.add_task(process_vendor_file, job_id, input_file_path)
        logger.debug(f"Background task scheduled for job: {job_id}")
        
        return {
            "job_id": job_id,
            "status": "pending",
            "message": f"File {file.filename} uploaded successfully and processing has started"
        }
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")

@app.get("/api/v1/jobs/{job_id}", response_model=Dict[str, Any])
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Check job status."""
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
    
    return {
        "job_id": job.id,
        "status": job.status,
        "progress": job.progress,
        "current_stage": job.current_stage,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "estimated_completion": job.estimated_completion if hasattr(job, 'estimated_completion') else None
    }

@app.get("/api/v1/jobs/{job_id}/download")
async def download_results(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Download job results."""
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job processing has not completed yet")
    
    if not job.output_file_name:
        raise HTTPException(status_code=404, detail="Output file not found")
    
    output_path = os.path.join("/data", "output", job_id, job.output_file_name)
    
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Output file not found")
    
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
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
    
    # Update job with notification email
    job.notification_email = email.get("email")
    db.commit()
    
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
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
    
    return {
        "vendors_processed": job.stats.get("total_vendors", 0),
        "unique_vendors": job.stats.get("unique_vendors", 0),
        "api_calls": job.stats.get("api_calls", 0),
        "tokens_used": job.stats.get("tokens_used", 0),
        "tavily_searches": job.stats.get("tavily_searches", 0),
        "processing_time": job.stats.get("processing_time", 0)
    }

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting application initialization")
    
    # Initialize database
    try:
        logger.info("Initializing database...")
        initialize_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
    
    # Log server information
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    logger.info(f"Server running on {hostname}, IP: {local_ip}")
    logger.info(f"Web server binding to 0.0.0.0:8000")
    
    # Check frontend files
    if os.path.exists("/frontend"):
        logger.info(f"Frontend directory contents: {os.listdir('/frontend')}")
    else:
        logger.error("Frontend directory not found!")

# Re-adding the main entry point
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server at 0.0.0.0:8000")
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")

# Add login endpoint
@app.post("/token", response_model=Dict[str, Any])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db = Depends(get_db)):
    """
    Get an access token for authentication.
    """
    logger.debug(f"Login attempt for user: {form_data.username}")
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            logger.warning(f"Failed login attempt for user: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        logger.info(f"User logged in successfully: {user.username}")
        return {"access_token": access_token, "token_type": "bearer", "username": user.username}
    except HTTPException:
        # Re-raise HTTP exceptions to preserve their status codes
        raise
    except Exception as e:
        logger.error(f"Error during login process: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during the login process",
        )