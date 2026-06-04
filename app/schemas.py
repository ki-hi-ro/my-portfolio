from datetime import date, datetime
from pydantic import BaseModel

class Work(BaseModel):
    title: str
    description: str
    github_url: str | None = None
    app_url: str | None = None
    tech_stack: str


class WorkResponse(BaseModel):
    id: int
    title: str
    description: str
    github_url: str | None = None
    app_url: str | None = None
    tech_stack: str
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


class Blog(BlogBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True