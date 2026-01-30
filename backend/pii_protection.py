"""PII Protection Module

This module provides functionality to detect, mask, and restore Personally Identifiable Information (PII)
in text before sending it to external APIs like Azure Content Safety.
"""

import re
from typing import Dict, Tuple


class PIIProtector:
    """Handles PII detection, masking, and restoration."""

    # PII patterns with regex
    PII_PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b(?:\+?1[-.]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        # URL pattern - simplified to catch common cases
        "url": r'\b(?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?\b',
    }

    def __init__(self):
        """Initialize the PII protector with an empty mapping."""
        self.pii_mapping: Dict[str, str] = {}
        self.placeholder_counter: Dict[str, int] = {key: 0 for key in self.PII_PATTERNS}

    def mask_pii(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Mask PII in the given text with placeholder tokens.

        Args:
            text: The input text potentially containing PII

        Returns:
            A tuple of (masked_text, pii_mapping) where:
            - masked_text: Text with PII replaced by placeholders
            - pii_mapping: Dictionary mapping placeholders to original values
        """
        masked_text = text
        pii_mapping = {}

        # Process each PII type
        for pii_type, pattern in self.PII_PATTERNS.items():
            masked_text, type_mapping = self._mask_pattern(
                masked_text, pattern, pii_type
            )
            pii_mapping.update(type_mapping)

        return masked_text, pii_mapping

    def _mask_pattern(
        self, text: str, pattern: str, pii_type: str
    ) -> Tuple[str, Dict[str, str]]:
        """
        Mask a specific PII pattern in text.

        Args:
            text: Input text
            pattern: Regex pattern to match
            pii_type: Type of PII (e.g., 'email', 'phone')

        Returns:
            Tuple of (masked_text, mapping_dict)
        """
        mapping = {}
        matches = re.finditer(pattern, text)

        # Process matches in reverse order to maintain string positions
        for match in reversed(list(matches)):
            original_value = match.group(0)
            
            # Skip if this exact value was already masked
            if original_value in [v for v in mapping.values()]:
                continue
            
            # Create placeholder
            self.placeholder_counter[pii_type] += 1
            placeholder = f"[{pii_type.upper()}_{self.placeholder_counter[pii_type]}]"
            
            # Replace in text
            text = text[: match.start()] + placeholder + text[match.end() :]
            mapping[placeholder] = original_value

        return text, mapping

    def restore_pii(self, text: str, pii_mapping: Dict[str, str]) -> str:
        """
        Restore original PII values in text using the mapping.

        Args:
            text: Text with placeholders
            pii_mapping: Dictionary mapping placeholders to original values

        Returns:
            Text with original PII values restored
        """
        restored_text = text
        
        # Sort by placeholder to ensure consistent restoration
        for placeholder, original_value in sorted(
            pii_mapping.items(), key=lambda x: x[0], reverse=True
        ):
            restored_text = restored_text.replace(placeholder, original_value)
        
        return restored_text

    def reset(self):
        """Reset the protector state."""
        self.pii_mapping = {}
        self.placeholder_counter = {key: 0 for key in self.PII_PATTERNS}


def mask_pii(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Convenience function to mask PII in text.

    Args:
        text: Input text potentially containing PII

    Returns:
        Tuple of (masked_text, pii_mapping)
    """
    protector = PIIProtector()
    return protector.mask_pii(text)


def restore_pii(text: str, pii_mapping: Dict[str, str]) -> str:
    """
    Convenience function to restore PII in text.

    Args:
        text: Text with PII placeholders
        pii_mapping: Dictionary mapping placeholders to original values

    Returns:
        Text with original PII restored
    """
    protector = PIIProtector()
    return protector.restore_pii(text, pii_mapping)
