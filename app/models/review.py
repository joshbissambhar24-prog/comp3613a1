from datetime import datetime

from sqlmodel import Field, SQLModel


class Review(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    feedback: str
    outcome: str
    reviewed_at: datetime
    submission_id: int = Field(foreign_key="submission.id")
    reviewer_id: int = Field(foreign_key="user.id")