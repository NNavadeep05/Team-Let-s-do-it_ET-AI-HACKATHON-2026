from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models import ChatSession, ChatMessage


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, user_id: Optional[UUID], title: Optional[str] = None) -> ChatSession:
        """Create a new chat session."""
        session = ChatSession(
            user_id=user_id,
            title=title or "New Chat Session",
            created_at=datetime.utcnow()
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_session(self, session_id: UUID) -> Optional[ChatSession]:
        """Fetch chat session by ID with messages preloaded."""
        stmt = (
            select(ChatSession)
            .where(ChatSession.id == session_id)
            .options(selectinload(ChatSession.messages))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_sessions(self, user_id: UUID, skip: int = 0, limit: int = 20) -> List[ChatSession]:
        """List all chat sessions for a user."""
        stmt = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete_session(self, session_id: UUID) -> bool:
        """Delete a chat session."""
        session = await self.db.get(ChatSession, session_id)
        if session:
            await self.db.delete(session)
            await self.db.flush()
            return True
        return False

    async def create_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        citations: Optional[list] = None,
        confidence: Optional[float] = None,
        agent_trace: Optional[dict] = None
    ) -> ChatMessage:
        """Append a message to a chat session."""
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            citations=citations or [],
            confidence=confidence,
            agent_trace=agent_trace or {},
            created_at=datetime.utcnow()
        )
        self.db.add(message)
        await self.db.flush()
        return message

    async def get_messages(self, session_id: UUID) -> List[ChatMessage]:
        """Retrieve all messages in a session ordered by creation time."""
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
