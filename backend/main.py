

import os
from pathlib import Path
from functools import lru_cache
import json
from backend.database import initialize_database,get_connection

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from openai import OpenAI

# Load the .env file from the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

INDEX_NAME = "smart-study-buddy-notes"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


@lru_cache(maxsize=1)
def get_embedding_model():
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


@lru_cache(maxsize=1)
def get_pinecone_index():
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise RuntimeError("PINECONE_API_KEY is missing from the project .env file.")
    return Pinecone(api_key=api_key).Index(INDEX_NAME)


app = FastAPI(title="Smart Study Buddy API")

@app.on_event("startup")
def startup_event():
    initialize_database()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str
    conversation_id: int
    before_message_id: int


class QuizRequest(BaseModel):
    topic: str
    num_questions: int


def detect_subject(question: str):
    question = question.lower()

    subject_keywords = {
        "biology": [
            "cell", "cells", "nucleus", "mitochondria",
            "chloroplast", "photosynthesis", "cell membrane",
            "dna", "biology"
        ],
        "physics": [
            "newton", "force", "gravity", "motion",
            "acceleration", "mass", "velocity",
            "physics"
        ],
        "computer_science": [
            "python", "list", "tuple", "dictionary",
            "set", "algorithm", "time complexity",
            "programming", "computer science"
        ]
    }

    for subject, keywords in subject_keywords.items():
        if any(keyword in question for keyword in keywords):
            return subject

    return None


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "message": "Smart Study Buddy backend is running",
        "index": INDEX_NAME,
    }


@app.post("/api/chat")
def chat(request: ChatRequest):
    question = request.question.strip()

    if not question:
        return {"answer": "Please enter a question."}

    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is missing from the project .env file.",
        )

    try:
        # 1. Convert the question to a 384-dimensional embedding.
        model = get_embedding_model()
        query_vector = model.encode(
            question,
            normalize_embeddings=False,
        ).tolist()

        if len(query_vector) != 384:
            raise RuntimeError(
                f"Expected 384 embedding values, got {len(query_vector)}."
            )

        # 2. Retrieve relevant lecture-note chunks from Pinecone.
        subject = detect_subject(question)
        print("DEBUG QUESTION:", question)
        print("DEBUG DETECTED SUBJECT:", subject)
        query_args = {
            "vector": query_vector,
            "top_k": 5,
            "include_metadata": True,
        }

        if subject:
            query_args["filter"] = {
                "source": {"$eq": f"{subject}_notes.txt"}
            }

        results = get_pinecone_index().query(**query_args)
        print("DEBUG PINECONE FILTER:", query_args.get("filter"))
        context_parts = []
        sources = []

        # Minimum similarity score for accepting a retrieved chunk.
        SIMILARITY_THRESHOLD = 0.15
        print("\n========== PINECONE RETRIEVAL DEBUG ==========", flush=True)

        for match in results.get("matches", []):
            metadata = match.get("metadata") or {}
            score = match.get("score")
            text = (
                metadata.get("text")
                or metadata.get("page_content")
                or metadata.get("content")
            )
            # Display retrieved results for debugging.
            print("Source:", metadata.get("source"), flush=True)
            print("Score:", score, flush=True)
            print("Text:", (text or "")[:200], flush=True)
            print("----------------------------------------------", flush=True)
            # Skip results with insufficient relevance.
            if score is None or score < SIMILARITY_THRESHOLD:
                continue
            if not text:
                continue
            source = metadata.get("source", "Lecture notes")

            # Add only relevant chunks to the AI context.
            context_parts.append(f"Source: {source}\n{text}")
            # Display each relevant filename only once.
            if not any(s["source"] == source for s in sources):
                sources.append({
                    "source": source,
                    "snippet": text[:120].strip()
                    + ("..." if len(text) > 120 else ""),
                    "score": round(float(score), 4),
                })

        print("========== END RETRIEVAL DEBUG ==========\n", flush=True)


        context = "\n\n---\n\n".join(context_parts)

        # 3. Retrieve previous messages from this conversation.
        with get_connection() as connection:
            history_rows = connection.execute(
                """
                SELECT role, content
                FROM messages
                WHERE conversation_id = ?
                AND id < ?
                ORDER BY id DESC
                LIMIT 10
                """,
                (request.conversation_id, request.before_message_id)
            ).fetchall()

            # Restore chronological order for the AI.
        conversation_history = [
            {"role": row["role"], "content": row["content"]}
            for row in reversed(history_rows)
        ]

        # 4. Allow personal-memory questions even without matching notes.
        if not context_parts and not conversation_history:
            return {
                "answer": (
                    "I couldn't find relevant information in your "
                    "lecture notes or this conversation."
                ),
                "sources": [],
            }


        # 5. Generate an answer grounded in the retrieved notes.
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Smart Study Buddy, a lecture-note-based study assistant. "
 "You are Smart Study Buddy, a lecture-note-based study assistant. "
