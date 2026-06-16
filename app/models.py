from sqlalchemy.orm import DeclarativeBase, relationship  
from sqlalchemy import Float, Column, Integer, String, Boolean, BigInteger, ForeignKey, DateTime
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # СВЯЗЬ: У одного юзера может быть много товаров (настройка для удобства)
    products = relationship("Product", back_populates="user", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False)
    title = Column(String, nullable=True)
    current_price = Column(Float, nullable=True)
    target_price = Column(Float, nullable=False)
    was_notified = Column(Boolean, default=False)
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    user = relationship("User", back_populates="products")