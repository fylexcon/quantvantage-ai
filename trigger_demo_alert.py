import asyncio
import sys
from dotenv import load_dotenv

load_dotenv("apps/api/.env")
sys.path.append("apps/api")

from utils.notifications import send_sentiment_alert

async def trigger_demo_alert():
    print("Triggering demo Telegram alert for video recording...")
    await send_sentiment_alert(
        ticker="AAPL",
        sentiment="Bullish",
        score=0.92,
        summary="BREAKING: Apple absolutely crushes Q4 earnings expectations, triggering a massive wave of bullish sentiment across institutional investors."
    )
    print("Alert sent! Check your Telegram.")

if __name__ == "__main__":
    asyncio.run(trigger_demo_alert())
