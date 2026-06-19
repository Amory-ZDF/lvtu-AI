from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()


def _build_engine():
    """构建 engine，根据数据库类型选择合适的连接池参数。

    SQLite（特别是内存数据库）不支持 QueuePool 的 pool_size/max_overflow 参数，
    因此仅在非 SQLite 时应用连接池调优。
    """
    db_url = settings.sqlalchemy_database_uri
    is_sqlite = db_url.startswith("sqlite")

    kwargs: dict = {"pool_pre_ping": True}

    if not is_sqlite:
        kwargs["pool_size"] = settings.db_pool_size
        kwargs["max_overflow"] = settings.db_max_overflow
        kwargs["pool_timeout"] = settings.db_pool_timeout
        kwargs["pool_recycle"] = settings.db_pool_recycle

    return create_engine(db_url, **kwargs)


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
