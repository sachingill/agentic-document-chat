"""
Pytest configuration and shared fixtures.
"""
import os
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from dotenv import load_dotenv

# Load environment variables for testing
load_dotenv()

# Set test environment variables
os.environ.setdefault("OPENAI_API_KEY", "test-api-key-for-testing")


@pytest.fixture(scope="session")
def test_client():
    """Create a test client for FastAPI app."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    mock_response = Mock()
    mock_response.content = "Mocked response"
    return mock_response


@pytest.fixture
def mock_chat_openai(mock_openai_response):
    """Mock ChatOpenAI instance."""
    with patch("langchain_openai.ChatOpenAI") as mock:
        instance = Mock()
        instance.invoke = Mock(return_value=mock_openai_response)
        instance.ainvoke = AsyncMock(return_value=mock_openai_response)
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_embeddings():
    """Mock HuggingFaceEmbeddings."""
    with patch("app.models.embeddings.HuggingFaceEmbeddings") as mock:
        instance = Mock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_vector_db():
    """Mock ChromaDB vector store."""
    with patch("app.models.embeddings.Chroma") as mock:
        instance = Mock()
        instance._collection = Mock()
        instance._collection.count = Mock(return_value=10)
        instance._collection.get = Mock(return_value={
            "documents": ["Test document 1", "Test document 2"],
            "metadatas": [{"filename": "doc1"}, {"filename": "doc2"}]
        })
        instance.add_documents = Mock()
        instance.persist = Mock()
        instance.as_retriever = Mock()
        
        # Mock retriever
        mock_retriever = Mock()
        mock_doc = Mock()
        mock_doc.page_content = "Test document content"
        mock_retriever.invoke = Mock(return_value=[mock_doc, mock_doc])
        instance.as_retriever.return_value = mock_retriever
        
        mock.return_value = instance
        yield instance


@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    return [
        "SIM provisioning is the process of activating, suspending, or moving SIMs within the CMP system.",
        "SIM provisioning triggers a retry engine in CMP",
        "Retries with exponential backoff and circuit breakers protect A1 upstream systems in case of failures.",
        "Circuit breaker protects A1 521 error storms and returns 429",
        "Billing plan is updated using BSS pipeline"
    ]


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing."""
    return [
        {"filename": "doc1", "topic": "provisioning"},
        {"filename": "doc2", "topic": "retries"},
        {"filename": "doc3", "topic": "circuit-breaker"},
        {"filename": "doc4", "topic": "billing"}
    ]


@pytest.fixture
def clean_memory():
    """Clear memory before and after test."""
    from app.models.memory import Memory
    Memory.clear_all()
    yield
    Memory.clear_all()


@pytest.fixture
def mock_model_loader():
    """Mock ModelLoader for sentiment prediction tests."""
    with patch("app.models.model_loader.ModelLoader") as mock:
        instance = Mock()
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        # Mock tokenizer
        mock_tokenizer.return_value = {
            "input_ids": Mock(),
            "attention_mask": Mock()
        }
        mock_tokenizer.__call__ = Mock(return_value={
            "input_ids": Mock(),
            "attention_mask": Mock()
        })
        
        # Mock model output
        mock_output = Mock()
        mock_output.logits = Mock()
        mock_output.logits.softmax = Mock(return_value=Mock())
        
        mock_model.return_value = mock_output
        mock_model.__call__ = Mock(return_value=mock_output)
        
        instance.load = Mock(return_value=(mock_model, mock_tokenizer))
        mock.load = Mock(return_value=(mock_model, mock_tokenizer))
        yield mock


@pytest.fixture(autouse=True)
def reset_env():
    """Reset environment variables after each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


