# <file path='app/services/file_service.py'>
# app/services/file_service.py
import os
import pandas as pd
from fastapi import UploadFile
import shutil
from typing import List, Dict, Any, Optional, Set
import uuid
import logging
from datetime import datetime
import io # Added for reading UploadFile in memory

from core.config import settings
# Import logger and context functions from refactored modules
from core.logging_config import get_logger
from core.log_context import set_log_context
# Import log helpers from utils
from utils.log_utils import LogTimer, log_function_call
# Import JobResultItem for type hinting
from schemas.job import JobResultItem

# Configure logger
logger = get_logger("vendor_classification.file_service")

# --- Define expected column names (case-insensitive matching) ---
VENDOR_NAME_COL = 'vendor_name'
# --- ADDED: List of all optional columns for easier checking ---
OPTIONAL_COLS_LOWER = {
    'optional_example_good_serviced_purchased',
    'vendor_address',
    'vendor_website',
    'internal_category',
    'parent_company',
    'spend_category'
}
# --- END ADDED ---

# --- Keep original definitions for reference in read_vendor_file ---
OPTIONAL_EXAMPLE_COL = 'optional_example_good_serviced_purchased'
OPTIONAL_ADDRESS_COL = 'vendor_address'
OPTIONAL_WEBSITE_COL = 'vendor_website'
OPTIONAL_INTERNAL_CAT_COL = 'internal_category'
OPTIONAL_PARENT_CO_COL = 'parent_company'
OPTIONAL_SPEND_CAT_COL = 'spend_category'
# --- End Define expected column names ---


# --- ADDED: Function to Validate File Header ---
@log_function_call(logger, include_args=False) # Keep args=False for UploadFile
def validate_file_header(file: UploadFile) -> Dict[str, Any]:
    """
    Reads only the header of an UploadFile (Excel) to validate its structure.

    Checks for:
    1. Readability as an Excel file.
    2. Presence of the mandatory 'vendor_name' column (case-insensitive).

    Returns a dictionary with validation status and detected columns.
    """
    log_extra = {"uploaded_filename": file.filename} # Renamed from 'filename'
    logger.info("Starting file header validation", extra=log_extra)

    result = {
        "is_valid": False,
        "message": "Validation not completed.",
        "detected_columns": [],
        "missing_mandatory_columns": []
    }

    try:
        # Read only the header row (or first few rows) to get columns
        # Using BytesIO to read from the UploadFile's stream in memory
        # Important: We read the stream here. If this same UploadFile object
        # needs to be read again later (e.g., in the main upload endpoint
        # without re-uploading), its stream position needs to be reset (await file.seek(0)).
        # However, the typical flow is validate -> frontend -> upload, which are separate requests.
        file_content = file.file.read()
        file.file.seek(0) # Reset stream position in case it's needed elsewhere (though unlikely in this flow)

        # --- FIX: Remove 'extra' from LogTimer call ---
        # The LogTimer class does not accept the 'extra' argument based on the TypeError.
        # Context logging should still capture the filename via log_extra used in logger calls.
        with LogTimer(logger, "Header read (pandas)"):
        # --- END FIX ---
            # nrows=0 reads only the header, nrows=1 reads header + first data row etc.
            # Using nrows=0 is sufficient and fastest for just column names.
            df_header = pd.read_excel(io.BytesIO(file_content), header=0, nrows=0)

        detected_columns_raw = list(df_header.columns)
        # Convert all column names to string for safety
        detected_columns = [str(col) for col in detected_columns_raw]
        result["detected_columns"] = detected_columns
        log_extra["detected_columns"] = detected_columns # Add detected columns to log_extra
        logger.debug(f"Detected columns: {detected_columns}", extra=log_extra)

        # --- Perform Validation ---
        normalized_detected_columns = {col.strip().lower(): col for col in detected_columns if isinstance(col, str)}

        # Check for mandatory column
        if VENDOR_NAME_COL not in normalized_detected_columns:
            result["is_valid"] = False
            result["message"] = f"Validation Failed: Mandatory column '{VENDOR_NAME_COL}' is missing (case-insensitive)."
            result["missing_mandatory_columns"] = [VENDOR_NAME_COL]
            logger.warning(f"Mandatory column '{VENDOR_NAME_COL}' missing.", extra=log_extra)
        else:
            result["is_valid"] = True
            result["message"] = f"Validation Successful: Found mandatory column '{normalized_detected_columns[VENDOR_NAME_COL]}'."
            # Optionally list found optional columns
            found_optional = [
                normalized_detected_columns[opt_col]
                for opt_col in OPTIONAL_COLS_LOWER
                if opt_col in normalized_detected_columns
            ]
            if found_optional:
                result["message"] += f" Found optional columns: {', '.join(found_optional)}."
            else:
                 result["message"] += " No optional context columns detected."
            logger.info("Mandatory column found.", extra=log_extra)

    except ValueError as e:
        # More specific error for pandas read errors
        logger.warning(f"Pandas ValueError during header read: {e}", extra=log_extra)
        result["message"] = f"File Read Error: Could not parse Excel header. Ensure it's a valid .xlsx or .xls file. Details: {str(e)[:100]}"
        raise ValueError(result["message"]) # Re-raise to be caught by API endpoint
    except Exception as e:
        logger.error(f"Unexpected error during header validation", exc_info=True, extra=log_extra)
        result["message"] = f"Internal Server Error: An unexpected error occurred during file validation. Details: {str(e)[:100]}"
        # Don't raise generic Exception here, let the endpoint handle it
        # Set is_valid to false as a precaution
        result["is_valid"] = False # Ensure invalid state on unexpected error

    return result
