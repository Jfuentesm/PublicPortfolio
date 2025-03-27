import os
import pandas as pd
from fastapi import UploadFile
import shutil
from typing import List, Dict, Any
import uuid
import logging # Make sure logging is imported
from datetime import datetime # <--- ADDED IMPORT

from core.config import settings
from core.logging_config import get_logger, LogTimer, log_function_call, set_log_context

# Configure logger
logger = get_logger("vendor_classification.file_service")

@log_function_call(logger, include_args=False) # Keep args=False for UploadFile
def save_upload_file(file: UploadFile, job_id: str) -> str:
    """
    Save uploaded file to the input directory.

    Args:
        file: Uploaded file object
        job_id: Job ID

    Returns:
        Path to saved file

    Raises:
        IOError: If the file cannot be saved.
        HTTPException: Can be raised by FastAPI if upload fails mid-stream.
    """
    job_dir = os.path.join(settings.INPUT_DATA_DIR, job_id)
    try:
        os.makedirs(job_dir, exist_ok=True)
        logger.debug(f"Ensured job directory exists", extra={"directory": job_dir})
    except OSError as e:
        logger.error(f"Failed to create job directory", exc_info=True, extra={"directory": job_dir})
        raise IOError(f"Could not create directory for job {job_id}: {e}")

    # Use original filename, ensure it's safe (basic check)
    # More robust sanitization might be needed depending on environment
    safe_filename = os.path.basename(file.filename or f"upload_{job_id}.tmp")
    if not safe_filename: # Handle empty filename after basename
         safe_filename = f"upload_{job_id}.tmp"

    file_path = os.path.join(job_dir, safe_filename)
    logger.info("Attempting to save file", extra={"path": file_path})

    with LogTimer(logger, "File saving"):
        try:
            with open(file_path, "wb") as buffer:
                # Copy file object efficiently
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            logger.error("Failed to save uploaded file content", exc_info=True, extra={"file_path": file_path})
            # Clean up potentially partially written file
            if os.path.exists(file_path):
                 try: os.remove(file_path)
                 except OSError: logger.warning("Could not remove partially written file on error.", extra={"file_path": file_path})
            raise IOError(f"Could not save uploaded file content: {e}")
        finally:
            # Ensure the file object provided by FastAPI is closed
            if hasattr(file, 'close') and callable(file.close):
                file.close()

    try:
        file_size = os.path.getsize(file_path)
        logger.info(f"File saved successfully",
                   extra={"path": file_path, "size_bytes": file_size})
    except OSError as e:
        logger.warning(f"Could not get size of saved file", exc_info=False, extra={"file_path": file_path, "error": str(e)})
        file_size = -1 # Indicate unknown size

    # Optional: Basic content check (e.g., is it a valid Excel file?)
    # This could be done here or in read_vendor_file
    # try:
    #     pd.ExcelFile(file_path).close() # Try opening without reading all data
    #     logger.debug("File appears to be a valid Excel file.")
    # except Exception as ex:
    #     logger.error("Uploaded file does not appear to be a valid Excel file", exc_info=False, extra={"file_path": file_path, "error": str(ex)})
    #     # Clean up invalid file
    #     os.remove(file_path)
    #     raise ValueError(f"Uploaded file is not a valid Excel file: {ex}")

    return file_path


