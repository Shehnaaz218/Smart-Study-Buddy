
import os
import hashlib
from pathlib import Path

from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

INDEX_NAME = "smart-study-buddy-notes"
NOTES_DIR = Path(__file__).resolve().parent.parent / "input_lecture_notes"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def main():
    if not os.getenv("PINECONE_API_KEY"):
        raise RuntimeError("PINECONE_API_KEY is missing from your .env file.")

    if not NOTES_DIR.exists():
        raise FileNotFoundError(f"Notes folder not found: {NOTES_DIR}")

    # Ingest only the three newly added notes.
    filenames = [
        "biology_notes.txt",
        "physics_notes.txt",
        "computer_science_notes.txt",
    ]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )

    documents = []
    for filename in filenames:
        path = NOTES_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing note file: {path}")

        loaded = TextLoader(str(path), encoding="utf-8").load()
        for doc in loaded:
            doc.metadata["source"] = filename
        documents.extend(splitter.split_documents(loaded))

    if not documents:
        print("No note chunks found.")
        return

    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    pc = Pinecone()
    index = pc.Index(INDEX_NAME)

    vectors = []
    for i, doc in enumerate(documents):
        vector = embeddings.embed_query(doc.page_content)
        source = doc.metadata["source"]

        # Stable IDs let repeated runs update the same chunks.
        chunk_hash = hashlib.sha256(
            f"{source}:{i}:{doc.page_content}".encode("utf-8")
        ).hexdigest()[:24]

        vectors.append({
            "id": f"{source}:{chunk_hash}",
            "values": vector,
            "metadata": {
                "text": doc.page_content,
                "source": source,
                "chunk": i,
            },
        })

    # Upload in small batches; existing unrelated vectors are preserved.
    for start in range(0, len(vectors), 100):
     response = index.upsert(vectors=vectors[start:start + 100])
     print("Pinecone upsert response:", response)

    print(f"Uploaded {len(vectors)} chunks from the three new notes.")
    print(index.describe_index_stats())

if __name__ == "__main__":
    main()