# --- END ADDED: Function to Validate File Header ---


@log_function_call(logger, include_args=False) # Keep args=False for UploadFile
def save_upload_file(file: UploadFile, job_id: str) -> str:
    """
    Save uploaded file to the input directory.
    """
    job_dir = os.path.join(settings.INPUT_DATA_DIR, job_id)
    log_extra = {"job_id": job_id} # Base log extra for this function
    try:
        os.makedirs(job_dir, exist_ok=True)
        logger.debug(f"Ensured job directory exists", extra={**log_extra, "directory": job_dir})
    except OSError as e:
        logger.error(f"Failed to create job directory", exc_info=True, extra={**log_extra, "directory": job_dir})
        raise IOError(f"Could not create directory for job {job_id}: {e}")

    safe_filename = os.path.basename(file.filename or f"upload_{job_id}.tmp")
    if not safe_filename:
         safe_filename = f"upload_{job_id}.tmp"

    file_path = os.path.join(job_dir, safe_filename)
    save_log_extra = {**log_extra, "path": file_path, "original_filename": file.filename}
    logger.info("Attempting to save file", extra=save_log_extra)

    # --- FIX: Remove 'extra' from LogTimer call ---
    with LogTimer(logger, "File saving"): # Removed extra=save_log_extra
    # --- END FIX ---
        try:
            # Ensure stream is at the beginning before copying
            # This is important if the stream was read previously (e.g., by validation
            # IF the same file object instance was somehow reused, which is not the case here)
            # await file.seek(0) # Use await for async file interface if needed, otherwise just file.seek(0)
            # For standard FastAPI UploadFile, file.file is a SpooledTemporaryFile (sync interface)
            file.file.seek(0)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            logger.error("Failed to save uploaded file content", exc_info=True, extra=save_log_extra)
            if os.path.exists(file_path):
                 try: os.remove(file_path)
                 except OSError: logger.warning("Could not remove partially written file on error.", extra=save_log_extra)
            raise IOError(f"Could not save uploaded file content: {e}")
        finally:
            # Close the underlying file handle of UploadFile
            if hasattr(file, 'close') and callable(file.close):
                try:
                    file.close()
                    logger.debug("Closed UploadFile stream after saving.", extra=save_log_extra)
                except Exception as close_err:
                    logger.warning(f"Error closing UploadFile stream: {close_err}", exc_info=False, extra=save_log_extra)


    try:
        file_size = os.path.getsize(file_path)
        logger.info(f"File saved successfully",
                   extra={**save_log_extra, "size_bytes": file_size})
    except OSError as e:
        logger.warning(f"Could not get size of saved file", exc_info=False, extra={**save_log_extra, "error": str(e)})
        file_size = -1

    return file_path