@log_function_call(logger)
def read_vendor_file(file_path: str) -> List[str]:
    """
    Read vendor names from Excel file, looking for 'vendor_name' column case-insensitively.

    Args:
        file_path: Path to Excel file

    Returns:
        List of vendor names (stripped, non-empty)

    Raises:
        FileNotFoundError: If the file_path does not exist.
        ValueError: If the file cannot be parsed or the required column is missing.
    """
    logger.info(f"Reading Excel file", extra={"file_path": file_path})

    if not os.path.exists(file_path):
         logger.error(f"Input file not found at path", extra={"file_path": file_path})
         raise FileNotFoundError(f"Input file not found at path: {file_path}")

    with LogTimer(logger, "Excel file reading", include_in_stats=True):
        try:
            # Read the Excel file, assuming header is in the first row (index 0)
            df = pd.read_excel(file_path, header=0)
            detected_columns = list(df.columns)
            logger.debug(f"Successfully read Excel file. Columns detected: {detected_columns}")
        except Exception as e:
            logger.error(f"Error reading Excel file with pandas", exc_info=True,
                        extra={"file_path": file_path})
            # Raise a clearer error message
            raise ValueError(f"Could not parse the Excel file. Please ensure it is a valid .xlsx or .xls file. Error details: {str(e)}")

    # --- Robust Column Finding ---
    target_col_normalized = 'vendor_name'
    vendor_col_name = None
    for col in df.columns:
        # Ensure col is a string before processing
        if isinstance(col, str) and col.strip().lower() == target_col_normalized:
            vendor_col_name = col # Store the original column name as found
            logger.info(f"Found '{target_col_normalized}' column as: '{vendor_col_name}'")
            break # Stop after finding the first match

    if vendor_col_name is None:
        logger.error(f"Required column like '{target_col_normalized}' not found in file.",
                    extra={"available_columns": detected_columns})
        # Raise a specific, user-friendly error
        raise ValueError(f"Input Excel file must contain a column named 'vendor_name' (case-insensitive). Found columns: {', '.join(map(str, detected_columns))}")
    # --- End Robust Column Finding ---

    # Extract vendor names using the found column name
    try:
        # Select column, convert to string, drop NaNs, strip whitespace
        vendors_series = df[vendor_col_name].astype(str).str.strip()
        # Filter out empty strings and common non-value strings like 'nan'
        vendors = vendors_series.loc[vendors_series.str.len() > 0 & ~vendors_series.str.lower().isin(['nan', 'none', 'null', ''])].tolist()

        logger.info(f"Extracted {len(vendors)} non-empty vendor names from column '{vendor_col_name}'.")
        if not vendors:
             logger.warning(f"No valid vendor names found in column '{vendor_col_name}'.")
             # Depending on requirements, could raise an error here or return empty list
             # raise ValueError(f"No valid vendor names found in column '{vendor_col_name}'.")

    except KeyError:
        # This check is somewhat redundant due to the robust finding above, but good failsafe
        logger.error(f"Internal Error: KeyError accessing column '{vendor_col_name}' after it was seemingly found.",
                     extra={"available_columns": detected_columns})
        raise ValueError(f"Internal error accessing vendor column '{vendor_col_name}'.")
    except Exception as e:
        logger.error(f"Error extracting or processing data from column '{vendor_col_name}'", exc_info=True)
        raise ValueError(f"Could not extract vendor names from column '{vendor_col_name}'. Please check data format. Error: {e}")

    return vendors


@log_function_call(logger)
def normalize_vendor_names(vendors: List[str]) -> List[str]:
    """
    Normalize vendor names by converting to title case and stripping whitespace.
    Filters out any resulting empty strings.

    Args:
        vendors: List of raw vendor names

    Returns:
        List of normalized, non-empty vendor names
    """
    start_count = len(vendors)
    logger.info(f"Normalizing {start_count} vendor names...")

    normalized_vendors = []
    empty_removed_count = 0

    with LogTimer(logger, "Vendor name normalization", include_in_stats=True):
        for vendor in vendors:
            if isinstance(vendor, str):
                # Strip whitespace first, then title case
                normalized = vendor.strip().title()
                if normalized: # Check if non-empty after stripping/casing
                    normalized_vendors.append(normalized)
                else:
                    empty_removed_count += 1
            else:
                # Handle non-string inputs if necessary (e.g., log warning, skip)
                logger.warning("Skipping non-string vendor value during normalization", extra={"value": vendor})
                empty_removed_count += 1


    final_count = len(normalized_vendors)
    logger.info(f"Vendor names normalized.",
               extra={
                   "original_count": start_count,
                   "normalized_count": final_count,
                   "empty_or_skipped": empty_removed_count
               })

    return normalized_vendors


