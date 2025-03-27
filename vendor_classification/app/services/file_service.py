import os
import pandas as pd
from fastapi import UploadFile
import shutil
from typing import List, Dict, Any
import uuid
import logging # Make sure logging is imported

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
    job_dir = os.path.join(settings.INPUT_DATA_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    logger.debug(f"Created job directory", extra={"directory": job_dir})

    file_path = os.path.join(job_dir, file.filename)
    with LogTimer(logger, "File saving"):
        try: # Add try/except for file operations
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            logger.error("Failed to save uploaded file", exc_info=True, extra={"file_path": file_path})
            raise IOError(f"Could not save uploaded file: {e}")

    file_size = os.path.getsize(file_path)
    logger.info(f"File saved successfully",
               extra={"path": file_path, "size_bytes": file_size})

    return file_path

@log_function_call(logger)
def read_vendor_file(file_path: str) -> List[str]:
    """
    Read vendor names from Excel file, looking for 'vendor_name' column case-insensitively.

    Args:
        file_path: Path to Excel file

    Returns:
        List of vendor names
    """
    logger.info(f"Reading Excel file", extra={"file_path": file_path})

    with LogTimer(logger, "Excel file reading", include_in_stats=True):
        try:
            # Explicitly tell pandas the header is on the first row (index 0)
            # If header might be elsewhere, adjust 'header' parameter or add 'skiprows'
            df = pd.read_excel(file_path, header=0)
            # --- ADDED LOGGING: Log detected columns ---
            detected_columns = list(df.columns)
            logger.debug(f"Columns read from Excel: {detected_columns}")
            # --- END ADDED LOGGING ---
        except Exception as e:
            logger.error(f"Error reading Excel file with pandas", exc_info=True,
                        extra={"file_path": file_path})
            # Provide a more specific error if it's file-not-found vs parsing error
            if isinstance(e, FileNotFoundError):
                 raise FileNotFoundError(f"Input file not found at path: {file_path}")
            raise ValueError(f"Error parsing Excel file: {str(e)}")

    # --- MODIFIED COLUMN CHECK ---
    # Find the vendor column, ignoring case and spaces
    vendor_col_name = None
    for col in df.columns:
        # Check if column name exists and is string before stripping/lowering
        if col and isinstance(col, str) and col.strip().lower() == 'vendor_name':
            vendor_col_name = col # Store the original column name as found in the DataFrame
            logger.info(f"Found 'vendor_name' column as: '{vendor_col_name}'")
            break # Stop after finding the first match

    if vendor_col_name is None:
        logger.error(f"Required column like 'vendor_name' not found in file",
                    extra={"available_columns": detected_columns}) # Use logged columns
        # Raise the specific error message seen in the frontend
        raise ValueError("Excel file must contain a 'vendor_name' column")
    # --- END MODIFIED COLUMN CHECK ---

    # Extract vendor names using the found column name
    try:
        vendors = df[vendor_col_name].dropna().astype(str).str.strip().tolist()
        # Filter out any potential empty strings after stripping
        vendors = [v for v in vendors if v]
        logger.info(f"Extracted vendor names from column '{vendor_col_name}'",
                   extra={"vendor_count": len(vendors)})
    except KeyError:
        # This shouldn't happen if vendor_col_name was found, but added as safety
        logger.error(f"KeyError accessing column '{vendor_col_name}' after it was seemingly found.",
                     extra={"available_columns": detected_columns})
        raise ValueError(f"Internal error accessing vendor column '{vendor_col_name}'.")
    except Exception as e:
        logger.error(f"Error extracting data from column '{vendor_col_name}'", exc_info=True)
        raise ValueError(f"Could not extract vendor names from column '{vendor_col_name}': {e}")


    return vendors

# --- Other functions (normalize_vendor_names, generate_output_file) remain the same ---

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
        vendor_str = str(vendor).strip()
        if vendor_str: # Only process non-empty strings
             # Standardize case (title case) - consider if lowercase is better for matching
            vendor_str = vendor_str.title()
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
                for level_key, level in result.items() if level_key.startswith("level") # Check only level keys
            ),
            # Safely extract URLs from sources
            "sources": ", ".join(
                source.get("url", "") for source in result.get("search_results", {}).get("sources", []) if isinstance(source, dict)
            ) if result.get("search_results", {}).get("sources") else ""
        }
        output_data.append(row)

    with LogTimer(logger, "Creating DataFrame"):
        df = pd.DataFrame(output_data)

    output_dir = os.path.join(settings.OUTPUT_DATA_DIR, job_id)
    os.makedirs(output_dir, exist_ok=True)
    logger.debug(f"Created output directory", extra={"directory": output_dir})

    output_file_name = f"vendor_classification_results_{uuid.uuid4().hex[:8]}.xlsx"
    output_path = os.path.join(output_dir, output_file_name)

    with LogTimer(logger, "Writing Excel file"):
        try: # Add try/except for file writing
            df.to_excel(output_path, index=False, engine='xlsxwriter') # Specify engine if needed
        except Exception as e:
            logger.error("Failed to write output Excel file", exc_info=True, extra={"output_path": output_path})
            raise IOError(f"Could not write output file: {e}")


    file_size = os.path.getsize(output_path)
    logger.info(f"Output file generated",
               extra={"file_name": output_file_name, "path": output_path, "size_bytes": file_size})

    return output_file_name