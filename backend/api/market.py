"""
Market data API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List

from backend.database.local_db import get_database
from backend.models.market import TreasuryYields, ETFPrice, MarketData

router = APIRouter()


@router.get("/yields", response_model=List[TreasuryYields])
async def get_treasury_yields(
    days: int = Query(30, description="Days of historical data to retrieve")
):
    """
    Get Treasury yield data.
    """
    try:
        db = get_database()
        yields_data = db.get_treasury_yields(days=days)
        
        # Convert to TreasuryYields models
        yields = []
        for item in yields_data:
            yield_item = TreasuryYields(
                timestamp=item['timestamp'],
                us_2y=item['us_2y'],
                us_5y=item['us_5y'],
                us_10y=item['us_10y'],
                us_30y=item['us_30y']
            )
            yields.append(yield_item)
        
        return yields
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch yields: {str(e)}")


@router.get("/etf/{ticker}", response_model=List[ETFPrice])
async def get_etf_prices(
    ticker: str,
    days: int = Query(30, description="Days of historical data to retrieve")
):
    """
    Get ETF price data for a specific ticker.
    """
    try:
        db = get_database()
        etf_data = db.get_etf_prices(ticker=ticker.upper(), days=days)
        
        # Convert to ETFPrice models
        prices = []
        for item in etf_data:
            price = ETFPrice(
                timestamp=item['timestamp'],
                ticker=item['ticker'],
                open=item['open'],
                high=item['high'],
                low=item['low'],
                close=item['close'],
                volume=item['volume']
            )
            prices.append(price)
        
        return prices
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch ETF data: {str(e)}")


@router.get("/combined")
async def get_combined_market_data(
    days: int = Query(30, description="Days of historical data"),
    etf_ticker: str = Query("TLT", description="ETF ticker to include")
):
    """
    Get combined market data (yields + ETF prices).
    """
    try:
        db = get_database()
        
        yields_data = db.get_treasury_yields(days=days)
        etf_data = db.get_etf_prices(ticker=etf_ticker.upper(), days=days)
        
        # Convert to models
        yields = [TreasuryYields(**item) for item in yields_data]
        etf_prices = [ETFPrice(**item) for item in etf_data]
        
        return MarketData(
            treasury_yields=yields,
            etf_prices=etf_prices,
            period_days=days
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch market data: {str(e)}")

