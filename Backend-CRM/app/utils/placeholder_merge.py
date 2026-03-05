"""
Placeholder Merge Utility

Replaces template placeholders (e.g., {{PI_NAME}}) with SiteProfile values
when creating AgreementDocuments from templates.

Placeholder format: {{FIELD_NAME}}
Supported fields:
- SITE_NAME
- HOSPITAL_NAME
- PI_NAME
- PI_EMAIL
- PRIMARY_CONTRACTING_ENTITY
- AUTHORIZED_SIGNATORY_NAME
- AUTHORIZED_SIGNATORY_EMAIL
- ADDRESS_LINE_1
- CITY
- STATE
- COUNTRY
- POSTAL_CODE
"""

from typing import Any, Dict, Optional
import json
import re
from app.models import SiteProfile


# Mapping of placeholder names to SiteProfile field names
PLACEHOLDER_MAP = {
    "SITE_NAME": "site_name",
    "HOSPITAL_NAME": "hospital_name",
    "PI_NAME": "pi_name",
    "PI_EMAIL": "pi_email",
    "PRIMARY_CONTRACTING_ENTITY": "primary_contracting_entity",
    "AUTHORIZED_SIGNATORY_NAME": "authorized_signatory_name",
    "AUTHORIZED_SIGNATORY_EMAIL": "authorized_signatory_email",
    "ADDRESS_LINE_1": "address_line_1",
    "CITY": "city",
    "STATE": "state",
    "COUNTRY": "country",
    "POSTAL_CODE": "postal_code",
}


def get_placeholder_value(placeholder_name: str, profile: SiteProfile) -> str:
    """
    Get the value for a placeholder from SiteProfile.
    
    Args:
        placeholder_name: The placeholder name (e.g., "PI_NAME")
        profile: The SiteProfile instance
        
    Returns:
        The value from SiteProfile, or empty string if not found
    """
    field_name = PLACEHOLDER_MAP.get(placeholder_name.upper())
    if not field_name:
        return ""
    
    value = getattr(profile, field_name, None)
    return str(value) if value is not None else ""


def replace_placeholders_in_text(text: str, profile: SiteProfile) -> tuple[str, list[str]]:
    """
    Replace placeholders in a text string and return which placeholders were found.
    
    Args:
        text: The text string that may contain placeholders
        profile: The SiteProfile instance
        
    Returns:
        Tuple of (text with placeholders replaced, list of placeholder names found)
    """
    if not text or not isinstance(text, str):
        return text, []
    
    # Find all placeholders in format {{FIELD_NAME}}
    pattern = r'\{\{([A-Z_]+)\}\}'
    found_placeholders = []
    
    def replace_match(match):
        placeholder_name = match.group(1)
        found_placeholders.append(placeholder_name)
        value = get_placeholder_value(placeholder_name, profile)
        return value
    
    replaced_text = re.sub(pattern, replace_match, text)
    return replaced_text, found_placeholders


def merge_placeholders_in_json(content: Any, profile: SiteProfile) -> tuple[Any, Dict[str, list]]:
    """
    Recursively merge placeholders in a JSON structure (TipTap document format).
    Returns both the merged content and a mapping of placeholder names to text nodes that contain them.
    
    Args:
        content: The JSON content (dict, list, or primitive)
        profile: The SiteProfile instance
        
    Returns:
        Tuple of (merged JSON structure, dict mapping placeholder names to lists of text values that contain them)
    """
    placeholder_locations = {}  # Maps placeholder_name -> list of text values that contain it
    
    def merge_recursive(item: Any) -> Any:
        if isinstance(item, dict):
            result = {}
            for key, value in item.items():
                if key == "text" and isinstance(value, str):
                    # This is a text node in TipTap format - replace placeholders
                    replaced_text, found_placeholders = replace_placeholders_in_text(value, profile)
                    result[key] = replaced_text
                    # Track which placeholders were in this text node
                    for placeholder_name in found_placeholders:
                        if placeholder_name not in placeholder_locations:
                            placeholder_locations[placeholder_name] = []
                        placeholder_locations[placeholder_name].append(replaced_text)
                elif isinstance(value, (dict, list)):
                    # Recursively process nested structures
                    result[key] = merge_recursive(value)
                elif isinstance(value, str):
                    # Replace placeholders in any string value
                    replaced_text, found_placeholders = replace_placeholders_in_text(value, profile)
                    result[key] = replaced_text
                    for placeholder_name in found_placeholders:
                        if placeholder_name not in placeholder_locations:
                            placeholder_locations[placeholder_name] = []
                        placeholder_locations[placeholder_name].append(replaced_text)
                else:
                    # Keep other types as-is
                    result[key] = value
            return result
        elif isinstance(item, list):
            return [merge_recursive(subitem) for subitem in item]
        elif isinstance(item, str):
            replaced_text, found_placeholders = replace_placeholders_in_text(item, profile)
            for placeholder_name in found_placeholders:
                if placeholder_name not in placeholder_locations:
                    placeholder_locations[placeholder_name] = []
                placeholder_locations[placeholder_name].append(replaced_text)
            return replaced_text
        else:
            return item
    
    merged_content = merge_recursive(content)
    return merged_content, placeholder_locations


def merge_template_with_profile(
    template_content: Dict[str, Any],
    profile: SiteProfile,
    placeholder_config: Optional[Dict[str, Dict[str, bool]]] = None,
    sponsor_signatory_name: Optional[str] = None,
    sponsor_signatory_email: Optional[str] = None,
    current_user_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Merge template content with SiteProfile data by replacing placeholders.
    Optionally applies locking based on placeholder_config.
    Also handles signature block placeholders (SITE_SIGNATURE_BLOCK, SPONSOR_SIGNATURE_BLOCK).
    
    Args:
        template_content: The template JSON content (TipTap format)
        profile: The SiteProfile instance
        placeholder_config: Optional configuration dict: {"PLACEHOLDER_NAME": {"editable": true/false}}
        sponsor_signatory_name: Optional sponsor signatory name from config
        sponsor_signatory_email: Optional sponsor signatory email from config
        current_user_email: Optional current user email for fallback
        
    Returns:
        Template content with placeholders replaced with actual values, signature blocks inserted, and locking applied if config provided
    """
    if not template_content:
        return template_content
    
    if not profile:
        raise ValueError("SiteProfile is required for placeholder merging")
    
    # Deep copy to avoid modifying the original template
    import copy
    merged_content = copy.deepcopy(template_content)
    
    # Step 1: Recursively replace regular placeholders and get placeholder locations
    merged_content, placeholder_locations = merge_placeholders_in_json(merged_content, profile)
    
    # Step 2: Apply signature block replacements (after regular placeholders, before locking)
    from app.utils.signature_blocks import apply_signature_blocks
    merged_content = apply_signature_blocks(
        merged_content,
        profile,
        sponsor_signatory_name,
        sponsor_signatory_email,
        current_user_email
    )
    
    # Step 3: Apply locking if configuration is provided
    if placeholder_config:
        from app.utils.placeholder_locking import apply_placeholder_locking
        merged_content = apply_placeholder_locking(merged_content, placeholder_config, placeholder_locations)
    
    return merged_content
