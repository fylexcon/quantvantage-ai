from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.sentiment import router as sentiment_router

app = FastAPI(title="QuantVantage API")

# ---------------------------------------------------------------------------
# CORS Middleware — allow Next.js (localhost:3000) and future mobile clients
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Router Registration
# ---------------------------------------------------------------------------
app.include_router(sentiment_router)


@app.get("/")
async def read_root() -> dict[str, str]:
    return {"status": "QuantVantage API Running"}