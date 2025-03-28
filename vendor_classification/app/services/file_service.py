# file path='app/services/file_service.py'
import os
import pandas as pd
from fastapi import UploadFile
import shutil
from typing import List, Dict, Any, Optional # <--- Added Optional
import uuid
import logging # Make sure logging is imported
from datetime import datetime # <--- ADDED IMPORT

from core.config import settings
from core.logging_config import get_logger, LogTimer, log_function_call, set_log_context

# Configure logger
logger = get_logger("vendor_classification.file_service")

# --- Define expected column names (case-insensitive matching) ---
VENDOR_NAME_COL = 'vendor_name'
OPTIONAL_DESC_COL = 'optional_vendor_description'
OPTIONAL_EXAMPLE_COL = 'optional_example_good_serviced_purchased'
# ---

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

    return file_path


@log_function_call(logger)
def read_vendor_file(file_path: str) -> List[Dict[str, Any]]: # <--- MODIFIED RETURN TYPE
    """
    Read vendor data from Excel file, looking for mandatory 'vendor_name'
    and optional description and example columns (case-insensitively).

    Args:
        file_path: Path to Excel file

    Returns:
        List of dictionaries, each containing vendor data.
        Example: [{'vendor_name': 'Acme Inc', 'description': '...', 'example': '...'}]

    Raises:
        FileNotFoundError: If the file_path does not exist.
        ValueError: If the file cannot be parsed or the required vendor_name column is missing.
    """
    logger.info(f"Reading Excel file for vendor data", extra={"file_path": file_path})

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

    # --- Find columns case-insensitively ---
    column_map: Dict[str, Optional[str]] = {
        'vendor_name': None,
        'description': None,
        'example': None
    }
    normalized_detected_columns = {str(col).strip().lower(): str(col) for col in detected_columns if isinstance(col, str)}

    # Find vendor_name (mandatory)
    if VENDOR_NAME_COL in normalized_detected_columns:
        column_map['vendor_name'] = normalized_detected_columns[VENDOR_NAME_COL]
        logger.info(f"Found mandatory column '{VENDOR_NAME_COL}' as: '{column_map['vendor_name']}'")
    else:
        logger.error(f"Required column '{VENDOR_NAME_COL}' not found in file.",
                    extra={"available_columns": detected_columns})
        raise ValueError(f"Input Excel file must contain a column named '{VENDOR_NAME_COL}' (case-insensitive). Found columns: {', '.join(map(str, detected_columns))}")

    # Find optional columns
    if OPTIONAL_DESC_COL in normalized_detected_columns:
        column_map['description'] = normalized_detected_columns[OPTIONAL_DESC_COL]
        logger.info(f"Found optional column '{OPTIONAL_DESC_COL}' as: '{column_map['description']}'")
    else:
        logger.info(f"Optional column '{OPTIONAL_DESC_COL}' not found.")

    if OPTIONAL_EXAMPLE_COL in normalized_detected_columns:
        column_map['example'] = normalized_detected_columns[OPTIONAL_EXAMPLE_COL]
        logger.info(f"Found optional column '{OPTIONAL_EXAMPLE_COL}' as: '{column_map['example']}'")
    else:
         logger.info(f"Optional column '{OPTIONAL_EXAMPLE_COL}' not found.")
    # --- End Find columns ---

    # --- Extract data into list of dictionaries ---
    vendors_data: List[Dict[str, Any]] = []
    processed_count = 0
    skipped_count = 0

    try:
        for index, row in df.iterrows():
            vendor_name_raw = row.get(column_map['vendor_name'])
            vendor_name = str(vendor_name_raw).strip() if pd.notna(vendor_name_raw) and str(vendor_name_raw).strip() else None

            # Skip row if vendor name is missing or empty after stripping
            if not vendor_name or vendor_name.lower() in ['nan', 'none', 'null']:
                skipped_count += 1
                continue

            vendor_entry: Dict[str, Any] = {'vendor_name': vendor_name}

            # Add optional fields if columns exist and data is present
            if column_map['description']:
                desc_raw = row.get(column_map['description'])
                description = str(desc_raw).strip() if pd.notna(desc_raw) and str(desc_raw).strip() else None
                if description:
                    vendor_entry['description'] = description

            if column_map['example']:
                example_raw = row.get(column_map['example'])
                example = str(example_raw).strip() if pd.notna(example_raw) and str(example_raw).strip() else None
                if example:
                    vendor_entry['example'] = example

            vendors_data.append(vendor_entry)
            processed_count += 1

        logger.info(f"Extracted data for {processed_count} vendors. Skipped {skipped_count} rows due to missing/invalid vendor name.")
        if not vendors_data:
             logger.warning(f"No valid vendor data found in the file after processing rows.")
             # Depending on requirements, could raise an error here or return empty list
             # raise ValueError(f"No valid vendor names found in column '{column_map['vendor_name']}'.")

    except KeyError as e:
        logger.error(f"Internal Error: KeyError accessing column '{e}' after it was seemingly mapped.",
                     extra={"column_map": column_map, "available_columns": detected_columns})
        raise ValueError(f"Internal error accessing column '{e}'.")
    except Exception as e:
        logger.error(f"Error extracting or processing data from file rows", exc_info=True)
        raise ValueError(f"Could not extract vendor data. Please check data format. Error: {e}")

    return vendors_data
    # --- End Extract data ---


