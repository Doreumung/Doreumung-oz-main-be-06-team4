# from typing import Generator
#
# from sqlalchemy import create_engine
# from sqlalchemy.orm import Session, sessionmaker
#
# from config import settings
#
# engine = create_engine(settings.database_url)
# SessionFactory = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
#
#
# def get_session() -> Generator[Session, None, None]:
#     session = SessionFactory()
#     try:
#         yield session
#     finally:
#         session.close()
