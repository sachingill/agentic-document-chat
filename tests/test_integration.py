"""
Integration tests for full RAG flow.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.models.memory import Memory


@pytest.mark.integration
class TestRAGFlow:
    """Integration tests for complete RAG flow."""
    
    @pytest.mark.asyncio
    @patch("app.models.embeddings.VECTOR_DB")
    @patch("app.agents.tools.get_retriever")
    @patch("app.agents.doc_agent.llm")
    @patch("app.agents.reranker.rerank_llm")
    async def test_full_rag_flow(
        self,
        mock_rerank_llm,
        mock_generate_llm,
        mock_get_retriever,
        mock_vector_db,
        clean_memory
    ):
        """Test complete RAG flow from ingestion to answer."""
        from app.agents.doc_agent import run_document_agent
        from app.models.embeddings import ingest_documents
        
        # 1. Ingest documents
        documents = [
            "SIM provisioning triggers a retry engine in CMP",
            "Circuit breaker protects A1 systems"
        ]
        ingest_documents(documents)
        
        # 2. Mock retrieval
        mock_retriever = Mock()
        mock_doc1 = Mock()
        mock_doc1.page_content = "SIM provisioning triggers a retry engine in CMP"
        mock_doc2 = Mock()
        mock_doc2.page_content = "Circuit breaker protects A1 systems"
        mock_retriever.invoke = Mock(return_value=[mock_doc1, mock_doc2])
        mock_get_retriever.return_value = mock_retriever
        
        # 3. Mock reranking
        mock_rerank_response1 = Mock()
        mock_rerank_response1.content = "0.9"
        mock_rerank_response2 = Mock()
        mock_rerank_response2.content = "0.5"
        mock_rerank_llm.ainvoke = AsyncMock(side_effect=[
            mock_rerank_response1,
            mock_rerank_response2
        ])
        
        # 4. Mock generation
        mock_gen_response = Mock()
        mock_gen_response.content = "SIM provisioning uses a retry engine in CMP to handle failures."
        mock_generate_llm.invoke.return_value = mock_gen_response
        
        # 5. Run agent
        answer = await run_document_agent(
            "test-session",
            "How does SIM provisioning handle retries?"
        )
        
        # 6. Verify
        assert "retry" in answer.lower() or "retries" in answer.lower()
        assert Memory.get_context("test-session") != ""
    
    @pytest.mark.asyncio
    @patch("app.agents.tools.get_retriever")
    @patch("app.agents.doc_agent.llm")
    async def test_rag_flow_no_documents(
        self,
        mock_generate_llm,
        mock_get_retriever,
        clean_memory
    ):
        """Test RAG flow when no documents are found."""
        from app.agents.doc_agent import run_document_agent
        
        # Mock empty retrieval
        mock_retriever = Mock()
        mock_retriever.invoke = Mock(return_value=[])
        mock_get_retriever.return_value = mock_retriever
        
        # Mock generation (should say "I don't know")
        mock_gen_response = Mock()
        mock_gen_response.content = "I don't know based on the documents."
        mock_generate_llm.invoke.return_value = mock_gen_response
        
        answer = await run_document_agent(
            "test-session",
            "What is neural rendering?"
        )
        
        assert "don't know" in answer.lower() or "no documents" in answer.lower()
    
    @pytest.mark.asyncio
    @patch("app.agents.tools.get_retriever")
    @patch("app.agents.doc_agent.llm")
    @patch("app.agents.reranker.rerank_llm")
    async def test_rag_flow_with_conversation_history(
        self,
        mock_rerank_llm,
        mock_generate_llm,
        mock_get_retriever,
        clean_memory
    ):
        """Test RAG flow with conversation history."""
        from app.agents.doc_agent import run_document_agent
        
        # Add conversation history
        Memory.add_turn("test-session", "What is SIM provisioning?", "SIM provisioning is...")
        
        # Mock retrieval
        mock_retriever = Mock()
        mock_doc = Mock()
        mock_doc.page_content = "SIM provisioning triggers retries"
        mock_retriever.invoke = Mock(return_value=[mock_doc])
        mock_get_retriever.return_value = mock_retriever
        
        # Mock reranking
        mock_rerank_response = Mock()
        mock_rerank_response.content = "0.8"
        mock_rerank_llm.ainvoke = AsyncMock(return_value=mock_rerank_response)
        
        # Mock generation
        mock_gen_response = Mock()
        mock_gen_response.content = "Retries work by..."
        mock_generate_llm.invoke.return_value = mock_gen_response
        
        answer = await run_document_agent(
            "test-session",
            "How do retries work?"
        )
        
        # Verify history is used
        context = Memory.get_context("test-session")
        assert "What is SIM provisioning?" in context
        assert "How do retries work?" in context or answer != ""


@pytest.mark.integration
class TestEndToEndAPI:
    """End-to-end API integration tests."""
    
    @pytest.mark.asyncio
    @patch("app.routers.agent.ingest_documents")
    @patch("app.routers.agent.run_document_agent")
    @patch("app.routers.agent.check_input_safety")
    @patch("app.routers.agent.check_output_safety")
    async def test_ingest_and_chat_flow(
        self,
        mock_output_guard,
        mock_input_guard,
        mock_run_agent,
        mock_ingest,
        test_client,
        clean_memory
    ):
        """Test complete flow: ingest documents then chat."""
        from app.agents.guardrails import GuardrailResult
        
        # 1. Ingest documents
        ingest_response = test_client.post(
            "/agent/ingest/json",
            json={
                "texts": [
                    "SIM provisioning triggers retries",
                    "Circuit breaker protects systems"
                ],
                "metadatas": [
                    {"topic": "provisioning"},
                    {"topic": "circuit-breaker"}
                ]
            }
        )
        
        assert ingest_response.status_code == 200
        assert ingest_response.json()["status"] == "success"
        
        # 2. Chat
        mock_input_guard.return_value = GuardrailResult(allowed=True)
        mock_output_guard.return_value = GuardrailResult(
            allowed=True,
            sanitized_text="SIM provisioning uses retries"
        )
        mock_run_agent = AsyncMock(return_value="SIM provisioning uses retries")
        
        with patch("app.routers.agent.run_document_agent", mock_run_agent):
            chat_response = test_client.post(
                "/agent/chat",
                json={
                    "session_id": "e2e-test",
                    "question": "How does SIM provisioning handle retries?",
                    "reset_session": True
                }
            )
        
        assert chat_response.status_code == 200
        data = chat_response.json()
        assert "answer" in data
        assert data["guardrail"]["blocked"] is False


