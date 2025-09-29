from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session
import warnings
warnings.filterwarnings('ignore')

# Try to import data science packages
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
    DataFrame = Any
except ImportError:
    PANDAS_AVAILABLE = False
    DataFrame = Any  # Fallback type
    print("Pandas not available, using basic forecasting methods")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("NumPy not available, using basic math operations")

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    LinearRegression = None
    StandardScaler = None
    SKLEARN_AVAILABLE = False
    print("scikit-learn not available, using simple linear forecasting")

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    Prophet = None
    PROPHET_AVAILABLE = False
    print("Prophet not available, using fallback forecasting methods")

from ..models.database import Transaction, Forecast

class ForecastingService:
    def __init__(self, db: Session):
        self.db = db
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
    
    async def generate_forecast(
        self,
        days_ahead: int = 90,
        model_type: str = "prophet",
        include_confidence_intervals: bool = True
    ) -> List[Forecast]:
        """Generate cash flow forecast using specified ML model"""
        
        # Get historical transaction data
        transactions = self._get_historical_data()
        
        if len(transactions) < 10:
            # Not enough data for ML, use simple projection
            return await self._generate_simple_forecast(days_ahead)
        
        # Prepare data for forecasting
        df = self._prepare_data_for_forecasting(transactions)
        
        if model_type == "prophet" and PROPHET_AVAILABLE:
            forecasts = self._forecast_with_prophet(df, days_ahead, include_confidence_intervals)
        elif model_type == "linear":
            forecasts = self._forecast_with_linear_regression(df, days_ahead, include_confidence_intervals)
        else:
            # Fallback to ARIMA-like approach
            forecasts = self._forecast_with_arima_like(df, days_ahead, include_confidence_intervals)
        
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
                model_version=model_type,
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
        
        # Get base forecast
        base_forecasts = await self.generate_forecast(days_ahead, "prophet")
        
        # Apply scenario modifications
        scenario_forecasts = []
        current_balance = self._get_current_cash_balance()
        
        for i, base_forecast in enumerate(base_forecasts):
            # Modify income and expenses based on scenario parameters
            modified_income = (base_forecast.predicted_income or 0) * (1 + revenue_change_percent / 100)
            modified_expenses = (base_forecast.predicted_expenses or 0) * (1 + expense_change_percent / 100)
            
            # Apply one-time adjustments on first day
            if i == 0:
                modified_income += one_time_income
                modified_expenses += one_time_expense
            
            # Calculate new cash balance
            if i == 0:
                new_balance = current_balance + modified_income - modified_expenses
            else:
                new_balance = scenario_forecasts[i-1].predicted_cash_balance + modified_income - modified_expenses
            
            scenario_forecast = Forecast(
                date=base_forecast.date,
                predicted_cash_balance=new_balance,
                predicted_income=modified_income,
                predicted_expenses=modified_expenses,
                confidence_interval_lower=base_forecast.confidence_interval_lower,
                confidence_interval_upper=base_forecast.confidence_interval_upper,
                model_version="scenario",
                scenario_params=f"rev:{revenue_change_percent}%,exp:{expense_change_percent}%"
            )
            
            scenario_forecasts.append(scenario_forecast)
        
        return scenario_forecasts
    
    def _get_historical_data(self) -> List[Transaction]:
        """Get historical transaction data for forecasting"""
        cutoff_date = datetime.now() - timedelta(days=365)  # Last year of data
        
        transactions = self.db.query(Transaction).filter(
            Transaction.date >= cutoff_date
        ).order_by(Transaction.date.asc()).all()
        
        return transactions
    
    def _prepare_data_for_forecasting(self, transactions: List[Transaction]):
        """Prepare transaction data for ML forecasting"""
        # Convert to DataFrame
        data = []
        for t in transactions:
            data.append({
                'date': t.date,
                'amount': t.amount,
                'type': t.type,
                'category': t.category or 'Other'
            })
        
        df = Any(data)
        df['date'] = pd.to_datetime(df['date'])
        
        # Aggregate by day
        daily_data = df.groupby([df['date'].dt.date, 'type'])['amount'].sum().unstack(fill_value=0)
        daily_data = daily_data.reset_index()
        daily_data['date'] = pd.to_datetime(daily_data['date'])
        
        # Ensure we have both income and expense columns
        if 'income' not in daily_data.columns:
            daily_data['income'] = 0
        if 'expense' not in daily_data.columns:
            daily_data['expense'] = 0
        
        # Calculate daily net cash flow and cumulative balance
        daily_data['net_flow'] = daily_data['income'] + daily_data['expense']  # expense is already negative
        daily_data['cumulative_balance'] = daily_data['net_flow'].cumsum()
        
        # Add current cash balance to cumulative
        current_balance = self._get_current_cash_balance()
        daily_data['cumulative_balance'] += current_balance
        
        return daily_data
    
    def _forecast_with_prophet(self, df: Any, days_ahead: int, include_confidence_intervals: bool) -> List[Dict[str, Any]]:
        """Use Prophet for time series forecasting"""
        if not PROPHET_AVAILABLE:
            return self._forecast_with_linear_regression(df, days_ahead, include_confidence_intervals)
        
        # Prepare data for Prophet
        prophet_df = df[['date', 'cumulative_balance']].copy()
        prophet_df.columns = ['ds', 'y']
        
        # Create and fit Prophet model
        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=True,
            interval_width=0.8 if include_confidence_intervals else 0
        )
        
        model.fit(prophet_df)
        
        # Create future dataframe
        future = model.make_future_dataframe(periods=days_ahead)
        forecast = model.predict(future)
        
        # Extract forecast data
        forecasts = []
        for i in range(len(prophet_df), len(forecast)):
            row = forecast.iloc[i]
            forecast_data = {
                "date": row['ds'].to_pydatetime(),
                "predicted_cash_balance": float(row['yhat']),
                "predicted_income": None,  # Prophet doesn't separate income/expenses
                "predicted_expenses": None,
            }
            
            if include_confidence_intervals:
                forecast_data["confidence_interval_lower"] = float(row['yhat_lower'])
                forecast_data["confidence_interval_upper"] = float(row['yhat_upper'])
            
            forecasts.append(forecast_data)
        
        return forecasts
    
    def _forecast_with_linear_regression(self, df: Any, days_ahead: int, include_confidence_intervals: bool) -> List[Dict[str, Any]]:
        """Use linear regression for forecasting"""
        # Prepare features (days since start)
        df['days_since_start'] = (df['date'] - df['date'].min()).dt.days
        
        X = df[['days_since_start']].values
        y = df['cumulative_balance'].values
        
        # Train model
        model = LinearRegression()
        model.fit(X, y)
        
        # Generate future predictions
        last_day = df['days_since_start'].max()
        future_days = np.arange(last_day + 1, last_day + 1 + days_ahead).reshape(-1, 1)
        predictions = model.predict(future_days)
        
        # Calculate confidence intervals (simple approximation)
        if include_confidence_intervals:
            residuals = y - model.predict(X)
            std_error = np.std(residuals)
            confidence_margin = 1.96 * std_error  # 95% confidence interval
        
        forecasts = []
        for i, pred in enumerate(predictions):
            forecast_date = df['date'].max() + timedelta(days=i+1)
            forecast_data = {
                "date": forecast_date,
                "predicted_cash_balance": float(pred),
                "predicted_income": None,
                "predicted_expenses": None,
            }
            
            if include_confidence_intervals:
                forecast_data["confidence_interval_lower"] = float(pred - confidence_margin)
                forecast_data["confidence_interval_upper"] = float(pred + confidence_margin)
            
            forecasts.append(forecast_data)
        
        return forecasts
    
    def _forecast_with_arima_like(self, df: Any, days_ahead: int, include_confidence_intervals: bool) -> List[Dict[str, Any]]:
        """Simple ARIMA-like forecasting using moving averages"""
        # Calculate moving averages
        window = min(30, len(df) // 2)  # 30-day or half the data, whichever is smaller
        df['ma_income'] = df['income'].rolling(window=window, min_periods=1).mean()
        df['ma_expense'] = df['expense'].rolling(window=window, min_periods=1).mean()
        df['ma_net_flow'] = df['net_flow'].rolling(window=window, min_periods=1).mean()
        
        # Get recent trends
        recent_avg_income = df['ma_income'].iloc[-window:].mean()
        recent_avg_expense = df['ma_expense'].iloc[-window:].mean()
        recent_avg_net_flow = df['ma_net_flow'].iloc[-window:].mean()
        
        # Calculate volatility for confidence intervals
        if include_confidence_intervals:
            income_std = df['income'].std()
            expense_std = df['expense'].std()
            net_flow_std = df['net_flow'].std()
        
        forecasts = []
        current_balance = df['cumulative_balance'].iloc[-1]
        
        for i in range(days_ahead):
            forecast_date = df['date'].max() + timedelta(days=i+1)
            
            # Project future cash flow with slight randomness
            projected_income = recent_avg_income * (1 + np.random.normal(0, 0.1))
            projected_expense = recent_avg_expense * (1 + np.random.normal(0, 0.1))
            projected_net_flow = recent_avg_net_flow
            
            current_balance += projected_net_flow
            
            forecast_data = {
                "date": forecast_date,
                "predicted_cash_balance": float(current_balance),
                "predicted_income": float(max(0, projected_income)),
                "predicted_expenses": float(abs(min(0, projected_expense))),
            }
            
            if include_confidence_intervals:
                margin = 1.96 * net_flow_std * np.sqrt(i + 1)  # Increasing uncertainty over time
                forecast_data["confidence_interval_lower"] = float(current_balance - margin)
                forecast_data["confidence_interval_upper"] = float(current_balance + margin)
            
            forecasts.append(forecast_data)
        
        return forecasts
    
    async def _generate_simple_forecast(self, days_ahead: int) -> List[Forecast]:
        """Generate simple forecast when insufficient historical data"""
        current_balance = self._get_current_cash_balance()
        
        # Use basic assumptions
        avg_daily_income = 1000  # Default assumption
        avg_daily_expense = 800   # Default assumption
        net_daily_flow = avg_daily_income - avg_daily_expense
        
        forecasts = []
        balance = current_balance
        
        for i in range(days_ahead):
            forecast_date = datetime.now() + timedelta(days=i+1)
            balance += net_daily_flow
            
            forecast = Forecast(
                date=forecast_date,
                predicted_cash_balance=balance,
                predicted_income=avg_daily_income,
                predicted_expenses=avg_daily_expense,
                model_version="simple",
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
