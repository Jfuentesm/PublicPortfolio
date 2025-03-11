import openai
import json
from typing import List, Dict, Any, Optional
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import settings
from models.taxonomy import Taxonomy, TaxonomyCategory

class LLMService:
    """Service for interacting with Azure OpenAI API."""
    
    def __init__(self):
        """Initialize the LLM service."""
        openai.api_type = "azure"
        openai.api_key = settings.AZURE_OPENAI_API_KEY
        openai.api_base = settings.AZURE_OPENAI_ENDPOINT
        openai.api_version = "2023-05-15"
        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def classify_batch(
        self,
        batch: List[str],
        level: int,
        taxonomy: Taxonomy,
        parent_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a batch of vendors to LLM for classification.
        
        Args:
            batch: List of vendor names
            level: Classification level (1-4)
            taxonomy: Taxonomy data
            parent_category: Parent category ID (required for levels 2-4)
            
        Returns:
            Classification results
        """
        # Create prompt based on level
        prompt = self._create_classification_prompt(batch, level, taxonomy, parent_category)
        
        # Call Azure OpenAI API
        try:
            response = await openai.ChatCompletion.acreate(
                engine=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are a vendor classification expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            # Extract JSON from response
            try:
                json_str = content.strip()
                # Handle case where JSON is wrapped in markdown code blocks
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0].strip()
                
                result = json.loads(json_str)
                
                # Track token usage
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
                
                return {
                    "result": result,
                    "usage": usage
                }
            
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON response: {e}")
                logging.error(f"Response content: {content}")
                raise ValueError(f"Failed to parse JSON response: {e}")
        
        except Exception as e:
            logging.error(f"Azure OpenAI API error: {e}")
            raise
    
    async def process_search_results(
        self,
        vendor: str,
        search_results: Dict[str, Any],
        taxonomy: Taxonomy
    ) -> Dict[str, Any]:
        """
        Process search results to determine classification.
        
        Args:
            vendor: Vendor name
            search_results: Search results from Tavily
            taxonomy: Taxonomy data
            
        Returns:
            Classification result
        """
        # Create prompt with search results
        prompt = self._create_search_results_prompt(vendor, search_results, taxonomy)
        
        # Call Azure OpenAI API
        try:
            response = await openai.ChatCompletion.acreate(
                engine=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are a vendor classification expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            # Extract JSON from response
            try:
                json_str = content.strip()
                # Handle case where JSON is wrapped in markdown code blocks
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0].strip()
                
                result = json.loads(json_str)
                
                # Track token usage
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
                
                return {
                    "result": result,
                    "usage": usage
                }
            
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON response: {e}")
                logging.error(f"Response content: {content}")
                raise ValueError(f"Failed to parse JSON response: {e}")
        
        except Exception as e:
            logging.error(f"Azure OpenAI API error: {e}")
            raise
    
    def _create_classification_prompt(
        self,
        vendors: List[str],
        level: int,
        taxonomy: Taxonomy,
        parent_category: Optional[str] = None
    ) -> str:
        """
        Create an appropriate prompt for the current classification level.
        
        Args:
            vendors: List of vendor names
            level: Classification level (1-4)
            taxonomy: Taxonomy data
            parent_category: Parent category ID (required for levels 2-4)
            
        Returns:
            Prompt string
        """
        if level == 1:
            categories = taxonomy.get_level1_categories()
            categories_str = "\n".join(f"- {cat.id}: {cat.name}" for cat in categories)
            
            prompt = f"""
            You are a vendor classification expert. Below is a list of company/vendor names.
            Please classify each vendor according to the following Level 1 categories:
            
            {categories_str}
            
            For each vendor, provide:
            1. The most appropriate category ID and name
            2. A confidence level (0.0-1.0)
            
            If you cannot determine a category with reasonable confidence, mark it as "classification_not_possible".
            
            Vendor list:
            {', '.join(vendors)}
            
            Respond with a JSON object matching this schema:
            {{
              "level": 1,
              "batch_id": "batch-{len(vendors)}",
              "classifications": [
                {{
                  "vendor_name": "Vendor Name",
                  "category_id": "ID",
                  "category_name": "Category Name",
                  "confidence": 0.95,
                  "classification_not_possible": false,
                  "classification_not_possible_reason": null
                }}
              ]
            }}
            """
        else:
            # For levels 2-4, include parent category info
            if level == 2:
                categories = taxonomy.get_level2_categories(parent_category)
            elif level == 3:
                categories = taxonomy.get_level3_categories(parent_category)
            else:  # level == 4
                categories = taxonomy.get_level4_categories(parent_category)
            
            categories_str = "\n".join(f"- {cat.id}: {cat.name}" for cat in categories)
            
            prompt = f"""
            You are a vendor classification expert. Below is a list of company/vendor names.
            These vendors have already been classified as belonging to the parent category:
            
            Parent Category: {parent_category}
            
            Please classify each vendor according to the following Level {level} categories:
            
            {categories_str}
            
            For each vendor, provide:
            1. The most appropriate category ID and name
            2. A confidence level (0.0-1.0)
            
            If you cannot determine a category with reasonable confidence, mark it as "classification_not_possible".
            
            Vendor list:
            {', '.join(vendors)}
            
            Respond with a JSON object matching this schema:
            {{
              "level": {level},
              "batch_id": "batch-{len(vendors)}",
              "parent_category_id": "{parent_category}",
              "classifications": [
                {{
                  "vendor_name": "Vendor Name",
                  "category_id": "ID",
                  "category_name": "Category Name",
                  "confidence": 0.95,
                  "classification_not_possible": false,
                  "classification_not_possible_reason": null
                }}
              ]
            }}
            """
        
        return prompt
    
    def _create_search_results_prompt(
        self,
        vendor: str,
        search_results: Dict[str, Any],
        taxonomy: Taxonomy
    ) -> str:
        """
        Create a prompt for processing search results.
        
        Args:
            vendor: Vendor name
            search_results: Search results from Tavily
            taxonomy: Taxonomy data
            
        Returns:
            Prompt string
        """
        # Get level 1 categories
        categories = taxonomy.get_level1_categories()
        categories_str = "\n".join(f"- {cat.id}: {cat.name}" for cat in categories)
        
        # Format search results
        sources_str = ""
        for i, source in enumerate(search_results.get("sources", [])):
            sources_str += f"""
            Source {i+1}:
            Title: {source.get('title', '')}
            URL: {source.get('url', '')}
            Content: {source.get('content', '')}
            """
        
        prompt = f"""
        You are a vendor classification expert. I need help classifying the following vendor:
        
        Vendor: {vendor}
        
        I've gathered the following information about this vendor:
        
        {sources_str}
        
        Based on this information, please classify the vendor according to the following Level 1 categories:
        
        {categories_str}
        
        Respond with a JSON object matching this schema:
        {{
          "vendor_name": "{vendor}",
          "category_id": "ID",
          "category_name": "Category Name",
          "confidence": 0.95,
          "classification_not_possible": false,
          "classification_not_possible_reason": null,
          "notes": "Brief explanation of classification"
        }}
        
        If you still cannot determine a category with reasonable confidence, set "classification_not_possible" to true and provide a reason.
        """
        
        return prompt
