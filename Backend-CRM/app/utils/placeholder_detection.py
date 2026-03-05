"""
Placeholder Detection Utility

Automatically detects placeholders (e.g., {{PI_NAME}}) in template content
and extracts unique placeholder names.
"""

from typing import Any, Dict, List, Set
import re


def detect_placeholders_in_text(text: str) -> Set[str]:
    """
    Detect all placeholders in a text string.
    
    Args:
        text: The text string to scan
        
    Returns:
        Set of placeholder names (without {{}})
    """
    if not text or not isinstance(text, str):
        return set()
    
    # Find all placeholders in format {{FIELD_NAME}}
    pattern = r'\{\{([A-Z_]+)\}\}'
    matches = re.findall(pattern, text)
    
    return set(matches)


def detect_placeholders_in_json(content: Any) -> Set[str]:
    """
    Recursively detect all placeholders in a JSON structure (TipTap document format).
    
    Args:
        content: The JSON content (dict, list, or primitive)
        
    Returns:
        Set of unique placeholder names (without {{}})
    """
    placeholders = set()
    
    if isinstance(content, dict):
        for key, value in content.items():
            if key == "text" and isinstance(value, str):
                # This is a text node in TipTap format - detect placeholders
                placeholders.update(detect_placeholders_in_text(value))
            elif isinstance(value, (dict, list)):
                # Recursively process nested structures
                placeholders.update(detect_placeholders_in_json(value))
            elif isinstance(value, str):
                # Detect placeholders in any string value
                placeholders.update(detect_placeholders_in_text(value))
    elif isinstance(content, list):
        for item in content:
            placeholders.update(detect_placeholders_in_json(item))
    elif isinstance(content, str):
        placeholders.update(detect_placeholders_in_text(content))
    
    return placeholders


def create_default_placeholder_config(placeholders: Set[str]) -> Dict[str, Dict[str, bool]]:
    """
    Create default placeholder configuration with all placeholders editable.
    
    Args:
        placeholders: Set of placeholder names
        
    Returns:
        Configuration dict: {"PLACEHOLDER_NAME": {"editable": true}}
    """
    config = {}
    for placeholder in placeholders:
        config[placeholder] = {"editable": True}
    return config


def detect_and_create_config(template_content: Dict[str, Any]) -> Dict[str, Dict[str, bool]]:
    """
    Detect placeholders in template content and create default configuration.
    
    Args:
        template_content: The template JSON content
        
    Returns:
        Configuration dict with all detected placeholders set to editable=True
    """
    placeholders = detect_placeholders_in_json(template_content)
    return create_default_placeholder_config(placeholders)
