"""
Форматтеры для сообщений бота
"""
from typing import List, Dict, Any
from SMPC.bot.config import BotConstants


def format_watchlist_item(item: Dict[str, Any], currency: str) -> str:
    """Форматирование элемента списка отслеживания"""
    current_price = item['item']['current_price_rub'] if currency == 'RUB' else item['item']['current_price_usd']
    # Округляем до 2 знаков после запятой для корректного отображения
    current_price = round(float(current_price), 2)
    buy_price = round(float(item['buy_target_price']), 2)
    sell_price = round(float(item['sell_target_price']), 2)
    
    return (
        f"{item['item']['name']}:\n"
        f"\tCurrent price: {current_price:.2f} {currency}\n"
        f"\tSell price: {sell_price:.2f} {currency}\n"
        f"\tBuy price: {buy_price:.2f} {currency}\n"
    )


def format_watchlist(watchlist: List[Dict[str, Any]], currency: str) -> str:
    """Форматирование всего списка отслеживания"""
    if not watchlist:
        return BotConstants.MESSAGES['EMPTY_WATCHLIST']
    
    response = ""
    for item in watchlist:
        response += format_watchlist_item(item, currency) + "\n"
    
    return response.strip()


def format_alerts_message(alerts: List[Dict[str, Any]], header: str, price_format: str, currency: str) -> str:
    """Форматирование сообщения с алертами"""
    if not alerts:
        return ""
    
    alert_lines = []
    for alert in alerts:
        current_price = alert['current_price_rub'] if currency == 'RUB' else alert['current_price_usd']
        price_info = price_format.format(current_price, alert['target_price'])
        alert_lines.append(f"{alert['item_name']}: {price_info} [LINK]({alert['url']})")
        alert_lines.append("-" * 50)
    
    return f"{header}\n" + "\n".join(alert_lines)


def format_help_message() -> str:
    """Форматирование справочного сообщения"""
    return """
/start - Start the bot
/add - Add an item to the watchlist
/subscribe - Subscribe to notifications, when price of item is reached to target prices (sell or buy)
/unsubscribe - Unsubscribe from notifications
/prices - Show the current prices of all items in the watchlist
/change_currency - Change your preferred currency (USD/RUB)
/help - Show this help message
    """.strip()


def format_error_message(error_type: str, details: str = "") -> str:
    """Форматирование сообщения об ошибке"""
    error_messages = {
        'validation': BotConstants.MESSAGES['INVALID_URL'],
        'price_validation': BotConstants.MESSAGES['INVALID_PRICE'],
        'item_exists': BotConstants.MESSAGES['ITEM_EXISTS'],
        'price_range': BotConstants.MESSAGES['BUY_PRICE_TOO_HIGH'],
        'server_error': BotConstants.MESSAGES['SOMETHING_WRONG'],
        'network_error': "Network error. Please try again later.",
        'timeout_error': "Request timeout. Please try again later."
    }
    
    message = error_messages.get(error_type, BotConstants.MESSAGES['SOMETHING_WRONG'])
    if details:
        message += f"\n\nDetails: {details}"
    
    return message

