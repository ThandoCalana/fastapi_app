from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, DateTime, String, Text, ForeignKey

from database import Base

# Each class is a table in our DB
class User(Base):
    __tablename__ = "Users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    profile_pic: Mapped[str] = mapped_column(String, nullable=True)

    @property
    def img_path(img_name):
        if img_name:
            return f"/media/profile_pics/{img_name}.jpg"
        return f"/static/profile_pics/default.jpg"


    # Establish a relationship between columns on separate tables 
    campaigns: Mapped[list[Campaigns]] = relationship(back_populates="author")


class Campaigns(Base):
    __tablename__ = "Campaigns"

    campaign_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    campaign_name: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[User] = relationship(back_populates="campaigns") # match relationship established earlier
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)
    campaign_details: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))