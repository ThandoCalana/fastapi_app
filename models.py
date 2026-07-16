from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, DateTime, String, Text, ForeignKey

from database import Base


# Each class is a table in our DB
class Users(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    profile_pic: Mapped[str | None] = mapped_column(
        String(200), nullable=True, default=None
    )
    # Establish a relationship between columns on separate tables
    campaigns: Mapped[list[Campaigns]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",  # if author user is deleted, all posts of that user will also be deleted
    )

    @property
    def img_path(self):
        if self.profile_pic:
            return f"/media/profile_pics/{self.profile_pic}"
        return f"/static/profile_pics/default.jpg"


class Campaigns(Base):
    __tablename__ = "campaigns"

    campaign_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    campaign_name: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[Users] = relationship(
        back_populates="campaigns"
    )  # match relationship established earlier
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"), nullable=False, index=True
    )
    campaign_details: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
