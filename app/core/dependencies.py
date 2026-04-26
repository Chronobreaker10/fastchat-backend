from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import db_helper

SessionDep = Annotated[AsyncSession, Depends(db_helper.get_session)]
