# Smart Study Buddy 📚

An AI-powered study assistant that helps students understand lecture notes, ask questions, generate quizzes, and revisit previous conversations using Retrieval-Augmented Generation (RAG).

## 🚀 Project Overview

Smart Study Buddy uses semantic search and Large Language Models to provide answers grounded in uploaded lecture notes. It retrieves relevant content from a Pinecone vector database and generates contextual responses using the OpenAI API.

The application also supports subject-wise retrieval, quiz generation, conversation history, and session-based conversational memory.

## ✨ Features

- **AI Question Answering:** Ask questions about uploaded lecture notes.
- **RAG Pipeline:** Retrieve relevant document chunks using semantic similarity.
- **Subject-wise Retrieval:** Filter content by Biology, Physics, and Computer Science.
- **AI Quiz Generation:** Generate multiple-choice quizzes from selected subjects.
- **Source References:** Display the lecture-note sources used to generate answers.
- **Conversation History:** Save and reopen previous conversations.
- **Conversational Memory:** Maintain context within a conversation.
- **Conversation Isolation:** Keep separate conversations independent.
- **Out-of-Scope Handling:** Indicate when information is unavailable in the uploaded notes.

## 🛠️ Technology Stack

| Component | Technologies |
|---|---|
| Frontend | React, Vite, JavaScript |
| Backend | Python, FastAPI |
| LLM | OpenAI API, GPT-4o-mini |
| Vector Database | Pinecone |
| Embeddings | Sentence Transformers, all-MiniLM-L6-v2 |
| RAG | Semantic search and vector retrieval |
| Database | SQLite |
| API | REST API |

## 🏗️ System Architecture

```text
             STUDENT
                |
                v
        REACT FRONTEND
                |
                v
         FASTAPI BACKEND
                |
          User Question
                |
                v
       SENTENCE TRANSFORMERS
          (Embeddings)
                |
                v
         PINECONE VECTOR DB
                |
        Relevant Note Chunks
                |
                v
           OPENAI API
                |
        Generated Response
                |
                v
          REACT FRONTEND
                |
                v
       ANSWER + SOURCE REFERENCES
```

SQLite stores conversation and message history.

## 📂 Project Structure

```text
IK_LLM_ASSIGNMENT/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   └── ingest_notes.py
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── input_lecture_notes/
│   ├── biology_notes.txt
│   ├── computer_science_notes.txt
│   └── physics_notes.txt
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Shehnaaz218/Smart-Study-Buddy.git
cd Smart-Study-Buddy
```

### 2. Set up the Python environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root using `.env.example` as a reference.

Add your credentials:

```env
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
```

Never commit your actual `.env` file or API keys to GitHub.

### 4. Start the backend

From the project root:

```bash
python -m uvicorn backend.main:app --reload
```

Backend URL:

`http://127.0.0.1:8000`

API documentation:

`http://127.0.0.1:8000/docs`

### 5. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

`http://localhost:5173`

## 🧪 Tested Functionality

The following functional checks were completed during development:

- Physics, Biology, and Computer Science question answering.
- Subject-specific source retrieval.
- Subject-specific quiz generation.
- Out-of-scope question handling.
- Conversation memory within a session.
- Isolation between separate conversations.

These are functional checks, not a formal benchmark of retrieval accuracy.

## 🔮 Future Enhancements

- Support PDF and DOCX lecture-note uploads.
- Add automated RAG evaluation metrics.
- Improve retrieval ranking and answer relevance.
- Add user authentication.
- Deploy the application to a cloud platform.

## 👩‍💻 Author

**Shaik Shahanaz Begum**

GitHub: [Shehnaaz218](https://github.com/Shehnaaz218)

## 📌 Repository

[Smart Study Buddy – GitHub](https://github.com/Shehnaaz218/Smart-Study-Buddy)
