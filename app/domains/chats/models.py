from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from core.base.models import Base
from sqlalchemy import String, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from domains.shared.utils import get_current_naive_dt


if TYPE_CHECKING:
    from domains.users.models import User


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))

    chat_users: Mapped[list[ChatUser]] = relationship(back_populates="chat", passive_deletes=True)
    created_at: Mapped[datetime] = mapped_column(
        default=get_current_naive_dt, server_default=func.now()
    )


class ChatUser(Base):
    __tablename__ = "chat_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    chat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))

    user: Mapped[User] = relationship(back_populates="user_chats")
    chat: Mapped[Chat] = relationship(back_populates="chat_users")
    joined_at: Mapped[datetime] = mapped_column(
        default=get_current_naive_dt, server_default=func.now()
    )
