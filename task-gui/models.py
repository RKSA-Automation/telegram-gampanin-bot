
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class AuthorizedUser(Base):
    __tablename__ = "authorized_users"
    user_id = Column(BigInteger, primary_key=True)
    full_name = Column(String(100))
    added_at = Column(DateTime, default=datetime.utcnow)
    entries = relationship("SuguanEntry", back_populates="user", cascade="all, delete", passive_deletes=True)
    tasks = relationship("TaskAssignment", back_populates="user", cascade="all, delete", passive_deletes=True)

class SuguanEntry(Base):
    __tablename__ = "suguan_entries"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    day = Column(String(20))
    time = Column(String(20))
    lokal = Column(String(100))
    gampanin = Column(String(100))
    language = Column(String(50))
    user_id = Column(BigInteger, ForeignKey("authorized_users.user_id", ondelete="CASCADE"))
    user = relationship("AuthorizedUser", back_populates="entries")

class TaskAssignment(Base):
    __tablename__ = "task_assignments"
    id = Column(Integer, primary_key=True)
    task = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(BigInteger, ForeignKey("authorized_users.user_id", ondelete="CASCADE"))
    user = relationship("AuthorizedUser", back_populates="tasks")
