# models/models.py

from sqlalchemy import Column, Integer, String, Text
from database import Base

class Template(Base):
    """
    Модель для шаблонов сообщений.
    """
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)  # Название шаблона
    text = Column(Text, nullable=True)                             # Текст сообщения
    image_path = Column(String, nullable=True)                    # Путь к изображению
    button_text = Column(String, nullable=True)                   # Текст кнопки
    button_url = Column(String, nullable=True)                    # URL кнопки
