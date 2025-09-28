import os
from azure.ai.contentsafety.aio import ContentSafetyClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from azure.ai.contentsafety.models import AnalyzeTextOptions, TextCategory
from dotenv import load_dotenv

load_dotenv()

async def is_content_safe(text: str) -> bool:
    key = os.environ["AZURE_CONTENT_SAFETY_KEY"]
    endpoint = os.environ["AZURE_CONTENT_SAFETY_ENDPOINT"]

    # Create an async Content Safety client
    async with ContentSafetyClient(endpoint, AzureKeyCredential(key)) as client:
        # Construct request
        request = AnalyzeTextOptions(text=text)

        try:
            response = await client.analyze_text(request)
            
            # Check for high severity in any category
            categories = {
                TextCategory.HATE: 0,
                TextCategory.SELF_HARM: 0,
                TextCategory.SEXUAL: 0,
                TextCategory.VIOLENCE: 0
            }
            
            for result in response.categories_analysis:
                categories[result.category] = result.severity

            # Return False if any category has severity >= 2 (moderate to high severity)
            return all(severity < 2 for severity in categories.values())
                
        except HttpResponseError as e:
            print(f"Content Safety API error: {str(e)}")
            return False
        except Exception as e:
            print(f"Unexpected error in content safety check: {str(e)}")
            return False
