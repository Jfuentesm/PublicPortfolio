# app/tasks/reclassification_prompts.py
import json
import logging
from typing import Dict, Any, Optional

from models.taxonomy import Taxonomy, TaxonomyCategory
from schemas.job import JobResultItem # To understand the structure of original_result

logger = logging.getLogger("vendor_classification.reclassification_prompts")

def generate_reclassification_prompt(
    original_vendor_data: Dict[str, Any],
    user_hint: str,
    original_classification: Optional[Dict[str, Any]], # Dict matching JobResultItem
    taxonomy: Taxonomy,
    target_level: int, # The target level for this reclassification attempt
    attempt_id: str = "unknown-attempt"
) -> str:
    """
    Create a prompt for re-classifying a single vendor based on original data,
    user hint, and previous classification attempt. Aims for the target_level.
    """
    vendor_name = original_vendor_data.get('vendor_name', 'UnknownVendor')
    logger.debug(f"Generating reclassification prompt for vendor: {vendor_name}",
                extra={"target_level": target_level, "attempt_id": attempt_id})

    # --- Build Original Vendor Data Section ---
    vendor_data_xml = "<original_vendor_data>\n"
    vendor_data_xml += f"  <name>{vendor_name}</name>\n"
    # Include all available fields from the original data
    optional_fields = [
        'example_goods_services', 'address', 'website',
        'internal_category', 'parent_company', 'spend_category'
    ]
    # Map internal keys to XML tags if needed (adjust based on original_vendor_data structure)
    field_map = {
        'example_goods_services': 'example_goods_services',
        'address': 'address',
        'website': 'website',
        'internal_category': 'internal_category',
        'parent_company': 'parent_company',
        'spend_category': 'spend_category',
        # Add mappings if keys in original_vendor_data are different
        'example': 'example_goods_services',
        'vendor_address': 'address',
        'vendor_website': 'website',
    }
    for field_key, xml_tag in field_map.items():
        value = original_vendor_data.get(field_key)
        if value:
            vendor_data_xml += f"  <{xml_tag}>{str(value)[:300]}</{xml_tag}>\n" # Limit length
    vendor_data_xml += "</original_vendor_data>"

    # --- Build User Hint Section ---
    user_hint_xml = f"<user_hint>{user_hint}</user_hint>"

    # --- Build Original Classification Section (Optional but helpful) ---
    original_classification_xml = "<original_classification_attempt>\n"
    if original_classification:
        original_status = original_classification.get('final_status', 'Unknown')
        original_level = original_classification.get('achieved_level', 0)
        original_reason = original_classification.get('classification_notes_or_reason', 'N/A')
        original_classification_xml += f"  <status>{original_status}</status>\n"
        original_classification_xml += f"  <achieved_level>{original_level}</achieved_level>\n"
        original_classification_xml += f"  <reason_or_notes>{original_reason}</reason_or_notes>\n"
        # Include original L1-L5 IDs/Names if available
        for i in range(1, 6):
             id_key = f'level{i}_id'
             name_key = f'level{i}_name'
             cat_id = original_classification.get(id_key)
             cat_name = original_classification.get(name_key)
             if cat_id and cat_name:
                 original_classification_xml += f"  <level_{i}_result id=\"{cat_id}\" name=\"{cat_name}\"/>\n"
    else:
        original_classification_xml += "  <message>No previous classification data available.</message>\n"
    original_classification_xml += "</original_classification_attempt>"

    # --- Define Output Format Section (Standard Classification Result) ---
    # We want the LLM to output the *new* classification in the standard format
    # It needs to perform the hierarchical classification again based on the hint.
    output_format_xml = f"""<output_format>
Respond *only* with a valid JSON object containing the *new* classification result for this vendor, based *primarily* on the <user_hint> and <original_vendor_data>.
The JSON object should represent the full classification attempt up to Level {target_level}, following the standard structure used previously.

```json
{{
  "level": {target_level},
  "attempt_id": "{attempt_id}",
  "vendor_name": "{vendor_name}",
  "classifications": [
    {{
      "vendor_name": "{vendor_name}",
      "level1": {{
        "category_id": "string",
        "category_name": "string",
        "confidence": "float",
        "classification_not_possible": "boolean",
        "classification_not_possible_reason": "string | null",
        "notes": "string | null"
      }},
      "level2": {{
        "category_id": "string",
        "category_name": "string",
        "confidence": "float",
        "classification_not_possible": "boolean",
        "classification_not_possible_reason": "string | null",
        "notes": "string | null"
      }},
      "level3": {{
        "category_id": "string",
        "category_name": "string",
        "confidence": "float",
        "classification_not_possible": "boolean",
        "classification_not_possible_reason": "string | null",
        "notes": "string | null"
      }},
      "level4": {{
        "category_id": "string",
        "category_name": "string",
        "confidence": "float",
        "classification_not_possible": "boolean",
        "classification_not_possible_reason": "string | null",
        "notes": "string | null"
      }},
      "level5": {{
        "category_id": "string",
        "category_name": "string",
        "confidence": "float",
        "classification_not_possible": "boolean",
        "classification_not_possible_reason": "string | null",
        "notes": "string | null"
      }}
    }}
  ]
}}
```

</output_format>"""

    # --- Assemble Final Prompt ---
    prompt = f"""
<role>You are a precise vendor classification expert using the NAICS taxonomy. You are re-evaluating a previous classification based on new user input.</role>

<task>Re-classify the vendor described in `<original_vendor_data>` using the crucial information provided in `<user_hint>`. The previous attempt is in `<original_classification_attempt>` for context. Your goal is to determine the most accurate NAICS classification up to **Level {target_level}** based *primarily* on the user hint combined with the original data.</task>

<instructions>
1.  **Prioritize the `<user_hint>`**. Assume it provides the most accurate context about the vendor's primary business activity for the user's purposes.
2.  Use the `<original_vendor_data>` to supplement the hint if necessary.
3.  Refer to the `<original_classification_attempt>` only for context on why the previous classification might have been incorrect or insufficient. Do not simply repeat the old result unless the hint strongly confirms it.
4.  Perform a hierarchical classification starting from Level 1 up to the target Level {target_level}.
5.  For **each level**:
    a.  Determine the most appropriate category based on the hint and data. Use the provided taxonomy structure (implicitly known or explicitly provided if needed in future versions).
    b.  If a confident classification for the current level is possible, provide the `category_id`, `category_name`, `confidence` (> 0.0), set `classification_not_possible` to `false`, and optionally add `notes`. Proceed to the next level if the target level allows.
    c.  If classification for the current level is **not possible** (due to ambiguity even with the hint, or the hint pointing to an activity outside the available subcategories), set `classification_not_possible` to `true`, `confidence` to `0.0`, provide a `classification_not_possible_reason`, set `category_id`/`category_name` to "N/A", and **stop** the classification process for this vendor (do not include results for subsequent levels).
6.  Structure your response as a **single JSON object** matching the schema in `<output_format>`. Ensure it contains results for all levels attempted up to the point of success or failure. Ensure the JSON is enclosed in ```json ... ```.
7.  The output JSON should represent the *new* classification attempt based on the hint.
8.  Respond *only* with the valid JSON object enclosed in the markdown code fence.
</instructions>

{vendor_data_xml}

{user_hint_xml}

{original_classification_xml}

{output_format_xml}
"""
    # Note: This prompt implicitly relies on the LLM having access to the taxonomy structure
    # or being trained on it. For dynamic taxonomies, the relevant category options for each
    # level would need to be injected similar to the original batch prompt.
    # For now, we assume the LLM can infer the hierarchy and valid IDs based on the target level and task.
    # A future enhancement could involve passing the relevant taxonomy branches.

    return prompt