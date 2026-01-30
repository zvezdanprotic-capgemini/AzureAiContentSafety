"""Test PII protection for Azure OpenAI calls."""

import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))


async def test_openai_masks_pii():
    """Test that OpenAI client masks PII before sending to Azure OpenAI."""
    from backend.openai_client import get_llm_response
    
    print("\n=== Testing OpenAI PII Masking ===\n")
    
    # Mock the Azure OpenAI client
    with patch('backend.openai_client._get_client') as mock_get_client:
        # Create a mock client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Sure, I can help with that!"
        
        # Make the create method async
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        # Test with PII in message
        user_message = "Contact me at john@example.com or call 555-1234"
        response = await get_llm_response(user_message)
        
        # Verify the client was called
        assert mock_client.chat.completions.create.called
        
        # Get the actual message sent to OpenAI
        call_args = mock_client.chat.completions.create.call_args
        messages_sent = call_args.kwargs['messages']
        actual_message = messages_sent[0]['content']
        
        print(f"Original message: {user_message}")
        print(f"Message sent to Azure OpenAI: {actual_message}")
        
        # Verify PII was masked
        assert "john@example.com" not in actual_message, "Email should be masked"
        assert "[EMAIL_" in actual_message, "Email placeholder should be present"
        
        print("✓ PII was masked before sending to Azure OpenAI")
        
        # Verify response was returned
        assert response == "Sure, I can help with that!"
        print("✓ Response was returned correctly")
        
    return True


async def test_openai_with_existing_mapping():
    """Test that OpenAI client uses existing PII mapping."""
    from backend.openai_client import get_llm_response
    
    print("\n=== Testing OpenAI with Existing Mapping ===\n")
    
    with patch('backend.openai_client._get_client') as mock_get_client:
        mock_client = MagicMock()
        mock_response = MagicMock()
        # Response that might reference the PII placeholder
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "I'll contact you at [EMAIL_1]"
        
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        # Provide existing PII mapping (as would come from safety checks)
        existing_mapping = {'[EMAIL_1]': 'john@example.com'}
        user_message = "Send me info at john@example.com"
        
        response = await get_llm_response(user_message, existing_mapping)
        
        print(f"Original message: {user_message}")
        print(f"LLM response (raw): I'll contact you at [EMAIL_1]")
        print(f"LLM response (restored): {response}")
        
        # Verify the placeholder was restored in the response
        assert "[EMAIL_1]" not in response, "Placeholder should be restored"
        assert "john@example.com" in response, "Original email should be in response"
        
        print("✓ PII placeholder was restored in the response")
        
    return True


async def test_openai_no_pii():
    """Test that messages without PII work normally."""
    from backend.openai_client import get_llm_response
    
    print("\n=== Testing OpenAI without PII ===\n")
    
    with patch('backend.openai_client._get_client') as mock_get_client:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello! How can I help you?"
        
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        user_message = "What is the weather like today?"
        response = await get_llm_response(user_message)
        
        # Get the actual message sent
        call_args = mock_client.chat.completions.create.call_args
        messages_sent = call_args.kwargs['messages']
        actual_message = messages_sent[0]['content']
        
        print(f"Original message: {user_message}")
        print(f"Message sent to Azure OpenAI: {actual_message}")
        
        # Verify message is unchanged when no PII
        assert actual_message == user_message, "Message without PII should be unchanged"
        print("✓ Message without PII was sent unchanged")
        
        assert response == "Hello! How can I help you?"
        print("✓ Response was returned correctly")
        
    return True


async def main():
    """Run all OpenAI PII protection tests."""
    print("\n" + "="*60)
    print("OpenAI PII Protection Tests")
    print("="*60)
    
    try:
        await test_openai_masks_pii()
        await test_openai_with_existing_mapping()
        await test_openai_no_pii()
        
        print("\n" + "="*60)
        print("✓ All OpenAI PII protection tests passed!")
        print("="*60 + "\n")
        return True
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}\n")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
