import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from core.base.models import Base
from sqlalchemy import ForeignKey, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from domains.shared.utils import get_current_naive_dt

if TYPE_CHECKING:
    from domains.chats.models import Chat
    from domains.users.models import User


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text)

    chat_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE")
    )
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    sender: Mapped[User] = relationship(
        back_populates="user_messages", foreign_keys=[sender_id]
    )
    chat: Mapped[Chat] = relationship(back_populates="messages")
    created_at: Mapped[datetime] = mapped_column(
        default=get_current_naive_dt, server_default=func.now(), index=True
    )

    __table_args__ = (Index("idx_messages_pagination", created_at.desc(), id.desc()),)
