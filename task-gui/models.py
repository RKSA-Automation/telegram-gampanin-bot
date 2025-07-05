from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class AuthorizedUser(Base):
    __tablename__ = 'authorized_users'

    user_id = Column(Integer, primary_key=True)
    full_name = Column(String(100))
    added_at = Column(DateTime, default=datetime.utcnow)

    entries = relationship("SuguanEntry", back_populates="user", cascade="all, delete-orphan")

class SuguanEntry(Base):
    __tablename__ = 'suguan_entries'

    id = Column(Integer, primary_key=True)
    day = Column(String(10))
    time = Column(String(20))
    lokal = Column(String(100))
    gampanin = Column(String(100))
    language = Column(String(50))
    user_id = Column(Integer, ForeignKey('authorized_users.user_id'))

    user = relationship("AuthorizedUser", back_populates="entries")
