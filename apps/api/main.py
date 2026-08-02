from fastapi import FastAPI

app = FastAPI(title="QuantVantage API")


@app.get("/")
async def read_root() -> dict[str, str]:
    return {"status": "QuantVantage API Running"}