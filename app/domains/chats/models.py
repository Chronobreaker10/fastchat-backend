import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from core.base.models import Base
from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from domains.shared.utils import get_current_naive_dt

if TYPE_CHECKING:
    from domains.messages.models import Message
    from domains.users.models import User


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    members: Mapped[list[ChatUser]] = relationship(
        back_populates="chat", passive_deletes=True, cascade="all, delete-orphan"
    )
    messages: Mapped[list[Message]] = relationship(
        back_populates="chat",
        passive_deletes=True,
        order_by="Message.created_at.desc()",
    )
    creator: Mapped[User] = relationship(back_populates="created_chats")
    created_at: Mapped[datetime] = mapped_column(
        default=get_current_naive_dt, server_default=func.now()
    )


class ChatUser(Base):
    __tablename__ = "chat_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    chat_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE")
    )
    invited_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    user: Mapped[User] = relationship(back_populates="chats", foreign_keys=[user_id])
    chat: Mapped[Chat] = relationship(back_populates="members")
    invited_user: Mapped[User | None] = relationship(
        back_populates="invitations", foreign_keys=[invited_id]
    )
    joined_at: Mapped[datetime] = mapped_column(
        default=get_current_naive_dt, server_default=func.now(), index=True
    )
