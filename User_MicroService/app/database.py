import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

if os.getenv("TESTING") == '1':
    URL_DATABASE = 'mysql+pymysql://test_user:test_password@localhost:3307/test_user_db'
else:
    # Use the actual MySQL database for normal operations
    URL_DATABASE = 'mysql+pymysql://user:VERY_SECURE_PASSWORD@localhost:3306/user_db'

engine = create_engine(URL_DATABASE)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()