@log_function_call(logger)
def normalize_vendor_data(vendors_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]: # <--- MODIFIED function name and type hint
    """
    Normalize vendor names within the list of dictionaries by converting
    to title case and stripping whitespace. Filters out entries with
    empty names after normalization.

    Args:
        vendors_data: List of dictionaries, each containing vendor data.

    Returns:
        List of dictionaries with normalized vendor names.
    """
    start_count = len(vendors_data)
    logger.info(f"Normalizing vendor names for {start_count} entries...")

    normalized_vendors_data = []
    empty_removed_count = 0

    with LogTimer(logger, "Vendor name normalization", include_in_stats=True):
        for entry in vendors_data:
            original_name = entry.get('vendor_name')
            if isinstance(original_name, str):
                # Strip whitespace first, then title case
                normalized_name = original_name.strip().title()
                if normalized_name: # Check if non-empty after stripping/casing
                    # Create a new dict or modify in place - creating new is safer
                    normalized_entry = entry.copy()
                    normalized_entry['vendor_name'] = normalized_name
                    normalized_vendors_data.append(normalized_entry)
                else:
                    empty_removed_count += 1
                    logger.warning("Skipping vendor entry due to empty name after normalization", extra={"original_name": original_name})
            else:
                # Handle non-string or missing names
                logger.warning("Skipping vendor entry due to missing or non-string name during normalization", extra={"entry": entry})
                empty_removed_count += 1

    final_count = len(normalized_vendors_data)
    logger.info(f"Vendor names normalized.",
               extra={
                   "original_count": start_count,
                   "normalized_count": final_count,
                   "empty_or_skipped": empty_removed_count
               })

    return normalized_vendors_data


