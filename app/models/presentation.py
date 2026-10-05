from datetime import date, time

from sqlmodel import Field, SQLModel


class Presentation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    submission_id: int = Field(foreign_key="submission.id", unique=True)
    presentation_date: date
    presentation_time: time
    location: str
