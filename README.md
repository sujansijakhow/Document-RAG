# Palm Mind RAG Backend

A small FastAPI backend for document search and conversational interview booking.

## What it does

The project exposes two main endpoints:

- `POST /api/v1/documents/upload` accepts PDF and TXT files, extracts their text,
  splits it with a selected chunking strategy, creates embeddings, and stores the
  chunks in Qdrant with document metadata in SQLite.
- `POST /api/v1/chat` answers questions about uploaded documents and handles
  multi-turn interview booking. Booking details are stored in SQLite and chat
  history is kept in Redis.

There is also `GET /api/v1/bookings` for checking saved bookings and `GET /health`
for a basic service check.

## Technology

- FastAPI and Uvicorn
- SQLAlchemy with SQLite
- Qdrant in local persistent mode
- Redis
- `pypdf` for PDF extraction
- Sentence Transformers for local embeddings
- Ollama for local LLM responses

The LLM provider is behind a small interface. OpenAI can be selected through the
environment if needed, but the default setup uses Ollama and does not require an
API key.

## Run locally

Create and activate a virtual environment, then install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
```

Copy `.env.example` to `.env`. The default values are set up for local development
with Ollama, SQLite, Qdrant, and Redis.

Start Redis:

```powershell
docker compose up -d redis
```

Install Ollama, download the model, and make sure Ollama is running:

```powershell
ollama pull llama3.1
```

Ollama normally runs as a background service on Windows. If it is not running,
start it with `ollama serve`.

Start the API:

```powershell
uvicorn app.main:app --reload
```

Open the interactive API documentation at <http://127.0.0.1:8000/docs>.

## Examples

Upload a document with the recursive chunker:

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/v1/documents/upload `
  -F "file=@sample.pdf" `
  -F "chunking_strategy=recursive_paragraph"
```

The other option is `fixed_size`.

Ask a question about the uploaded documents:

```powershell
$body = @{ session_id = "demo-1"; message = "What is this document about?" } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8000/api/v1/chat -Method Post `
  -ContentType "application/json" -Body $body
```

Start an interview booking in the same chat endpoint. The assistant collects the
name, email, date, and time over one or more messages. Check saved bookings with:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/bookings
```

## Tests

Run the test suite with:

```powershell
python -m pytest
```

The project does not use FAISS, Chroma, or `RetrievalQAChain`.

## Configuration

Keep `.env` local. It is ignored by Git. `.env.example` contains safe default
values and no secrets.

To use OpenAI instead of Ollama, set these values in `.env`:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4o-mini
```
