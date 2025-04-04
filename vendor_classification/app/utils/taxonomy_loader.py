# <file path='app/utils/taxonomy_loader.py'>
# --- file path='app/utils/taxonomy_loader.py' ---
import os
import json
import pandas as pd
import re # <<< Added import
from typing import Dict, Any

# --- ADDED: Import logging for the main script part ---
import logging
# --- END ADDED ---

from core.config import settings
# --- MODIFIED IMPORT: Import all level classes including L5 ---
from models.taxonomy import Taxonomy, TaxonomyLevel1, TaxonomyLevel2, TaxonomyLevel3, TaxonomyLevel4, TaxonomyLevel5
# --- END MODIFIED IMPORT ---
from core.logging_config import get_logger

# Configure logger
logger = get_logger("vendor_classification.taxonomy_loader")

# --- Global cache for taxonomy ---
_taxonomy_cache: Taxonomy | None = None

def load_taxonomy(force_reload: bool = False) -> Taxonomy:
    """
    Load taxonomy data, using cache if available unless forced.
    Tries JSON first, then Excel as fallback.

    Args:
        force_reload: If True, bypass cache and reload from file.

    Returns:
        Taxonomy object

    Raises:
        FileNotFoundError: If neither JSON nor Excel file can be found.
        ValueError: If both JSON and Excel loading fail or result in empty taxonomy.
    """
    global _taxonomy_cache
    if _taxonomy_cache is not None and not force_reload:
        logger.info("Returning cached taxonomy.")
        return _taxonomy_cache

    excel_path = os.path.join(settings.TAXONOMY_DATA_DIR, "2022_NAICS_Codes.xlsx")
    json_path = os.path.join(settings.TAXONOMY_DATA_DIR, "naics_taxonomy.json")

    taxonomy = None

    # --- Try JSON first ---
    if os.path.exists(json_path):
        try:
            logger.info(f"Attempting to load taxonomy from JSON: {json_path}")
            with open(json_path, "r") as f:
                taxonomy_data = json.load(f)

            # Validate structure before creating Taxonomy object
            if not taxonomy_data.get("categories"):
                raise ValueError("JSON data is missing the 'categories' key.")

            taxonomy = Taxonomy(**taxonomy_data)
            logger.info(f"Taxonomy loaded successfully from JSON with {len(taxonomy.categories)} top-level categories.")
            _taxonomy_cache = taxonomy # Update cache
            return taxonomy
        except json.JSONDecodeError as json_err:
            logger.error(f"Failed to decode JSON from {json_path}: {json_err}", exc_info=False)
            logger.warning(f"JSON parsing failed. Will attempt fallback to Excel if available.")
        except Exception as e:
            logger.error(f"Error loading taxonomy from JSON: {e}", exc_info=True)
            logger.warning(f"Unexpected error loading JSON. Will attempt fallback to Excel if available.")
            taxonomy = None # Ensure taxonomy is None if JSON loading fails

    # --- Fallback to Excel if JSON failed or didn't exist ---
    if taxonomy is None and os.path.exists(excel_path):
        try:
            logger.warning(f"JSON load failed or file missing, attempting to load taxonomy from Excel: {excel_path}")
            taxonomy = load_taxonomy_from_excel(excel_path)

            # Save as JSON for future use IF successful
            logger.info(f"Saving newly loaded taxonomy to JSON: {json_path}")
            os.makedirs(settings.TAXONOMY_DATA_DIR, exist_ok=True)
            with open(json_path, "w") as f:
                # Use model_dump for Pydantic v2
                json.dump(taxonomy.model_dump(exclude_none=True, mode='json'), f, indent=2) # Added mode='json'

            logger.info(f"Taxonomy loaded successfully from Excel with {len(taxonomy.categories)} top-level categories and saved to JSON.")
            _taxonomy_cache = taxonomy # Update cache
            return taxonomy
        except Exception as e:
            logger.error(f"Error loading taxonomy from Excel after JSON failure: {e}", exc_info=True)
            taxonomy = None # Ensure taxonomy is None if Excel loading also fails

    # --- If both failed, raise error ---
    if taxonomy is None:
        error_msg = f"Failed to load taxonomy. Neither JSON ({json_path}) nor Excel ({excel_path}) file could be loaded or found."
        logger.critical(error_msg)
        raise FileNotFoundError(error_msg)

    # This part should theoretically not be reached if errors are raised correctly
    logger.critical("Reached unexpected end of load_taxonomy function.")
    raise RuntimeError("Taxonomy loading finished in an unexpected state.")


