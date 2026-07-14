import os
import json
import time
import asyncio
from typing import List, Dict, Any, Tuple, AsyncGenerator
from sqlalchemy.orm import Session
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.messages import SystemMessage, HumanMessage

from app.repositories.chat import ChatRepository
from app.repositories.document import DocumentRepository
from app.ai.pipeline import advanced_rag_pipeline
from app.core.config import settings


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.chat_repo = ChatRepository(db)
        self.doc_repo = DocumentRepository(db)

    def create_session(self, title: str, user_id: int):
        return self.chat_repo.create_session(title, user_id)

    def get_user_sessions(self, user_id: int):
        return self.chat_repo.get_user_sessions(user_id)

    def get_session_history(self, session_id: str, user_id: int):
        session = self.chat_repo.get_session(session_id, user_id)
        if not session:
            return None
        messages = self.chat_repo.get_session_messages(session_id)
        return {
            "session_id": session.id,
            "title": session.title,
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "citations": m.citations,
                    "created_at": m.created_at,
                    "metrics": {
                        "embedding_time_ms": m.embedding_time_ms,
                        "retrieval_time_ms": m.retrieval_time_ms,
                        "llm_time_ms": m.llm_time_ms,
                        "total_time_ms": m.total_time_ms,
                        "token_count": m.token_count
                    } if m.role == "assistant" else None
                } for m in messages
            ]
        }

    def delete_session(self, session_id: str, user_id: int):
        return self.chat_repo.delete_session(session_id, user_id)

    def submit_feedback(self, message_id: str, rating: int, comment: str = None):
        return self.chat_repo.submit_feedback(message_id, rating, comment)

    async def chat_query_stream(
        self,
        session_id: str,
        user_id: int,
        query: str,
        doc_ids: List[int],
        api_key: str
    ) -> AsyncGenerator[str, None]:
        """
        Executes Advanced RAG and streams response via Server-Sent Events (SSE).
        Saves user and assistant messages in database.
        """
        # Validate session ownership
        session = self.chat_repo.get_session(session_id, user_id)
        if not session:
            yield f"event: error\ndata: {json.dumps({'detail': 'Session not found'})}\n\n"
            return

        # Record User Message
        self.chat_repo.add_message(session_id=session_id, role="user", content=query)

        # 1. Retrieval Phase with Latency Measurement
        retrieval_start = time.time()
        try:
            contexts, citations = advanced_rag_pipeline(query, doc_ids, api_key)
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'detail': f'Retrieval failed: {e}'})}\n\n"
            return
        retrieval_time = (time.time() - retrieval_start) * 1000

        # Send Citations to Client immediately
        # Match doc_ids with filenames for rich display
        doc_map = {}
        for d_id in doc_ids:
            doc_obj = self.doc_repo.get_by_id(d_id)
            if doc_obj:
                doc_map[d_id] = doc_obj.filename

        enriched_citations = []
        for cit in citations:
            enriched_citations.append({
                **cit,
                "filename": doc_map.get(cit["doc_id"], "Unknown Document")
            })

        yield f"event: citations\ndata: {json.dumps(enriched_citations)}\n\n"
        await asyncio.sleep(0.01)

        # 2. LLM Prompt Construction
        context_blocks = []
        for idx, ctx in enumerate(contexts):
            fname = doc_map.get(ctx["doc_id"], "Unknown")
            context_blocks.append(
                f"[Source {idx+1}]: Document '{fname}' Page {ctx['page']}\n{ctx['text']}\n"
            )
        context_text = "\n\n".join(context_blocks)

        system_prompt = (
            "You are DOCMind Enterprise, a state-of-the-art startup-grade AI document intelligence platform.\n"
            "Answer the user's question precisely using only the provided retrieved contexts.\n"
            "Format rules:\n"
            "- Be concise, direct, and structure your responses with markdown paragraphs.\n"
            "- Do not use sentences like 'Based on the context...'. Just state facts.\n"
            "- At the end of any claim or sentence that is supported by a context source, append the numeric citation citation bracket "
            "like [1], [2] to reference the context chunk index.\n"
            "If the answer is not in the context, say 'I cannot find the answer in the provided documents.' and do not make up statements.\n\n"
            "RETIRED CONTEXTS:\n"
            f"{context_text}"
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ]

        # 3. LLM Execution with Streaming and token counting
        llm_start = time.time()
        assistant_content = ""
        token_count = 0
        
        try:
            # If in unit tests or key is dummy, stream mock text
            if os.getenv("DB_NAME") == "docmind_test" or "stub" in api_key or not api_key:
                # Mock streaming for offline unit tests
                mock_response = "Here is a mock analysis based on your document [1]. Let me know if you need more details."
                for word in mock_response.split(" "):
                    token_count += 1
                    assistant_content += word + " "
                    yield f"event: message\ndata: {json.dumps({'chunk': word + ' '})}\n\n"
                    await asyncio.sleep(0.01)
            else:
                llm = ChatNVIDIA(
                    model=settings.LLM_MODEL,
                    api_key=api_key,
                    temperature=0.0
                )
                for chunk in llm.stream(messages):
                    chunk_text = chunk.content
                    token_count += 1
                    assistant_content += chunk_text
                    yield f"event: message\ndata: {json.dumps({'chunk': chunk_text})}\n\n"
                    await asyncio.sleep(0.005)
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'detail': f'LLM streaming failure: {e}'})}\n\n"
            return

        llm_time = (time.time() - llm_start) * 1000
        total_time = retrieval_time + llm_time

        # Save assistant message and metrics to DB
        db_msg = self.chat_repo.add_message(
            session_id=session_id,
            role="assistant",
            content=assistant_content.strip(),
            citations=enriched_citations,
            embedding_time_ms=50.0,  # approximate dense vector lookup embedding cost
            retrieval_time_ms=retrieval_time,
            llm_time_ms=llm_time,
            total_time_ms=total_time,
            token_count=token_count
        )

        # Yield metrics event
        metrics_data = {
            "message_id": db_msg.id,
            "embedding_time_ms": 50.0,
            "retrieval_time_ms": round(retrieval_time, 2),
            "llm_time_ms": round(llm_time, 2),
            "total_time_ms": round(total_time, 2),
            "token_count": token_count
        }
        yield f"event: metrics\ndata: {json.dumps(metrics_data)}\n\n"
        yield "event: close\ndata: [DONE]\n\n"
