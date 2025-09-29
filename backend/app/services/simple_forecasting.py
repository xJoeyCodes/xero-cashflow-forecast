"""
Simple forecasting service that works without pandas/numpy/sklearn
This provides basic cash flow forecasting using simple mathematical operations
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models.database import Transaction, Forecast

class SimpleForecastingService:
    def __init__(self, db: Session):
        self.db = db
    
    async def generate_forecast(
        self,
        days_ahead: int = 90,
        model_type: str = "simple",
        include_confidence_intervals: bool = True
    ) -> List[Forecast]:
        """Generate cash flow forecast using simple mathematical methods"""
        
        # Get historical transaction data
        transactions = self._get_historical_data()
        
        if len(transactions) < 5:
            # Not enough data, use default projections
            return await self._generate_default_forecast(days_ahead)
        
        # Calculate basic statistics
        stats = self._calculate_transaction_stats(transactions)
        
        # Generate forecasts
        forecasts = self._generate_simple_forecast(stats, days_ahead, include_confidence_intervals)
        
        # Save forecasts to database
        forecast_objects = []
        for forecast_data in forecasts:
            forecast = Forecast(
                date=forecast_data["date"],
                predicted_cash_balance=forecast_data["predicted_cash_balance"],
                predicted_income=forecast_data.get("predicted_income"),
                predicted_expenses=forecast_data.get("predicted_expenses"),
                confidence_interval_lower=forecast_data.get("confidence_interval_lower"),
                confidence_interval_upper=forecast_data.get("confidence_interval_upper"),
                model_version="simple",
                scenario_params=None
            )
            self.db.add(forecast)
            forecast_objects.append(forecast)
        
        self.db.commit()
        return forecast_objects
    
    async def generate_scenario_forecast(
        self,
        days_ahead: int = 90,
        revenue_change_percent: float = 0,
        expense_change_percent: float = 0,
        one_time_income: float = 0,
        one_time_expense: float = 0
    ) -> List[Forecast]:
        """Generate scenario-based forecast with parameter modifications"""
        
        # Get base statistics
        transactions = self._get_historical_data()
        stats = self._calculate_transaction_stats(transactions)
        
        # Apply scenario modifications
        modified_stats = {
            "avg_daily_income": stats["avg_daily_income"] * (1 + revenue_change_percent / 100),
            "avg_daily_expense": stats["avg_daily_expense"] * (1 + expense_change_percent / 100),
            "income_volatility": stats["income_volatility"],
            "expense_volatility": stats["expense_volatility"]
        }
        
        # Generate forecasts with modifications
        forecasts = self._generate_simple_forecast(modified_stats, days_ahead, True)
        
        # Apply one-time adjustments to first day
        if forecasts and (one_time_income != 0 or one_time_expense != 0):
            forecasts[0]["predicted_income"] += one_time_income
            forecasts[0]["predicted_expenses"] += one_time_expense
            
            # Recalculate cash balances
            current_balance = self._get_current_cash_balance()
            for i, forecast in enumerate(forecasts):
                if i == 0:
                    current_balance += forecast["predicted_income"] - forecast["predicted_expenses"]
                else:
                    current_balance += forecast["predicted_income"] - forecast["predicted_expenses"]
                forecast["predicted_cash_balance"] = current_balance
        
        # Convert to Forecast objects
        scenario_forecasts = []
        for forecast_data in forecasts:
            forecast = Forecast(
                date=forecast_data["date"],
                predicted_cash_balance=forecast_data["predicted_cash_balance"],
                predicted_income=forecast_data["predicted_income"],
                predicted_expenses=forecast_data["predicted_expenses"],
                confidence_interval_lower=forecast_data.get("confidence_interval_lower"),
                confidence_interval_upper=forecast_data.get("confidence_interval_upper"),
                model_version="simple_scenario",
                scenario_params=f"rev:{revenue_change_percent}%,exp:{expense_change_percent}%"
            )
            scenario_forecasts.append(forecast)
        
        return scenario_forecasts
    
    def _get_historical_data(self) -> List[Transaction]:
        """Get historical transaction data for forecasting"""
        cutoff_date = datetime.now() - timedelta(days=365)  # Last year of data
        
        transactions = self.db.query(Transaction).filter(
            Transaction.date >= cutoff_date
        ).order_by(Transaction.date.asc()).all()
        
        return transactions
    
    def _calculate_transaction_stats(self, transactions: List[Transaction]) -> Dict[str, float]:
        """Calculate basic statistics from transactions"""
        if not transactions:
            return {
                "avg_daily_income": 500.0,
                "avg_daily_expense": 400.0,
                "income_volatility": 100.0,
                "expense_volatility": 80.0
            }
        
        # Separate income and expenses
        incomes = [t.amount for t in transactions if t.amount > 0]
        expenses = [abs(t.amount) for t in transactions if t.amount < 0]
        
        # Calculate averages
        total_days = (transactions[-1].date - transactions[0].date).days or 1
        
        avg_daily_income = sum(incomes) / total_days if incomes else 0
        avg_daily_expense = sum(expenses) / total_days if expenses else 0
        
        # Calculate simple volatility (standard deviation approximation)
        income_volatility = self._calculate_volatility(incomes) if len(incomes) > 1 else avg_daily_income * 0.2
        expense_volatility = self._calculate_volatility(expenses) if len(expenses) > 1 else avg_daily_expense * 0.2
        
        return {
            "avg_daily_income": avg_daily_income,
            "avg_daily_expense": avg_daily_expense,
            "income_volatility": income_volatility,
            "expense_volatility": expense_volatility
        }
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate simple volatility (standard deviation approximation)"""
        if len(values) < 2:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _generate_simple_forecast(
        self, 
        stats: Dict[str, float], 
        days_ahead: int, 
        include_confidence_intervals: bool
    ) -> List[Dict[str, Any]]:
        """Generate simple forecast using basic projections"""
        
        forecasts = []
        current_balance = self._get_current_cash_balance()
        
        for i in range(days_ahead):
            forecast_date = datetime.now() + timedelta(days=i+1)
            
            # Add some randomness to make it more realistic (simple pseudo-random)
            day_factor = (i % 7) / 10  # Weekly pattern
            random_factor = ((i * 17) % 100) / 1000  # Simple pseudo-random
            
            # Project daily income and expenses with some variation
            daily_income = stats["avg_daily_income"] * (1 + day_factor + random_factor)
            daily_expense = stats["avg_daily_expense"] * (1 + day_factor - random_factor)
            
            # Ensure positive values
            daily_income = max(0, daily_income)
            daily_expense = max(0, daily_expense)
            
            # Update balance
            current_balance += daily_income - daily_expense
            
            forecast_data = {
                "date": forecast_date,
                "predicted_cash_balance": current_balance,
                "predicted_income": daily_income,
                "predicted_expenses": daily_expense,
            }
            
            # Add confidence intervals if requested
            if include_confidence_intervals:
                # Simple confidence intervals based on volatility
                income_margin = stats["income_volatility"] * 1.96  # ~95% confidence
                expense_margin = stats["expense_volatility"] * 1.96
                
                lower_bound = current_balance - income_margin - expense_margin
                upper_bound = current_balance + income_margin + expense_margin
                
                forecast_data["confidence_interval_lower"] = lower_bound
                forecast_data["confidence_interval_upper"] = upper_bound
            
            forecasts.append(forecast_data)
        
        return forecasts
    
    async def _generate_default_forecast(self, days_ahead: int) -> List[Forecast]:
        """Generate default forecast when insufficient historical data"""
        current_balance = self._get_current_cash_balance()
        
        # Default assumptions
        avg_daily_income = 800
        avg_daily_expense = 600
        
        forecasts = []
        balance = current_balance
        
        for i in range(days_ahead):
            forecast_date = datetime.now() + timedelta(days=i+1)
            
            # Add some variation
            daily_income = avg_daily_income * (1 + (i % 5) * 0.1)
            daily_expense = avg_daily_expense * (1 + (i % 3) * 0.1)
            
            balance += daily_income - daily_expense
            
            forecast = Forecast(
                date=forecast_date,
                predicted_cash_balance=balance,
                predicted_income=daily_income,
                predicted_expenses=daily_expense,
                model_version="default",
                scenario_params=None
            )
            
            self.db.add(forecast)
            forecasts.append(forecast)
        
        self.db.commit()
        return forecasts
    
    def _get_current_cash_balance(self) -> float:
        """Calculate current cash balance from transactions"""
        transactions = self.db.query(Transaction).all()
        
        if not transactions:
            return 50000.0  # Default starting balance
        
        total_balance = sum(t.amount for t in transactions)
        return total_balance
