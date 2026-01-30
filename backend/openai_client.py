import os
from typing import Dict
from openai import AsyncAzureOpenAI

from .env import load_env
from .pii_protection import mask_pii, restore_pii

load_env()


def _get_client() -> AsyncAzureOpenAI:
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

    # Let the SDK raise a clear error if any required value is missing.
    return AsyncAzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=azure_endpoint,
    )


async def get_llm_response(user_message: str, pii_mapping: Dict[str, str] = None) -> str:
    """
    Get LLM response from Azure OpenAI with PII protection.
    
    Args:
        user_message: The user's message (may contain PII)
        pii_mapping: Optional existing PII mapping from safety checks.
                     If provided, will be used; otherwise will mask PII from scratch.
    
    Returns:
        LLM response with PII restored if it was masked
    """
    try:
        # If no PII mapping provided, mask PII in the message
        if pii_mapping is None:
            masked_message, pii_mapping = mask_pii(user_message)
        else:
            # Use existing mapping to mask the message
            masked_message, new_mapping = mask_pii(user_message)
            # Merge any new PII found with existing mapping
            pii_mapping = {**pii_mapping, **new_mapping}
        
        print(f"Sending to Azure OpenAI - Original length: {len(user_message)}, Masked length: {len(masked_message)}")
        if pii_mapping:
            print(f"Protected {len(pii_mapping)} PII items from Azure OpenAI")
        
        # Send masked message to Azure OpenAI
        client = _get_client()
        response = await client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[{"role": "user", "content": masked_message}],
        )
        
        llm_response = response.choices[0].message.content
        
        # Restore any PII placeholders in the response
        if pii_mapping and llm_response:
            restored_response = restore_pii(llm_response, pii_mapping)
            return restored_response
        
        return llm_response
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        return "⚠️ Sorry, I couldn't process your request."
