import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv("apps/web/.env.local")

sys.path.append("apps/api")
from routers.sentiment import get_sentiment_summary

async def main():
    try:
        res = await get_sentiment_summary("AAPL")
        print(res)
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
