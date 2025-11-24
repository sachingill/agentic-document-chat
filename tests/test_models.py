"""
Tests for model classes (memory, embeddings, model_loader).
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.models.memory import Memory
from app.models.embeddings import ingest_documents, get_retriever


@pytest.mark.unit
class TestMemory:
    """Tests for Memory class."""
    
    def test_add_turn(self, clean_memory):
        """Test adding conversation turn."""
        Memory.add_turn("session1", "Hello", "Hi there!")
        
        context = Memory.get_context("session1")
        assert "Hello" in context
        assert "Hi there!" in context
    
    def test_get_context_empty(self, clean_memory):
        """Test getting context for empty session."""
        context = Memory.get_context("nonexistent")
        assert context == ""
    
    def test_get_context_multiple_turns(self, clean_memory):
        """Test getting context with multiple turns."""
        Memory.add_turn("session1", "Q1", "A1")
        Memory.add_turn("session1", "Q2", "A2")
        Memory.add_turn("session1", "Q3", "A3")
        
        context = Memory.get_context("session1")
        assert "Q1" in context
        assert "A1" in context
        assert "Q2" in context
        assert "A2" in context
        assert "Q3" in context
        assert "A3" in context
    
    def test_get_context_max_turns(self, clean_memory):
        """Test context respects max_turns limit."""
        # Add 10 turns
        for i in range(10):
            Memory.add_turn("session1", f"Q{i}", f"A{i}")
        
        # Get context with max_turns=3
        context = Memory.get_context("session1", max_turns=3)
        
        # Should only contain last 3 turns
        assert "Q7" in context
        assert "Q8" in context
        assert "Q9" in context
        assert "Q0" not in context
        assert "Q6" not in context
    
    def test_clear_session(self, clean_memory):
        """Test clearing a specific session."""
        Memory.add_turn("session1", "Q1", "A1")
        Memory.add_turn("session2", "Q2", "A2")
        
        Memory.clear_session("session1")
        
        assert Memory.get_context("session1") == ""
        assert Memory.get_context("session2") != ""
    
    def test_clear_all(self, clean_memory):
        """Test clearing all sessions."""
        Memory.add_turn("session1", "Q1", "A1")
        Memory.add_turn("session2", "Q2", "A2")
        
        Memory.clear_all()
        
        assert Memory.get_context("session1") == ""
        assert Memory.get_context("session2") == ""
    
    def test_multiple_sessions_isolation(self, clean_memory):
        """Test that different sessions are isolated."""
        Memory.add_turn("session1", "Q1", "A1")
        Memory.add_turn("session2", "Q2", "A2")
        
        context1 = Memory.get_context("session1")
        context2 = Memory.get_context("session2")
        
        assert "Q1" in context1
        assert "Q2" not in context1
        assert "Q2" in context2
        assert "Q1" not in context2


@pytest.mark.unit
class TestEmbeddings:
    """Tests for embeddings module."""
    
    @patch("app.models.embeddings.VECTOR_DB")
    def test_ingest_documents(self, mock_db, sample_documents, sample_metadata):
        """Test document ingestion."""
        ingest_documents(sample_documents, metadata=sample_metadata)
        
        # Verify add_documents was called
        mock_db.add_documents.assert_called_once()
        mock_db.persist.assert_called_once()
        
        # Verify documents were added
        call_args = mock_db.add_documents.call_args
        assert call_args is not None
        docs = call_args[0][0] if call_args[0] else []
        assert len(docs) > 0
    
    @patch("app.models.embeddings.VECTOR_DB")
    def test_ingest_documents_no_metadata(self, mock_db, sample_documents):
        """Test document ingestion without metadata."""
        ingest_documents(sample_documents)
        
        mock_db.add_documents.assert_called_once()
        mock_db.persist.assert_called_once()
    
    @patch("app.models.embeddings.VECTOR_DB")
    def test_get_retriever(self, mock_db):
        """Test getting retriever."""
        mock_retriever = Mock()
        mock_db.as_retriever.return_value = mock_retriever
        
        retriever = get_retriever(k=5)
        
        assert retriever == mock_retriever
        mock_db.as_retriever.assert_called_once_with(search_kwargs={"k": 5})
    
    @patch("app.models.embeddings.VECTOR_DB")
    def test_get_retriever_default_k(self, mock_db):
        """Test get_retriever with default k value."""
        mock_retriever = Mock()
        mock_db.as_retriever.return_value = mock_retriever
        
        retriever = get_retriever()
        
        mock_db.as_retriever.assert_called_once_with(search_kwargs={"k": 4})


@pytest.mark.unit
class TestModelLoader:
    """Tests for ModelLoader class."""
    
    @patch("app.models.model_loader.AutoTokenizer")
    @patch("app.models.model_loader.AutoModelForSequenceClassification")
    def test_load_model_first_time(self, mock_model_class, mock_tokenizer_class):
        """Test loading model for the first time."""
        from app.models.model_loader import ModelLoader
        
        # Reset class variables
        ModelLoader.model = None
        ModelLoader.tokenizer = None
        
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_model.eval = Mock()
        
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model
        
        model, tokenizer = ModelLoader.load()
        
        assert model == mock_model
        assert tokenizer == mock_tokenizer
        mock_model.eval.assert_called_once()
    
    @patch("app.models.model_loader.AutoTokenizer")
    @patch("app.models.model_loader.AutoModelForSequenceClassification")
    def test_load_model_cached(self, mock_model_class, mock_tokenizer_class):
        """Test that model is cached after first load."""
        from app.models.model_loader import ModelLoader
        
        # Reset
        ModelLoader.model = None
        ModelLoader.tokenizer = None
        
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_model.eval = Mock()
        
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model
        
        # First load
        model1, tokenizer1 = ModelLoader.load()
        
        # Reset mocks
        mock_tokenizer_class.from_pretrained.reset_mock()
        mock_model_class.from_pretrained.reset_mock()
        
        # Second load - should use cached
        model2, tokenizer2 = ModelLoader.load()
        
        # Should not call from_pretrained again
        mock_tokenizer_class.from_pretrained.assert_not_called()
        mock_model_class.from_pretrained.assert_not_called()
        
        # Should return same instances
        assert model1 == model2
        assert tokenizer1 == tokenizer2


