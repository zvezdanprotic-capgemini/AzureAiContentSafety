#!/usr/bin/env python3
"""
Demonstration of PII Protection Feature

This script demonstrates how PII is masked before being sent to ALL Azure services
(Content Safety, OpenAI, etc.) and how it is restored in responses.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from backend.pii_protection import mask_pii, restore_pii


def print_separator(char="-", length=80):
    """Print a separator line."""
    print(char * length)


def demonstrate_pii_masking():
    """Demonstrate PII masking with various examples."""
    print("\n" + "=" * 80)
    print("PII PROTECTION DEMONSTRATION")
    print("=" * 80 + "\n")
    
    examples = [
        {
            "name": "Email Address",
            "text": "Please contact me at john.doe@example.com for more information.",
        },
        {
            "name": "Phone Number",
            "text": "You can reach me at (555) 123-4567 or 555-987-6543.",
        },
        {
            "name": "Social Security Number",
            "text": "My SSN is 123-45-6789 for verification purposes.",
        },
        {
            "name": "Credit Card",
            "text": "Use card number 1234-5678-9012-3456 for the payment.",
        },
        {
            "name": "IP Address",
            "text": "The server is located at 192.168.1.100 and backup at 10.0.0.50.",
        },
        {
            "name": "URL",
            "text": "Visit https://example.com/profile or www.github.com/user.",
        },
        {
            "name": "Multiple PII Types",
            "text": "Contact John at john@example.com, call 555-1234, or visit https://john-doe.com.",
        },
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['name']}")
        print_separator()
        
        original = example["text"]
        masked, mapping = mask_pii(original)
        restored = restore_pii(masked, mapping)
        
        print(f"\n📝 Original Message:")
        print(f"   {original}")
        
        print(f"\n🔒 Masked Message (sent to ALL Azure services):")
        print(f"   {masked}")
        
        print(f"\n🔑 PII Mappings:")
        if mapping:
            for placeholder, value in mapping.items():
                print(f"   {placeholder} → {value}")
        else:
            print("   (none)")
        
        print(f"\n✅ Restored Message:")
        print(f"   {restored}")
        
        # Verify restoration
        if restored == original:
            print(f"\n✓ Restoration successful!")
        else:
            print(f"\n✗ Restoration failed!")
        
        print_separator()
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80 + "\n")
    
    print("Summary:")
    print("--------")
    print("✓ PII is automatically detected and masked before sending to ALL Azure services")
    print("✓ This includes: Azure Content Safety, Azure OpenAI, and all other Azure APIs")
    print("✓ Masked placeholders (e.g., [EMAIL_1], [PHONE_1]) are sent instead of real data")
    print("✓ Original PII is restored in user-facing responses for proper context")
    print("✓ Supported PII types: Email, Phone, SSN, Credit Card, IP Address, URL")
    print()


if __name__ == "__main__":
    demonstrate_pii_masking()
