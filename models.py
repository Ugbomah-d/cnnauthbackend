from datetime import datetime, timezone
from database import db
from sqlalchemy import Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False, default="")
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    history: Mapped[list["History"]] = relationship("History", back_populates="user")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name or self.email.split("@")[0],
            "created_at": self.created_at.isoformat()
        }


class History(db.Model):
    __tablename__ = "history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    image_filename: Mapped[str] = mapped_column(String, nullable=False)
    predicted_class: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="history")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "image_filename": self.image_filename,
            "image_url": f"/uploads/{self.image_filename}",
            "predicted_class": self.predicted_class,
            "confidence": round(self.confidence * 100, 2),
            "created_at": self.created_at.isoformat()
        }