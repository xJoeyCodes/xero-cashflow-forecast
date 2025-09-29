from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Import only the database models
from app.models.database import engine, Base, get_db, Transaction, Forecast, User

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Cash Flow Forecasting API - Simple Version",
    description="A fintech solution for SMEs with Xero integration (Simplified for Windows)",
    version="1.0.0-simple",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Cash Flow Forecasting API - Simple Version", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "simple"}

# Simple authentication endpoint (no JWT, just for demo)
@app.post("/auth/login")
async def login(db: Session = Depends(get_db)):
    # For demo purposes, always return success
    return {
        "access_token": "demo-token-12345",
        "token_type": "bearer",
        "message": "Demo login successful"
    }

@app.post("/auth/register")
async def register(db: Session = Depends(get_db)):
    return {"message": "Demo registration successful"}

@app.get("/auth/me")
async def get_me():
    return {
        "id": 1,
        "email": "demo@example.com",
        "is_active": True
    }

# Simple transactions endpoint
@app.get("/api/transactions")
async def get_transactions(db: Session = Depends(get_db)):
    transactions = db.query(Transaction).order_by(Transaction.date.desc()).limit(100).all()
    
    # Convert to simple dict format
    result = []
    for t in transactions:
        result.append({
            "id": t.id,
            "date": t.date.isoformat(),
            "description": t.description,
            "amount": t.amount,
            "type": t.type,
            "category": t.category,
            "account_name": t.account_name,
            "contact_name": t.contact_name,
            "created_at": t.created_at.isoformat()
        })
    
    return result

@app.post("/api/transactions")
async def create_transaction(db: Session = Depends(get_db)):
    # Create a sample transaction for demo
    from datetime import datetime
    
    transaction = Transaction(
        date=datetime.now(),
        description="Demo Transaction",
        amount=1000.0,
        type="income",
        category="Demo",
        account_name="Demo Account"
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return {
        "id": transaction.id,
        "message": "Transaction created successfully"
    }

@app.get("/api/transactions/summary")
async def get_transactions_summary(db: Session = Depends(get_db)):
    transactions = db.query(Transaction).all()
    
    total_income = sum(t.amount for t in transactions if t.amount > 0)
    total_expenses = sum(abs(t.amount) for t in transactions if t.amount < 0)
    
    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_cash_flow": total_income - total_expenses,
        "transaction_count": len(transactions)
    }

@app.post("/api/transactions/sync-xero")
async def sync_xero():
    return {"message": "Xero sync simulated - 5 transactions synced"}

# Simple forecast endpoint
@app.post("/api/forecast")
async def generate_forecast(db: Session = Depends(get_db)):
    from datetime import datetime, timedelta
    
    # Generate simple demo forecasts
    forecasts = []
    current_balance = 50000  # Starting balance
    
    for i in range(90):  # 90 days
        forecast_date = datetime.now() + timedelta(days=i+1)
        
        # Simple projection
        daily_income = 800 + (i % 10) * 50  # Varying income
        daily_expense = 600 + (i % 7) * 30   # Varying expenses
        current_balance += daily_income - daily_expense
        
        forecast = Forecast(
            date=forecast_date,
            predicted_cash_balance=current_balance,
            predicted_income=daily_income,
            predicted_expenses=daily_expense,
            model_version="simple"
        )
        
        db.add(forecast)
        forecasts.append(forecast)
    
    db.commit()
    
    # Return simplified format
    result = []
    for f in forecasts:
        result.append({
            "id": f.id,
            "date": f.date.isoformat(),
            "predicted_cash_balance": f.predicted_cash_balance,
            "predicted_income": f.predicted_income,
            "predicted_expenses": f.predicted_expenses
        })
    
    return result

@app.get("/api/forecast/latest")
async def get_latest_forecast(db: Session = Depends(get_db)):
    from datetime import datetime, timedelta
    
    # Get existing forecasts or generate new ones
    forecasts = db.query(Forecast).filter(
        Forecast.date >= datetime.now()
    ).order_by(Forecast.date.asc()).limit(30).all()
    
    if not forecasts:
        # Generate some if none exist
        await generate_forecast(db)
        forecasts = db.query(Forecast).filter(
            Forecast.date >= datetime.now()
        ).order_by(Forecast.date.asc()).limit(30).all()
    
    result = []
    for f in forecasts:
        result.append({
            "date": f.date.isoformat(),
            "predicted_cash_balance": f.predicted_cash_balance,
            "predicted_income": f.predicted_income or 0,
            "predicted_expenses": f.predicted_expenses or 0
        })
    
    return {
        "forecasts": result,
        "summary": {
            "total_forecasts": len(result),
            "cash_flow_trend": "positive" if result and result[-1]["predicted_cash_balance"] > result[0]["predicted_cash_balance"] else "stable"
        }
    }

# Simple simulation endpoint
@app.post("/api/simulate")
async def run_simulation():
    from datetime import datetime, timedelta
    
    # Generate sample simulation results
    forecasts = []
    current_balance = 50000
    
    for i in range(90):
        forecast_date = datetime.now() + timedelta(days=i+1)
        
        # Simulate scenario with 10% revenue increase
        daily_income = (800 + (i % 10) * 50) * 1.1
        daily_expense = 600 + (i % 7) * 30
        current_balance += daily_income - daily_expense
        
        forecasts.append({
            "date": forecast_date.isoformat(),
            "predicted_cash_balance": current_balance,
            "predicted_income": daily_income,
            "predicted_expenses": daily_expense
        })
    
    return {
        "scenario_name": "Revenue Growth Scenario",
        "forecasts": forecasts,
        "summary": {
            "final_cash_balance": current_balance,
            "net_cash_flow": current_balance - 50000,
            "cash_runway_days": 90
        },
        "comparison_with_baseline": {
            "improvement_percentage": 10.0
        }
    }

@app.get("/api/simulate/presets")
async def get_simulation_presets():
    return {
        "presets": [
            {
                "name": "Revenue Growth",
                "description": "10% revenue increase",
                "parameters": {
                    "revenue_change_percent": 10,
                    "expense_change_percent": 0
                }
            },
            {
                "name": "Cost Reduction",
                "description": "15% expense reduction",
                "parameters": {
                    "revenue_change_percent": 0,
                    "expense_change_percent": -15
                }
            }
        ]
    }

# Add some sample data on startup
@app.on_event("startup")
async def create_sample_data():
    from datetime import datetime, timedelta
    
    db = next(get_db())
    
    # Check if we already have data
    existing_transactions = db.query(Transaction).count()
    
    if existing_transactions == 0:
        # Create sample transactions
        sample_transactions = [
            Transaction(
                date=datetime.now() - timedelta(days=30),
                description="Initial Investment",
                amount=100000,
                type="income",
                category="Investment"
            ),
            Transaction(
                date=datetime.now() - timedelta(days=25),
                description="Office Rent",
                amount=-2000,
                type="expense",
                category="Rent"
            ),
            Transaction(
                date=datetime.now() - timedelta(days=20),
                description="Client Payment",
                amount=5000,
                type="income",
                category="Revenue"
            ),
            Transaction(
                date=datetime.now() - timedelta(days=15),
                description="Marketing Campaign",
                amount=-1500,
                type="expense",
                category="Marketing"
            ),
            Transaction(
                date=datetime.now() - timedelta(days=10),
                description="Consulting Revenue",
                amount=3500,
                type="income",
                category="Revenue"
            )
        ]
        
        for transaction in sample_transactions:
            db.add(transaction)
        
        db.commit()
        print("Sample data created!")
    
    db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