@log_function_call(logger)
def read_vendor_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Read vendor data from Excel file, looking for mandatory 'vendor_name'
    and several optional context columns (case-insensitively).
    """
    log_extra = {"file_path": file_path}
    logger.info(f"Reading Excel file for vendor data", extra=log_extra)

    if not os.path.exists(file_path):
         logger.error(f"Input file not found at path", extra=log_extra)
         raise FileNotFoundError(f"Input file not found at path: {file_path}")

    # --- FIX: Remove 'extra' from LogTimer call ---
    with LogTimer(logger, "Excel file reading", include_in_stats=True): # Removed extra=log_extra
    # --- END FIX ---
        try:
            # Read the entire file now
            df = pd.read_excel(file_path, header=0)
            detected_columns = list(df.columns)
            logger.debug(f"Successfully read Excel file. Columns detected: {detected_columns}", extra=log_extra)
        except Exception as e:
            logger.error(f"Error reading Excel file with pandas", exc_info=True, extra=log_extra)
            raise ValueError(f"Could not parse the Excel file. Please ensure it is a valid .xlsx or .xls file. Error details: {str(e)}")

    # --- Find columns case-insensitively ---
    column_map: Dict[str, Optional[str]] = {
        'vendor_name': None,
        'example': None,
        'address': None,
        'website': None,
        'internal_cat': None,
        'parent_co': None,
        'spend_cat': None
    }
    # Convert all detected columns to string for reliable matching
    normalized_detected_columns = {str(col).strip().lower(): str(col) for col in detected_columns if isinstance(col, (str, int, float))} # Allow numeric cols but treat as str

    # Find vendor_name (mandatory)
    if VENDOR_NAME_COL in normalized_detected_columns:
        column_map['vendor_name'] = normalized_detected_columns[VENDOR_NAME_COL]
        logger.info(f"Found mandatory column '{VENDOR_NAME_COL}' as: '{column_map['vendor_name']}'", extra=log_extra)
    else:
        logger.error(f"Required column '{VENDOR_NAME_COL}' not found in file.",
                    extra={**log_extra, "available_columns": detected_columns})
        # This error should ideally be caught by the pre-validation step now
        raise ValueError(f"Input Excel file must contain a column named '{VENDOR_NAME_COL}' (case-insensitive). Found columns: {', '.join(map(str, detected_columns))}")

    # Find optional columns (using original constants here)
    optional_cols = {
        'example': OPTIONAL_EXAMPLE_COL,
        'address': OPTIONAL_ADDRESS_COL,
        'website': OPTIONAL_WEBSITE_COL,
        'internal_cat': OPTIONAL_INTERNAL_CAT_COL,
        'parent_co': OPTIONAL_PARENT_CO_COL,
        'spend_cat': OPTIONAL_SPEND_CAT_COL
    }
    for key, col_name in optional_cols.items():
        # Check against the lowercased OPTIONAL_COLS_LOWER set for consistency
        if col_name.lower() in normalized_detected_columns:
            column_map[key] = normalized_detected_columns[col_name.lower()]
            logger.info(f"Found optional column '{col_name}' as: '{column_map[key]}'", extra=log_extra)
        else:
            logger.info(f"Optional column '{col_name}' not found.", extra=log_extra)
    # --- End Find columns ---

    # --- Extract data into list of dictionaries ---
    vendors_data: List[Dict[str, Any]] = []
    processed_count = 0
    skipped_count = 0

    try:
        for index, row in df.iterrows():
            vendor_name_raw = row.get(column_map['vendor_name'])
            vendor_name = str(vendor_name_raw).strip() if pd.notna(vendor_name_raw) and str(vendor_name_raw).strip() else None

            if not vendor_name or vendor_name.lower() in ['nan', 'none', 'null']:
                skipped_count += 1
                continue

            vendor_entry: Dict[str, Any] = {'vendor_name': vendor_name}

            # Add optional fields if found
            for key, mapped_col in column_map.items():
                if key != 'vendor_name' and mapped_col: # Check if optional column was found
                    raw_value = row.get(mapped_col)
                    # Ensure value is treated as string, handle potential NaN/None from Pandas
                    value = str(raw_value).strip() if pd.notna(raw_value) and str(raw_value).strip() else None
                    if value and value.lower() not in ['nan', 'none', 'null', '#n/a']: # Additional check for common excel non-values
                        output_key = key # Default key
                        # Map internal key back to original (or desired output) key name
                        if key == 'example': output_key = 'example' # Keep as 'example' if needed, or map to full name
                        elif key == 'address': output_key = 'vendor_address'
                        elif key == 'website': output_key = 'vendor_website'
                        elif key == 'internal_cat': output_key = 'internal_category'
                        elif key == 'parent_co': output_key = 'parent_company'
                        elif key == 'spend_cat': output_key = 'spend_category'
                        vendor_entry[output_key] = value

            vendors_data.append(vendor_entry)
            processed_count += 1

        logger.info(f"Extracted data for {processed_count} vendors. Skipped {skipped_count} rows due to missing/invalid vendor name.", extra=log_extra)
        if not vendors_data:
             logger.warning(f"No valid vendor data found in the file after processing rows.", extra=log_extra)

    except KeyError as e:
        logger.error(f"Internal Error: KeyError accessing column '{e}' after it was seemingly mapped.",
                     extra={**log_extra, "column_map": column_map, "available_columns": detected_columns})
        raise ValueError(f"Internal error accessing column '{e}'.")
    except Exception as e:
        logger.error(f"Error extracting or processing data from file rows", exc_info=True, extra=log_extra)
        raise ValueError(f"Could not extract vendor data. Please check data format. Error: {e}")

    return vendors_data
    # --- End Extract data ---


@log_function_call(logger)
def normalize_vendor_data(vendors_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize vendor names within the list of dictionaries by converting
    to title case and stripping whitespace. Filters out entries with
    empty names after normalization. Preserves other fields.
    """
    start_count = len(vendors_data)
    log_extra = {"original_count": start_count}
    logger.info(f"Normalizing vendor names for {start_count} entries...", extra=log_extra)

    normalized_vendors_data = []
    empty_removed_count = 0

    # --- FIX: Remove 'extra' from LogTimer call ---
    with LogTimer(logger, "Vendor name normalization", include_in_stats=True): # Removed extra=log_extra
    # --- END FIX ---
        for entry in vendors_data:
            original_name = entry.get('vendor_name')
            if isinstance(original_name, str):
                normalized_name = original_name.strip().title()
                if normalized_name:
                    normalized_entry = entry.copy()
                    normalized_entry['vendor_name'] = normalized_name
                    normalized_vendors_data.append(normalized_entry)
                else:
                    empty_removed_count += 1
                    # Avoid logging potentially large 'entry' in warning
                    logger.warning("Skipping vendor entry due to empty name after normalization", extra={"original_name": original_name})
            else:
                # Avoid logging potentially large 'entry' in warning
                logger.warning("Skipping vendor entry due to missing or non-string name during normalization", extra={"original_name": original_name})
                empty_removed_count += 1

    final_count = len(normalized_vendors_data)
    logger.info(f"Vendor names normalized.",
               extra={
                   "original_count": start_count,
                   "normalized_count": final_count,
                   "empty_or_skipped": empty_removed_count
               })

    return normalized_vendors_data


