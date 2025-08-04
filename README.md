# Insurance Plan AI Assistant API

A REST API for Insurance Plan Shopping Agent with AI capabilities, built with FastAPI and integrating with ChromaDB and OpenAI.

## Features

- REST API for chat-based insurance plan queries
- Automatic PDF document processing and embedding generation
- ChromaDB vector database for semantic search
- OpenAI integration for intelligent responses
- CORS support for Angular frontend integration
- Automatic database refresh on startup

## Setup and Installation

### Prerequisites

- Python 3.8+
- OpenAI API key
- PDF documents in `plan_documents/` directory

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd IFP-Plan-Shopping-Agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables**
   ```bash
   # Windows
   set OPENAI_API_KEY=your_openai_api_key_here
   
   # Linux/Mac
   export OPENAI_API_KEY=your_openai_api_key_here
   ```

5. **Prepare plan documents**
   - Create a `plan_documents/` directory
   - Place your insurance plan PDF files in this directory
   - Files will be automatically processed on startup

## Running the Application

### Development Mode
```bash
python main.py
```

### Production Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 8081
```

The API will be available at: `http://localhost:8081`

## API Endpoints

### Health Check
- **GET** `/` - Root health check
- **GET** `/health` - Detailed health status

### Chat API
- **POST** `/api/v1/chat` - Main chat endpoint
  
  **Request Body:**
  ```json
  {
    "query": "What is the deductible for the Gold plan?"
  }
  ```
  
  **Response:**
  ```json
  {
    "answer": "The Gold plan has a deductible of $1,000 for individuals...",
    "source_documents": [
      {
        "content": "Document excerpt...",
        "metadata": {"plan_id": "Gold_80_Trio_HMO", "page": 1},
        "plan_id": "Gold_80_Trio_HMO"
      }
    ]
  }
  ```

### Plans API
- **GET** `/api/v1/plans` - Get list of available plans
  
  **Response:**
  ```json
  {
    "plans": [
      {
        "plan_id": "Gold_80_Trio_HMO",
        "filename": "Gold_80_Trio_HMO.pdf"
      }
    ]
  }
  ```

## Frontend Integration

### Angular Service Example

```typescript
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private apiUrl = 'http://localhost:8081/api/v1';

  constructor(private http: HttpClient) {}

  sendMessage(query: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/chat`, {
      query: query
    });
  }

  getAvailablePlans(): Observable<any> {
    return this.http.get(`${this.apiUrl}/plans`);
  }
}
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY` - Required. Your OpenAI API key
- `CHROMA_DB_PATH` - Optional. Path for ChromaDB storage (default: "./chroma_db")
- `PLAN_DOCUMENTS_DIR` - Optional. Directory containing PDF files (default: "plan_documents")

### CORS Configuration

The API is configured to allow requests from:
- `http://localhost:4200` (Angular default)
- `http://localhost:3000` (React default)

To add more origins, modify the `allow_origins` list in `main.py`.

## Development

### Project Structure
```
IFP-Plan-Shopping-Agent/
├── main.py                          # FastAPI application
├── requirements.txt                 # Python dependencies
├── Embeddings/
│   ├── IFPPlanKnowledgeBase.py     # Main knowledge base class
│   ├── VectorDatabaseManager.py     # ChromaDB management
│   ├── DocumentChunker.py          # Legacy document chunking logic
│   └── DocumentChunkerV2.py        # Advanced proposition-based chunking
├── Extraction/
│   ├── PlanDocumentPipeline.py     # Document processing pipeline
│   ├── PlanDocumentProcessor.py    # PDF processing
│   └── PlanInformationExtractor.py # Information extraction
└── plan_documents/                  # PDF files directory
```

### Adding New Features

1. Add new endpoints in `main.py`
2. Extend the knowledge base functionality in `Embeddings/`
3. Add new document processing capabilities in `Extraction/`

## Troubleshooting

### Common Issues

1. **"OPENAI_API_KEY not set"**
   - Ensure the environment variable is properly set
   - Check that the API key is valid

2. **"Knowledge base not initialized"**
   - Check if PDF files exist in `plan_documents/` directory
   - Verify file permissions

3. **CORS errors**
   - Ensure your frontend URL is in the `allow_origins` list
   - Check that the API is running on the expected port

4. **SSL Certificate errors**
   - Update certificates: `pip install --upgrade certifi`
   - Set `REQUESTS_CA_BUNDLE` if behind corporate firewall

### Logs

The application logs important events including:
- Startup progress
- Document processing status
- API request/response information
- Error details

## Production Deployment

For production deployment, consider:

1. **Environment Variables**: Use proper secret management
2. **Database**: Consider persistent storage for ChromaDB
3. **Security**: Add authentication and authorization
4. **Monitoring**: Implement proper logging and monitoring
5. **Scaling**: Use proper ASGI server configuration

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8081/docs`
- ReDoc: `http://localhost:8081/redoc`
