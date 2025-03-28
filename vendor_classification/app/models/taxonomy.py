# --- file path='app/models/taxonomy.py' ---
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

# --- ADDED: Import logger ---
from core.logging_config import get_logger
logger = get_logger("vendor_classification.taxonomy_model")
# --- END ADDED ---


class TaxonomyCategory(BaseModel):
    """Base taxonomy category model."""
    id: str
    name: str
    description: Optional[str] = None

class TaxonomyLevel4(TaxonomyCategory):
    """Level 4 taxonomy category (most specific)."""
    pass

class TaxonomyLevel3(TaxonomyCategory):
    """Level 3 taxonomy category."""
    children: Dict[str, TaxonomyLevel4]

class TaxonomyLevel2(TaxonomyCategory):
    """Level 2 taxonomy category."""
    children: Dict[str, TaxonomyLevel3]

class TaxonomyLevel1(TaxonomyCategory):
    """Level 1 taxonomy category (most general)."""
    children: Dict[str, TaxonomyLevel2]

class Taxonomy(BaseModel):
    """Complete taxonomy model."""
    name: str
    version: str
    description: Optional[str] = None
    categories: Dict[str, TaxonomyLevel1]

    def get_level1_categories(self) -> List[TaxonomyCategory]:
        """Get all level 1 categories."""
        logger.debug(f"get_level1_categories: Retrieving {len(self.categories)} L1 categories.")
        return [
            TaxonomyCategory(id=cat_id, name=cat.name, description=cat.description)
            for cat_id, cat in self.categories.items()
        ]

    def get_level2_categories(self, parent_id: str) -> List[TaxonomyCategory]:
        """Get level 2 categories for a given parent."""
        logger.debug(f"get_level2_categories: Attempting to get children for L1 parent '{parent_id}'.")
        if parent_id not in self.categories:
            logger.warning(f"get_level2_categories: Parent ID '{parent_id}' not found in L1 categories.")
            return []

        level1_cat = self.categories[parent_id]
        if not hasattr(level1_cat, 'children') or not level1_cat.children:
             logger.warning(f"get_level2_categories: Parent L1 category '{parent_id}' has no children dictionary or it is empty.")
             return []

        children_count = len(level1_cat.children)
        logger.debug(f"get_level2_categories: Found {children_count} L2 children for parent '{parent_id}'.")
        return [
            TaxonomyCategory(id=cat_id, name=cat.name, description=cat.description)
            for cat_id, cat in level1_cat.children.items()
        ]

    def get_level3_categories(self, parent_id: str) -> List[TaxonomyCategory]:
        """Get level 3 categories for a given parent ID (expected format: L1.L2 or just L2 ID)."""
        logger.debug(f"get_level3_categories: Attempting to get children for L2 parent '{parent_id}'.")
        # --- MODIFIED: Handle both L1.L2 and just L2 ---
        level1_id = None
        level2_id = None
        if '.' in parent_id:
            parts = parent_id.split('.')
            if len(parts) == 2:
                level1_id, level2_id = parts[0], parts[1]
            else:
                 logger.error(f"get_level3_categories: Invalid parent ID format '{parent_id}'. Expected 'L1.L2' or 'L2'.")
                 return []
        else:
            # Assume it's just the L2 ID - need to find its L1 parent
            level2_id = parent_id
            for l1_key, l1_node in self.categories.items():
                if level2_id in getattr(l1_node, 'children', {}):
                    level1_id = l1_key
                    break
            if not level1_id:
                logger.warning(f"get_level3_categories: Could not find L1 parent for L2 ID '{level2_id}'.")
                return []
        # --- END MODIFIED ---

        logger.debug(f"get_level3_categories: Parsed parent ID into L1='{level1_id}', L2='{level2_id}'.")

        if level1_id not in self.categories:
            logger.warning(f"get_level3_categories: L1 parent ID '{level1_id}' not found.")
            return []

        level1_cat = self.categories[level1_id]
        if not hasattr(level1_cat, 'children') or level2_id not in level1_cat.children:
             logger.warning(f"get_level3_categories: L2 parent ID '{level2_id}' not found under L1 '{level1_id}'.")
             return []

        level2_cat = level1_cat.children[level2_id]
        if not hasattr(level2_cat, 'children') or not level2_cat.children:
             logger.warning(f"get_level3_categories: Parent L2 category '{level2_id}' has no children dictionary or it is empty.")
             return []

        children_count = len(level2_cat.children)
        logger.debug(f"get_level3_categories: Found {children_count} L3 children for parent '{parent_id}'.")
        return [
            TaxonomyCategory(id=cat_id, name=cat.name, description=cat.description)
            for cat_id, cat in level2_cat.children.items()
        ]

    def get_level4_categories(self, parent_id: str) -> List[TaxonomyCategory]:
        """Get level 4 categories for a given parent ID (expected format: L1.L2.L3 or just L3 ID)."""
        logger.debug(f"get_level4_categories: Attempting to get children for L3 parent '{parent_id}'.")
        # --- MODIFIED: Handle both L1.L2.L3 and just L3 ---
        level1_id = None
        level2_id = None
        level3_id = None
        if '.' in parent_id:
            parts = parent_id.split('.')
            if len(parts) == 3:
                level1_id, level2_id, level3_id = parts[0], parts[1], parts[2]
            else:
                 logger.error(f"get_level4_categories: Invalid parent ID format '{parent_id}'. Expected 'L1.L2.L3' or 'L3'.")
                 return []
        else:
            # Assume it's just the L3 ID - need to find its L1/L2 parents
            level3_id = parent_id
            found = False
            for l1_key, l1_node in self.categories.items():
                for l2_key, l2_node in getattr(l1_node, 'children', {}).items():
                    if level3_id in getattr(l2_node, 'children', {}):
                        level1_id = l1_key
                        level2_id = l2_key
                        found = True
                        break
                if found:
                    break
            if not found:
                 logger.warning(f"get_level4_categories: Could not find L1/L2 parents for L3 ID '{level3_id}'.")
                 return []
        # --- END MODIFIED ---

        logger.debug(f"get_level4_categories: Parsed parent ID into L1='{level1_id}', L2='{level2_id}', L3='{level3_id}'.")

        if level1_id not in self.categories:
            logger.warning(f"get_level4_categories: L1 parent ID '{level1_id}' not found.")
            return []

        level1_cat = self.categories[level1_id]
        if not hasattr(level1_cat, 'children') or level2_id not in level1_cat.children:
            logger.warning(f"get_level4_categories: L2 parent ID '{level2_id}' not found under L1 '{level1_id}'.")
            return []

        level2_cat = level1_cat.children[level2_id]
        if not hasattr(level2_cat, 'children') or level3_id not in level2_cat.children:
            logger.warning(f"get_level4_categories: L3 parent ID '{level3_id}' not found under L2 '{level2_id}'.")
            return []

        level3_cat = level2_cat.children[level3_id]
        if not hasattr(level3_cat, 'children') or not level3_cat.children:
             logger.warning(f"get_level4_categories: Parent L3 category '{level3_id}' has no children dictionary or it is empty.")
             return []

        children_count = len(level3_cat.children)
        logger.debug(f"get_level4_categories: Found {children_count} L4 children for parent '{parent_id}'.")
        return [
            TaxonomyCategory(id=cat_id, name=cat.name, description=cat.description)
            for cat_id, cat in level3_cat.children.items()
        ]

# --- ADDED: Import re for fallback parsing ---
import re
# --- END ADDED ---