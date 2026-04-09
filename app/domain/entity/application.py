from datetime import datetime
import uuid

from sqlmodel import Column, Field, JSON, SQLModel, text


class Application(SQLModel, table=True):
    __tablename__ = "applications"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        max_length=36,
        sa_column_kwargs={"server_default": text("uuid_generate_v4()")},
    )
    app_name: str = Field(max_length=255, index=True)
    app_key: str = Field(max_length=255, unique=True, index=True)
    app_secret: str = Field(max_length=255)
    callback_url: str | None = Field(default=None, max_length=500)
    status: str = Field(default="active", max_length=50, index=True)
    app_metadata: dict | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
