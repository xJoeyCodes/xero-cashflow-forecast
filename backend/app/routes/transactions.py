from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel

from ..models.database import get_db, Transaction
from ..services.xero_service import XeroService

router = APIRouter()

class TransactionCreate(BaseModel):
    date: datetime
    description: str
    amount: float
    category: Optional[str] = None
    type: str  # 'income' or 'expense'
    account_name: Optional[str] = None
    contact_name: Optional[str] = None

class TransactionResponse(BaseModel):
    id: int
    xero_id: Optional[str]
    date: datetime
    description: str
    amount: float
    category: Optional[str]
    type: str
    account_name: Optional[str]
    contact_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    transaction_type: Optional[str] = Query(None, regex="^(income|expense)$"),
    db: Session = Depends(get_db)
):
    """Get transactions with optional filtering"""
    query = db.query(Transaction)
    
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    if transaction_type:
        query = query.filter(Transaction.type == transaction_type)
    
    transactions = query.order_by(Transaction.date.desc()).offset(skip).limit(limit).all()
    return transactions

@router.post("/transactions", response_model=TransactionResponse)
async def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):
    """Create a new transaction"""
    db_transaction = Transaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific transaction"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@router.delete("/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    """Delete a transaction"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    db.delete(transaction)
    db.commit()
    return {"message": "Transaction deleted successfully"}

@router.post("/transactions/sync-xero")
async def sync_xero_transactions(
    db: Session = Depends(get_db)
):
    """Sync transactions from Xero API"""
    try:
        xero_service = XeroService()
        synced_count = await xero_service.sync_transactions(db)
        return {"message": f"Successfully synced {synced_count} transactions from Xero"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync with Xero: {str(e)}")

@router.get("/transactions/summary")
async def get_transactions_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get transaction summary statistics"""
    query = db.query(Transaction)
    
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    
    transactions = query.all()
    
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expenses = sum(abs(t.amount) for t in transactions if t.type == 'expense')
    net_cash_flow = total_income - total_expenses
    
    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_cash_flow": net_cash_flow,
        "transaction_count": len(transactions),
        "period": {
            "start_date": start_date,
            "end_date": end_date
        }
    }
