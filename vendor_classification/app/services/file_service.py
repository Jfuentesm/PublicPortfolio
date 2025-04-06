
# app/services/file_service.py
import os
import pandas as pd
from fastapi import UploadFile
import shutil
from typing import List, Dict, Any, Optional, Set
import uuid
import logging
from datetime import datetime

from core.config import settings
# Import logger and context functions from refactored modules
from core.logging_config import get_logger
from core.log_context import set_log_context
# Import log helpers from utils
from utils.log_utils import LogTimer, log_function_call

# Configure logger
logger = get_logger("vendor_classification.file_service")

# --- Define expected column names (case-insensitive matching) ---
VENDOR_NAME_COL = 'vendor_name'
OPTIONAL_EXAMPLE_COL = 'optional_example_good_serviced_purchased'
OPTIONAL_ADDRESS_COL = 'vendor_address'
OPTIONAL_WEBSITE_COL = 'vendor_website'
OPTIONAL_INTERNAL_CAT_COL = 'internal_category'
OPTIONAL_PARENT_CO_COL = 'parent_company'
OPTIONAL_SPEND_CAT_COL = 'spend_category'
# --- End Define expected column names ---

@log_function_call(logger, include_args=False) # Keep args=False for UploadFile
def save_upload_file(file: UploadFile, job_id: str) -> str:
    """
    Save uploaded file to the input directory.
    """
    job_dir = os.path.join(settings.INPUT_DATA_DIR, job_id)
    try:
        os.makedirs(job_dir, exist_ok=True)
        logger.debug(f"Ensured job directory exists", extra={"directory": job_dir})
    except OSError as e:
        logger.error(f"Failed to create job directory", exc_info=True, extra={"directory": job_dir})
        raise IOError(f"Could not create directory for job {job_id}: {e}")

    safe_filename = os.path.basename(file.filename or f"upload_{job_id}.tmp")
    if not safe_filename:
         safe_filename = f"upload_{job_id}.tmp"

    file_path = os.path.join(job_dir, safe_filename)
    logger.info("Attempting to save file", extra={"path": file_path})

    with LogTimer(logger, "File saving"):
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            logger.error("Failed to save uploaded file content", exc_info=True, extra={"file_path": file_path})
            if os.path.exists(file_path):
                 try: os.remove(file_path)
                 except OSError: logger.warning("Could not remove partially written file on error.", extra={"file_path": file_path})
            raise IOError(f"Could not save uploaded file content: {e}")
        finally:
            if hasattr(file, 'close') and callable(file.close):
                file.close()

    try:
        file_size = os.path.getsize(file_path)
        logger.info(f"File saved successfully",
                   extra={"path": file_path, "size_bytes": file_size})
    except OSError as e:
        logger.warning(f"Could not get size of saved file", exc_info=False, extra={"file_path": file_path, "error": str(e)})
        file_size = -1

    return file_path


