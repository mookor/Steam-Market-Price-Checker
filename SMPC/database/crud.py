from SMPC.database.session import get_session
from SMPC.database.models import User, Item, UserItemWatchlist
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID



class CRUD:
    session_factory = None

    @classmethod
    def init_session(cls, session_factory):
        cls.session_factory = session_factory

    @staticmethod
    async def create_user(user: User):
        async with get_session(CRUD.session_factory) as session:
            session.add(user)
            await session.commit()
            return user.id

    @staticmethod
    async def create_or_get_item(item: Item):
        """Create item if it doesn't exist, or get existing one"""
        async with get_session(CRUD.session_factory) as session:
            # Try to find existing item
            stmt = select(Item).where(Item.name == item.name)
            result = await session.execute(stmt)
            existing_item = result.scalar_one_or_none()
            
            if existing_item:
                # Update price and URL if item exists, with rounding
                existing_item.current_price_usd = round(float(item.current_price_usd), 2)
                existing_item.current_price_rub = round(float(item.current_price_rub), 2)
                existing_item.url = item.url
                await session.commit()
                return existing_item.id
            else:
                # Create new item with rounded prices
                new_item = Item(
                    listing_id=item.listing_id, 
                    name=item.name, 
                    current_price_usd=round(float(item.current_price_usd), 2), 
                    current_price_rub=round(float(item.current_price_rub), 2), 
                    url=item.url
                )
                
                session.add(new_item)
                await session.commit()
                return new_item.id

    @staticmethod
    async def add_item_to_watchlist(watchlist_item: UserItemWatchlist):
        """Add item to user's watchlist"""
        async with get_session(CRUD.session_factory) as session:
            # Проверяем, есть ли уже такая запись в watchlist
            existing_item = await session.execute(
                select(UserItemWatchlist).where(
                    UserItemWatchlist.user_id == watchlist_item.user_id,
                    UserItemWatchlist.item_id == watchlist_item.item_id
                )
            )
            existing_item = existing_item.scalar_one_or_none()
            
            if existing_item:
                # Если товар уже есть в watchlist, возвращаем его ID и флаг, что это существующая запись
                return existing_item.id, False
            
            # Если товара нет, добавляем новый с округлением цен
            watchlist_item = UserItemWatchlist(
                user_id=watchlist_item.user_id,
                item_id=watchlist_item.item_id,
                buy_target_price=round(float(watchlist_item.buy_target_price), 2),
                sell_target_price=round(float(watchlist_item.sell_target_price), 2),
                url=watchlist_item.url
            )
            session.add(watchlist_item)
            await session.commit()
            return watchlist_item.id, True

    @staticmethod
    async def read_user(user_id: UUID):
        async with get_session(CRUD.session_factory) as session:
            user = await session.get(User, user_id)
            return user

    @staticmethod
    async def read_user_watchlist(user_id: UUID):
        """Get user's watchlist with item details"""
        async with get_session(CRUD.session_factory) as session:
            stmt = select(UserItemWatchlist).options(
                selectinload(UserItemWatchlist.item)
            ).where(UserItemWatchlist.user_id == user_id)
            result = await session.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def read_item(item_id: UUID):
        async with get_session(CRUD.session_factory) as session:
            item = await session.get(Item, item_id)
            return item

    @staticmethod
    async def update_item_price(name: str, new_price_usd: float, new_price_rub: float):
        """Update item prices by name"""
        async with get_session(CRUD.session_factory) as session:
            stmt = select(Item).where(Item.name == name)
            result = await session.execute(stmt)
            item = result.scalar_one_or_none()
            
            if item:
                # Округляем цены до 2 знаков после запятой
                item.current_price_usd = round(float(new_price_usd), 2)
                item.current_price_rub = round(float(new_price_rub), 2)
                await session.commit()
                return True
            return False

    @staticmethod
    async def remove_from_watchlist(user_id: UUID, item_id: UUID):
        """Remove item from user's watchlist"""
        async with get_session(CRUD.session_factory) as session:
            stmt = select(UserItemWatchlist).where(
                UserItemWatchlist.user_id == user_id,
                UserItemWatchlist.item_id == item_id
            )
            result = await session.execute(stmt)
            watchlist_item = result.scalar_one_or_none()
            
            if watchlist_item:
                await session.delete(watchlist_item)
                await session.commit()
                return True
            return False

    @staticmethod
    async def get_watchlist_price_alerts(user_id: UUID, currency: str = 'usd'):
        """
        Get watchlist items where current price triggers buy/sell alerts
        Returns dict with 'buy' and 'sell' lists of items
        
        Args:
            user_id: User UUID
            currency: Currency to use for price comparison ('usd' or 'rub')
        
        Buy alert: current_price <= buy_target_price (good time to buy)
        Sell alert: current_price >= sell_target_price (good time to sell)
        """
        async with get_session(CRUD.session_factory) as session:
            stmt = select(UserItemWatchlist).options(
                selectinload(UserItemWatchlist.item)
            ).where(UserItemWatchlist.user_id == user_id)
            result = await session.execute(stmt)
            watchlist_items = result.scalars().all()
            
            buy_alerts = []
            sell_alerts = []
            
            for watchlist_item in watchlist_items:
                current_price_usd = watchlist_item.item.current_price_usd
                current_price_rub = watchlist_item.item.current_price_rub
                buy_target = watchlist_item.buy_target_price
                sell_target = watchlist_item.sell_target_price
                
                # Choose which price to use for comparison based on currency parameter
                if currency.lower() == 'rub':
                    current_price_for_comparison = current_price_rub
                else:  # default to USD
                    current_price_for_comparison = current_price_usd
                print(123, current_price_for_comparison, buy_target)
                # Buy alert: current price is at or below buy target
                if round(current_price_for_comparison, 2) <= round(buy_target, 2):
                    buy_alerts.append({
                        'watchlist_id': watchlist_item.id,
                        'item_id': watchlist_item.item.id,
                        'item_name': watchlist_item.item.name,
                        'listing_id': watchlist_item.item.listing_id,
                        'current_price_usd': current_price_usd,
                        'current_price_rub': current_price_rub,
                        'target_price': buy_target,
                        'difference': buy_target - current_price_for_comparison,
                        'comparison_currency': currency.lower(),
                        'url': watchlist_item.url
                    })
                
                # Sell alert: current price is at or above sell target
                if round(current_price_for_comparison, 2) >= round(sell_target, 2):
                    sell_alerts.append({
                        'watchlist_id': watchlist_item.id,
                        'item_id': watchlist_item.item.id,
                        'item_name': watchlist_item.item.name,
                        'listing_id': watchlist_item.item.listing_id,
                        'current_price_usd': current_price_usd,
                        'current_price_rub': current_price_rub,
                        'target_price': sell_target,
                        'difference': current_price_for_comparison - sell_target,
                        'comparison_currency': currency.lower(),
                        'url': watchlist_item.url
                    })
            
            print(buy_alerts, sell_alerts)
            return {
                'buy': buy_alerts,
                'sell': sell_alerts
            }

    @staticmethod
    async def get_subscribers():
        """Get all users who are subscribers"""
        async with get_session(CRUD.session_factory) as session:
            stmt = select(User).where(User.subscriber == True)
            result = await session.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def get_all_items():
        """Get all items"""
        async with get_session(CRUD.session_factory) as session:
            stmt = select(Item)
            result = await session.execute(stmt)
            return result.scalars().all()


    @staticmethod
    async def check_item_exists_by_name(name: str):
        """Check if item exists by name, returns item if found or None"""
        async with get_session(CRUD.session_factory) as session:
            stmt = select(Item).where(Item.name == name)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def check_item_in_user_watchlist(user_id: UUID, item_id: UUID):
        """Check if item exists in user's watchlist, returns watchlist item if found or None"""
        async with get_session(CRUD.session_factory) as session:
            stmt = select(UserItemWatchlist).where(
                UserItemWatchlist.user_id == user_id,
                UserItemWatchlist.item_id == item_id
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @staticmethod
    async def change_user_subscription(user_id: UUID, subscriber: bool):
        """Change user's subscription status"""
        async with get_session(CRUD.session_factory) as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user is None:
                raise ValueError(f"User with ID {user_id} not found")
            
            user.subscriber = subscriber
            await session.commit()
            return user.id

    @staticmethod
    async def change_user_currency(user_id: UUID, currency: str):
        """Change user's currency"""
        async with get_session(CRUD.session_factory) as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user is None:
                raise ValueError(f"User with ID {user_id} not found")
            
            user.currency = currency
            await session.commit()
            return user.id

    @staticmethod
    async def update_watchlist_item_prices(user_id: UUID, watchlist_id: UUID, buy_target_price: float, sell_target_price: float):
        """Update buy and sell target prices for a watchlist item"""
        async with get_session(CRUD.session_factory) as session:
            stmt = select(UserItemWatchlist).where(
                UserItemWatchlist.id == watchlist_id,
                UserItemWatchlist.user_id == user_id
            )
            result = await session.execute(stmt)
            watchlist_item = result.scalar_one_or_none()
            
            if watchlist_item is None:
                return False
            
            # Округляем цены до 2 знаков после запятой
            watchlist_item.buy_target_price = round(float(buy_target_price), 2)
            watchlist_item.sell_target_price = round(float(sell_target_price), 2)
            await session.commit()
            return True

async def main():
    from session import create_session_factory
    CRUD.init_session(create_session_factory())

    # # Create user
    # user = User(subscriber=True, period=5)
    # user_id = await CRUD.create_user(user)
    # print(f"Created user with ID: {user_id}")

    # # Create or get item (normalized approach)
    # item_id = await CRUD.create_or_get_item(
    #     listing_id=730,
    #     name="AK-47 | Redline",
    #     current_price=25.50
    # )
    # item_id2 = await CRUD.create_or_get_item(
    #     listing_id=730,
    #     name="AK-47 | Redline (Field-Tested)",
    #     current_price=35.50
    # )
    # print(f"Created/found item with ID: {item_id}")

    # # Add item to user's watchlist
    # watchlist_id = await CRUD.add_item_to_watchlist(
    #     user_id=user_id,
    #     item_id=item_id,
    #     buy_target_price=20.0,
    #     sell_target_price=30.0
    # )
    # watchlist_id = await CRUD.add_item_to_watchlist(
    #     user_id=user_id,
    #     item_id=item_id2,
    #     buy_target_price=20.0,
    #     sell_target_price=70.0
    # )
    # print(f"Added to watchlist with ID: {watchlist_id}")

    # Read user and their watchlist
    # user = await CRUD.read_user(user_id)
    # watchlist = await CRUD.read_user_watchlist(user_id)
    
    # print(f"User: {user}")
    # print(f"Watchlist items: {len(watchlist)}")
    # for watchlist_item in watchlist:
    #     print(f"  - {watchlist_item.item.name}: buy at {watchlist_item.buy_target_price}, sell at {watchlist_item.sell_target_price}, current: {watchlist_item.item.current_price_usd} USD / {watchlist_item.item.current_price_rub} RUB")

    # # Update item price (simulating price update from Steam API)
    # await CRUD.update_item_price(name="AK-47 | Redline", new_price_usd=32.75, new_price_rub=2950.0)
    # print("Updated item prices to 32.75 USD / 2950.0 RUB")

    # Read updated watchlist
    from uuid import UUID
    user_id = UUID("2798fee3-be76-43be-8d28-2e9182dfc89f")
    watchlist = await CRUD.read_user_watchlist(user_id)
    for watchlist_item in watchlist:
        print(f"  - {watchlist_item.item.name}: current price now {watchlist_item.item.current_price_usd} USD / {watchlist_item.item.current_price_rub} RUB")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())