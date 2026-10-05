from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Submission(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    title: str
    description: str
    research_type: str
    file_url: str | None = None
    submitted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    status: str
    student_id: int = Field(foreign_key="user.id")