import os
import json
import pandas as pd
from typing import Dict, Any

from core.config import settings
from models.taxonomy import Taxonomy, TaxonomyLevel1, TaxonomyLevel2, TaxonomyLevel3, TaxonomyLevel4
from core.logging_config import get_logger

# Configure logger
logger = get_logger("vendor_classification.taxonomy_loader")

def load_taxonomy() -> Taxonomy:
    """
    Load taxonomy data from Excel file.
    
    Returns:
        Taxonomy object
    """
    excel_path = os.path.join(settings.TAXONOMY_DATA_DIR, "2022_NAICS_Codes.xlsx")
    json_path = os.path.join(settings.TAXONOMY_DATA_DIR, "naics_taxonomy.json")
    
    # First try to load from Excel file
    if os.path.exists(excel_path):
        try:
            logger.info(f"Loading taxonomy from Excel file: {excel_path}")
            taxonomy = load_taxonomy_from_excel(excel_path)
            
            # Save as JSON for future use
            os.makedirs(settings.TAXONOMY_DATA_DIR, exist_ok=True)
            with open(json_path, "w") as f:
                json.dump(taxonomy.dict(), f, indent=2)
                
            logger.info(f"Taxonomy loaded from Excel with {len(taxonomy.categories)} top-level categories")
            return taxonomy
        except Exception as e:
            logger.error(f"Error loading taxonomy from Excel: {e}", exc_info=True)
            # If Excel loading fails, try JSON fallback
    
    # If Excel file doesn't exist or loading failed, try JSON
    if os.path.exists(json_path):
        try:
            logger.info(f"Loading taxonomy from JSON: {json_path}")
            with open(json_path, "r") as f:
                taxonomy_data = json.load(f)
            
            taxonomy = Taxonomy(**taxonomy_data)
            logger.info(f"Taxonomy loaded from JSON with {len(taxonomy.categories)} top-level categories")
            return taxonomy
        except Exception as e:
            logger.error(f"Error loading taxonomy from JSON: {e}", exc_info=True)
    
    # If all else fails, create a sample taxonomy
    logger.warning("Creating sample taxonomy as fallback")
    return create_sample_taxonomy()

