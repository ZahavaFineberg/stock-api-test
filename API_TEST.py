from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
import yfinance as yf
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Stock Market API",
    description="API for retrieving stock market data using yfinance"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StockData(BaseModel):
    full_name: str
    close_prices: Dict[str, float]

class StockResponse(BaseModel):
    data: Dict[str, StockData]

@app.get("/stocks/{ticker}", response_model=StockData)
async def get_stock_data(ticker: str):
    """Get historical data for a single stock ticker"""
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info
        long_name = info.get('longName', 'N/A')

        if not long_name or long_name == 'N/A':
            raise HTTPException(status_code=404, detail=f"Could not retrieve full name for {ticker}")

        hist = stock.history(period="1y", interval="1d")
        if hist.empty:
            hist = stock.history(period="max", interval="1d")

        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No historical data available for {ticker}")

        close_prices = hist['Close'].dropna().to_dict()
        close_prices = {str(date): price for date, price in close_prices.items()}

        return StockData(
            full_name=long_name,
            close_prices=close_prices
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stocks", response_model=StockResponse)
async def get_multiple_stocks(tickers: str):
    """Get historical data for multiple stock tickers (comma-separated)"""
    ticker_list = [ticker.strip().upper() for ticker in tickers.split(',')]
    all_data = {}

    for ticker in ticker_list:
        try:
            stock_data = await get_stock_data(ticker)
            all_data[ticker] = stock_data
        except HTTPException as e:
            all_data[ticker] = {"error": e.detail}

    return StockResponse(data=all_data)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
