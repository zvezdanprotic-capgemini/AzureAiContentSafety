# Safe LLM Bot with React Frontend

This project consists of a Python FastAPI backend that provides a safe LLM chat interface using Azure OpenAI and Azure Content Safety, and a React frontend for the chat interface.

## Project Structure

```
.
├── frontend/          # React frontend application
└── backend/          # Python FastAPI backend
    ├── app.py        # Main FastAPI application
    ├── content_safety.py  # Content safety checking
    └── openai_client.py   # OpenAI client configuration
```

## Setup

### Backend

1. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Create a `.env` file in the root directory with your Azure credentials:
```env
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment
AZURE_CONTENT_SAFETY_ENDPOINT=your_endpoint
AZURE_CONTENT_SAFETY_KEY=your_key

# Optional: if you already have an Azure OpenAI "API base" URL from another sample,
# you can set this instead of AZURE_OPENAI_ENDPOINT and the backend will derive it.
# AZURE_OPENAI_API_BASE=https://<resource>.openai.azure.com/openai/v1/
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Run the backend:
```bash
uvicorn backend.app:app --reload
```

### Frontend

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at http://localhost:5173 and will connect to the backend at http://localhost:8000.

## Features

- Real-time chat interface
- **PII Protection**: Automatically masks personally identifiable information before sending to Azure Content Safety
- Content safety checking using Azure Content Moderator
- Jailbreak attempt detection
- LLM responses using Azure OpenAI
- Modern UI with Chakra UI
- TypeScript support
- Fully asynchronous backend

### PII Protection

The application automatically detects and masks PII (emails, phone numbers, SSNs, credit cards, IP addresses, URLs) before sending messages to Azure Content Safety APIs. This ensures user privacy while still allowing effective content moderation.

For detailed information, see [PII_PROTECTION.md](PII_PROTECTION.md).