"Use previous conversation messages to remember information "
"explicitly shared by the student, such as their name, preferences, "
"and earlier questions. Use this conversation history only for "
"personal context and continuity. For academic questions about "
"lecture topics, use only information explicitly supported by the "
"supplied lecture-note context. Do not introduce unsupported "
"academic facts from general knowledge. If the lecture notes do not "
"contain the requested academic information, clearly say: "
"'This information is not available in your uploaded lecture notes.' "
"Explain available information in simple language while preserving "
"the meaning of the original notes."
                    ),
                },
                *conversation_history,
                {
        "role": "user",
        "content": (
            f"Lecture-note context:\n{context}\n\n"
            f"Student's question: {question}"
        ),
    },

                {
                    "role": "user",
                    "content": (
                        f"Lecture-note context:\n{context}\n\n"
                        f"Student's question: {question}"
                    ),
                },
            ],
            temperature=0.2,
        )

        answer = response.choices[0].message.content

        return {
            "answer": answer or "I couldn't generate an answer. Please try again.",
            "sources": sources,
        }

    except Exception as exc:
        # Details appear in the backend terminal, not in the public response.
        print(f"Smart Study Buddy error: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=500,
            detail=(
                "The study assistant encountered an error. "
                "Check the backend terminal for details."
            ),
        )

@app.post("/api/quiz")
def generate_quiz(request: QuizRequest):
    topic = request.topic.strip() or "all lecture notes"

    if not 1 <= request.num_questions <= 10:
        raise HTTPException(
            status_code=400,
            detail="num_questions must be between 1 and 10.",
        )

    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is missing from the project .env file.",
        )

    try:
        # 1. Convert the topic into an embedding.
        model = get_embedding_model()
        query_vector = model.encode(
            topic,
            normalize_embeddings=False,
        ).tolist()

        # 2. Retrieve relevant lecture notes from Pinecone.
        subject = detect_subject(topic)

        query_args = {
            "vector": query_vector,
            "top_k": 5,
            "include_metadata": True,
        }
        if subject:
            query_args["filter"] = {
                "source": {"$eq": f"{subject}_notes.txt"}
            }
        results = get_pinecone_index().query(**query_args)

        SIMILARITY_THRESHOLD = 0.15
        context_parts = []

        print("\n========== QUIZ RETRIEVAL DEBUG ==========", flush=True)

        for match in results.get("matches", []):
            metadata = match.get("metadata") or {}
            score = match.get("score")
            note_text = (
                metadata.get("text")
                or metadata.get("page_content")
                or metadata.get("content")
            )
            source = metadata.get("source", "Lecture notes")

            print("Source:", source, flush=True)
            print("Score:", score, flush=True)

            # Skip results with insufficient relevance.
            if score is None or score < SIMILARITY_THRESHOLD:
                print("Skipped: Low similarity", flush=True)
                continue
            if not note_text:
                continue

            # Add only relevant chunks to the quiz context.
            context_parts.append(f"Source: {source}\n{note_text}")
            print("Included in quiz context", flush=True)

        print("Relevant chunks:", len(context_parts), flush=True)
        print("========== END QUIZ RETRIEVAL DEBUG ==========\n", flush=True)

        if not context_parts:
            raise HTTPException(
                status_code=404,
                detail=(
                    "No relevant lecture notes were found for this topic. "
                    "Try a topic covered in your uploaded notes."
                ),
            )

        context = "\n\n---\n\n".join(context_parts)

        # 3. Generate a quiz using the retrieved notes.
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Smart Study Buddy, a quiz generator. "
                        "Create a multiple-choice quiz using only the "
                        "provided lecture-note context. Do not invent "
                        "facts. Return valid JSON with a single key "
                        "'questions'. Its value must be a list of objects. "
                        "Each object must contain 'question', 'options', "
                        "'answer', and 'explanation'. 'options' must be "
                        "a list of exactly four answer choices. 'answer' "
                        "must exactly match one option. Keep explanations "
                        "grounded in the notes."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Topic: {topic}\n"
                        f"Create exactly {request.num_questions} questions.\n"
                        f"Lecture-note context:\n{context}"
                    ),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )

        quiz_data = json.loads(
            response.choices[0].message.content
        )

        questions = quiz_data.get("questions")

        if not isinstance(questions, list) or not questions:
            raise ValueError("The AI returned no quiz questions.")

        # Check the basic structure before sending it to React.
        for item in questions:
            if not all(
                key in item
                for key in ("question", "options", "answer", "explanation")
            ):
                raise ValueError("A quiz question has missing fields.")

            if (
                not isinstance(item["options"], list)
                or len(item["options"]) != 4
                or item["answer"] not in item["options"]
            ):
                raise ValueError("A quiz question has invalid options or answer.")

        return {
            "topic": topic,
            "questions": questions[:request.num_questions],
        }

    except HTTPException:
        raise
    except Exception as exc:
        print(f"Quiz generation error: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Quiz generation failed. Check the backend terminal.",
        )


