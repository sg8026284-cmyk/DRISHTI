from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Update with your MySQL root password:
# Format: "mysql+pymysql://<user>:<password>@<host>:<port>/<database_name>"
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:220704@localhost:3306/dristi_db"

# If using XAMPP (no password by default):
# SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:@localhost:3306/dristi-db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    pool_pre_ping=True, 
    pool_recycle=3600
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()