# --- UPDATED: generate_output_file to accept List[JobResultItem] ---
@log_function_call(logger)
def generate_output_file(
    job_id: str,
    detailed_results: List[JobResultItem]
) -> str:
    """
    Generate output Excel file directly from the List[JobResultItem] structure.
    This is used for initial generation and regeneration after merging.
    """
    log_extra = {"job_id": job_id, "result_item_count": len(detailed_results)}
    logger.info(f"Generating output file for job {job_id} using {len(detailed_results)} result items.",
               extra=log_extra)

    output_data = []

    # --- FIX: Remove 'extra' from LogTimer call ---
    with LogTimer(logger, "Processing JobResultItems for Excel"): # Removed extra=log_extra
    # --- END FIX ---
        for item in detailed_results:
            # Determine the reason/notes string based on status
            reason_or_notes = item.classification_notes_or_reason
            if item.final_status == "Not Possible" and not reason_or_notes:
                reason_or_notes = "Classification not possible" # Default reason if none provided
            elif item.final_status == "Error" and not reason_or_notes:
                 reason_or_notes = "Processing error occurred"

            # Determine classification_not_possible flag
            classification_not_possible_flag = item.final_status != "Classified"

            # TODO: How to get original optional fields (address, website, etc.)?
            # The JobResultItem schema currently doesn't store the original optional fields.
            # OPTION 1: Add these fields to JobResultItem schema and ensure they are populated during classification/review.
            # OPTION 2: Modify this function to re-read the original input file (less efficient, requires file path).
            # OPTION 3: Store the original input data alongside detailed_results in the Job model (maybe in stats or a new field).
            # For now, we'll leave these columns blank as the data isn't available in detailed_results.
            # This needs to be addressed for the output file to be complete.
            # --- Placeholder values ---
            original_address = ""
            original_website = ""
            original_internal_cat = ""
            original_parent_co = ""
            original_spend_cat = ""
            original_example = ""
            search_sources_urls = "" # This info is also not directly in JobResultItem, needs adding or separate storage.
            # --- End Placeholder values ---

            row = {
                "vendor_name": item.vendor_name,
                "vendor_address": original_address, # Placeholder
                "vendor_website": original_website, # Placeholder
                "internal_category": original_internal_cat, # Placeholder
                "parent_company": original_parent_co, # Placeholder
                "spend_category": original_spend_cat, # Placeholder
                "Optional_example_good_serviced_purchased": original_example, # Placeholder
                "level1_category_id": item.level1_id or "",
                "level1_category_name": item.level1_name or "",
                "level2_category_id": item.level2_id or "",
                "level2_category_name": item.level2_name or "",
                "level3_category_id": item.level3_id or "",
                "level3_category_name": item.level3_name or "",
                "level4_category_id": item.level4_id or "",
                "level4_category_name": item.level4_name or "",
                "level5_category_id": item.level5_id or "",
                "level5_category_name": item.level5_name or "",
                "final_confidence": item.final_confidence if item.final_confidence is not None else 0.0,
                "classification_not_possible": classification_not_possible_flag,
                "classification_notes_or_reason": reason_or_notes or "",
                "classification_source": item.classification_source or "Unknown",
                "sources": search_sources_urls # Placeholder
            }
            output_data.append(row)

    output_columns = [
        "vendor_name", "vendor_address", "vendor_website", "internal_category", "parent_company", "spend_category",
        "Optional_example_good_serviced_purchased", # Match the exact optional column name
        "level1_category_id", "level1_category_name", "level2_category_id", "level2_category_name",
        "level3_category_id", "level3_category_name", "level4_category_id", "level4_category_name",
        "level5_category_id", "level5_category_name",
        "final_confidence", "classification_not_possible", "classification_notes_or_reason",
        "classification_source", "sources"
    ]
    if not output_data:
        logger.warning("No data rows generated for the output file.", extra=log_extra)
        # Create empty DataFrame with correct columns if no results
        df = pd.DataFrame(columns=output_columns)
    else:
        # --- FIX: Remove 'extra' from LogTimer call ---
        with LogTimer(logger, "Creating DataFrame for output"): # Removed extra=log_extra
        # --- END FIX ---
            df = pd.DataFrame(output_data, columns=output_columns)

    output_dir = os.path.join(settings.OUTPUT_DATA_DIR, job_id)
    try:
        os.makedirs(output_dir, exist_ok=True)
        logger.debug(f"Ensured output directory exists", extra={**log_extra, "directory": output_dir})
    except OSError as e:
        logger.error(f"Failed to create output directory", exc_info=True, extra={**log_extra, "directory": output_dir})
        raise IOError(f"Could not create output directory for job {job_id}: {e}")

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Use a consistent base name, maybe incorporating 'merged' if applicable?
    output_file_name = f"classification_results_{job_id[:8]}_{timestamp_str}.xlsx"
    output_path = os.path.join(output_dir, output_file_name)

    output_log_extra = {**log_extra, "output_path": output_path, "output_filename": output_file_name}
    logger.info("Attempting to write final results to Excel file.", extra=output_log_extra)
    # --- FIX: Remove 'extra' from LogTimer call ---
    with LogTimer(logger, "Writing Excel file"): # Removed extra=output_log_extra
    # --- END FIX ---
        try:
            df.to_excel(output_path, index=False, engine='xlsxwriter')
        except Exception as e:
            logger.error("Failed to write output Excel file", exc_info=True, extra=output_log_extra)
            raise IOError(f"Could not write output file: {e}")

    try:
        file_size = os.path.getsize(output_path)
        logger.info(f"Output file generated successfully",
                   extra={**output_log_extra, "size_bytes": file_size})
    except OSError as e:
         logger.warning(f"Could not get size of generated output file", exc_info=False, extra={**output_log_extra, "error": str(e)})

    return output_file_name
# --- END UPDATED ---