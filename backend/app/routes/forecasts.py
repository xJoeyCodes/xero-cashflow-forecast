from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta
from pydantic import BaseModel

from ..models.database import get_db, Forecast

# Try to import the full forecasting service, fall back to simple version
try:
    from ..services.forecasting_service import ForecastingService
    FULL_FORECASTING_AVAILABLE = True
except ImportError:
    from ..services.simple_forecasting import SimpleForecastingService as ForecastingService
    FULL_FORECASTING_AVAILABLE = False
    print("Using simple forecasting service (pandas/sklearn not available)")

router = APIRouter()

class ForecastResponse(BaseModel):
    id: int
    date: datetime
    predicted_cash_balance: float
    predicted_income: Optional[float]
    predicted_expenses: Optional[float]
    confidence_interval_lower: Optional[float]
    confidence_interval_upper: Optional[float]
    model_version: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class ForecastRequest(BaseModel):
    days_ahead: int = 90
    model_type: str = "prophet"  # or "arima", "linear"
    include_confidence_intervals: bool = True

@router.post("/forecast", response_model=List[ForecastResponse])
async def generate_forecast(
    request: ForecastRequest,
    db: Session = Depends(get_db)
):
    """Generate cash flow forecast using ML models"""
    try:
        forecasting_service = ForecastingService(db)
        forecasts = await forecasting_service.generate_forecast(
            days_ahead=request.days_ahead,
            model_type=request.model_type,
            include_confidence_intervals=request.include_confidence_intervals
        )
        return forecasts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate forecast: {str(e)}")

@router.get("/forecast", response_model=List[ForecastResponse])
async def get_forecasts(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get existing forecasts"""
    query = db.query(Forecast)
    
    if start_date:
        query = query.filter(Forecast.date >= start_date)
    if end_date:
        query = query.filter(Forecast.date <= end_date)
    
    forecasts = query.order_by(Forecast.date.asc()).limit(limit).all()
    return forecasts

@router.get("/forecast/latest")
async def get_latest_forecast(
    days_ahead: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get the most recent forecast data"""
    end_date = datetime.now() + timedelta(days=days_ahead)
    
    forecasts = db.query(Forecast).filter(
        Forecast.date >= datetime.now(),
        Forecast.date <= end_date
    ).order_by(Forecast.date.asc()).all()
    
    if not forecasts:
        # Generate new forecast if none exists
        forecasting_service = ForecastingService(db)
        forecasts = await forecasting_service.generate_forecast(days_ahead=days_ahead)
    
    return {
        "forecasts": [ForecastResponse.from_orm(f) for f in forecasts],
        "summary": {
            "total_forecasts": len(forecasts),
            "date_range": {
                "start": forecasts[0].date if forecasts else None,
                "end": forecasts[-1].date if forecasts else None
            },
            "cash_flow_trend": _calculate_trend(forecasts) if forecasts else None
        }
    }

@router.delete("/forecast")
async def clear_forecasts(
    before_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Clear old forecasts"""
    query = db.query(Forecast)
    
    if before_date:
        query = query.filter(Forecast.date < before_date)
    else:
        # Default: clear forecasts older than 30 days
        cutoff_date = datetime.now() - timedelta(days=30)
        query = query.filter(Forecast.created_at < cutoff_date)
    
    deleted_count = query.count()
    query.delete()
    db.commit()
    
    return {"message": f"Deleted {deleted_count} old forecasts"}

def _calculate_trend(forecasts: List[Forecast]) -> str:
    """Calculate overall trend from forecasts"""
    if len(forecasts) < 2:
        return "insufficient_data"
    
    first_balance = forecasts[0].predicted_cash_balance
    last_balance = forecasts[-1].predicted_cash_balance
    
    change_percent = ((last_balance - first_balance) / abs(first_balance)) * 100
    
    if change_percent > 10:
        return "positive"
    elif change_percent < -10:
        return "negative"
    else:
        return "stable"
