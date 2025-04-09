
# <file path='app/tasks/classification_prompts.py'>
# app/prompts/classification_prompts.py
import json
import logging
from typing import List, Dict, Any, Optional

from models.taxonomy import Taxonomy, TaxonomyCategory

# Configure logger for this module
logger = logging.getLogger("vendor_classification.prompts")

def generate_batch_prompt(
    vendors_data: List[Dict[str, Any]],
    level: int,
    taxonomy: Taxonomy,
    parent_category_id: Optional[str] = None,
    batch_id: str = "unknown-batch",
    search_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create an appropriate prompt for the current classification level (1-5),
    optionally including search context for post-search classification.
    """
    context_type = "Search Context" if search_context else "Initial Data"
    logger.debug(f"generate_batch_prompt: Generating prompt for Level {level} using {context_type}",
                extra={ "vendor_count": len(vendors_data), "parent_category_id": parent_category_id, "batch_id": batch_id, "has_search_context": bool(search_context) })

    # --- Build Vendor Data Section ---
    vendor_data_xml = "<vendor_data>\n"
    for i, vendor_entry in enumerate(vendors_data):
        vendor_name = vendor_entry.get('vendor_name', f'UnknownVendor_{i}')
        example = vendor_entry.get('example')
        address = vendor_entry.get('vendor_address')
        website = vendor_entry.get('vendor_website')
        internal_cat = vendor_entry.get('internal_category')
        parent_co = vendor_entry.get('parent_company')
        spend_cat = vendor_entry.get('spend_category')

        vendor_data_xml += f"  <vendor index=\"{i+1}\">\n"
        vendor_data_xml += f"    <name>{vendor_name}</name>\n"
        if example: vendor_data_xml += f"    <example_goods_services>{str(example)[:200]}</example_goods_services>\n"
        if address: vendor_data_xml += f"    <address>{str(address)[:200]}</address>\n"
        if website: vendor_data_xml += f"    <website>{str(website)[:100]}</website>\n"
        if internal_cat: vendor_data_xml += f"    <internal_category>{str(internal_cat)[:100]}</internal_category>\n"
        if parent_co: vendor_data_xml += f"    <parent_company>{str(parent_co)[:100]}</parent_company>\n"
        if spend_cat: vendor_data_xml += f"    <spend_category>{str(spend_cat)[:100]}</spend_category>\n"
        vendor_data_xml += f"  </vendor>\n"
    vendor_data_xml += "</vendor_data>"

    # --- Build Search Context Section ---
    search_context_xml = ""
    if search_context and level > 1: # Only include search context for L2+ post-search attempts
        logger.debug(f"Including search context in prompt for Level {level}", extra={"batch_id": batch_id})
        search_context_xml += "<search_context>\n"
        summary = search_context.get("summary")
        sources = search_context.get("sources")
        if summary:
            search_context_xml += f"  <summary>{str(summary)[:1000]}</summary>\n" # Limit length
        if sources and isinstance(sources, list):
            search_context_xml += "  <sources>\n"
            for j, source in enumerate(sources[:3]): # Limit to top 3 sources for brevity
                title = source.get('title', 'N/A')
                url = source.get('url', 'N/A')
                content_preview = str(source.get('content', ''))[:500] # Limit length
                search_context_xml += f"    <source index=\"{j+1}\">\n"
                search_context_xml += f"      <title>{title}</title>\n"
                search_context_xml += f"      <url>{url}</url>\n"
                search_context_xml += f"      <content_snippet>{content_preview}...</content_snippet>\n"
                search_context_xml += f"    </source>\n"
            search_context_xml += "  </sources>\n"
        else:
             search_context_xml += "  <message>No relevant search results sources were provided.</message>\n"
        search_context_xml += "</search_context>\n"

    # --- Get Category Options ---
    categories: List[TaxonomyCategory] = []
    parent_category_name = "N/A"
    category_lookup_successful = True
    try:
        logger.debug(f"generate_batch_prompt: Retrieving categories via taxonomy methods for Level {level}, Parent: {parent_category_id}")
        parent_obj = None
        if level == 1:
            categories = taxonomy.get_level1_categories()
        elif parent_category_id:
            # --- UPDATED: Use taxonomy methods consistently ---
            if level == 2:
                categories = taxonomy.get_level2_categories(parent_category_id)
                parent_obj = taxonomy.categories.get(parent_category_id)
            elif level == 3:
                categories = taxonomy.get_level3_categories(parent_category_id)
                # Need to find the L2 object to get its name
                l1_id, l2_id = parent_category_id.split('.') if '.' in parent_category_id else (None, parent_category_id)
                if not l1_id:
                    for l1k, l1n in taxonomy.categories.items():
                        if l2_id in getattr(l1n, 'children', {}): l1_id = l1k; break
                if l1_id: parent_obj = taxonomy.categories.get(l1_id, {}).children.get(l2_id)
            elif level == 4:
                categories = taxonomy.get_level4_categories(parent_category_id)
                # Need to find the L3 object to get its name
                # Handle different possible parent_id formats (L1.L2.L3, L2.L3, L3)
                parts = parent_category_id.split('.')
                l1_id, l2_id, l3_id = None, None, None
                if len(parts) == 3: l1_id, l2_id, l3_id = parts[0], parts[1], parts[2]
                elif len(parts) == 2: # L2.L3 format
                    l2_p, l3_p = parts[0], parts[1]
                    for l1k, l1n in taxonomy.categories.items():
                         if l2_p in getattr(l1n, 'children', {}): l1_id = l1k; l2_id = l2_p; l3_id = l3_p; break
                elif len(parts) == 1: # L3 format
                    l3_p = parts[0]
                    for l1k, l1n in taxonomy.categories.items():
                        for l2k, l2n in getattr(l1n, 'children', {}).items():
                            if l3_p in getattr(l2n, 'children', {}): l1_id = l1k; l2_id = l2k; l3_id = l3_p; break
                        if l1_id: break
                if l1_id and l2_id and l3_id:
                    parent_obj = taxonomy.categories.get(l1_id, {}).children.get(l2_id, {}).children.get(l3_id)
            elif level == 5:
                categories = taxonomy.get_level5_categories(parent_category_id)
                # Need to find the L4 object to get its name
                # Handle different possible parent_id formats (L1.L2.L3.L4, L2.L3.L4, L3.L4, L4)
                parts = parent_category_id.split('.')
                l1_id, l2_id, l3_id, l4_id = None, None, None, None
                if len(parts) == 4: l1_id, l2_id, l3_id, l4_id = parts[0], parts[1], parts[2], parts[3]
                elif len(parts) == 3: # L2.L3.L4 format
                    l2_p, l3_p, l4_p = parts[0], parts[1], parts[2]
                    for l1k, l1n in taxonomy.categories.items():
                        if l2_p in getattr(l1n, 'children', {}): l1_id = l1k; l2_id = l2_p; l3_id = l3_p; l4_id = l4_p; break
                elif len(parts) == 2: # L3.L4 format
                    l3_p, l4_p = parts[0], parts[1]
                    for l1k, l1n in taxonomy.categories.items():
                        for l2k, l2n in getattr(l1n, 'children', {}).items():
                             if l3_p in getattr(l2n, 'children', {}): l1_id = l1k; l2_id = l2k; l3_id = l3_p; l4_id = l4_p; break
                        if l1_id: break
                elif len(parts) == 1: # L4 format
                    l4_p = parts[0]
                    for l1k, l1n in taxonomy.categories.items():
                        for l2k, l2n in getattr(l1n, 'children', {}).items():
                            for l3k, l3n in getattr(l2n, 'children', {}).items():
                                if l4_p in getattr(l3n, 'children', {}): l1_id = l1k; l2_id = l2k; l3_id = l3k; l4_id = l4_p; break
                            if l1_id: break
                        if l1_id: break
                if l1_id and l2_id and l3_id and l4_id:
                    parent_obj = taxonomy.categories.get(l1_id, {}).children.get(l2_id, {}).children.get(l3_id, {}).children.get(l4_id)
            # --- END UPDATED ---

            if parent_obj: parent_category_name = parent_obj.name
        else: # level > 1 and no parent_category_id
            logger.error(f"Parent category ID is required for level {level} prompt generation but was not provided.")
            category_lookup_successful = False

        if not categories and level > 1 and parent_category_id:
             logger.warning(f"No subcategories found for Level {level}, Parent '{parent_category_id}'.")
             # Don't mark as failure if parent exists but has no children (valid scenario)
             # category_lookup_successful = False # Removed this line
        elif not categories and level == 1:
             logger.error(f"No Level 1 categories found in taxonomy!")
             category_lookup_successful = False

        logger.debug(f"generate_batch_prompt: Retrieved {len(categories)} categories for Level {level}, Parent '{parent_category_id}' ('{parent_category_name}').")

    except Exception as e:
        logger.error(f"Error retrieving categories for prompt (Level {level}, Parent: {parent_category_id})", exc_info=True)
        category_lookup_successful = False

    # --- Build Category Options Section ---
    category_options_xml = "<category_options>\n"
    if category_lookup_successful:
        category_options_xml += f"  <level>{level}</level>\n"
        if level > 1 and parent_category_id:
            category_options_xml += f"  <parent_id>{parent_category_id}</parent_id>\n"
            category_options_xml += f"  <parent_name>{parent_category_name}</parent_name>\n"
        category_options_xml += "  <categories>\n"
        if categories: # Check if categories list is not empty
            for cat in categories:
                category_options_xml += f"    <category id=\"{cat.id}\" name=\"{cat.name}\"/>\n"
        else:
             category_options_xml += f"    <message>No subcategories available for this level and parent.</message>\n"
        category_options_xml += "  </categories>\n"
    else:
        category_options_xml += f"  <error>Could not retrieve valid categories for Level {level}, Parent '{parent_category_id}'. Classification is not possible.</error>\n"
    category_options_xml += "</category_options>"

    # --- Define Output Format Section ---
    output_format_xml = f"""<output_format>
Respond *only* with a valid JSON object matching this exact schema. Do not include any text before or after the JSON object.

json
{{
  "level": {level},
  "batch_id": "{batch_id}",
  "parent_category_id": {json.dumps(parent_category_id)},
  "classifications": [
    {{
      "vendor_name": "string", // Exact vendor name from input <vendor_data>
      "category_id": "string", // ID from <category_options> or "N/A" if not possible
      "category_name": "string", // Name corresponding to category_id or "N/A"
      "confidence": "float", // 0.0 to 1.0. MUST be 0.0 if classification_not_possible is true.
      "classification_not_possible": "boolean", // true if classification cannot be confidently made from options, false otherwise.
      "classification_not_possible_reason": "string | null", // Brief reason if true (e.g., "Ambiguous", "Insufficient info"), null if false.
      "notes": "string | null" // Optional brief justification or reasoning, especially if confidence is low or not possible.
    }}
    // ... one entry for EACH vendor in <vendor_data>
  ]
}}

</output_format>"""

    # --- Assemble Final Prompt ---
    prompt_base = f"""
<role>You are a precise vendor classification expert using the NAICS taxonomy.</role>

<task>Classify each vendor provided in `<vendor_data>` into **ONE** appropriate NAICS category from the `<category_options>` for Level {level}. {f"Consider that these vendors belong to the parent category '{parent_category_id}: {parent_category_name}'. " if level > 1 and parent_category_id and parent_category_name != 'N/A' else ""}</task>"""

    if search_context_xml:
        prompt_base += f"""
<search_context_instruction>You have been provided with additional context from a web search in `<search_context>`. Use this information, along with the original `<vendor_data>`, to make the most accurate classification decision for Level {level}.</search_context_instruction>"""

    prompt_base += f"""
<instructions>
1.  Analyze each vendor's details in `<vendor_data>` {f"and the supplementary information in `<search_context>`" if search_context_xml else ""}.
2.  Compare the vendor's likely primary business activity against the available categories in `<category_options>`.
3.  Assign the **single most specific and appropriate** category ID and name from the list.
4.  Provide a confidence score (0.0 to 1.0).
5.  **CRITICAL:** If the vendor's primary activity is genuinely ambiguous, cannot be determined from the provided information, or does not fit well into *any* of the specific categories listed in `<category_options>`, **DO NOT GUESS**. Instead: Set `classification_not_possible` to `true`, `confidence` to `0.0`, provide a brief `classification_not_possible_reason`, and set `category_id`/`category_name` to "N/A".
6.  If classification *is* possible (`classification_not_possible: false`), ensure `confidence` > 0.0 and `category_id`/`category_name` are populated correctly from `<category_options>`.
7.  Provide brief optional `notes` for reasoning, especially if confidence is low or classification was not possible.
8.  Ensure the `batch_id` in the final JSON output matches the `batch_id` specified in `<output_format>`.
9.  Ensure the output contains an entry for **every** vendor listed in `<vendor_data>`.
10. Respond *only* with the valid JSON object as specified in `<output_format>`.
</instructions>

{vendor_data_xml}
{search_context_xml if search_context_xml else ""}
{category_options_xml}
{output_format_xml}
"""
    prompt = prompt_base

    # Handle case where category lookup failed (e.g., bad parent ID for L2+)
    if not category_lookup_successful and level > 1:
         prompt = f"""
<role>You are a precise vendor classification expert using the NAICS taxonomy.</role>
<task>Acknowledge that classification is not possible for the vendors in `<vendor_data>` at Level {level} because the necessary subcategories could not be provided (likely due to an invalid or non-existent parent category ID: {parent_category_id}).</task>
<instructions>
1. For **every** vendor listed in `<vendor_data>`, create a classification entry in the final JSON output.
2. In each entry, set `classification_not_possible` to `true`.
3. Set `confidence` to `0.0`.
4. Set `category_id` and `category_name` to "N/A".
5. Set `classification_not_possible_reason` to "No subcategories defined or retrievable for parent {parent_category_id} at Level {level}".
6. Ensure the `batch_id` in the final JSON output matches the `batch_id` specified in `<output_format>`.
7. Respond *only* with the valid JSON object as specified in `<output_format>`.
</instructions>
{vendor_data_xml}
{category_options_xml}
{output_format_xml}
"""
    # Handle case where L1 lookup failed (taxonomy load issue)
    elif not category_lookup_successful and level == 1:
         prompt = f"""
<role>You are a precise vendor classification expert using the NAICS taxonomy.</role>
<task>Acknowledge that classification is not possible for the vendors in `<vendor_data>` at Level 1 because the top-level categories could not be loaded or provided.</task>
<instructions>
1. For **every** vendor listed in `<vendor_data>`, create a classification entry in the final JSON output.
2. In each entry, set `classification_not_possible` to `true`.
3. Set `confidence` to `0.0`.
4. Set `category_id` and `category_name` to "N/A".
5. Set `classification_not_possible_reason` to "Level 1 categories could not be loaded or retrieved.".
6. Ensure the `batch_id` in the final JSON output matches the `batch_id` specified in `<output_format>`.
7. Respond *only* with the valid JSON object as specified in `<output_format>`.
</instructions>
{vendor_data_xml}
{category_options_xml}
{output_format_xml}
"""


    return prompt


def generate_search_prompt(
    vendor_data: Dict[str, Any],
    search_results: Dict[str, Any],
    taxonomy: Taxonomy,
    attempt_id: str = "unknown-attempt"
) -> str:
    """
    Create a prompt for processing search results, aiming for Level 1 classification.
    """
    logger.debug(f"Entering generate_search_prompt for vendor: {vendor_data.get('vendor_name', 'Unknown')}")
    vendor_name = vendor_data.get('vendor_name', 'UnknownVendor')
    example = vendor_data.get('example')
    address = vendor_data.get('vendor_address')
    website = vendor_data.get('vendor_website')
    internal_cat = vendor_data.get('internal_category')
    parent_co = vendor_data.get('parent_company')
    spend_cat = vendor_data.get('spend_category')

    logger.debug(f"Creating search results prompt for vendor",
                extra={ "vendor": vendor_name, "source_count": len(search_results.get("sources", [])), "attempt_id": attempt_id })

    # --- Build Vendor Data Section ---
    vendor_data_xml = "<vendor_data>\n"
    vendor_data_xml += f"  <name>{vendor_name}</name>\n"
    if example: vendor_data_xml += f"  <example_goods_services>{str(example)[:300]}</example_goods_services>\n"
    if address: vendor_data_xml += f"  <address>{str(address)[:200]}</address>\n"
    if website: vendor_data_xml += f"  <website>{str(website)[:100]}</website>\n"
    if internal_cat: vendor_data_xml += f"  <internal_category>{str(internal_cat)[:100]}</internal_category>\n"
    if parent_co: vendor_data_xml += f"  <parent_company>{str(parent_co)[:100]}</parent_company>\n"
    if spend_cat: vendor_data_xml += f"  <spend_category>{str(spend_cat)[:100]}</spend_category>\n"
    vendor_data_xml += "</vendor_data>"

    # --- Build Search Results Section ---
    search_results_xml = "<search_results>\n"
    sources = search_results.get("sources")
    if sources and isinstance(sources, list):
        search_results_xml += "  <sources>\n"
        for i, source in enumerate(sources):
            content_preview = str(source.get('content', ''))[:1500] # Limit length
            search_results_xml += f"    <source index=\"{i+1}\">\n"
            search_results_xml += f"      <title>{source.get('title', 'N/A')}</title>\n"
            search_results_xml += f"      <url>{source.get('url', 'N/A')}</url>\n"
            search_results_xml += f"      <content_snippet>{content_preview}...</content_snippet>\n"
            search_results_xml += f"    </source>\n"
        search_results_xml += "  </sources>\n"
    else:
        search_results_xml += "  <message>No relevant search results sources were found.</message>\n"

    summary_str = search_results.get("summary", "")
    if summary_str:
        search_results_xml += f"  <summary>{summary_str}</summary>\n"
    search_results_xml += "</search_results>"

    # --- Get Level 1 Category Options ---
    categories = taxonomy.get_level1_categories()
    category_options_xml = "<category_options>\n"
    category_options_xml += "  <level>1</level>\n" # Explicitly state Level 1
    category_options_xml += "  <categories>\n"
    for cat in categories:
        category_options_xml += f"    <category id=\"{cat.id}\" name=\"{cat.name}\"/>\n" # Omit description
    category_options_xml += "  </categories>\n"
    category_options_xml += "</category_options>"

    # --- Define Output Format Section ---
    output_format_xml = f"""<output_format>
Respond *only* with a valid JSON object matching this exact schema. Do not include any text before or after the JSON object.

json
{{
  "attempt_id": "{attempt_id}", // ID for this specific attempt
  "vendor_name": "{vendor_name}", // Exact vendor name from input <vendor_data>
  "category_id": "string", // Level 1 ID from <category_options> or "N/A" if not possible
  "category_name": "string", // Name corresponding to category_id or "N/A"
  "confidence": "float", // 0.0 to 1.0. MUST be 0.0 if classification_not_possible is true.
  "classification_not_possible": "boolean", // true if classification cannot be confidently made from options based *only* on provided info, false otherwise.
  "classification_not_possible_reason": "string | null", // Brief reason if true (e.g., "Insufficient info", "Conflicting sources"), null if false.
  "notes": "string | null" // Brief explanation of decision based *only* on the provided context and search results. Reference specific sources if helpful.
}}

</output_format>"""

    # --- Assemble Final Prompt ---
    prompt = f"""
<role>You are a precise vendor classification expert using the NAICS taxonomy.</role>

<task>Analyze the vendor details in `<vendor_data>` and the web search information in `<search_results>` to classify the vendor into **ONE** appropriate **Level 1** NAICS category from `<category_options>`. Base your decision *only* on the provided information.</task>

<instructions>
1.  Carefully review the vendor details in `<vendor_data>` (name, examples, address, website, internal category, parent company, spend category).
2.  Carefully review the search results in `<search_results>` (sources and summary).
3.  Synthesize all provided information to understand the vendor's **primary business activity**. Focus on what the company *does*, not just what it might resell.
4.  Compare this primary activity against the **Level 1** categories listed in `<category_options>`.
5.  Assign the **single most appropriate** Level 1 category ID and name.
6.  Provide a confidence score (0.0 to 1.0) based on the clarity, consistency, and relevance of the provided information.
7.  **CRITICAL:** If the provided information (vendor data + search results) is insufficient, contradictory, irrelevant, focuses only on products sold rather than the business activity, or does not allow for confident determination of the primary business activity *from the listed L1 categories*, **DO NOT GUESS**. Instead: Set `classification_not_possible` to `true`, `confidence` to `0.0`, provide a brief `classification_not_possible_reason`, and set `category_id`/`category_name` to "N/A".
8.  If classification *is* possible (`classification_not_possible: false`), ensure `confidence` > 0.0 and `category_id`/`category_name` are populated correctly from `<category_options>`.
9.  Provide brief optional `notes` explaining your reasoning, referencing specific details from `<vendor_data>` or `<search_results>`.
10. Ensure the `vendor_name` in the final JSON output matches the name in `<vendor_data>`.
11. Respond *only* with the valid JSON object as specified in `<output_format>`.
</instructions>

{vendor_data_xml}

{search_results_xml}

{category_options_xml}

{output_format_xml}
"""
    return prompt