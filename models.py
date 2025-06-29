from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# ✅ Authorized users table
class AuthorizedUser(Base):
    __tablename__ = "authorized_users"

    user_id = Column(BigInteger, primary_key=True)
    full_name = Column(String(100), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    entries = relationship(
        "SuguanEntry",
        back_populates="user",
        cascade="all, delete",
        passive_deletes=True
    )
    tasks = relationship(
        "TaskAssignment",
        back_populates="user",
        cascade="all, delete",
        passive_deletes=True
    )

# ✅ Suguan entries submitted by users
class SuguanEntry(Base):
    __tablename__ = "suguan_entries"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    day = Column(String(20), nullable=False)
    time = Column(String(20), nullable=False)
    lokal = Column(String(100), nullable=False)
    gampanin = Column(String(100), nullable=False)
    language = Column(String(50), nullable=False)

    user_id = Column(BigInteger, ForeignKey("authorized_users.user_id", ondelete="CASCADE"), nullable=False)
    user = relationship("AuthorizedUser", back_populates="entries")

    def __repr__(self):
        return f"<SuguanEntry(id={self.id}, day={self.day}, time={self.time}, lokal={self.lokal}, gampanin={self.gampanin}, language={self.language})>"

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "day": self.day,
            "time": self.time,
            "lokal": self.lokal,
            "gampanin": self.gampanin,
            "language": self.language,
            "user_id": self.user_id
        }

# ✅ Tasks assigned by admin to users
class TaskAssignment(Base):
    __tablename__ = "task_assignments"

    id = Column(Integer, primary_key=True)
    task = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user_id = Column(BigInteger, ForeignKey("authorized_users.user_id", ondelete="CASCADE"), nullable=False)
    user = relationship("AuthorizedUser", back_populates="tasks")

    def __repr__(self):
        return f"<TaskAssignment(id={self.id}, task='{self.task}', user_id={self.user_id})>"
