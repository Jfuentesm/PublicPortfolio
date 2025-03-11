import re
import unicodedata
from typing import List, Dict, Any

def normalize_vendor_name(name: str) -> str:
    """
    Normalize a vendor name by removing special characters, 
    standardizing whitespace, and converting to lowercase.
    
    Args:
        name: Vendor name to normalize
        
    Returns:
        Normalized vendor name
    """
    if not name or not isinstance(name, str):
        return ""
    
    # Convert to lowercase
    normalized = name.lower()
    
    # Normalize unicode characters
    normalized = unicodedata.normalize('NFKD', normalized)
    normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])
    
    # Remove legal entity indicators
    entity_indicators = [
        r'\bllc\b', r'\binc\b', r'\bltd\b', r'\bcorp\b', r'\bcorporation\b',
        r'\bco\b', r'\bcompany\b', r'\bgroup\b', r'\bholdings\b', r'\bservices\b',
        r'\bsolutions\b', r'\bsystems\b', r'\btechnologies\b', r'\btech\b',
        r'\benterprises\b', r'\blimited\b', r'\bpartners\b', r'\bassociates\b',
        r'\bgmbh\b', r'\bplc\b', r'\bpte\b', r'\bpty\b', r'\bag\b', r'\bsa\b',
        r'\bsrl\b', r'\bs\.r\.l\b', r'\bs\.p\.a\b', r'\bs\.a\b', r'\bs\.a\.s\b',
        r'\bb\.v\b', r'\blp\b', r'\bllp\b', r'\blp\b', r'\bl\.p\b', r'\bl\.l\.c\b',
        r'\bl\.l\.p\b', r'\bincorporated\b'
    ]
    
    for indicator in entity_indicators:
        normalized = re.sub(indicator, '', normalized)
    
    # Remove special characters and replace with space
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    
    # Replace multiple spaces with a single space
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Remove leading/trailing whitespace
    normalized = normalized.strip()
    
    return normalized

def normalize_vendor_names(vendors: List[str]) -> List[str]:
    """
    Normalize a list of vendor names.
    
    Args:
        vendors: List of vendor names
        
    Returns:
        List of normalized vendor names
    """
    return [normalize_vendor_name(vendor) for vendor in vendors]

def extract_vendor_names_from_dataframe(df: Any, column_name: str = 'vendor_name') -> List[str]:
    """
    Extract vendor names from a pandas DataFrame.
    
    Args:
        df: Pandas DataFrame
        column_name: Name of the column containing vendor names
        
    Returns:
        List of vendor names
    """
    if column_name not in df.columns:
        # Try to find a column that might contain vendor names
        potential_columns = [col for col in df.columns if 'vendor' in col.lower() or 'company' in col.lower()]
        
        if potential_columns:
            column_name = potential_columns[0]
        else:
            # Use the first column as a fallback
            column_name = df.columns[0]
    
    # Extract vendor names
    vendors = df[column_name].astype(str).tolist()
    
    # Filter out empty or NaN values
    vendors = [vendor for vendor in vendors if vendor and vendor.lower() != 'nan']
    
    return vendors