@log_function_call(logger)
def generate_output_file(
    original_vendor_data: List[Dict[str, Any]], # <--- MODIFIED: Use original data list
    classification_results: Dict[str, Dict], # Results keyed by *unique* normalized names
    job_id: str
) -> str:
    """
    Generate output Excel file with classification results, mapping back to
    original vendor data including optional fields.

    Args:
        original_vendor_data: Original list of vendor dictionaries from the input file (normalized names).
        classification_results: Classification results keyed by unique, normalized vendor names.
        job_id: Job ID

    Returns:
        File name of the generated output file (not the full path).

    Raises:
        IOError: If the file cannot be written.
    """
    logger.info(f"Generating output file for {len(original_vendor_data)} original vendor entries",
               extra={"job_id": job_id})

    output_data = []
    # Temporary mapping from normalized name back to results for efficiency
    # Ensure keys in classification_results are also normalized consistently
    normalized_to_result = {str(vendor).strip().title(): res for vendor, res in classification_results.items() if isinstance(vendor, str)}

    with LogTimer(logger, "Mapping results to original vendors"):
        for original_entry in original_vendor_data:
            original_vendor_name = original_entry.get('vendor_name', '') # Get normalized name
            original_description = original_entry.get('description') # Get original optional description
            original_example = original_entry.get('example') # Get original optional example

            # The key to lookup results *is* the normalized name
            normalized_key = original_vendor_name

            result = normalized_to_result.get(normalized_key, {}) # Get results using normalized key

            # --- Safely access nested results using .get() ---
            level1 = result.get("level1", {})
            level2 = result.get("level2", {})
            level3 = result.get("level3", {})
            level4 = result.get("level4", {})
            search_results_data = result.get("search_results", {})
            search_classification = search_results_data.get("classification", {})

            # Determine final classification status and reason
            final_classification_possible_l4 = level4.get("category_id") and level4.get("category_id") not in ["N/A", "ERROR"]
            classification_not_possible_flag = True # Assume impossible unless proven otherwise
            reason = "Not fully classified" # Default reason
            final_notes = ""
            final_confidence = 0.0
            final_level1_id = level1.get("category_id", "")
            final_level1_name = level1.get("category_name", "")
            final_level2_id = level2.get("category_id", "")
            final_level2_name = level2.get("category_name", "")
            final_level3_id = level3.get("category_id", "")
            final_level3_name = level3.get("category_name", "")
            final_level4_id = level4.get("category_id", "")
            final_level4_name = level4.get("category_name", "")


            if final_classification_possible_l4:
                classification_not_possible_flag = False
                reason = None
                final_notes = level4.get("notes", "")
                final_confidence = level4.get("confidence", 0.0)
                # Keep L1-L4 as they are
            elif search_classification and not search_classification.get("classification_not_possible", True):
                 # If search provided a valid L1 classification, use that as the 'best' result
                 classification_not_possible_flag = False # Mark as classified (at least L1)
                 reason = None
                 final_notes = f"Classified via search: {search_classification.get('notes', '')}"
                 final_confidence = search_classification.get("confidence", 0.0) # Use L1 confidence from search
                 # Overwrite L1, clear L2-L4
                 final_level1_id = search_classification.get("category_id", "")
                 final_level1_name = search_classification.get("category_name", "")
                 final_level2_id = ""
                 final_level2_name = ""
                 final_level3_id = ""
                 final_level3_name = ""
                 final_level4_id = ""
                 final_level4_name = ""
            else:
                # Find the first level where classification failed, if any
                failure_reason_found = False
                for lvl in range(1, 5):
                     lvl_res = result.get(f"level{lvl}", {})
                     if lvl_res.get("classification_not_possible", False):
                          reason = lvl_res.get("classification_not_possible_reason", f"Classification failed at Level {lvl}")
                          final_notes = lvl_res.get("notes", "") # Use notes from the failed level if available
                          failure_reason_found = True
                          break
                if not failure_reason_found: # If no level explicitly failed, check search results reason
                     if search_classification and search_classification.get("classification_not_possible", False):
                           reason = search_classification.get("classification_not_possible_reason", "Search did not yield classification")
                           final_notes = search_classification.get("notes", "")
                     elif search_results_data.get("error"):
                           reason = f"Search error: {search_results_data.get('error')}"
                     # else 'Not fully classified' remains

            row = {
                "vendor_name": original_vendor_name, # Use the normalized name from the input data
                "Optional_vendor_description": original_description or "", # Include original description
                "Optional_example_good_serviced_purchased": original_example or "", # Include original example
                "level1_category_id": final_level1_id,
                "level1_category_name": final_level1_name,
                "level2_category_id": final_level2_id,
                "level2_category_name": final_level2_name,
                "level3_category_id": final_level3_id,
                "level3_category_name": final_level3_name,
                "level4_category_id": final_level4_id,
                "level4_category_name": final_level4_name,
                "final_confidence": final_confidence,
                "classification_not_possible": classification_not_possible_flag,
                "classification_notes_or_reason": reason or final_notes or "", # Provide reason if failed, else notes
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
        # --- Define column order explicitly ---
        output_columns = [
            "vendor_name",
            "Optional_vendor_description",
            "Optional_example_good_serviced_purchased",
            "level1_category_id",
            "level1_category_name",
            "level2_category_id",
            "level2_category_name",
            "level3_category_id",
            "level3_category_name",
            "level4_category_id",
            "level4_category_name",
            "final_confidence",
            "classification_not_possible",
            "classification_notes_or_reason",
            "sources"
        ]
        df = pd.DataFrame(output_data, columns=output_columns)
        # --- End Define column order ---


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