@log_function_call(logger)
def generate_output_file(
    original_vendors: List[str], # Use the original list (including duplicates)
    classification_results: Dict[str, Dict], # Results keyed by *unique* normalized names
    job_id: str
) -> str:
    """
    Generate output Excel file with classification results, mapping back to original vendor names.

    Args:
        original_vendors: Original list of vendors from the input file (raw, possibly with duplicates).
        classification_results: Classification results keyed by unique, normalized vendor names.
        job_id: Job ID

    Returns:
        File name of the generated output file (not the full path).

    Raises:
        IOError: If the file cannot be written.
    """
    logger.info(f"Generating output file for {len(original_vendors)} original vendor entries",
               extra={"job_id": job_id})

    output_data = []
    # Temporary mapping from normalized name back to results for efficiency
    normalized_to_result = {vendor.strip().title(): res for vendor, res in classification_results.items()}

    with LogTimer(logger, "Mapping results to original vendors"):
        for original_vendor_name in original_vendors:
            # Normalize the original name *in the same way* as done for classification
            normalized_key = str(original_vendor_name).strip().title() if isinstance(original_vendor_name, str) else ""

            result = normalized_to_result.get(normalized_key, {}) # Get results using normalized key

            # --- Safely access nested results using .get() ---
            level1 = result.get("level1", {})
            level2 = result.get("level2", {})
            level3 = result.get("level3", {})
            level4 = result.get("level4", {})
            search_results_data = result.get("search_results", {})
            search_classification = search_results_data.get("classification", {})

            # Determine final classification status and reason
            final_classification_possible = level4.get("category_id") and level4.get("category_id") not in ["N/A", "ERROR"]
            classification_not_possible_flag = True # Assume impossible unless proven otherwise
            reason = "Not fully classified" # Default reason

            if final_classification_possible:
                classification_not_possible_flag = False
                reason = None
            elif search_classification and not search_classification.get("classification_not_possible", True):
                 # If search provided a valid L1 classification, use that as the 'best' result
                 level1 = search_classification # Overwrite L1 with search result
                 level1['notes'] = f"Classified via search: {level1.get('notes', '')}"
                 classification_not_possible_flag = False # Mark as classified (at least L1)
                 reason = None
                 # Clear L2-L4 as they are no longer valid if L1 changed
                 level2, level3, level4 = {}, {}, {}
            else:
                # Find the first level where classification failed, if any
                for lvl in range(1, 5):
                     lvl_res = result.get(f"level{lvl}", {})
                     if lvl_res.get("classification_not_possible", False):
                          reason = lvl_res.get("classification_not_possible_reason", f"Classification failed at Level {lvl}")
                          break
                else: # If no level explicitly failed, check search results reason
                     if search_classification and search_classification.get("classification_not_possible", False):
                           reason = search_classification.get("classification_not_possible_reason", "Search did not yield classification")
                     elif search_results_data.get("error"):
                           reason = f"Search error: {search_results_data.get('error')}"
                     # else 'Not fully classified' remains

            row = {
                "vendor_name": original_vendor_name, # Use the original name from the input
                "level1_category_id": level1.get("category_id", ""),
                "level1_category_name": level1.get("category_name", ""),
                "level2_category_id": level2.get("category_id", ""),
                "level2_category_name": level2.get("category_name", ""),
                "level3_category_id": level3.get("category_id", ""),
                "level3_category_name": level3.get("category_name", ""),
                "level4_category_id": level4.get("category_id", ""),
                "level4_category_name": level4.get("category_name", ""),
                "final_confidence": level4.get("confidence", 0) if not classification_not_possible_flag else level1.get("confidence", 0), # Use L4 confidence if classified, else L1 (could be from search)
                "classification_not_possible": classification_not_possible_flag,
                "classification_notes_or_reason": reason or level4.get("notes") or level1.get("notes", ""), # Provide reason if failed, else notes
                # Safely extract URLs from sources list (which should contain dicts)
                "sources": ", ".join(
                    source.get("url", "") for source in search_results_data.get("sources", []) if isinstance(source, dict) and source.get("url")
                ) if isinstance(search_results_data.get("sources"), list) else ""
            }
            output_data.append(row)
            # --- End Safe Access ---

    if not output_data:
        logger.warning("No data rows generated for the output file.")
        # Handle appropriately - maybe raise error or return indicator?
        # For now, create an empty file.
        # return "empty_output_generated.xlsx" # Or similar indicator

    with LogTimer(logger, "Creating DataFrame for output"):
        df = pd.DataFrame(output_data)

    output_dir = os.path.join(settings.OUTPUT_DATA_DIR, job_id)
    try:
        os.makedirs(output_dir, exist_ok=True)
        logger.debug(f"Ensured output directory exists", extra={"directory": output_dir})
    except OSError as e:
        logger.error(f"Failed to create output directory", exc_info=True, extra={"directory": output_dir})
        raise IOError(f"Could not create output directory for job {job_id}: {e}")

    # Generate a unique-ish but potentially more readable filename
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S") # <--- datetime used here
    output_file_name = f"classification_results_{job_id[:8]}_{timestamp_str}.xlsx"
    output_path = os.path.join(output_dir, output_file_name)

    with LogTimer(logger, "Writing Excel file"):
        try:
            # Use XlsxWriter for potentially better handling of large files/formatting
            df.to_excel(output_path, index=False, engine='xlsxwriter')
        except Exception as e:
            logger.error("Failed to write output Excel file", exc_info=True, extra={"output_path": output_path})
            raise IOError(f"Could not write output file: {e}")

    try:
        file_size = os.path.getsize(output_path)
        logger.info(f"Output file generated successfully",
                   extra={"file_name": output_file_name, "path": output_path, "size_bytes": file_size})
    except OSError as e:
         logger.warning(f"Could not get size of generated output file", exc_info=False, extra={"output_path": output_path, "error": str(e)})

    return output_file_name # Return only the filename, not the full path