def load_taxonomy_from_excel(file_path: str) -> Taxonomy:
    """
    Load taxonomy from Excel file.
    
    Args:
        file_path: Path to Excel file
        
    Returns:
        Taxonomy object
    """
    try:
        # Read Excel file
        logger.debug(f"Reading Excel file: {file_path}")
        
        try:
            # Try reading as Excel
            df = pd.read_excel(file_path)
            logger.debug(f"Successfully read Excel file with {len(df)} rows")
        except Exception as excel_error:
            # If Excel reading fails, try as CSV with pipe delimiter
            logger.warning(f"Failed to read as Excel, trying as pipe-delimited text: {str(excel_error)}")
            try:
                df = pd.read_csv(file_path, delimiter='|', quotechar='"')
                logger.debug(f"Successfully read pipe-delimited file with {len(df)} rows")
            except Exception as csv_error:
                # If both fail, raise original Excel error
                logger.error(f"Failed to read as pipe-delimited text: {str(csv_error)}")
                raise excel_error
        
        # Check columns and normalize format
        if all(col in df.columns for col in ['Seq. No.', '2022 NAICS US   Code', '2022 NAICS US Title', 'Description']):
            # Standard format with expected columns
            code_column = '2022 NAICS US   Code'
            title_column = '2022 NAICS US Title'
            desc_column = 'Description'
            logger.debug("Standard column format detected")
        elif len(df.columns) == 1 and '|' in str(df.iloc[0, 0]):
            # Single column with pipe-delimited values
            logger.debug("Pipe-delimited text in first column detected")
            # Split into new DataFrame
            new_df = pd.DataFrame()
            
            for idx, row in df.iterrows():
                text = row.iloc[0]
                if isinstance(text, str):
                    # Remove any surrounding quotes
                    if text.startswith('"') and text.endswith('"'):
                        text = text[1:-1]
                    
                    parts = text.split('|')
                    if len(parts) >= 4:
                        if idx == 0 and 'NAICS' in parts[1]:  # This is likely a header row
                            continue
                        
                        new_row = {
                            'Seq. No.': parts[0],
                            'NAICS Code': parts[1],
                            'Title': parts[2],
                            'Description': parts[3] if len(parts) > 3 else ''
                        }
                        new_df = pd.concat([new_df, pd.DataFrame([new_row])], ignore_index=True)
            
            df = new_df
            code_column = 'NAICS Code'
            title_column = 'Title'
            desc_column = 'Description'
            logger.debug(f"Parsed pipe-delimited data into {len(df)} rows")
        else:
            # Try to identify relevant columns by name patterns
            code_col = next((col for col in df.columns if 'NAICS' in col and 'Code' in col), None)
            title_col = next((col for col in df.columns if 'Title' in col), None)
            desc_col = next((col for col in df.columns if 'Description' in col or 'Desc' in col), None)
            
            if code_col and title_col:
                code_column = code_col
                title_column = title_col
                desc_column = desc_col if desc_col else 'Description'  # Use default if not found
                logger.debug(f"Identified columns by patterns: {code_column}, {title_column}, {desc_column}")
            else:
                error_msg = f"Could not identify required columns in the file"
                logger.error(error_msg, extra={"columns": list(df.columns)})
                raise ValueError(error_msg)
        
        # Clean data
        df = df.dropna(subset=[code_column])
        df[code_column] = df[code_column].astype(str).str.strip()
        
        # Clean title - remove trailing 'T' if present
        df[title_column] = df[title_column].astype(str).str.strip()
        df[title_column] = df[title_column].str.replace('T$', '', regex=True)
        
        # Fill missing descriptions
        if desc_column in df.columns:
            df[desc_column] = df[desc_column].fillna('').astype(str).str.strip()
        else:
            df[desc_column] = ''
        
        # Build taxonomy structure
        categories_level1 = {}
        categories_level2 = {}
        categories_level3 = {}
        categories_level4 = {}
        
        # Process each row
        rows_processed = 0
        for _, row in df.iterrows():
            code = row[code_column]
            title = row[title_column]
            description = row[desc_column] if desc_column in row else ''
            
            # Skip rows with invalid codes
            if not code or not code.strip().replace('.', '').isdigit():
                logger.debug(f"Skipping row with invalid code: {code}")
                continue
                
            # Clean code - remove any non-digit characters
            code = ''.join(c for c in code if c.isdigit())
            
            if not code:
                logger.debug(f"Skipping row with empty code after cleaning")
                continue
                
            rows_processed += 1
            
            # Determine level based on code length
            code_length = len(code)
            
            if code_length == 2:  # Level 1
                categories_level1[code] = TaxonomyLevel1(
                    id=code,
                    name=title,
                    description=description,
                    children={}
                )
            elif code_length == 3:  # Level 2
                parent_code = code[:2]
                categories_level2[code] = TaxonomyLevel2(
                    id=code,
                    name=title,
                    description=description,
                    children={}
                )
            elif code_length == 4:  # Level 3
                parent_code = code[:3]
                categories_level3[code] = TaxonomyLevel3(
                    id=code,
                    name=title,
                    description=description,
                    children={}
                )
            elif code_length >= 5:  # Level 4
                parent_code = code[:4]
                categories_level4[code] = TaxonomyLevel4(
                    id=code,
                    name=title,
                    description=description
                )
        
        if rows_processed == 0:
            error_msg = f"No valid taxonomy entries found in the file"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Connect level 4 to level 3
        for code, category in categories_level4.items():
            parent_code = code[:4]
            if parent_code in categories_level3:
                categories_level3[parent_code].children[code] = category
        
        # Connect level 3 to level 2
        for code, category in categories_level3.items():
            parent_code = code[:3]
            if parent_code in categories_level2:
                categories_level2[parent_code].children[code] = category
        
        # Connect level 2 to level 1
        for code, category in categories_level2.items():
            parent_code = code[:2]
            if parent_code in categories_level1:
                categories_level1[parent_code].children[code] = category
        
        # Create taxonomy
        taxonomy = Taxonomy(
            name="NAICS Taxonomy",
            version="2022",
            description="North American Industry Classification System",
            categories=categories_level1
        )
        
        # Log some stats
        logger.info(f"Taxonomy built with {len(categories_level1)} L1, {len(categories_level2)} L2, " +
                    f"{len(categories_level3)} L3, {len(categories_level4)} L4 categories")
        
        return taxonomy
    
    except Exception as e:
        logger.error(f"Error processing taxonomy file: {e}", exc_info=True)
        raise

