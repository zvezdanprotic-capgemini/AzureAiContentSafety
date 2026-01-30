"""Integration test to verify the backend imports and basic functionality."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_imports():
    """Test that all backend modules can be imported."""
    print("Testing imports...")
    
    try:
        from backend.pii_protection import PIIProtector, mask_pii, restore_pii
        print("✓ pii_protection imported successfully")
        
        from backend.content_safety import is_content_safe
        print("✓ content_safety imported successfully")
        
        from backend.prompt_shield import is_prompt_safe_from_jailbreak
        print("✓ prompt_shield imported successfully")
        
        # Note: app.py requires environment variables, so we'll skip importing it
        # It will be validated when the app starts
        
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_pii_functionality():
    """Test basic PII functionality."""
    print("\nTesting PII functionality...")
    
    try:
        from backend.pii_protection import mask_pii, restore_pii
        
        # Test with a message containing PII
        original = "Contact me at john@example.com or call 555-1234"
        masked, mapping = mask_pii(original)
        
        print(f"Original: {original}")
        print(f"Masked: {masked}")
        print(f"Mappings: {mapping}")
        
        # Verify masking worked
        assert "john@example.com" not in masked, "Email should be masked"
        assert len(mapping) > 0, "Should have PII mappings"
        
        # Verify restoration works
        restored = restore_pii(masked, mapping)
        assert restored == original, "Restored text should match original"
        
        print("✓ PII functionality working correctly")
        return True
    except Exception as e:
        print(f"✗ PII functionality test failed: {e}")
        return False


def test_signature_compatibility():
    """Test that function signatures are compatible with the app."""
    print("\nTesting function signature compatibility...")
    
    try:
        from backend.content_safety import is_content_safe
        from backend.prompt_shield import is_prompt_safe_from_jailbreak
        import inspect
        
        # Check content_safety signature
        sig = inspect.signature(is_content_safe)
        params = list(sig.parameters.keys())
        assert 'text' in params, "is_content_safe should have 'text' parameter"
        print(f"✓ is_content_safe signature: {sig}")
        
        # Check prompt_shield signature
        sig = inspect.signature(is_prompt_safe_from_jailbreak)
        params = list(sig.parameters.keys())
        assert 'user_prompt' in params, "is_prompt_safe_from_jailbreak should have 'user_prompt' parameter"
        print(f"✓ is_prompt_safe_from_jailbreak signature: {sig}")
        
        return True
    except Exception as e:
        print(f"✗ Signature compatibility test failed: {e}")
        return False


def main():
    """Run all integration tests."""
    print("=== Backend Integration Tests ===\n")
    
    all_passed = True
    
    all_passed &= test_imports()
    all_passed &= test_pii_functionality()
    all_passed &= test_signature_compatibility()
    
    print("\n" + ("="*50))
    if all_passed:
        print("✓ All integration tests passed!")
        print("="*50 + "\n")
        return 0
    else:
        print("✗ Some tests failed")
        print("="*50 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
