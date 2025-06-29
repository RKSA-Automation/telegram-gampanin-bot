from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime

Base = declarative_base()

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime)
    day = Column(String(50))
    time = Column(String(50))
    lokal = Column(String(255))
    gampanin = Column(String(255))
    language = Column(String(50))
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime

Base = declarative_base()

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime)
    day = Column(String(50))
    time = Column(String(50))
    lokal = Column(String(255))
    gampanin = Column(String(255))
    language = Column(String(50))
