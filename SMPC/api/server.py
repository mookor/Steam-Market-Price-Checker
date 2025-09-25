from fastapi import FastAPI, HTTPException, Depends, Request
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
import asyncio
import sys
import os
import time
import logging
import traceback
from asyncpg.exceptions import UniqueViolationError


from SMPC.database import CRUD, create_session_factory, models
from SMPC.database.models import User, Item, UserItemWatchlist


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/api.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("steam_api")


# Middleware for request logging
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log incoming request
        logger.info(f"🔵 Incoming request: {request.method} {request.url.path}")
        logger.debug(f"Request headers: {dict(request.headers)}")
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"Client IP: {client_ip}")
        
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(f"✅ Response: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
            
            # Add processing time to response headers
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"❌ Error processing request: {request.method} {request.url.path} - Time: {process_time:.3f}s - Error: {str(e)}")
            raise


# Pydantic models for requests/responses
class UserCreate(BaseModel):
    id: UUID
    telegram_id: int
    subscriber: bool = True
    currency: str = "USD"


class UserResponse(BaseModel):
    id: UUID
    telegram_id: int
    subscriber: bool
    currency: str
    
    
    class Config:
        from_attributes = True


class ItemCreate(BaseModel):
    listing_id: int
    name: str
    current_price_usd: float
    current_price_rub: float
    url: str


class ItemResponse(BaseModel):
    id: UUID
    listing_id: int
    name: str
    current_price_usd: float
    current_price_rub: float
    url: str
    
    
    class Config:
        from_attributes = True


class WatchlistItemCreate(BaseModel):
    item_id: UUID
    buy_target_price: float
    sell_target_price: float
    url: str


class WatchlistItemResponse(BaseModel):
    id: UUID
    user_id: UUID
    item_id: UUID
    buy_target_price: float
    sell_target_price: float
    url: str
    item: ItemResponse
    
    
    class Config:
        from_attributes = True


class ItemPriceUpdate(BaseModel):
    name: str
    new_price_usd: float
    new_price_rub: float


class PriceAlertItem(BaseModel):
    watchlist_id: UUID
    item_id: UUID
    item_name: str
    listing_id: int
    current_price_usd: float
    current_price_rub: float
    target_price: float
    difference: float
    comparison_currency: str
    url: str

class PriceAlertsResponse(BaseModel):
    buy: List[PriceAlertItem]
    sell: List[PriceAlertItem]


# Initialize FastAPI app
app = FastAPI(
    title="Steam Watchlist API",
    description="API для управления watchlist Steam товаров",
    version="1.0.0"
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)


# Initialize database session on startup
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting Steam Watchlist API...")
    try:
        session_factory = create_session_factory()
        CRUD.init_session(session_factory)
        logger.info("✅ Database connection initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {str(e)}")
        raise


# User endpoints
@app.post("/users/", response_model=dict)
async def create_user(user_data: UserCreate):
    """Создать нового пользователя"""
    logger.info(f"👤 Creating user with ID: {user_data.id}, subscriber: {user_data.subscriber}")
    
    try:
        user = User(id=user_data.id, telegram_id=user_data.telegram_id, subscriber=user_data.subscriber, currency=user_data.currency)
        user_id = await CRUD.create_user(user)
        
        logger.info(f"✅ User created successfully: {user_id}")
        return {"user_id": user_id, "message": "User created successfully"}
        
    except UniqueViolationError:
        logger.warning(f"⚠️ Attempt to create duplicate user: {user_data.id}, telegram_id: {user_data.telegram_id}")
        raise HTTPException(status_code=400, detail="User already exists")
    except Exception as e:
        logger.error(f"❌ Error creating user {user_data.id}, telegram_id: {user_data.telegram_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")


