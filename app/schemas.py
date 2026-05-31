from datetime import date, datetime
from pydantic import BaseModel

class Post(BaseModel):
    title: str
    content: str
    task_type: str
    start_time: datetime
    end_time: datetime

class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    task_type: str
    work_time_minutes: int
    created_at: datetime

    class Config:
        from_attributes = True

class Work(BaseModel):
    title: str
    description: str
    github_url: str | None = None
    app_url: str | None = None
    technologies: list[str]

class WorkResponse(BaseModel):
    id: int
    title: str
    description: str
    github_url: str | None = None
    app_url: str | None = None
    technologies: list[str]
    created_at: datetime

    class Config:
        from_attributes = True

class BlogBase(BaseModel):
    title: str
    url: str | None = None
    summary: str | None = None
    tags: str | None = None
    published_at: date | None = None


class BlogCreate(BlogBase):
    pass


class Blog(BlogBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True