from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import get_supabase_service_client
from ml.sentiment_model import load_sentiment_model
from ml.data_loader import DEFAULT_WEIGHTS_DIR
from routers.sentiment import router as sentiment_router
from routers.predict import router as predict_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the Supabase client singleton
    get_supabase_service_client()
    
    # Load the sentiment model globally
    model_path = DEFAULT_WEIGHTS_DIR / "sentiment_model.pth"
    app.state.sentiment_model = load_sentiment_model(model_path)
    
    yield

app = FastAPI(title="QuantVantage API", lifespan=lifespan)

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
app.include_router(predict_router)


@app.get("/")
async def read_root() -> dict[str, str]:
    return {"status": "QuantVantage API Running"}