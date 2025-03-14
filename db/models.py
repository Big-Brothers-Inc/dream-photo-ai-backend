from sqlalchemy import Column, Integer, String, BigInteger, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()


class User(Base):
    """Таблица пользователей"""
    __tablename__ = "user"
    
    user_id = Column(BigInteger, primary_key=True)
    activation_date = Column(DateTime, default=func.now())
    tokens_left = Column(Integer, default=0)
    source_id = Column(Integer, ForeignKey("source.source_id"), nullable=True)
    blocked = Column(Boolean, default=False)
    language = Column(String, default="ru")
    referral_code = Column(String, unique=True)
    referral_tokens = Column(Integer, default=0)
    
    # Отношения с другими таблицами
    source = relationship("Source", back_populates="users")
    payments = relationship("Payment", back_populates="user")
    messages = relationship("Message", back_populates="user")
    actions = relationship("Action", back_populates="user")
    generations = relationship("Generation", back_populates="user")
    models = relationship("Model", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")
    analytics_events = relationship("AnalyticsEvent", back_populates="user")


class Source(Base):
    """Таблица источников регистрации"""
    __tablename__ = "source"
    
    source_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    
    # Отношения с другими таблицами
    users = relationship("User", back_populates="source")


class Payment(Base):
    """Таблица платежей"""
    __tablename__ = "payment"
    
    payment_id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("user.user_id"), nullable=False)
    date = Column(DateTime, default=func.now())
    amount = Column(Numeric, nullable=False)
    tokens = Column(Integer, nullable=False)
    
    # Отношения с другими таблицами
    user = relationship("User", back_populates="payments")


class Message(Base):
    """Таблица сообщений"""
    __tablename__ = "message"
    
    message_id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("user.user_id"), nullable=False)
    date = Column(DateTime, default=func.now())
    type = Column(String, nullable=False)
    
    # Отношения с другими таблицами
    user = relationship("User", back_populates="messages")


class Action(Base):
    """Таблица действий пользователей"""
    __tablename__ = "action"
    
    action_id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("user.user_id"), nullable=False)
    type = Column(String, nullable=False)
    date = Column(DateTime, default=func.now())
    
    # Отношения с другими таблицами
    user = relationship("User", back_populates="actions")


class Admin(Base):
    """Таблица администраторов"""
    __tablename__ = "admin"
    
    admin_id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("user.user_id"), nullable=False)
    
    # Отношения с другими таблицами
    user = relationship("User")


class Generation(Base):
    """Таблица генераций"""
    __tablename__ = "generation"
    
    generation_id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("user.user_id"), nullable=False)
    model_id = Column(Integer, ForeignKey("model.model_id"), nullable=False)
    sex = Column(String, nullable=True)
    start_date = Column(DateTime, default=func.now())
    finish_date = Column(DateTime, nullable=True)
    error_date = Column(DateTime, nullable=True)
    mark = Column(Integer, nullable=True)
    type = Column(String, default="photo")
    
    # Отношения с другими таблицами
    user = relationship("User", back_populates="generations")
    model = relationship("Model", back_populates="generations")


class Model(Base):
    """Таблица моделей"""
    __tablename__ = "model"
    
    model_id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("user.user_id"), nullable=False)
    name = Column(String, nullable=False)
    trigger_word = Column(String, nullable=False)
    status = Column(String, default="created")
    preview_url = Column(String, nullable=True)
    training_id = Column(String, nullable=True)
    
    # Отношения с другими таблицами
    user = relationship("User", back_populates="models")
    generations = relationship("Generation", back_populates="model")


class Subscription(Base):
    """Таблица подписок"""
    __tablename__ = "subscriptions"
    
    subscription_id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("user.user_id"), nullable=False)
    level = Column(String, nullable=False)
    start_date = Column(DateTime, default=func.now())
    end_date = Column(DateTime, nullable=False)
    tokens = Column(Integer, nullable=False)
    
    # Отношения с другими таблицами
    user = relationship("User", back_populates="subscriptions")


class AnalyticsEvent(Base):
    """Таблица аналитических событий"""
    __tablename__ = "analytics_events"
    
    event_id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("user.user_id"), nullable=False)
    event_type = Column(String, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    details = Column(String, nullable=True)
    
    # Отношения с другими таблицами
    user = relationship("User", back_populates="analytics_events") 