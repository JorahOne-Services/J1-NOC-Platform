from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

from .config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
Base = declarative_base()
