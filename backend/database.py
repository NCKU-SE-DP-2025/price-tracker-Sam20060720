# External imports
from sqlalchemy import Column, ForeignKey, Integer, Table, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

user_news_association_table = Table(
    "user_news_upvotes",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column(
        "news_articles_id", Integer, ForeignKey("news_articles.id"), primary_key=True
    ),
)

engine = create_engine("sqlite:///news_database.db", echo=True)

# Import all models to ensure they're registered with Base.metadata
# This must happen before create_all() is called
from auth.models import User  # noqa: F401, E402
from news.models import NewsArticle  # noqa: F401, E402

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Database session dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

