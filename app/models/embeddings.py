from __future__ import annotations

import os
import time
import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# Try to use newer packages, fallback to deprecated ones for compatibility
try:
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_chroma import Chroma
except ImportError:
    # Fallback to deprecated packages if new ones aren't available
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import Chroma

EMBEDDINGS = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


def _fresh_dir(base_dir: str) -> str:
    return os.getenv("RAGDB_FALLBACK_DIR") or f"{base_dir}_fresh_{int(time.time())}"


def _init_vector_db(*, base_dir: str | None = None, force_fresh: bool = False) -> Chroma:
    """
    Initialize Chroma with a persistent directory.

    We occasionally see older/incompatible SQLite metadata in ./ragdb (e.g. after upgrades),
    which can crash ingestion. To be robust, we fall back to a fresh directory WITHOUT
    deleting the original data.
    """
    base_dir = base_dir or os.getenv("RAGDB_DIR", "./ragdb")
    chosen_dir = _fresh_dir(base_dir) if force_fresh else base_dir
    try:
        db = Chroma(persist_directory=chosen_dir, collection_name="doc", embedding_function=EMBEDDINGS)
        # Trigger underlying storage initialization early so corruption is detected on startup.
        _ = db._collection.count()
        return db
    except (TypeError, Exception) as e:
        # Known symptom: TypeError: object of type 'int' has no len() from chromadb sqlite metadata
        # This happens when ChromaDB metadata is corrupted or incompatible
        error_msg = str(e)
        is_corruption_error = (
            "has no len()" in error_msg or
            isinstance(e, TypeError) or
            "seq_id" in error_msg.lower()
        )
        
        if is_corruption_error:
            fallback_dir = _fresh_dir(base_dir)
            logger.warning(
                "ChromaDB at %s appears corrupted (%s). Falling back to fresh DB at %s.",
                chosen_dir,
                type(e).__name__,
                fallback_dir,
            )
            db = Chroma(persist_directory=fallback_dir, collection_name="doc", embedding_function=EMBEDDINGS)
            try:
                _ = db._collection.count()
            except Exception as fallback_error:
                logger.error("Fallback Chroma DB at %s also failed to initialize: %s", fallback_dir, fallback_error, exc_info=True)
                raise
            return db
        else:
            # Re-raise if it's not a corruption error
            raise


VECTOR_DB = _init_vector_db()

def ingest_documents(texts: list[str], metadata=None):
    # Slightly more structure-aware splitting to preserve headings/bullets in curated docs.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=180,
        separators=["\n\n", "\n", ". ", " ", ""],
        add_start_index=True,
    )
    docs = []

    for i, t in enumerate(texts):
        meta_base = metadata[i] if metadata and i < len(metadata) else {}
        # Ensure metadata is a dict and avoid accidental shared references
        if meta_base is None:
            meta_base = {}
        meta_base = dict(meta_base)

        # Prefer stable doc_id if caller provided one
        doc_id = meta_base.get("doc_id") or f"doc_{i}"

        chunks = splitter.create_documents([t], metadatas=[meta_base])
        for chunk_index, d in enumerate(chunks):
            # Attach chunk identifiers to help debugging and filtering.
            d.metadata = dict(d.metadata or {})
            d.metadata.setdefault("doc_id", doc_id)
            d.metadata["chunk_index"] = chunk_index
            d.metadata["chunk_id"] = f"{doc_id}::chunk_{chunk_index}"
            docs.append(d)


    # If a persisted DB becomes incompatible at runtime (rare), rebuild to a fresh directory.
    global VECTOR_DB
    try:
        VECTOR_DB.add_documents(docs)
        VECTOR_DB.persist()
    except TypeError as e:
        # Known Chroma SQLite metadata incompatibility symptom
        if "has no len()" in str(e):
            logger.error("Chroma DB appears incompatible; switching to a fresh DB and retrying ingestion.", exc_info=True)
            VECTOR_DB = _init_vector_db(force_fresh=True)
            VECTOR_DB.add_documents(docs)
            VECTOR_DB.persist()
        else:
            raise


def get_retriever(k: int = 4):
    return VECTOR_DB.as_retriever(search_kwargs={"k": k})