@log_function_call(logger)
def read_vendor_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Read vendor data from Excel file, looking for mandatory 'vendor_name'
    and several optional context columns (case-insensitively).
    """
    logger.info(f"Reading Excel file for vendor data", extra={"file_path": file_path})

    if not os.path.exists(file_path):
         logger.error(f"Input file not found at path", extra={"file_path": file_path})
         raise FileNotFoundError(f"Input file not found at path: {file_path}")

    with LogTimer(logger, "Excel file reading", include_in_stats=True):
        try:
            df = pd.read_excel(file_path, header=0)
            detected_columns = list(df.columns)
            logger.debug(f"Successfully read Excel file. Columns detected: {detected_columns}")
        except Exception as e:
            logger.error(f"Error reading Excel file with pandas", exc_info=True,
                        extra={"file_path": file_path})
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
    optional_cols = {
        'example': OPTIONAL_EXAMPLE_COL,
        'address': OPTIONAL_ADDRESS_COL,
        'website': OPTIONAL_WEBSITE_COL,
        'internal_cat': OPTIONAL_INTERNAL_CAT_COL,
        'parent_co': OPTIONAL_PARENT_CO_COL,
        'spend_cat': OPTIONAL_SPEND_CAT_COL
    }
    for key, col_name in optional_cols.items():
        if col_name in normalized_detected_columns:
            column_map[key] = normalized_detected_columns[col_name]
            logger.info(f"Found optional column '{col_name}' as: '{column_map[key]}'")
        else:
            logger.info(f"Optional column '{col_name}' not found.")
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
                    value = str(raw_value).strip() if pd.notna(raw_value) and str(raw_value).strip() else None
                    if value:
                        output_key = key
                        if key == 'example': output_key = 'example'
                        elif key == 'address': output_key = 'vendor_address'
                        elif key == 'website': output_key = 'vendor_website'
                        elif key == 'internal_cat': output_key = 'internal_category'
                        elif key == 'parent_co': output_key = 'parent_company'
                        elif key == 'spend_cat': output_key = 'spend_category'
                        vendor_entry[output_key] = value

            vendors_data.append(vendor_entry)
            processed_count += 1

        logger.info(f"Extracted data for {processed_count} vendors. Skipped {skipped_count} rows due to missing/invalid vendor name.")
        if not vendors_data:
             logger.warning(f"No valid vendor data found in the file after processing rows.")

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
def normalize_vendor_data(vendors_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize vendor names within the list of dictionaries by converting
    to title case and stripping whitespace. Filters out entries with
    empty names after normalization. Preserves other fields.
    """
    start_count = len(vendors_data)
    logger.info(f"Normalizing vendor names for {start_count} entries...")

    normalized_vendors_data = []
    empty_removed_count = 0

    with LogTimer(logger, "Vendor name normalization", include_in_stats=True):
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
                    logger.warning("Skipping vendor entry due to empty name after normalization", extra={"original_name": original_name})
            else:
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
    original_vendor_data: List[Dict[str, Any]],
    classification_results: Dict[str, Dict],
    job_id: str
) -> str:
    """
    Generate output Excel file with classification results (up to Level 5), mapping back to
    original vendor data including optional fields read from the input.
    """
    logger.info(f"Generating output file for {len(original_vendor_data)} original vendor entries",
               extra={"job_id": job_id})

    output_data = []

    with LogTimer(logger, "Mapping results to original vendors"):
        for original_entry in original_vendor_data:
            original_vendor_name = original_entry.get('vendor_name', '')
            result = classification_results.get(original_vendor_name, {})

            final_level1_id = ""; final_level1_name = ""
            final_level2_id = ""; final_level2_name = ""
            final_level3_id = ""; final_level3_name = ""
            final_level4_id = ""; final_level4_name = ""
            final_level5_id = ""; final_level5_name = ""
            final_confidence = 0.0
            classification_not_possible_flag = True
            final_notes = ""
            reason = "Classification not possible"
            classification_source = "Initial"

            highest_successful_level = 0
            for level in range(5, 0, -1):
                level_key = f"level{level}"
                level_res = result.get(level_key)
                if level_res and isinstance(level_res, dict) and not level_res.get("classification_not_possible", True):
                    highest_successful_level = level
                    break

            if highest_successful_level > 0:
                classification_not_possible_flag = False
                reason = None
                final_confidence = result[f"level{highest_successful_level}"].get("confidence", 0.0)
                final_notes = result[f"level{highest_successful_level}"].get("notes", "")

                for level in range(1, highest_successful_level + 1):
                    level_res = result.get(f"level{level}", {})
                    if level == 1: final_level1_id = level_res.get("category_id", ""); final_level1_name = level_res.get("category_name", "")
                    elif level == 2: final_level2_id = level_res.get("category_id", ""); final_level2_name = level_res.get("category_name", "")
                    elif level == 3: final_level3_id = level_res.get("category_id", ""); final_level3_name = level_res.get("category_name", "")
                    elif level == 4: final_level4_id = level_res.get("category_id", ""); final_level4_name = level_res.get("category_name", "")
                    elif level == 5: final_level5_id = level_res.get("category_id", ""); final_level5_name = level_res.get("category_name", "")

                if result.get("classified_via_search"):
                    classification_source = "Search"
                    final_notes = f"Classified via search: {final_notes}"

            else: # No level was successfully classified
                classification_not_possible_flag = True
                final_confidence = 0.0
                failure_reason_found = False
                for level in range(5, 0, -1):
                     level_res = result.get(f"level{level}")
                     if level_res and isinstance(level_res, dict) and level_res.get("classification_not_possible", False):
                          reason = level_res.get("classification_not_possible_reason", f"Classification failed at Level {level}")
                          final_notes = level_res.get("notes", "")
                          failure_reason_found = True
                          break
                if not failure_reason_found:
                     if result.get("search_attempted"):
                          search_l1_result = result.get("search_results", {}).get("classification_l1", {})
                          if search_l1_result and search_l1_result.get("classification_not_possible", False):
                               reason = search_l1_result.get("classification_not_possible_reason", "Search did not yield classification")
                               final_notes = search_l1_result.get("notes", "")
                          elif result.get("search_results", {}).get("error"):
                               reason = f"Search error: {result['search_results']['error']}"

            original_address = original_entry.get('vendor_address')
            original_website = original_entry.get('vendor_website')
            original_internal_cat = original_entry.get('internal_category')
            original_parent_co = original_entry.get('parent_company')
            original_spend_cat = original_entry.get('spend_category')
            original_example = original_entry.get('example')

            search_sources_urls = ""
            search_data = result.get("search_results", {})
            if search_data and isinstance(search_data.get("sources"), list):
                 search_sources_urls = ", ".join(
                     source.get("url", "") for source in search_data["sources"] if isinstance(source, dict) and source.get("url")
                 )

            row = {
                "vendor_name": original_vendor_name,
                "vendor_address": original_address or "",
                "vendor_website": original_website or "",
                "internal_category": original_internal_cat or "",
                "parent_company": original_parent_co or "",
                "spend_category": original_spend_cat or "",
                "Optional_example_good_serviced_purchased": original_example or "",
                "level1_category_id": final_level1_id, "level1_category_name": final_level1_name,
                "level2_category_id": final_level2_id, "level2_category_name": final_level2_name,
                "level3_category_id": final_level3_id, "level3_category_name": final_level3_name,
                "level4_category_id": final_level4_id, "level4_category_name": final_level4_name,
                "level5_category_id": final_level5_id, "level5_category_name": final_level5_name,
                "final_confidence": final_confidence,
                "classification_not_possible": classification_not_possible_flag,
                "classification_notes_or_reason": reason or final_notes or "",
                "classification_source": classification_source,
                "sources": search_sources_urls
            }
            output_data.append(row)

    output_columns = [
        "vendor_name", "vendor_address", "vendor_website", "internal_category", "parent_company", "spend_category",
        "Optional_example_good_serviced_purchased",
        "level1_category_id", "level1_category_name", "level2_category_id", "level2_category_name",
        "level3_category_id", "level3_category_name", "level4_category_id", "level4_category_name",
        "level5_category_id", "level5_category_name",
        "final_confidence", "classification_not_possible", "classification_notes_or_reason",
        "classification_source", "sources"
    ]
    if not output_data:
        logger.warning("No data rows generated for the output file.")
        df = pd.DataFrame(columns=output_columns)
    else:
        with LogTimer(logger, "Creating DataFrame for output"):
            df = pd.DataFrame(output_data, columns=output_columns)

    output_dir = os.path.join(settings.OUTPUT_DATA_DIR, job_id)
    try:
        os.makedirs(output_dir, exist_ok=True)
        logger.debug(f"Ensured output directory exists", extra={"directory": output_dir})
    except OSError as e:
        logger.error(f"Failed to create output directory", exc_info=True, extra={"directory": output_dir})
        raise IOError(f"Could not create output directory for job {job_id}: {e}")

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file_name = f"classification_results_{job_id[:8]}_{timestamp_str}.xlsx"
    output_path = os.path.join(output_dir, output_file_name)

    logger.info("Attempting to write final results to Excel file.", extra={"output_path": output_path})
    with LogTimer(logger, "Writing Excel file"):
        try:
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

    return output_file_name