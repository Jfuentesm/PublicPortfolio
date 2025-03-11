import os
import json
import logging
from typing import Dict, Any

from core.config import settings
from models.taxonomy import Taxonomy, TaxonomyLevel1, TaxonomyLevel2, TaxonomyLevel3, TaxonomyLevel4

def load_taxonomy() -> Taxonomy:
    """
    Load taxonomy data from file.
    
    Returns:
        Taxonomy object
    """
    taxonomy_path = os.path.join(settings.TAXONOMY_DATA_DIR, "naics_taxonomy.json")
    
    # Check if taxonomy file exists
    if not os.path.exists(taxonomy_path):
        # Create sample taxonomy if file doesn't exist
        taxonomy = create_sample_taxonomy()
        
        # Save sample taxonomy
        os.makedirs(settings.TAXONOMY_DATA_DIR, exist_ok=True)
        with open(taxonomy_path, "w") as f:
            json.dump(taxonomy.dict(), f, indent=2)
        
        return taxonomy
    
    # Load taxonomy from file
    try:
        with open(taxonomy_path, "r") as f:
            taxonomy_data = json.load(f)
        
        return Taxonomy(**taxonomy_data)
    
    except Exception as e:
        logging.error(f"Error loading taxonomy: {e}")
        # Create sample taxonomy as fallback
        return create_sample_taxonomy()

def create_sample_taxonomy() -> Taxonomy:
    """
    Create a sample NAICS taxonomy for testing.
    
    Returns:
        Taxonomy object
    """
    # Create level 4 categories
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
            children=level2_categories_51
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
