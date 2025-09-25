#!/usr/bin/env python3
"""
Скрипт для запуска FastAPI сервера
"""
import uvicorn

if __name__ == "__main__":
    print("🚀 Запуск Steam Watchlist API сервера...")
    print("📍 Сервер будет доступен по адресу: http://localhost:8000")
    print("📚 Документация API: http://localhost:8000/docs")
    print("🔧 Альтернативная документация: http://localhost:8000/redoc")
    
    uvicorn.run(
        "SMPC.api.server:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
