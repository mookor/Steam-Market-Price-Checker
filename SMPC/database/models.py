from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Boolean, DECIMAL,
    ForeignKey, CheckConstraint, Index,
    DateTime, REAL, UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True) # UUID
    telegram_id = Column(Integer, nullable=False)
    subscriber = Column(Boolean, default=False)
    currency = Column(String(3), nullable=False)
    # Relationships
    watchlist_items = relationship("UserItemWatchlist", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, subscriber='{self.subscriber}', currency='{self.currency}')>"


class Item(Base):
    __tablename__ = 'items'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4) # UUID
    listing_id = Column(Integer, nullable=False)  # Steam listing ID
    name = Column(String(255), nullable=False)
    current_price_usd = Column(REAL, nullable=False)
    current_price_rub = Column(REAL, nullable=False)
    url = Column(String(500), nullable=False)  # URL to the item
    
    # Relationships
    user_watchlists = relationship("UserItemWatchlist", back_populates="item", cascade="all, delete-orphan")
    
    # Table constraints
    __table_args__ = (
        Index('idx_items_listing_id', 'listing_id'),
        Index('idx_items_name', 'name'),
        Index('idx_items_current_price_usd', 'current_price_usd'),
        Index('idx_items_current_price_rub', 'current_price_rub'),
        Index('idx_items_url', 'url'),
    )
    
    def __repr__(self):
        return f"<Item(id={self.id}, listing_id={self.listing_id}, name='{self.name}', current_price_usd={self.current_price_usd}, current_price_rub={self.current_price_rub}, url='{self.url}')>"


class UserItemWatchlist(Base):
    __tablename__ = 'user_item_watchlist'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4) # UUID
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    item_id = Column(UUID(as_uuid=True), ForeignKey('items.id', ondelete='CASCADE'), nullable=False)
    url = Column(String(500), nullable=False)
    buy_target_price = Column(REAL, nullable=False)
    sell_target_price = Column(REAL, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="watchlist_items")
    item = relationship("Item", back_populates="user_watchlists")
    
    # Table constraints
    __table_args__ = (
        CheckConstraint('buy_target_price >= 0', name='buy_target_price_check'),
        CheckConstraint('sell_target_price >= 0', name='sell_target_price_check'),
        CheckConstraint('sell_target_price > buy_target_price', name='price_check'),
        UniqueConstraint('user_id', 'item_id', name='unique_user_item_watchlist'),
        Index('idx_watchlist_user_id', 'user_id'),
        Index('idx_watchlist_item_id', 'item_id'),
        Index('idx_watchlist_prices', 'buy_target_price', 'sell_target_price'),
    )
    
    def __repr__(self):
        return f"<UserItemWatchlist(id={self.id}, user_id={self.user_id}, item_id={self.item_id}, buy_target_price={self.buy_target_price}, sell_target_price={self.sell_target_price})>"

