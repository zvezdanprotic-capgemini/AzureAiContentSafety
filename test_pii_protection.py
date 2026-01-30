"""Tests for PII Protection Module"""

import sys
import os

# Add parent directory to path to import backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.pii_protection import PIIProtector, mask_pii, restore_pii


def test_email_masking():
    """Test that emails are properly masked and restored."""
    text = "Contact me at john.doe@example.com for more info."
    masked, mapping = mask_pii(text)
    
    # Check that email is masked
    assert "john.doe@example.com" not in masked
    assert "[EMAIL_" in masked
    assert len(mapping) == 1
    
    # Check that we can restore it
    restored = restore_pii(masked, mapping)
    assert restored == text
    print(f"✓ Email test passed: {text} -> {masked} -> {restored}")


def test_phone_masking():
    """Test that phone numbers are properly masked and restored."""
    test_cases = [
        "Call me at 555-123-4567",
        "My number is (555) 123-4567",
        "Phone: 555.123.4567",
    ]
    
    for text in test_cases:
        masked, mapping = mask_pii(text)
        
        # Check that phone is masked
        assert "555" not in masked or "[PHONE_" in masked
        assert len(mapping) >= 1
        
        # Check that we can restore it
        restored = restore_pii(masked, mapping)
        assert restored == text
        print(f"✓ Phone test passed: {text} -> {masked}")


def test_multiple_pii_types():
    """Test masking multiple types of PII in one text."""
    text = "Email john@example.com or call 555-1234 or visit https://example.com"
    masked, mapping = mask_pii(text)
    
    # Should have masked email, phone, and url
    assert "john@example.com" not in masked
    assert len(mapping) >= 2  # At least email and phone/url
    
    # Check restoration
    restored = restore_pii(masked, mapping)
    assert restored == text
    print(f"✓ Multiple PII test passed: {len(mapping)} items masked")


def test_ssn_masking():
    """Test that SSNs are properly masked."""
    text = "My SSN is 123-45-6789"
    masked, mapping = mask_pii(text)
    
    assert "123-45-6789" not in masked
    assert "[SSN_" in masked
    assert len(mapping) == 1
    
    restored = restore_pii(masked, mapping)
    assert restored == text
    print(f"✓ SSN test passed: {text} -> {masked}")


def test_credit_card_masking():
    """Test that credit card numbers are properly masked."""
    text = "Card: 1234-5678-9012-3456"
    masked, mapping = mask_pii(text)
    
    assert "1234-5678-9012-3456" not in masked
    assert "[CREDIT_CARD_" in masked
    
    restored = restore_pii(masked, mapping)
    assert restored == text
    print(f"✓ Credit card test passed")


def test_no_pii():
    """Test that text without PII remains unchanged."""
    text = "This is a simple message with no personal information."
    masked, mapping = mask_pii(text)
    
    assert masked == text
    assert len(mapping) == 0
    print(f"✓ No PII test passed")


def test_ip_address_masking():
    """Test that IP addresses are properly masked."""
    text = "Server IP is 192.168.1.1 and backup is 10.0.0.5"
    masked, mapping = mask_pii(text)
    
    assert "192.168.1.1" not in masked
    assert "10.0.0.5" not in masked
    assert "[IP_ADDRESS_" in masked
    assert len(mapping) == 2
    
    restored = restore_pii(masked, mapping)
    assert restored == text
    print(f"✓ IP address test passed: masked {len(mapping)} IPs")


def test_url_masking():
    """Test that URLs are properly masked."""
    test_cases = [
        "Visit https://example.com for more info",
        "Check www.github.com/repo",
        "Go to http://test.org/path/to/page",
    ]
    
    for text in test_cases:
        masked, mapping = mask_pii(text)
        assert "[URL_" in masked
        assert len(mapping) >= 1
        
        restored = restore_pii(masked, mapping)
        assert restored == text
        print(f"✓ URL test passed: {text[:30]}...")


def test_url_doesnt_match_email():
    """Test that emails are not double-masked by URL pattern."""
    text = "Email: user@example.com"
    masked, mapping = mask_pii(text)
    
    # Should only have one mapping (email), not two (email + url)
    assert len(mapping) == 1
    assert "[EMAIL_" in masked
    assert "[URL_" not in masked
    print(f"✓ Email/URL distinction test passed")


def test_pii_protector_reset():
    """Test that PIIProtector can be reset between uses."""
    protector = PIIProtector()
    
    text1 = "Email: test@example.com"
    masked1, mapping1 = protector.mask_pii(text1)
    assert "[EMAIL_1]" in masked1
    
    protector.reset()
    
    text2 = "Another email: another@example.com"
    masked2, mapping2 = protector.mask_pii(text2)
    assert "[EMAIL_1]" in masked2  # Counter should reset
    print(f"✓ Reset test passed")


def run_all_tests():
    """Run all PII protection tests."""
    print("\n=== Running PII Protection Tests ===\n")
    
    try:
        test_email_masking()
        test_phone_masking()
        test_multiple_pii_types()
        test_ssn_masking()
        test_credit_card_masking()
        test_no_pii()
        test_ip_address_masking()
        test_url_masking()
        test_url_doesnt_match_email()
        test_pii_protector_reset()
        
        print("\n✓ All tests passed!\n")
        return True
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}\n")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