@app.get("/users/subscribers", response_model=List[UserResponse])
async def get_subscribers():
    """Получить список всех пользователей-подписчиков"""
    logger.info("📋 Fetching all subscribers")
    
    try:
        subscribers = await CRUD.get_subscribers()
        logger.info(f"✅ Found {len(subscribers)} subscribers")
        return subscribers
        
    except Exception as e:
        logger.error(f"❌ Error getting subscribers: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting subscribers: {str(e)}")


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: UUID):
    """Получить пользователя по ID"""
    logger.info(f"🔍 Fetching user: {user_id}")
    
    try:
        user = await CRUD.read_user(user_id)
        if not user:
            logger.warning(f"⚠️ User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"✅ User found: {user_id}, telegram_id: {user.telegram_id}, subscriber: {user.subscriber}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error reading user {user_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error reading user: {str(e)}")


# Item endpoints
@app.post("/items/", response_model=dict)
async def create_or_get_item(item_data: ItemCreate):
    """Создать товар или получить существующий"""
    logger.info(f"📦 Creating/getting item: {item_data.name} (listing_id: {item_data.listing_id}, price_usd: {item_data.current_price_usd}, price_rub: {item_data.current_price_rub})")
    
    try:
        item = Item(
            listing_id=item_data.listing_id,
            name=item_data.name,
            current_price_usd=item_data.current_price_usd,
            current_price_rub=item_data.current_price_rub,
            url=item_data.url
        )
        item_id = await CRUD.create_or_get_item(item=item)
        
        logger.info(f"✅ Item processed successfully: {item_data.name} -> {item_id}")
        return {"item_id": item_id, "message": "Item created/updated successfully"}
        
    except UniqueViolationError:
        logger.warning(f"⚠️ Attempt to create duplicate item: {item_data.name}")
        raise HTTPException(status_code=400, detail="Item already exists")
    except Exception as e:
        logger.error(f"❌ Error creating/updating item {item_data.name}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error creating/updating item: {str(e)}")


@app.get("/items/", response_model=List[ItemResponse])
async def get_all_items():
    """Получить все товары"""
    logger.info("📋 Fetching all items")
    items = await CRUD.get_all_items()
    return items

@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: UUID):
    """Получить товар по ID"""
    logger.info(f"🔍 Fetching item: {item_id}")
    
    try:
        item = await CRUD.read_item(item_id)
        if not item:
            logger.warning(f"⚠️ Item not found: {item_id}")
            raise HTTPException(status_code=404, detail="Item not found")
        
        logger.info(f"✅ Item found: {item.name} (price_usd: {item.current_price_usd}, price_rub: {item.current_price_rub})")
        return item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error reading item {item_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error reading item: {str(e)}")


@app.put("/items/price", response_model=dict)
async def update_item_price(price_update: ItemPriceUpdate):
    """Обновить цены товара по имени"""
    logger.info(f"💰 Updating prices for item: {price_update.name} -> USD: {price_update.new_price_usd}, RUB: {price_update.new_price_rub}")
    
    try:
        success = await CRUD.update_item_price(
            name=price_update.name,
            new_price_usd=price_update.new_price_usd,
            new_price_rub=price_update.new_price_rub
        )
        if not success:
            logger.warning(f"⚠️ Item not found for price update: {price_update.name}")
            raise HTTPException(status_code=404, detail="Item not found")
        
        logger.info(f"✅ Prices updated successfully for: {price_update.name}")
        return {"message": "Item prices updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating price for {price_update.name}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error updating item price: {str(e)}")


@app.get("/items/exists/{item_name}", response_model=dict)
async def check_item_exists(item_name: str):
    """Проверить существование товара по имени"""
    logger.info(f"🔍 Checking existence of item: {item_name}")
    
    try:
        item = await CRUD.check_item_exists_by_name(item_name)
        if item:
            logger.info(f"✅ Item exists: {item_name} (id: {item.id}, price_usd: {item.current_price_usd}, price_rub: {item.current_price_rub})")
            return {
                "exists": True,
                "item_id": item.id,
                "listing_id": item.listing_id,
                "current_price_usd": item.current_price_usd,
                "current_price_rub": item.current_price_rub,
                "url": item.url
            }
        else:
            logger.info(f"ℹ️ Item does not exist: {item_name}")
            return {"exists": False}
            
    except Exception as e:
        logger.error(f"❌ Error checking existence of {item_name}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error checking item existence: {str(e)}")


# Watchlist endpoints
@app.post("/users/{user_id}/watchlist", response_model=dict)
async def add_to_watchlist(user_id: UUID, watchlist_item: WatchlistItemCreate):
    """Добавить товар в watchlist пользователя"""
    logger.info(f"📝 Adding item to watchlist: user={user_id}, item={watchlist_item.item_id}, buy_target={watchlist_item.buy_target_price}, sell_target={watchlist_item.sell_target_price}")
    
    try:
        # Проверяем существование пользователя
        user = await CRUD.read_user(user_id)
        if not user:
            logger.warning(f"⚠️ User not found for watchlist operation: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Проверяем существование товара
        item = await CRUD.read_item(watchlist_item.item_id)
        if not item:
            logger.warning(f"⚠️ Item not found for watchlist operation: {watchlist_item.item_id}")
            raise HTTPException(status_code=404, detail="Item not found")
        
        logger.info(f"📦 Adding item '{item.name}' to user {user_id} watchlist, url={watchlist_item.url}")
        
        watchlist_id, was_added = await CRUD.add_item_to_watchlist(
            watchlist_item=UserItemWatchlist(
                user_id=user_id,
                item_id=watchlist_item.item_id,
                buy_target_price=watchlist_item.buy_target_price,
                sell_target_price=watchlist_item.sell_target_price,
                url=watchlist_item.url
            )
        )
        
        if was_added:
            message = "Item added to watchlist successfully"
            logger.info(f"✅ Item added to watchlist: {item.name} -> {watchlist_id}")
        else:
            message = "Item already in watchlist"
            logger.info(f"ℹ️ Item already in watchlist: {item.name}")
            
        return {"watchlist_id": watchlist_id, "message": message}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error adding to watchlist for user {user_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error adding to watchlist: {str(e)}")


@app.get("/users/{user_id}/watchlist", response_model=List[WatchlistItemResponse])
async def get_user_watchlist(user_id: UUID):
    """Получить watchlist пользователя"""
    logger.info(f"📋 Fetching watchlist for user: {user_id}")
    
    try:
        # Проверяем существование пользователя
        user = await CRUD.read_user(user_id)
        if not user:
            logger.warning(f"⚠️ User not found for watchlist fetch: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        watchlist = await CRUD.read_user_watchlist(user_id)
        logger.info(f"✅ Watchlist fetched: {len(watchlist)} items for user {user_id}")
        return watchlist
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error reading watchlist for user {user_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error reading watchlist: {str(e)}")


@app.delete("/users/{user_id}/watchlist/{item_id}", response_model=dict)
async def remove_from_watchlist(user_id: UUID, item_id: UUID):
    """Удалить товар из watchlist пользователя"""
    logger.info(f"🗑️ Removing item from watchlist: user={user_id}, item={item_id}")
    
    try:
        success = await CRUD.remove_from_watchlist(user_id=user_id, item_id=item_id)
        if not success:
            logger.warning(f"⚠️ Watchlist item not found for removal: user={user_id}, item={item_id}")
            raise HTTPException(status_code=404, detail="Watchlist item not found")
        
        logger.info(f"✅ Item removed from watchlist: user={user_id}, item={item_id}")
        return {"message": "Item removed from watchlist successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error removing from watchlist: user={user_id}, item={item_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error removing from watchlist: {str(e)}")


@app.get("/users/{user_id}/watchlist/alerts", response_model=PriceAlertsResponse)
async def get_watchlist_price_alerts(user_id: UUID, currency: str = 'usd'):
    """Получить алерты по ценам из watchlist пользователя"""
    logger.info(f"🚨 Fetching price alerts for user: {user_id}, currency: {currency}")
    
    try:
        # Проверяем существование пользователя
        user = await CRUD.read_user(user_id)
        if not user:
            logger.warning(f"⚠️ User not found for price alerts: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Получаем алерты по ценам
        alerts_data = await CRUD.get_watchlist_price_alerts(user_id, currency=currency)
        
        # Преобразуем данные в Pydantic модели
        buy_alerts = [
            PriceAlertItem(
                watchlist_id=alert['watchlist_id'],
                item_id=alert['item_id'],
                item_name=alert['item_name'],
                listing_id=alert['listing_id'],
                current_price_usd=alert['current_price_usd'],
                current_price_rub=alert['current_price_rub'],
                target_price=alert['target_price'],
                difference=alert['difference'],
                comparison_currency=alert['comparison_currency'],
                url=alert['url']
            )
            for alert in alerts_data['buy']
        ]
        
        sell_alerts = [
            PriceAlertItem(
                watchlist_id=alert['watchlist_id'],
                item_id=alert['item_id'],
                item_name=alert['item_name'],
                listing_id=alert['listing_id'],
                current_price_usd=alert['current_price_usd'],
                current_price_rub=alert['current_price_rub'],
                target_price=alert['target_price'],
                difference=alert['difference'],
                comparison_currency=alert['comparison_currency'],
                url=alert['url']
            )
            for alert in alerts_data['sell']
        ]
        print(sell_alerts)
        logger.info(f"✅ Price alerts fetched: {len(buy_alerts)} buy alerts, {len(sell_alerts)} sell alerts for user {user_id}")
        return PriceAlertsResponse(buy=buy_alerts, sell=sell_alerts)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting price alerts for user {user_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error getting price alerts: {str(e)}")


@app.get("/users/{user_id}/watchlist/check/{item_id}", response_model=dict)
async def check_item_in_watchlist(user_id: UUID, item_id: UUID):
    """Проверить, есть ли предмет в watchlist пользователя"""
    logger.info(f"🔍 Checking if item is in watchlist: user={user_id}, item={item_id}")
    
    try:
        # Проверяем существование пользователя
        user = await CRUD.read_user(user_id)
        if not user:
            logger.warning(f"⚠️ User not found for watchlist check: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Проверяем существование товара
        item = await CRUD.read_item(item_id)
        if not item:
            logger.warning(f"⚠️ Item not found for watchlist check: {item_id}")
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Проверяем наличие в watchlist
        watchlist_item = await CRUD.check_item_in_user_watchlist(user_id, item_id)
        
        if watchlist_item:
            logger.info(f"✅ Item found in watchlist: {item.name} for user {user_id}")
            return {
                "in_watchlist": True,
                "watchlist_id": watchlist_item.id,
                "buy_target_price": watchlist_item.buy_target_price,
                "sell_target_price": watchlist_item.sell_target_price,
                "url": watchlist_item.url
            }
        else:
            logger.info(f"ℹ️ Item not in watchlist: {item.name} for user {user_id}")
            return {"in_watchlist": False}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error checking item in watchlist: user={user_id}, item={item_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error checking item in watchlist: {str(e)}")

@app.put("/subscription/{user_id}", response_model=dict)
async def change_user_subscription(user_id: UUID, request: dict):
    """Изменить статус подписки пользователя"""
    subscriber = request.get("subscriber")
    if subscriber is None:
        raise HTTPException(status_code=400, detail="subscriber field is required")
    
    logger.info(f"🔍 Changing subscription status for user: {user_id} to {subscriber}")
    try:
        await CRUD.change_user_subscription(user_id=user_id, subscriber=subscriber)
        logger.info(f"✅ Subscription status changed successfully for user: {user_id} to {subscriber}")
        return {"message": "Subscription status changed successfully"}
    except ValueError as e:
        logger.error(f"❌ User not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error changing subscription status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error changing subscription status: {str(e)}")


@app.put("/users/{user_id}/currency", response_model=dict)
async def change_user_currency(user_id: UUID, request: dict):
    """Изменить валюту пользователя"""
    currency = request.get("currency")
    if currency is None:
        raise HTTPException(status_code=400, detail="currency field is required")
    
    if currency not in ["USD", "RUB"]:
        raise HTTPException(status_code=400, detail="currency must be USD or RUB")
    
    logger.info(f"💱 Changing currency for user: {user_id} to {currency}")
    try:
        await CRUD.change_user_currency(user_id=user_id, currency=currency)
        logger.info(f"✅ Currency changed successfully for user: {user_id} to {currency}")
        return {"message": "Currency changed successfully"}
    except ValueError as e:
        logger.error(f"❌ User not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error changing currency: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error changing currency: {str(e)}")


@app.put("/users/{user_id}/watchlist/{watchlist_id}/prices", response_model=dict)
async def update_watchlist_item_prices(user_id: UUID, watchlist_id: UUID, request: dict):
    """Обновить цены покупки и продажи для элемента watchlist"""
    buy_target_price = request.get("buy_target_price")
    sell_target_price = request.get("sell_target_price")
    
    if buy_target_price is None or sell_target_price is None:
        raise HTTPException(status_code=400, detail="buy_target_price and sell_target_price are required")
    
    logger.info(f"💰 Updating watchlist item prices: user={user_id}, watchlist_id={watchlist_id}, buy={buy_target_price}, sell={sell_target_price}")
    try:
        success = await CRUD.update_watchlist_item_prices(
            user_id=user_id,
            watchlist_id=watchlist_id,
            buy_target_price=buy_target_price,
            sell_target_price=sell_target_price
        )
        if not success:
            logger.warning(f"⚠️ Watchlist item not found: user={user_id}, watchlist_id={watchlist_id}")
            raise HTTPException(status_code=404, detail="Watchlist item not found")
        
        logger.info(f"✅ Watchlist item prices updated successfully")
        return {"message": "Watchlist item prices updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating watchlist item prices: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating watchlist item prices: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Проверка состояния сервиса"""
    logger.debug("❤️ Health check requested")
    return {"status": "healthy", "timestamp": datetime.now()}


if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting Steam Watchlist API server...")
    logger.info("📍 Server will be available at: http://0.0.0.0:8000")
    logger.info("📖 API documentation will be available at: http://0.0.0.0:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