@app.post("/api/conversations")
def create_conversation():
    try:
        with get_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO conversations (title) VALUES (?)",
                ("New Chat",)
            )
            conversation_id = cursor.lastrowid

        return {
            "id": conversation_id,
            "title": "New Chat"
        }

    except Exception as exc:
        print(f"Create conversation error: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Could not create conversation."
        )


@app.get("/api/conversations")
def get_conversations():
    try:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, title, created_at
                FROM conversations
                ORDER BY id DESC
                """
            ).fetchall()

        return [dict(row) for row in rows]

    except Exception as exc:
        print(f"Get conversations error: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve conversations."
        )

class SaveMessageRequest(BaseModel):
    role: str
    content: str


@app.post("/api/conversations/{conversation_id}/messages")
def save_message(conversation_id: int, request: SaveMessageRequest):
    if request.role not in ("user", "assistant"):
        raise HTTPException(
            status_code=400,
            detail="Role must be 'user' or 'assistant'."
        )

    if not request.content.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    try:
        with get_connection() as connection:
            conversation = connection.execute(
                "SELECT id FROM conversations WHERE id = ?",
                (conversation_id,)
            ).fetchone()

            if conversation is None:
                raise HTTPException(
                    status_code=404,
                    detail="Conversation not found."
                )

            cursor = connection.execute(
                """
                INSERT INTO messages (conversation_id, role, content)
                VALUES (?, ?, ?)
                """,
                (conversation_id, request.role, request.content)
            )

            message_id = cursor.lastrowid
# Automatically title the conversation using the first user message.
            if request.role == "user":
                connection.execute(
                    """
                    UPDATE conversations
                    SET title = ?
                    WHERE id = ?
                    AND title = 'New Chat'
                    AND NOT EXISTS (
                        SELECT 1
                        FROM messages
                        WHERE conversation_id = ?
                        AND role = 'user'
                        AND id != ?
                    )
                    """,
                    (
                        request.content[:40],
                        conversation_id,
                        conversation_id,
                        message_id,
                    ),
                )

        return {
            "id": message_id,
            "conversation_id": conversation_id,
            "role": request.role,
            "content": request.content
        }

    except HTTPException:
        raise
    except Exception as exc:
        print(f"Save message error: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Could not save message."
        )



@app.get("/api/conversations/{conversation_id}/messages")
def get_messages(conversation_id: int):
    with get_connection() as connection:
        conversation = connection.execute(
            "SELECT id FROM conversations WHERE id = ?",
            (conversation_id,)
        ).fetchone()

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found."
            )

        rows = connection.execute(
            """
            SELECT id, conversation_id, role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,)
        ).fetchall()

    return [dict(row) for row in rows]
