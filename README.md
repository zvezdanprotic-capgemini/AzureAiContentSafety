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

1. Create a `.env` file in the root directory with your Azure credentials:
```env
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_KEY=your_key
AZURE_OPENAI_DEPLOYMENT=your_deployment
AZURE_CONTENT_SAFETY_ENDPOINT=your_endpoint
AZURE_CONTENT_SAFETY_KEY=your_key
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Run the backend:
```bash
uvicorn app:app --reload
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
- Content safety checking using Azure Content Moderator
- LLM responses using Azure OpenAI
- Modern UI with Chakra UI
- TypeScript support
- Fully asynchronous backend