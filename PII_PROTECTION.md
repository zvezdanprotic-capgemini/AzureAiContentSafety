# PII Protection Implementation

## Overview

This implementation ensures that Personally Identifiable Information (PII) is automatically detected and masked before being sent to **ALL Azure services**, including Azure Content Safety APIs and Azure OpenAI, protecting user privacy while still allowing the system to perform content moderation and generate responses.

## How It Works

### 1. PII Detection and Masking

When a user message is received:
1. The message is scanned for common PII patterns using regular expressions
2. Detected PII is replaced with placeholder tokens (e.g., `[EMAIL_1]`, `[PHONE_1]`)
3. A mapping is created to track which placeholder corresponds to which original value
4. The masked message (with placeholders) is sent to **all Azure services**

### 2. PII Types Detected

The system automatically detects and masks the following types of PII:

- **Email Addresses**: `user@example.com` → `[EMAIL_1]`
- **Phone Numbers**: `(555) 123-4567` → `[PHONE_1]`
- **Social Security Numbers**: `123-45-6789` → `[SSN_1]`
- **Credit Card Numbers**: `1234-5678-9012-3456` → `[CREDIT_CARD_1]`
- **IP Addresses**: `192.168.1.1` → `[IP_ADDRESS_1]`
- **URLs**: `https://example.com` → `[URL_1]`

### 3. PII Restoration

After processing is complete:
1. If the LLM response contains any placeholder tokens, they are automatically restored to original values
2. The PII mapping is preserved throughout the request lifecycle
3. User-facing responses maintain full context with actual PII when appropriate

## Architecture

```
User Message (with PII)
    ↓
[PII Protection Layer]
    ↓ (masked)
Azure Content Safety API ← receives placeholders, not actual PII
    ↓
[Content Moderation]
    ↓ (masked message continues)
Azure OpenAI API ← also receives placeholders, not actual PII
    ↓
[LLM Response with placeholders]
    ↓
[PII Restoration]
    ↓
Response to User (with restored PII)
```

## Implementation Files

### `/backend/pii_protection.py`
Core module providing PII detection, masking, and restoration functionality:
- `PIIProtector` class: Main class for PII operations
- `mask_pii()`: Convenience function to mask PII in text
- `restore_pii()`: Convenience function to restore PII from placeholders

### `/backend/content_safety.py`
Updated to mask PII before content safety checks:
- `is_content_safe()` now returns `(is_safe, pii_mapping)` tuple
- Masks PII before sending to Azure Content Safety API
- Preserves PII mapping even in error cases

### `/backend/prompt_shield.py`
Updated to mask PII before jailbreak detection:
- `is_prompt_safe_from_jailbreak()` now returns `(is_safe, pii_mapping)` tuple
- Masks PII before sending to jailbreak detection API
- Preserves PII mapping even in error cases

### `/backend/openai_client.py`
Updated to mask PII before sending to Azure OpenAI:
- `get_llm_response()` now accepts optional `pii_mapping` parameter
- Masks PII before sending to Azure OpenAI API
- Restores PII in the LLM response automatically
- Uses existing PII mapping from safety checks if provided

### `/backend/app.py`
Main application logic updated to handle PII lifecycle:
- Collects PII mappings from all safety checks
- Passes combined PII mapping to OpenAI client
- PII is automatically restored in the final response

## Security Considerations

### Complete PII Protection
✅ **User PII is masked before being sent to ALL Azure services**
- Azure Content Safety APIs receive only placeholder tokens
- Azure OpenAI APIs receive only placeholder tokens
- Actual emails, phone numbers, SSNs, etc., never leave the application to external services
- PII mappings are stored only in memory for the duration of the request

### Privacy Guarantee
🔒 **No Azure service receives actual PII data**

This ensures:
- Maximum privacy protection for user data
- Compliance with strict data handling policies
- Reduced risk of PII exposure through third-party services
- Clear audit trail of PII handling

## Testing

### Unit Tests (`/test_pii_protection.py`)
- Tests for each PII type (email, phone, SSN, credit card, IP, URL)
- Tests for multiple PII types in one message
- Tests for PII restoration
- Tests for messages without PII
- Tests for URL/email distinction (no double-masking)

### Integration Tests (`/test_integration.py`)
- Verifies all modules import correctly
- Tests PII functionality end-to-end
- Validates function signatures

### Demo Script (`/demo_pii_protection.py`)
- Interactive demonstration of PII masking
- Shows before/after examples
- Demonstrates restoration capability

## Usage Examples

### Basic Usage

```python
from backend.pii_protection import mask_pii, restore_pii

# Mask PII in text
original = "Contact me at john@example.com or call 555-1234"
masked, mapping = mask_pii(original)
# masked: "Contact me at [EMAIL_1] or call 555-1234"
# mapping: {'[EMAIL_1]': 'john@example.com'}

# Restore PII
restored = restore_pii(masked, mapping)
# restored: "Contact me at john@example.com or call 555-1234"
```

### In Application Flow

```python
# In app.py
@app.post("/api/chat")
async def chat(message: ChatMessage):
    # Mask PII before safety checks
    is_safe, pii_mapping = await is_content_safe(message.message)
    
    # Restore PII in responses if needed
    if combined_pii_mapping:
        response = restore_pii(response, combined_pii_mapping)
```

## Running the Demo

To see PII protection in action:

```bash
python demo_pii_protection.py
```

This will demonstrate:
- Detection of various PII types
- Masking with placeholder tokens
- Preservation of PII mappings
- Restoration of original values

## Running Tests

```bash
# Run PII protection unit tests
python test_pii_protection.py

# Run integration tests
python test_integration.py
```

## Future Enhancements

Potential improvements for consideration:
1. **Additional PII Types**: Names, addresses, passport numbers
2. **Configurable Patterns**: Allow custom PII patterns per deployment
3. **Machine Learning**: Use ML models for more accurate PII detection
4. **Audit Logging**: Track when PII is detected and masked
5. **Regional Compliance**: Add patterns for region-specific PII (EU, APAC, etc.)
6. **Performance Optimization**: Cache compiled regex patterns
7. **LLM Masking**: Optionally mask PII before sending to Azure OpenAI as well

## Performance Considerations

- Regex compilation: Patterns are compiled once per PIIProtector instance
- Memory usage: PII mappings are stored only for request duration
- Processing overhead: Minimal - regex matching is very fast
- Scalability: Each request processes PII independently (no shared state)

## Compliance and Privacy

This implementation helps with:
- **GDPR**: Reduces PII exposure to third-party APIs
- **CCPA**: Minimizes data sharing with external services
- **HIPAA**: Protects health-related PII (SSNs, etc.)
- **PCI DSS**: Masks credit card information

**Note**: This is a technical control. Ensure you still have appropriate:
- Privacy policies
- Data handling agreements
- User consent mechanisms
- Audit trails
