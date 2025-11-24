from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

EMBEDDINGS = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

VECTOR_DB = Chroma(persist_directory="./ragdb",collection_name="doc", embedding_function=EMBEDDINGS)

def ingest_documents(texts: list[str], metadata=None):
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
    docs = []

    for i, t in enumerate(texts):
        chunks = splitter.split_text(t)
        for c in chunks:
            meta = metadata[i] if metadata and i < len(metadata) else {}
            docs.append(Document(page_content=c, metadata=meta))


    VECTOR_DB.add_documents(docs)
    VECTOR_DB.persist()


def get_retriever(k: int = 4):
    return VECTOR_DB.as_retriever(search_kwargs={"k": k})



