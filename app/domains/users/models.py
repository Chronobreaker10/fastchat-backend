from datetime import datetime

from core.base.models import Base
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from domains.shared.utils import get_current_naive_dt


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        default=get_current_naive_dt, server_default=func.now()
    )
