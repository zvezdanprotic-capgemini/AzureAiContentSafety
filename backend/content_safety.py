import os
from typing import Dict, Tuple

from azure.ai.contentsafety.aio import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions, TextCategory
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

from .env import load_env
from .pii_protection import mask_pii

load_env()


async def is_content_safe(text: str) -> Tuple[bool, Dict[str, str]]:
    """
    Check if content is safe using Azure Content Safety API.
    
    Args:
        text: The text to check for safety
        
    Returns:
        Tuple of (is_safe, pii_mapping) where:
        - is_safe: True if content is safe, False otherwise
        - pii_mapping: Dictionary mapping PII placeholders to original values
    """
    key = os.environ["AZURE_CONTENT_SAFETY_KEY"]
    endpoint = os.environ["AZURE_CONTENT_SAFETY_ENDPOINT"]
    
    # Mask PII before sending to Azure Content Safety
    masked_text, pii_mapping = mask_pii(text)
    
    print(f"Original text length: {len(text)}, Masked text length: {len(masked_text)}")
    if pii_mapping:
        print(f"Masked {len(pii_mapping)} PII items")

    # Create an async Content Safety client
    async with ContentSafetyClient(endpoint, AzureKeyCredential(key)) as client:
        # Construct request with masked text
        request = AnalyzeTextOptions(text=masked_text)

        try:
            response = await client.analyze_text(request)

            # Check for high severity in any category
            categories = {
                TextCategory.HATE: 0,
                TextCategory.SELF_HARM: 0,
                TextCategory.SEXUAL: 0,
                TextCategory.VIOLENCE: 0,
            }

            for result in response.categories_analysis:
                categories[result.category] = result.severity

            # Return False if any category has severity >= 2 (moderate to high severity)
            is_safe = all(severity < 2 for severity in categories.values())
            return is_safe, pii_mapping

        except HttpResponseError as e:
            print(f"Content Safety API error: {str(e)}")
            return False, {}
        except Exception as e:
            print(f"Unexpected error in content safety check: {str(e)}")
            return False, {}
