from pydantic import BaseModel, Field
from typing import Dict, List, Optional

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
        return [
            TaxonomyCategory(id=cat_id, name=cat.name, description=cat.description)
            for cat_id, cat in self.categories.items()
        ]
    
    def get_level2_categories(self, parent_id: str) -> List[TaxonomyCategory]:
        """Get level 2 categories for a given parent."""
        if parent_id not in self.categories:
            return []
        
        return [
            TaxonomyCategory(id=cat_id, name=cat.name, description=cat.description)
            for cat_id, cat in self.categories[parent_id].children.items()
        ]
    
    def get_level3_categories(self, parent_id: str) -> List[TaxonomyCategory]:
        """Get level 3 categories for a given parent."""
        parent_parts = parent_id.split('.')
        if len(parent_parts) != 2:
            return []
        
        level1_id, level2_id = parent_parts
        if level1_id not in self.categories:
            return []
        
        if level2_id not in self.categories[level1_id].children:
            return []
        
        return [
            TaxonomyCategory(id=cat_id, name=cat.name, description=cat.description)
            for cat_id, cat in self.categories[level1_id].children[level2_id].children.items()
        ]
    
    def get_level4_categories(self, parent_id: str) -> List[TaxonomyCategory]:
        """Get level 4 categories for a given parent."""
        parent_parts = parent_id.split('.')
        if len(parent_parts) != 3:
            return []
        
        level1_id, level2_id, level3_id = parent_parts
        if level1_id not in self.categories:
            return []
        
        if level2_id not in self.categories[level1_id].children:
            return []
        
        if level3_id not in self.categories[level1_id].children[level2_id].children:
            return []
        
        return [
            TaxonomyCategory(id=cat_id, name=cat.name, description=cat.description)
            for cat_id, cat in self.categories[level1_id].children[level2_id].children[level3_id].children.items()
        ]
