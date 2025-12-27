"""
Embeddings and Vector Store
Same as structured RAG - shared vector database
"""
import sys
import os
from pathlib import Path

# Add parent directory to path to access main app
parent_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(parent_dir))

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Use same vector DB as main project (shared knowledge base)
RAGDB_PATH = os.path.join(parent_dir, "ragdb")

EMBEDDINGS = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
VECTOR_DB = Chroma(persist_directory=RAGDB_PATH, collection_name="doc", embedding_function=EMBEDDINGS)

def ingest_documents(texts: list[str], metadata=None):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=180,
        separators=["\n\n", "\n", ". ", " ", ""],
        add_start_index=True,
    )
    docs = []

    for i, t in enumerate(texts):
        meta_base = metadata[i] if metadata and i < len(metadata) else {}
        if meta_base is None:
            meta_base = {}
        meta_base = dict(meta_base)
        doc_id = meta_base.get("doc_id") or f"doc_{i}"

        chunks = splitter.create_documents([t], metadatas=[meta_base])
        for chunk_index, d in enumerate(chunks):
            d.metadata = dict(d.metadata or {})
            d.metadata.setdefault("doc_id", doc_id)
            d.metadata["chunk_index"] = chunk_index
            d.metadata["chunk_id"] = f"{doc_id}::chunk_{chunk_index}"
            docs.append(d)

    VECTOR_DB.add_documents(docs)
    VECTOR_DB.persist()

def get_retriever(k: int = 4):
    return VECTOR_DB.as_retriever(search_kwargs={"k": k})

