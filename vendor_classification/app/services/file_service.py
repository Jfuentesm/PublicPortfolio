import os
import pandas as pd
from fastapi import UploadFile
import shutil
from typing import List, Dict, Any
import uuid

from core.config import settings
from core.logging_config import get_logger, LogTimer, log_function_call

# Configure logger
logger = get_logger("vendor_classification.file_service")

@log_function_call(logger)
def save_upload_file(file: UploadFile, job_id: str) -> str:
    """
    Save uploaded file to the input directory.
    
    Args:
        file: Uploaded file
        job_id: Job ID
        
    Returns:
        Path to saved file
    """
    # Create directory for job
    job_dir = os.path.join(settings.INPUT_DATA_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    logger.debug(f"Created job directory", extra={"directory": job_dir})
    
    # Save file
    file_path = os.path.join(job_dir, file.filename)
    with LogTimer(logger, "File saving"):
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    
    file_size = os.path.getsize(file_path)
    logger.info(f"File saved successfully", 
               extra={"path": file_path, "size_bytes": file_size})
    
    return file_path

@log_function_call(logger)
def read_vendor_file(file_path: str) -> List[str]:
    """
    Read vendor names from Excel file.
    
    Args:
        file_path: Path to Excel file
        
    Returns:
        List of vendor names
    """
    logger.info(f"Reading Excel file", extra={"file_path": file_path})
    
    # Read Excel file
    with LogTimer(logger, "Excel file reading", include_in_stats=True):
        try:
            df = pd.read_excel(file_path)
            logger.debug(f"Excel file read successfully", 
                        extra={"columns": list(df.columns), "rows": len(df)})
        except Exception as e:
            logger.error(f"Error reading Excel file", exc_info=True,
                        extra={"file_path": file_path})
            raise ValueError(f"Error reading Excel file: {str(e)}")
    
    # Validate required columns
    if 'vendor_name' not in df.columns:
        logger.error(f"Required column 'vendor_name' not found", 
                    extra={"available_columns": list(df.columns)})
        raise ValueError("Excel file must contain a 'vendor_name' column")
    
    # Extract vendor names
    vendors = df['vendor_name'].dropna().str.strip().tolist()
    logger.info(f"Extracted vendor names", 
               extra={"vendor_count": len(vendors)})
    
    return vendors

@log_function_call(logger)
def normalize_vendor_names(vendors: List[str]) -> List[str]:
    """
    Normalize vendor names by removing special characters and standardizing case.
    
    Args:
        vendors: List of vendor names
        
    Returns:
        List of normalized vendor names
    """
    logger.info(f"Normalizing vendor names", 
               extra={"vendor_count": len(vendors)})
    
    normalized_vendors = []
    
    for vendor in vendors:
        # Convert to string if not already
        vendor_str = str(vendor)
        
        # Strip whitespace
        vendor_str = vendor_str.strip()
        
        # Standardize case (title case)
        vendor_str = vendor_str.title()
        
        # Add to normalized list if not empty
        if vendor_str:
            normalized_vendors.append(vendor_str)
    
    logger.debug(f"Vendor names normalized", 
               extra={
                   "original_count": len(vendors),
                   "normalized_count": len(normalized_vendors),
                   "empty_removed": len(vendors) - len(normalized_vendors)
               })
    
    return normalized_vendors

@log_function_call(logger)
def generate_output_file(
    original_vendors: List[str],
    classification_results: Dict[str, Dict],
    job_id: str
) -> str:
    """
    Generate output Excel file with classification results.
    
    Args:
        original_vendors: Original list of vendors
        classification_results: Classification results
        job_id: Job ID
        
    Returns:
        Path to output file
    """
    logger.info(f"Generating output file", 
               extra={"vendor_count": len(original_vendors), "job_id": job_id})
    
    # Prepare data for Excel
    output_data = []
    
    for vendor in original_vendors:
        result = classification_results.get(vendor, {})
        
        row = {
            "vendor_name": vendor,
            "level1_category_id": result.get("level1", {}).get("category_id", ""),
            "level1_category_name": result.get("level1", {}).get("category_name", ""),
            "level2_category_id": result.get("level2", {}).get("category_id", ""),
            "level2_category_name": result.get("level2", {}).get("category_name", ""),
            "level3_category_id": result.get("level3", {}).get("category_id", ""),
            "level3_category_name": result.get("level3", {}).get("category_name", ""),
            "level4_category_id": result.get("level4", {}).get("category_id", ""),
            "level4_category_name": result.get("level4", {}).get("category_name", ""),
            "confidence": result.get("level4", {}).get("confidence", 0),
            "classification_not_possible": any(
                level.get("classification_not_possible", False) 
                for level in result.values()
            ),
            "sources": ", ".join(
                [source.get("url", "") for source in result.get("search_results", {}).get("sources", [])]
            )
        }
        
        output_data.append(row)
    
    # Create DataFrame
    with LogTimer(logger, "Creating DataFrame"):
        df = pd.DataFrame(output_data)
    
    # Create output directory
    output_dir = os.path.join(settings.OUTPUT_DATA_DIR, job_id)
    os.makedirs(output_dir, exist_ok=True)
    logger.debug(f"Created output directory", extra={"directory": output_dir})
    
    # Generate output file name
    output_file_name = f"vendor_classification_results_{uuid.uuid4().hex[:8]}.xlsx"
    output_path = os.path.join(output_dir, output_file_name)
    
    # Write to Excel
    with LogTimer(logger, "Writing Excel file"):
        df.to_excel(output_path, index=False)
    
    file_size = os.path.getsize(output_path)
    logger.info(f"Output file generated", 
               extra={"file_name": output_file_name, "path": output_path, "size_bytes": file_size})
    
    return output_file_name