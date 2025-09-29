from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from ..models.database import get_db
from ..services.forecasting_service import ForecastingService

router = APIRouter()

class SimulationParameters(BaseModel):
    revenue_change_percent: float = Field(0, ge=-100, le=500, description="Revenue change percentage")
    expense_change_percent: float = Field(0, ge=-100, le=500, description="Expense change percentage")
    one_time_income: Optional[float] = Field(0, description="One-time income injection")
    one_time_expense: Optional[float] = Field(0, description="One-time expense")
    days_ahead: int = Field(90, ge=1, le=365, description="Days to forecast ahead")
    scenario_name: Optional[str] = Field("Custom Scenario", description="Name for this scenario")

class SimulationResult(BaseModel):
    scenario_name: str
    parameters: SimulationParameters
    forecasts: List[Dict[str, Any]]
    summary: Dict[str, Any]
    comparison_with_baseline: Dict[str, Any]

@router.post("/simulate", response_model=SimulationResult)
async def run_simulation(
    params: SimulationParameters,
    db: Session = Depends(get_db)
):
    """Run cash flow simulation with custom parameters"""
    try:
        forecasting_service = ForecastingService(db)
        
        # Generate baseline forecast
        baseline_forecasts = await forecasting_service.generate_forecast(
            days_ahead=params.days_ahead,
            model_type="prophet"
        )
        
        # Generate scenario forecast with modifications
        scenario_forecasts = await forecasting_service.generate_scenario_forecast(
            days_ahead=params.days_ahead,
            revenue_change_percent=params.revenue_change_percent,
            expense_change_percent=params.expense_change_percent,
            one_time_income=params.one_time_income,
            one_time_expense=params.one_time_expense
        )
        
        # Calculate summary statistics
        scenario_summary = _calculate_scenario_summary(scenario_forecasts)
        baseline_summary = _calculate_scenario_summary(baseline_forecasts)
        
        # Compare with baseline
        comparison = _compare_scenarios(baseline_summary, scenario_summary)
        
        return SimulationResult(
            scenario_name=params.scenario_name,
            parameters=params,
            forecasts=[
                {
                    "date": f.date.isoformat(),
                    "predicted_cash_balance": f.predicted_cash_balance,
                    "predicted_income": f.predicted_income,
                    "predicted_expenses": f.predicted_expenses,
                    "confidence_interval_lower": f.confidence_interval_lower,
                    "confidence_interval_upper": f.confidence_interval_upper
                } for f in scenario_forecasts
            ],
            summary=scenario_summary,
            comparison_with_baseline=comparison
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

@router.post("/simulate/batch")
async def run_batch_simulation(
    scenarios: List[SimulationParameters],
    db: Session = Depends(get_db)
):
    """Run multiple simulation scenarios"""
    if len(scenarios) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 scenarios allowed per batch")
    
    results = []
    
    for scenario in scenarios:
        try:
            result = await run_simulation(scenario, db)
            results.append(result)
        except Exception as e:
            results.append({
                "scenario_name": scenario.scenario_name,
                "error": str(e),
                "parameters": scenario.dict()
            })
    
    return {"results": results, "total_scenarios": len(scenarios)}

@router.get("/simulate/presets")
async def get_simulation_presets():
    """Get predefined simulation scenarios"""
    return {
        "presets": [
            {
                "name": "Optimistic Growth",
                "description": "15% revenue increase, 5% expense increase",
                "parameters": {
                    "revenue_change_percent": 15,
                    "expense_change_percent": 5,
                    "scenario_name": "Optimistic Growth"
                }
            },
            {
                "name": "Conservative Growth",
                "description": "5% revenue increase, 3% expense increase",
                "parameters": {
                    "revenue_change_percent": 5,
                    "expense_change_percent": 3,
                    "scenario_name": "Conservative Growth"
                }
            },
            {
                "name": "Economic Downturn",
                "description": "20% revenue decrease, 10% expense decrease",
                "parameters": {
                    "revenue_change_percent": -20,
                    "expense_change_percent": -10,
                    "scenario_name": "Economic Downturn"
                }
            },
            {
                "name": "Cost Optimization",
                "description": "Same revenue, 15% expense reduction",
                "parameters": {
                    "revenue_change_percent": 0,
                    "expense_change_percent": -15,
                    "scenario_name": "Cost Optimization"
                }
            },
            {
                "name": "Major Investment",
                "description": "Large one-time expense with gradual revenue increase",
                "parameters": {
                    "revenue_change_percent": 10,
                    "expense_change_percent": 5,
                    "one_time_expense": 50000,
                    "scenario_name": "Major Investment"
                }
            }
        ]
    }

def _calculate_scenario_summary(forecasts) -> Dict[str, Any]:
    """Calculate summary statistics for a scenario"""
    if not forecasts:
        return {}
    
    total_predicted_income = sum(f.predicted_income or 0 for f in forecasts)
    total_predicted_expenses = sum(f.predicted_expenses or 0 for f in forecasts)
    final_cash_balance = forecasts[-1].predicted_cash_balance
    initial_cash_balance = forecasts[0].predicted_cash_balance
    
    cash_runway_days = _calculate_cash_runway(forecasts)
    
    return {
        "total_predicted_income": total_predicted_income,
        "total_predicted_expenses": total_predicted_expenses,
        "net_cash_flow": total_predicted_income - total_predicted_expenses,
        "final_cash_balance": final_cash_balance,
        "initial_cash_balance": initial_cash_balance,
        "cash_change": final_cash_balance - initial_cash_balance,
        "cash_runway_days": cash_runway_days,
        "period_days": len(forecasts)
    }

def _compare_scenarios(baseline: Dict[str, Any], scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Compare scenario results with baseline"""
    if not baseline or not scenario:
        return {}
    
    return {
        "cash_flow_difference": scenario["net_cash_flow"] - baseline["net_cash_flow"],
        "final_balance_difference": scenario["final_cash_balance"] - baseline["final_cash_balance"],
        "runway_difference_days": scenario["cash_runway_days"] - baseline["cash_runway_days"],
        "improvement_percentage": (
            (scenario["final_cash_balance"] - baseline["final_cash_balance"]) / 
            abs(baseline["final_cash_balance"]) * 100
            if baseline["final_cash_balance"] != 0 else 0
        )
    }

def _calculate_cash_runway(forecasts) -> int:
    """Calculate how many days until cash runs out"""
    for i, forecast in enumerate(forecasts):
        if forecast.predicted_cash_balance <= 0:
            return i
    return len(forecasts)  # Cash doesn't run out in forecast period
