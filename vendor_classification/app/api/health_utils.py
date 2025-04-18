# app/api/health_utils.py
import socket
import sqlalchemy
import httpx
import os
from datetime import datetime, timezone
from fastapi import HTTPException, status # Import if needed for direct use, though health_check returns dict

# --- Core Imports ---
from core import config # Import config module directly
from core.config import settings
from core.database import SessionLocal
from core.logging_config import get_logger
from tasks.celery_app import celery_app

logger = get_logger("vendor_classification.health_check")

# --- Moved Health Check Logic ---
async def health_check():
    """Health check logic, moved from main.py to avoid circular imports."""
    hostname = socket.gethostname()
    local_ip = ""
    try:
        local_ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        try:
            # Fallback for environments where hostname might not resolve directly
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1.0) # Add timeout
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception as ip_err:
                logger.warning(f"Could not resolve local IP via fallback: {ip_err}")
                local_ip = "Could not resolve IP"

    logger.debug(f"Health check called", extra={"hostname": hostname, "ip": local_ip})
    db_status = "unknown"
    db = None
    try:
        db = SessionLocal()
        # Use a simple query that doesn't lock tables
        db.execute(sqlalchemy.text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Health Check: Database connection error", exc_info=True, extra={"error_details": str(e)})
        db_status = f"error: {str(e)[:100]}"
    finally:
        if db:
            db.close()

    # Check Vue frontend index file existence (relative path assumed from Docker context)
    # This path is checked within the container after build
    vue_build_dir = "/app/frontend/dist"
    vue_index_file = os.path.join(vue_build_dir, "index.html")
    vue_frontend_status = "found" if os.path.exists(vue_index_file) else "missing"

    celery_broker_status = "unknown"
    celery_connection = None
    try:
        # Use a short timeout for health check connection attempt
        celery_connection = celery_app.connection(heartbeat=2.0, transport_options={'max_retries': 1})
        celery_connection.ensure_connection(max_retries=1, timeout=2)
        celery_broker_status = "connected"
    except Exception as celery_e:
        logger.error(f"Celery broker connection error during health check: {str(celery_e)}", exc_info=False)
        celery_broker_status = f"error: {str(celery_e)[:100]}"
    finally:
            if celery_connection:
                try: celery_connection.close()
                except Exception as close_err: logger.warning(f"Error closing celery connection in health check: {close_err}")

    # API Checks (using manually loaded config)
    openrouter_status = "unknown"
    tavily_status = "unknown"
    tavily_api_functional = False

    if config.MANUAL_OPENROUTER_PROVISIONING_KEYS and settings.OPENROUTER_API_BASE:
        openrouter_status = "CONFIGURED"
        if any("REPLACE_WITH_YOUR_VALID" in k for k in config.MANUAL_OPENROUTER_PROVISIONING_KEYS):
             openrouter_status = "CONFIGURED (PLACEHOLDER KEYS)"
             logger.warning("OpenRouter health check: Provisioning keys appear to be placeholders.")
    else:
        openrouter_status = "NOT CONFIGURED"
        logger.warning("OpenRouter provisioning keys or API base missing/empty for health check.")

    if config.MANUAL_TAVILY_API_KEYS:
        tavily_status = "CONFIGURED"
        if any("REPLACE_WITH_YOUR_VALID" in k for k in config.MANUAL_TAVILY_API_KEYS):
             tavily_status = "CONFIGURED (PLACEHOLDER KEYS)"
             logger.warning("Tavily health check: API keys appear to be placeholders.")
        else:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    test_payload = {"api_key": config.MANUAL_TAVILY_API_KEYS[0], "query": "test", "max_results": 1}
                    # Use the correct Tavily API endpoint URL
                    tavily_api_url = settings.TAVILY_API_URL or "https://api.tavily.com/search"
                    response = await client.post(tavily_api_url, json=test_payload)
                    if response.status_code == 200:
                        tavily_api_functional = True
                        tavily_status = "API FUNCTIONAL"
                    else:
                        logger.warning(f"Tavily health check API call failed with status {response.status_code}")
                        tavily_status = f"API ERROR ({response.status_code})"
            except Exception as e:
                logger.error(f"Tavily health check API call failed: {e}", exc_info=False)
                tavily_status = f"API ERROR ({type(e).__name__})"
    else:
        tavily_status = "NOT CONFIGURED"
        logger.warning("Tavily API keys missing/empty for health check.")

    email_status = "configured" if settings.SMTP_HOST and settings.SMTP_USER and settings.EMAIL_FROM else "not_configured"

    return {
        "status": "healthy", # Overall status, might need adjustment based on component checks
        "hostname": hostname,
        "ip": local_ip,
        "database": db_status,
        "celery_broker": celery_broker_status,
        "vue_frontend_index": vue_frontend_status,
        "email_service": email_status,
        "openrouter_status": openrouter_status,
        "tavily_status": tavily_status,
        "tavily_api_functional": tavily_api_functional,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
