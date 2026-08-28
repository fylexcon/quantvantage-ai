import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv("apps/web/.env.local")

sys.path.append("apps/api")
from routers.sentiment import get_sentiment

async def main():
    try:
        res = await get_sentiment("AAPL")
        print(len(res))
        if len(res) > 0:
            print(res[0])
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
