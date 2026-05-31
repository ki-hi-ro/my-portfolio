from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(String)
    task_type = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    work_time_minutes = Column(Integer)
    work_id = Column(Integer, ForeignKey("works.id"))
    work = relationship(
        "Work",
        back_populates="posts"
    )
    created_at = Column(DateTime, default=datetime.now)

class Work(Base):
    __tablename__ = "works"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    github_url = Column(String)
    app_url = Column(String)
    tech_stack = Column(String)
    posts = relationship(
        "Post",
        back_populates="work"
    )    
    image_url = Column(String)
    created_at = Column(DateTime, default=datetime.now)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="admin")

class Blog(Base):
    __tablename__ = "blogs"

    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    url = Column(String(500))
    summary = Column(Text)
    tags = Column(String(255))
    published_at = Column(Date)
    created_at = Column(DateTime)