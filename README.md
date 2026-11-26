# Smart Study Buddy

An AI-powered, document-grounded study assistant that helps students understand lecture notes, ask questions, generate practice quizzes, and maintain conversational context across study sessions.

## Features

- **Retrieval-Augmented Generation (RAG):** Retrieves relevant information from uploaded lecture notes using semantic similarity search.
- **Document Ingestion:** Loads, splits, and processes lecture-note text files using LangChain components.
- **Vector Search:** Stores and retrieves document embeddings using Pinecone.
- **AI-Powered Question Answering:** Uses OpenAI to generate answers grounded in retrieved lecture-note content.
- **Conversational Memory:** Maintains context across multiple messages within the same conversation using SQLite-backed session history.
- **Conversation Isolation:** Keeps separate conversations independent of one another.
- **Conversation History:** Saves and retrieves previous conversations and messages.
- **Automatic Conversation Titles:** Generates conversation titles from the first user message.
- **Quiz Generation:** Creates multiple-choice quizzes from relevant lecture notes, including answers and explanations.
- **Source References:** Displays the lecture-note sources used to generate answers.

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Frontend | React, Vite |
| Backend | FastAPI |
| LLM | OpenAI API (GPT-4o-mini by default) |
| Embedding Model | sentence-transformers/all-MiniLM-L6-v2 |
| Vector Database | Pinecone |
| Document Processing | LangChain Community, LangChain Text Splitters |
| Conversation Storage | SQLite |
| API Server | Uvicorn |

## Architecture

1. The student submits a question through the React frontend.
2. FastAPI receives the question and active conversation details.
3. The embedding model converts the question into a vector.
4. Pinecone retrieves relevant lecture-note chunks.
5. FastAPI retrieves previous messages from the same conversation using SQLite.
6. Retrieved document context and conversation history are supplied to OpenAI.
7. OpenAI generates a response grounded in the available lecture notes and relevant conversation context.
8. The assistant response is saved in SQLite and displayed in the frontend.

## Project Structure

```text
IK_LLM_ASSIGNMENT/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── ingest_notes.py
│   └── chat_history.db       # Generated locally; not committed
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   ├── package.json
│   └── ...
│
├── input_lecture_notes/
│   ├── biology_notes.txt
│   ├── computer_science_notes.txt
│   ├── physics_notes.txt
│   ├── sample_lecture.txt
│   └── sample_lecture1.txt
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.12 or compatible version
- Node.js and npm
- OpenAI API key
- Pinecone account and API key

## Installation and Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd IK_LLM_ASSIGNMENT
```

### 2. Create a Python virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root using `.env.example` as a template.

```env
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
OPENAI_MODEL=gpt-4o-mini
```

Do not upload your actual `.env` file or API keys to GitHub.

### 5. Configure Pinecone

Create a Pinecone index with the following configuration:

- Index name: `smart-study-buddy-notes`
- Dimension: `384`
- Metric: `cosine`
- Vector type: Dense

The embedding model used is `sentence-transformers/all-MiniLM-L6-v2`.

### 6. Ingest lecture notes

From the project root, run:

```bash
python -m backend.ingest_notes
```

The current ingestion script processes the Biology, Computer Science, and Physics note files.

### 7. Start the FastAPI backend

From the project root:

```bash
python -m uvicorn backend.main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/api/health
```

### 8. Install frontend dependencies

Open a second terminal:

```bash
cd frontend
npm install
```

### 9. Start the React frontend

```bash
npm run dev
```

Open the application:

```text
http://localhost:5173/
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Check backend status |
| POST | `/api/chat` | Ask questions using RAG and conversational memory |
| POST | `/api/quiz` | Generate multiple-choice quizzes |
| POST | `/api/conversations` | Create a conversation |
| GET | `/api/conversations` | Retrieve conversation history |
| POST | `/api/conversations/{conversation_id}/messages` | Save a conversation message |
| GET | `/api/conversations/{conversation_id}/messages` | Retrieve messages from a conversation |

## Conversational Memory

Smart Study Buddy uses SQLite to persist conversation messages.

For each chat request:

- The frontend sends the active conversation ID and current saved message ID.
- The backend retrieves up to 10 previous messages from that conversation.
- Previous messages are supplied to the LLM along with the retrieved lecture-note context.
- A new conversation starts with independent conversation history.

This enables multi-turn interactions while keeping separate study sessions isolated.

## Testing and Validation

The following functionality has been manually tested:

- Backend startup and health endpoint.
- Frontend application startup.
- Pinecone retrieval and source references.
- Academic question answering using lecture notes.
- Quiz generation with five multiple-choice questions.
- SQLite conversation persistence.
- Automatic conversation title generation.
- Multi-turn conversational memory.
- Conversation isolation between new and existing sessions.

The current project contains five lecture-note text files, while the ingestion script processes three of them.

## Security

- API keys are stored in a local `.env` file.
- `.env` is excluded from Git tracking.
- Virtual environments, frontend dependencies, build output, and SQLite database files are excluded through `.gitignore`.
- `.env.example` provides placeholder configuration only.

## Future Improvements

- Support PDF lecture-note ingestion.
- Add automated backend and frontend tests.
- Evaluate retrieval relevance using a larger question-answer test set.
- Add document upload functionality.
- Improve conversational memory management for longer sessions.
- Deploy the application to a cloud platform.

## Author

**Shahanaz Begum**

Computer Science and Engineering | Generative AI | Python | RAG | FastAPI
