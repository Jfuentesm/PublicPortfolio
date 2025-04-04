# --- file path='app/models/taxonomy.py' ---
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import re # Added import

# --- ADDED: Import logger ---
from core.logging_config import get_logger
logger = get_logger("vendor_classification.taxonomy_model")
# --- END ADDED ---


class TaxonomyCategory(BaseModel):
    """Base taxonomy category model."""
    id: str
    name: str
    description: Optional[str] = None

# --- ADDED: Level 5 Model ---
class TaxonomyLevel5(TaxonomyCategory):
    """Level 5 taxonomy category (most specific - typically 6 digits)."""
    pass
# --- END ADDED ---

class TaxonomyLevel4(TaxonomyCategory):
    """Level 4 taxonomy category (typically 5 digits)."""
    # --- MODIFIED: Add children for Level 5 ---
    children: Dict[str, TaxonomyLevel5] = Field(default_factory=dict)
    # --- END MODIFIED ---

class TaxonomyLevel3(TaxonomyCategory):
    """Level 3 taxonomy category."""
    children: Dict[str, TaxonomyLevel4] = Field(default_factory=dict)

class TaxonomyLevel2(TaxonomyCategory):
    """Level 2 taxonomy category."""
    children: Dict[str, TaxonomyLevel3] = Field(default_factory=dict)

class TaxonomyLevel1(TaxonomyCategory):
    """Level 1 taxonomy category (most general)."""
    children: Dict[str, TaxonomyLevel2] = Field(default_factory=dict)

class Taxonomy(BaseModel):
    """Complete taxonomy model."""
    name: str
    version: str
    description: Optional[str] = None
    categories: Dict[str, TaxonomyLevel1] = Field(default_factory=dict)

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

    # --- ADDED: get_level5_categories ---
    def get_level5_categories(self, parent_id: str) -> List[TaxonomyCategory]:
        """Get level 5 categories for a given parent ID (expected format: L1.L2.L3.L4 or just L4 ID)."""
        logger.debug(f"get_level5_categories: Attempting to get children for L4 parent '{parent_id}'.")
        level1_id = None
        level2_id = None
        level3_id = None
        level4_id = None
        if '.' in parent_id:
            parts = parent_id.split('.')
            if len(parts) == 4:
                level1_id, level2_id, level3_id, level4_id = parts[0], parts[1], parts[2], parts[3]
            else:
                 logger.error(f"get_level5_categories: Invalid parent ID format '{parent_id}'. Expected 'L1.L2.L3.L4' or 'L4'.")
                 return []
        else:
            # Assume it's just the L4 ID - need to find its parents
            level4_id = parent_id
            found = False
            for l1_key, l1_node in self.categories.items():
                for l2_key, l2_node in getattr(l1_node, 'children', {}).items():
                    for l3_key, l3_node in getattr(l2_node, 'children', {}).items():
                        if level4_id in getattr(l3_node, 'children', {}):
                            level1_id = l1_key
                            level2_id = l2_key
                            level3_id = l3_key
                            found = True
                            break
                    if found: break
                if found: break
            if not found:
                 logger.warning(f"get_level5_categories: Could not find L1/L2/L3 parents for L4 ID '{level4_id}'.")
                 return []

        logger.debug(f"get_level5_categories: Parsed parent ID into L1='{level1_id}', L2='{level2_id}', L3='{level3_id}', L4='{level4_id}'.")

        # Traverse the hierarchy
        if level1_id not in self.categories:
            logger.warning(f"get_level5_categories: L1 parent ID '{level1_id}' not found.")
            return []
        level1_cat = self.categories[level1_id]

        if not hasattr(level1_cat, 'children') or level2_id not in level1_cat.children:
            logger.warning(f"get_level5_categories: L2 parent ID '{level2_id}' not found under L1 '{level1_id}'.")
            return []
        level2_cat = level1_cat.children[level2_id]

        if not hasattr(level2_cat, 'children') or level3_id not in level2_cat.children:
            logger.warning(f"get_level5_categories: L3 parent ID '{level3_id}' not found under L2 '{level2_id}'.")
            return []
        level3_cat = level2_cat.children[level3_id]

        if not hasattr(level3_cat, 'children') or level4_id not in level3_cat.children:
            logger.warning(f"get_level5_categories: L4 parent ID '{level4_id}' not found under L3 '{level3_id}'.")
            return []
        level4_cat = level3_cat.children[level4_id]

        # Get L5 children
        if not hasattr(level4_cat, 'children') or not level4_cat.children:
             logger.warning(f"get_level5_categories: Parent L4 category '{level4_id}' has no children dictionary or it is empty.")
             return []

        children_count = len(level4_cat.children)
        logger.debug(f"get_level5_categories: Found {children_count} L5 children for parent '{parent_id}'.")
        return [
            TaxonomyCategory(id=cat_id, name=cat.name, description=cat.description)
            for cat_id, cat in level4_cat.children.items()
        ]
    # --- END ADDED ---