# Keep the existing create_sample_taxonomy function unchanged
def create_sample_taxonomy() -> Taxonomy:
    """
    Create a sample NAICS taxonomy for testing.
    
    Returns:
        Taxonomy object
    """
    # Level 4 categories
    level4_categories_11 = {
        "11.11.111110": TaxonomyLevel4(
            id="11.11.111110",
            name="Soybean Farming",
            description="Industry comprising establishments primarily engaged in growing soybeans and/or producing soybean seeds."
        ),
        "11.11.111120": TaxonomyLevel4(
            id="11.11.111120",
            name="Oilseed (except Soybean) Farming",
            description="Industry comprising establishments primarily engaged in growing fibrous oilseed producing plants and/or producing oilseed seeds, such as sunflower, safflower, flax, rape, canola, and sesame."
        )
    }
    
    level4_categories_23 = {
        "23.23.236115": TaxonomyLevel4(
            id="23.23.236115",
            name="New Single-Family Housing Construction",
            description="Industry comprising establishments primarily responsible for the entire construction of new single-family housing, such as single-family detached houses and town houses or row houses where each housing unit is separated by a ground-to-roof wall and where no housing units are constructed above or below."
        ),
        "23.23.236116": TaxonomyLevel4(
            id="23.23.236116",
            name="New Multifamily Housing Construction",
            description="Industry comprising establishments primarily responsible for the construction of new multifamily residential housing units (e.g., high-rise, garden, town house apartments, and condominiums where each unit is not separated by a ground-to-roof wall)."
        )
    }
    
    level4_categories_51 = {
        "51.51.511210": TaxonomyLevel4(
            id="51.51.511210",
            name="Software Publishers",
            description="Industry comprising establishments primarily engaged in computer software publishing or publishing and reproduction. Establishments in this industry carry out operations necessary for producing and distributing computer software, such as designing, providing documentation, assisting in installation, and providing support services to software purchasers. These establishments may design, develop, and publish, or publish only."
        ),
        "51.51.518210": TaxonomyLevel4(
            id="51.51.518210",
            name="Data Processing, Hosting, and Related Services",
            description="Industry comprising establishments primarily engaged in providing infrastructure for hosting or data processing services."
        )
    }
    
    # Create level 3 categories
    level3_categories_11 = {
        "11.11": TaxonomyLevel3(
            id="11.11",
            name="Crop Production",
            description="Industry Group comprising establishments, such as farms, orchards, groves, greenhouses, and nurseries, primarily engaged in growing crops, plants, vines, or trees and their seeds.",
            children=level4_categories_11
        )
    }
    
    level3_categories_23 = {
        "23.23": TaxonomyLevel3(
            id="23.23",
            name="Building, Developing, and General Contracting",
            description="Industry Group comprising establishments primarily engaged in the construction of buildings or engineering projects (e.g., highways and utility systems).",
            children=level4_categories_23
        )
    }
    
    level3_categories_51 = {
        "51.51": TaxonomyLevel3(
            id="51.51",
            name="Information Services and Data Processing Services",
            description="Industry Group comprising establishments primarily engaged in providing information, storing and providing access to information, searching and retrieving information, operating Web sites that use search engines to allow for searching information on the Internet, or publishing and/or broadcasting content exclusively on the Internet.",
            children=level4_categories_51
        )
    }
    
    # Create level 2 categories
    level2_categories_11 = {
        "11": TaxonomyLevel2(
            id="11",
            name="Agriculture, Forestry, Fishing and Hunting",
            description="The Agriculture, Forestry, Fishing and Hunting sector comprises establishments primarily engaged in growing crops, raising animals, harvesting timber, and harvesting fish and other animals from a farm, ranch, or their natural habitats.",
            children=level3_categories_11
        )
    }
    
    level2_categories_23 = {
        "23": TaxonomyLevel2(
            id="23",
            name="Construction",
            description="The Construction sector comprises establishments primarily engaged in the construction of buildings or engineering projects (e.g., highways and utility systems).",
            children=level3_categories_23
        )
    }
    
    level2_categories_51 = {
        "51": TaxonomyLevel2(
            id="51",
            name="Information",
            description="The Information sector comprises establishments engaged in the following processes: (a) producing and distributing information and cultural products, (b) providing the means to transmit or distribute these products as well as data or communications, and (c) processing data.",
            children=level3_categories_51
        )
    }
    
    # Create level 1 categories
    level1_categories = {
        "11": TaxonomyLevel1(
            id="11",
            name="Agriculture, Forestry, Fishing and Hunting",
            description="The Agriculture, Forestry, Fishing and Hunting sector comprises establishments primarily engaged in growing crops, raising animals, harvesting timber, and harvesting fish and other animals from a farm, ranch, or their natural habitats.",
            children=level2_categories_11
        ),
        "23": TaxonomyLevel1(
            id="23",
            name="Construction",
            description="The Construction sector comprises establishments primarily engaged in the construction of buildings or engineering projects (e.g., highways and utility systems).",
            children=level2_categories_23
        ),
        "51": TaxonomyLevel1(
            id="51",
            name="Information",
            description="The Information sector comprises establishments engaged in the following processes: (a) producing and distributing information and cultural products, (b) providing the means to transmit or distribute these products as well as data or communications, and (c) processing data.",
            children=level3_categories_51
        )
    }
    
    # Create taxonomy
    taxonomy = Taxonomy(
        name="NAICS Taxonomy",
        version="2022",
        description="North American Industry Classification System",
        categories=level1_categories
    )
    
    return taxonomy