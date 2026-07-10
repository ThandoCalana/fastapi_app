from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

FILE_PATH = f"./campaigns.db"

SQL_ALCHEMY_DATABASE_URL = f"sqlite:///{FILE_PATH}"

engine = create_engine(
        SQL_ALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread":False} # Specific to SQLite, now we can use multiple threads for one db connection
        ) 

# Creates a session every time we interact with backend db
SessionLocal = sessionmaker(bind=engine, auto_commit=False, auto_flush=False)

class Base(DeclarativeBase):
    pass

# Generator to provide a db session each time the function is called
# Pauses execution and can be called again to resume 
def get_db():
    with SessionLocal() as db:
        yield db