from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    message_thread_id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column()
    closed: Mapped[bool] = mapped_column(default=False)