def load_taxonomy_from_excel(file_path: str) -> Taxonomy:
    """
    Load taxonomy from Excel file, building the hierarchical structure up to 5 levels.
    Correctly handles sector range titles.

    Args:
        file_path: Path to Excel file

    Returns:
        Taxonomy object

    Raises:
        FileNotFoundError: If the file_path does not exist.
        ValueError: If the file cannot be parsed or required columns are missing.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Taxonomy Excel file not found at {file_path}")

    try:
        # Read Excel file
        logger.debug(f"Reading Excel file: {file_path}")

        try:
            # Try reading as Excel first
            df = pd.read_excel(file_path, dtype=str) # Read all as string initially
            logger.debug(f"Successfully read Excel file with {len(df)} rows")
        except Exception as excel_error:
            # Fallback to CSV with pipe delimiter if Excel read fails
            logger.warning(f"Failed to read as Excel ({str(excel_error)}), trying as pipe-delimited text...")
            try:
                # Assuming the Excel file provided might actually be pipe-delimited
                df = pd.read_csv(file_path, delimiter='|', quotechar='"', dtype=str, skipinitialspace=True)
                logger.debug(f"Successfully read pipe-delimited file with {len(df)} rows")
            except Exception as csv_error:
                logger.error(f"Failed to read as pipe-delimited text: {str(csv_error)}")
                raise ValueError(f"Could not parse taxonomy file '{file_path}'. Tried Excel and Pipe-Delimited CSV.") from excel_error

        # --- Column Identification ---
        code_col_options = ['naics code', '2022 naics us code', 'code']
        title_col_options = ['naics title', '2022 naics us title', 'title']
        desc_col_options = ['description', 'desc']

        df_cols_lower = {col.lower().strip(): col for col in df.columns}

        code_column = next((df_cols_lower[opt] for opt in code_col_options if opt in df_cols_lower), None)
        title_column = next((df_cols_lower[opt] for opt in title_col_options if opt in df_cols_lower), None)
        desc_column = next((df_cols_lower[opt] for opt in desc_col_options if opt in df_cols_lower), None)

        if not code_column or not title_column:
            error_msg = f"Could not identify required 'code' and 'title' columns in the taxonomy file. Found columns: {list(df.columns)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        logger.info(f"Identified taxonomy columns - Code: '{code_column}', Title: '{title_column}', Desc: '{desc_column or 'None'}'")

        # --- Data Cleaning ---
        df = df.dropna(subset=[code_column])
        df[code_column] = df[code_column].astype(str).str.strip()
        df[title_column] = df[title_column].astype(str).str.strip().str.replace(r'\s*T$', '', regex=True) # Remove trailing 'T'

        if desc_column:
            df[desc_column] = df[desc_column].fillna('').astype(str).str.strip()
        else:
            desc_column = 'Description' # Assign a name
            df[desc_column] = ''
            logger.warning("No description column found, descriptions will be empty.")

        # --- Filter out rows with non-standard codes BEFORE processing ranges ---
        valid_code_pattern = r'^(\d{2}-\d{2}|\d+)$'
        original_row_count = len(df)
        df = df[df[code_column].str.match(valid_code_pattern)]
        filtered_row_count = len(df)
        if original_row_count != filtered_row_count:
            logger.warning(f"Filtered out {original_row_count - filtered_row_count} rows with invalid code formats (neither ##-## nor numeric).")

        # --- Build taxonomy structure ---
        categories_level1: Dict[str, TaxonomyLevel1] = {}
        logger.info("Building taxonomy hierarchy...")

        rows_processed = 0
        skipped_rows = 0
        for index, row in df.iterrows():
            code_raw = row[code_column].strip()
            title = row[title_column].strip()
            description = row[desc_column].strip()

            code = code_raw
            original_code = code_raw
            is_range = '-' in code

            # --- Range Handling ---
            if is_range:
                range_match = re.match(r'^(\d{2})-\d{2}$', code)
                if range_match:
                    start_code = range_match.group(1)
                    range_title = title
                    logger.debug(f"Row {index}: Processing range code '{original_code}' ('{range_title}') - Associating title with start code '{start_code}'")
                    if start_code not in categories_level1:
                        categories_level1[start_code] = TaxonomyLevel1(id=start_code, name=range_title, description=description, children={})
                        logger.info(f"Row {index}: Added L1 '{start_code}' using range title '{range_title}'.")
                    else:
                        existing_name = categories_level1[start_code].name
                        if existing_name != range_title:
                            logger.warning(f"Row {index}: L1 '{start_code}' already exists with name '{existing_name}'. Overwriting with range title '{range_title}'.")
                            categories_level1[start_code].name = range_title
                        if not categories_level1[start_code].description and description:
                             categories_level1[start_code].description = description
                             logger.debug(f"Row {index}: Updated empty L1 '{start_code}' description.")
                    rows_processed += 1
                    continue # Skip rest of hierarchy logic for this row
                else:
                    logger.warning(f"Row {index}: Skipping row with unhandled range format code: '{original_code}' ('{title}')")
                    skipped_rows += 1
                    continue
            elif not code.isdigit():
                logger.warning(f"Row {index}: Skipping row with non-numeric/non-range code: '{original_code}' ('{title}')")
                skipped_rows += 1
                continue
            # --- End Range Handling ---

            # --- Hierarchy Building for Numeric Codes ---
            code_length = len(code)
            try:
                if code_length == 2:  # Level 1 (Specific code)
                    if code not in categories_level1:
                        categories_level1[code] = TaxonomyLevel1(id=code, name=title, description=description, children={})
                        logger.debug(f"Row {index}: Added L1: {code} - {title}")
                    elif not categories_level1[code].description and description:
                        categories_level1[code].description = description
                        logger.debug(f"Row {index}: Updated L1 '{code}' description (already existed).")

                elif code_length == 3: # Level 2
                    l1_code = code[:2]
                    if l1_code in categories_level1:
                        l1_cat = categories_level1[l1_code]
                        if code not in l1_cat.children:
                            l1_cat.children[code] = TaxonomyLevel2(id=code, name=title, description=description, children={})
                            logger.debug(f"Row {index}:   Added L2: {code} under {l1_code}")
                    else:
                        logger.warning(f"Row {index}: L1 parent '{l1_code}' not found for L2 code '{code}' ('{title}'). Skipping.")
                        skipped_rows += 1; continue

                elif code_length == 4: # Level 3
                    l1_code = code[:2]; l2_code = code[:3]
                    if l1_code in categories_level1 and l2_code in categories_level1[l1_code].children:
                        l2_cat = categories_level1[l1_code].children[l2_code]
                        if code not in l2_cat.children:
                            l2_cat.children[code] = TaxonomyLevel3(id=code, name=title, description=description, children={})
                            logger.debug(f"Row {index}:     Added L3: {code} under {l2_code}")
                    else:
                        logger.warning(f"Row {index}: L1/L2 parent '{l1_code}/{l2_code}' not found for L3 code '{code}' ('{title}'). Skipping.")
                        skipped_rows += 1; continue

                elif code_length == 5: # Level 4
                    l1_code = code[:2]; l2_code = code[:3]; l3_code = code[:4]
                    if l1_code in categories_level1 and \
                       l2_code in categories_level1[l1_code].children and \
                       l3_code in categories_level1[l1_code].children[l2_code].children:
                        l3_cat = categories_level1[l1_code].children[l2_code].children[l3_code]
                        if code not in l3_cat.children:
                            # Create L4 with empty children dict for potential L5
                            l3_cat.children[code] = TaxonomyLevel4(id=code, name=title, description=description, children={})
                            logger.debug(f"Row {index}:       Added L4: {code} under {l3_code}")
                    else:
                        logger.warning(f"Row {index}: L1/L2/L3 parent '{l1_code}/{l2_code}/{l3_code}' not found for L4 code '{code}' ('{title}'). Skipping.")
                        skipped_rows += 1; continue

                elif code_length == 6: # Level 5
                    l1_code = code[:2]; l2_code = code[:3]; l3_code = code[:4]; l4_code = code[:5]
                    if l1_code in categories_level1 and \
                       l2_code in categories_level1[l1_code].children and \
                       l3_code in categories_level1[l1_code].children[l2_code].children and \
                       l4_code in categories_level1[l1_code].children[l2_code].children[l3_code].children:
                        l4_cat = categories_level1[l1_code].children[l2_code].children[l3_code].children[l4_code]
                        if code not in l4_cat.children:
                            l4_cat.children[code] = TaxonomyLevel5(id=code, name=title, description=description)
                            logger.debug(f"Row {index}:         Added L5: {code} under {l4_code}")
                    else:
                        logger.warning(f"Row {index}: L1/L2/L3/L4 parent '{l1_code}/{l2_code}/{l3_code}/{l4_code}' not found for L5 code '{code}' ('{title}'). Skipping.")
                        skipped_rows += 1; continue
                else:
                     logger.warning(f"Row {index}: Code '{code}' has unhandled length {code_length}. Skipping.")
                     skipped_rows += 1; continue

                rows_processed += 1

            except Exception as hierarchy_error:
                 logger.error(f"Row {index}: Error building hierarchy for code '{code}' ('{title}')", exc_info=True)
                 skipped_rows += 1

        if not categories_level1:
            error_msg = f"No valid Level 1 categories found after processing {rows_processed + skipped_rows} rows from the file."
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Create final taxonomy object
        taxonomy = Taxonomy(
            name="NAICS Taxonomy",
            version="2022", # Or extract from filename/content if possible
            description="North American Industry Classification System", # Or extract
            categories=categories_level1
        )

        # Log final stats including L5
        l1_count = len(taxonomy.categories)
        l2_count = sum(len(getattr(l1, 'children', {})) for l1 in taxonomy.categories.values())
        l3_count = sum(len(getattr(l2, 'children', {})) for l1 in taxonomy.categories.values() for l2 in getattr(l1, 'children', {}).values())
        l4_count = sum(len(getattr(l3, 'children', {})) for l1 in taxonomy.categories.values() for l2 in getattr(l1, 'children', {}).values() for l3 in getattr(l2, 'children', {}).values())
        l5_count = sum(len(getattr(l4, 'children', {})) for l1 in taxonomy.categories.values() for l2 in getattr(l1, 'children', {}).values() for l3 in getattr(l2, 'children', {}).values() for l4 in getattr(l3, 'children', {}).values())
        logger.info(f"Taxonomy hierarchy built with {l1_count} L1, {l2_count} L2, {l3_count} L3, {l4_count} L4, {l5_count} L5 categories from {rows_processed} processed rows ({skipped_rows} skipped).")

        return taxonomy

    except FileNotFoundError: # Raised explicitly above
        raise
    except ValueError as ve: # Raised explicitly above for parsing/column errors
         logger.error(f"Value error processing taxonomy Excel file '{file_path}': {ve}", exc_info=False)
         raise # Re-raise specific error
    except Exception as e:
        logger.error(f"Unexpected error processing taxonomy Excel file '{file_path}': {e}", exc_info=True)
        raise ValueError(f"Could not process taxonomy Excel file: {e}") from e


# --- create_sample_taxonomy function remains unchanged ---
# (It's a fallback and doesn't need L5 for this update)
def create_sample_taxonomy() -> Taxonomy:
    """
    Create a sample NAICS taxonomy for testing or fallback.
    (This function remains unchanged from the original provided code)
    """
    # Level 4 categories
    level4_categories_11 = {
        "111110": TaxonomyLevel4(id="111110", name="Soybean Farming", description="...", children={}), # Add empty children
        "111120": TaxonomyLevel4(id="111120", name="Oilseed (except Soybean) Farming", description="...", children={}),
    }
    # ... other sample L4 categories ...
    level4_categories_23 = { "236115": TaxonomyLevel4(id="236115", name="New Single-Family Housing Construction", description="...", children={}) }
    level4_categories_51 = { "513210": TaxonomyLevel4(id="513210", name="Software Publishers", description="...", children={}) }

    # Create level 3 categories
    level3_categories_11 = {
        "1111": TaxonomyLevel3(id="1111", name="Oilseed and Grain Farming", description="...", children=level4_categories_11),
    }
    level3_categories_23 = { "2361": TaxonomyLevel3(id="2361", name="Residential Building Construction", description="...", children=level4_categories_23) }
    level3_categories_51 = { "5132": TaxonomyLevel3(id="5132", name="Software Publishers", description="...", children=level3_categories_51) }


    # Create level 2 categories
    level2_categories_11 = {
        "111": TaxonomyLevel2(id="111", name="Crop Production", description="...", children=level3_categories_11),
    }
    level2_categories_23 = { "236": TaxonomyLevel2(id="236", name="Construction of Buildings", description="...", children=level3_categories_23) }
    level2_categories_51 = { "513": TaxonomyLevel2(id="513", name="Publishing Industries", description="...", children=level3_categories_51) }

    # Create level 1 categories
    level1_categories = {
        "11": TaxonomyLevel1(id="11", name="Agriculture, Forestry, Fishing and Hunting", description="...", children=level2_categories_11),
        "23": TaxonomyLevel1(id="23", name="Construction", description="...", children=level2_categories_23),
        "51": TaxonomyLevel1(id="51", name="Information", description="...", children=level2_categories_51)
    }

    # Create taxonomy
    taxonomy = Taxonomy(
        name="NAICS Taxonomy (Sample)",
        version="2022_Sample",
        description="Sample North American Industry Classification System",
        categories=level1_categories
    )
    logger.warning("Generated and using a sample taxonomy.")
    return taxonomy


if __name__ == "__main__":
     # --- ADDED: Import logging for test block ---
     import logging
     # --- END ADDED ---
     # Example usage for testing
     print("Testing taxonomy loader...")
     try:
         # Ensure settings are available or provide a default path
         if 'settings' not in locals() and 'settings' not in globals():
              class MockSettings:
                  TAXONOMY_DATA_DIR = os.path.join(os.path.dirname(__file__), '../../data/taxonomy')
              settings = MockSettings()
              print(f"Using mock settings for TAXONOMY_DATA_DIR: {settings.TAXONOMY_DATA_DIR}")
         else:
              if not hasattr(settings, 'TAXONOMY_DATA_DIR') or not settings.TAXONOMY_DATA_DIR:
                   settings.TAXONOMY_DATA_DIR = os.path.join(os.path.dirname(__file__), '../../data/taxonomy')
              print(f"Using settings.TAXONOMY_DATA_DIR: {settings.TAXONOMY_DATA_DIR}")

         # --- Ensure log directory exists for testing ---
         log_test_dir = "./logs_test"
         os.makedirs(log_test_dir, exist_ok=True)
         from core.logging_config import setup_logging
         setup_logging(log_level=logging.DEBUG, log_to_file=True, log_dir=log_test_dir, async_logging=False)
         # ---

         # Force reload from Excel (or CSV fallback)
         tax = load_taxonomy(force_reload=True)
         print(f"\nLoaded taxonomy: {tax.name} - Version: {tax.version}")
         print(f"Number of L1 categories: {len(tax.categories)}")

         # Verification for a specific L5 code (example)
         print("\n--- Verification for L5 Code (e.g., 311111) ---")
         try:
             l1 = tax.categories.get('31')
             l2 = l1.children.get('311') if l1 else None
             l3 = l2.children.get('3111') if l2 else None
             l4 = l3.children.get('31111') if l3 else None
             l5 = l4.children.get('311111') if l4 else None
             if l5:
                 print(f"L5 '311111' FOUND. Name: '{l5.name}'")
             else:
                 print("L5 '311111' NOT FOUND (or parent missing).")
         except Exception as e:
             print(f"Error during L5 verification: {e}")

     except Exception as e:
         print(f"\nError during testing: {e}")
         import traceback
         traceback.print_exc()