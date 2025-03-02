from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./test.db"  # Pour SQLite
# DATABASE_URL = "postgresql://user:password@localhost/dbname"  # Pour PostgreSQL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})  # Pour SQLite
# engine = create_engine(DATABASE_URL)  # Pour PostgreSQL

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Function to create all tables
def create_tables():
    Base.metadata.create_all(bind=engine)
