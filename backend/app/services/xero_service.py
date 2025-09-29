import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import httpx

# Optional Xero imports - gracefully handle if not available
try:
    from xero_python.api_client import ApiClient
    from xero_python.accounting import AccountingApi
    XERO_AVAILABLE = True
except ImportError:
    ApiClient = None
    AccountingApi = None
    XERO_AVAILABLE = False

from ..models.database import Transaction, User

class XeroService:
    def __init__(self):
        self.client_id = os.getenv("XERO_CLIENT_ID")
        self.client_secret = os.getenv("XERO_CLIENT_SECRET")
        self.redirect_uri = os.getenv("XERO_REDIRECT_URI", "http://localhost:8000/auth/xero/callback")
        
        # Only require credentials if Xero integration is being used
        if not XERO_AVAILABLE:
            print("Warning: Xero Python SDK not available. Using demo mode only.")
        elif not self.client_id or not self.client_secret:
            print("Warning: Xero credentials not configured. Using demo mode only.")
    
    def get_authorization_url(self) -> str:
        """Get Xero OAuth2 authorization URL"""
        scopes = ["accounting.transactions", "accounting.contacts", "accounting.settings"]
        
        # In a real implementation, you'd use the xero-python SDK
        # For demo purposes, we'll construct the URL manually
        auth_url = (
            f"https://login.xero.com/identity/connect/authorize"
            f"?response_type=code"
            f"&client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&scope={' '.join(scopes)}"
            f"&state=demo_state"
        )
        
        return auth_url
    
    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access tokens"""
        # In a real implementation, you'd use the xero-python SDK
        # This is a simplified version for demonstration
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://identity.xero.com/connect/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                raise Exception(f"Token exchange failed: {response.text}")
            
            tokens = response.json()
            
            # Get tenant information
            tenant_response = await client.get(
                "https://api.xero.com/connections",
                headers={"Authorization": f"Bearer {tokens['access_token']}"}
            )
            
            if tenant_response.status_code == 200:
                tenants = tenant_response.json()
                if tenants:
                    tokens["tenant_id"] = tenants[0]["tenantId"]
            
            return tokens
    
    async def sync_transactions(self, db: Session, user: Optional[User] = None) -> int:
        """Sync transactions from Xero API"""
        if not user or not user.xero_access_token:
            # For demo purposes, create sample transactions
            return await self._create_sample_transactions(db)
        
        try:
            # In a real implementation, you'd use the xero-python SDK to fetch transactions
            # This is simplified for demonstration
            
            synced_count = 0
            
            # Sample data that would come from Xero API
            sample_xero_transactions = [
                {
                    "TransactionID": "xero_001",
                    "Date": datetime.now() - timedelta(days=30),
                    "Description": "Sales Revenue - Client A",
                    "Total": 5000.00,
                    "Type": "RECEIVE",
                    "Contact": {"Name": "Client A"},
                    "Account": {"Name": "Revenue"}
                },
                {
                    "TransactionID": "xero_002", 
                    "Date": datetime.now() - timedelta(days=25),
                    "Description": "Office Rent",
                    "Total": -2000.00,
                    "Type": "SPEND",
                    "Contact": {"Name": "Property Management Co"},
                    "Account": {"Name": "Rent Expense"}
                },
                {
                    "TransactionID": "xero_003",
                    "Date": datetime.now() - timedelta(days=20),
                    "Description": "Consulting Services - Client B",
                    "Total": 3500.00,
                    "Type": "RECEIVE",
                    "Contact": {"Name": "Client B"},
                    "Account": {"Name": "Revenue"}
                }
            ]
            
            for xero_transaction in sample_xero_transactions:
                # Check if transaction already exists
                existing = db.query(Transaction).filter(
                    Transaction.xero_id == xero_transaction["TransactionID"]
                ).first()
                
                if not existing:
                    transaction = Transaction(
                        xero_id=xero_transaction["TransactionID"],
                        date=xero_transaction["Date"],
                        description=xero_transaction["Description"],
                        amount=xero_transaction["Total"],
                        type="income" if xero_transaction["Total"] > 0 else "expense",
                        contact_name=xero_transaction.get("Contact", {}).get("Name"),
                        account_name=xero_transaction.get("Account", {}).get("Name"),
                        category=self._categorize_transaction(xero_transaction["Description"])
                    )
                    
                    db.add(transaction)
                    synced_count += 1
            
            db.commit()
            
            # Update user's last sync time
            if user:
                user.last_sync_at = datetime.utcnow()
                db.commit()
            
            return synced_count
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to sync transactions: {str(e)}")
    
    async def _create_sample_transactions(self, db: Session) -> int:
        """Create sample transactions for demonstration"""
        sample_transactions = [
            {
                "date": datetime.now() - timedelta(days=60),
                "description": "Initial Capital Investment",
                "amount": 100000.00,
                "type": "income",
                "category": "Investment",
                "account_name": "Capital Account"
            },
            {
                "date": datetime.now() - timedelta(days=45),
                "description": "Office Equipment Purchase",
                "amount": -15000.00,
                "type": "expense", 
                "category": "Equipment",
                "account_name": "Fixed Assets"
            },
            {
                "date": datetime.now() - timedelta(days=40),
                "description": "Software Subscription - Annual",
                "amount": -3600.00,
                "type": "expense",
                "category": "Software",
                "account_name": "Operating Expenses"
            },
            {
                "date": datetime.now() - timedelta(days=35),
                "description": "Client Payment - Project Alpha",
                "amount": 25000.00,
                "type": "income",
                "category": "Revenue",
                "account_name": "Accounts Receivable"
            },
            {
                "date": datetime.now() - timedelta(days=30),
                "description": "Marketing Campaign",
                "amount": -5000.00,
                "type": "expense",
                "category": "Marketing",
                "account_name": "Marketing Expenses"
            },
            {
                "date": datetime.now() - timedelta(days=25),
                "description": "Client Payment - Project Beta",
                "amount": 18000.00,
                "type": "income",
                "category": "Revenue",
                "account_name": "Accounts Receivable"
            },
            {
                "date": datetime.now() - timedelta(days=20),
                "description": "Employee Salaries",
                "amount": -12000.00,
                "type": "expense",
                "category": "Payroll",
                "account_name": "Payroll Expenses"
            },
            {
                "date": datetime.now() - timedelta(days=15),
                "description": "Consulting Revenue",
                "amount": 8500.00,
                "type": "income",
                "category": "Revenue",
                "account_name": "Revenue"
            },
            {
                "date": datetime.now() - timedelta(days=10),
                "description": "Office Utilities",
                "amount": -800.00,
                "type": "expense",
                "category": "Utilities",
                "account_name": "Operating Expenses"
            },
            {
                "date": datetime.now() - timedelta(days=5),
                "description": "Client Payment - Project Gamma",
                "amount": 22000.00,
                "type": "income",
                "category": "Revenue",
                "account_name": "Accounts Receivable"
            }
        ]
        
        synced_count = 0
        
        for transaction_data in sample_transactions:
            # Check if similar transaction already exists
            existing = db.query(Transaction).filter(
                Transaction.description == transaction_data["description"],
                Transaction.amount == transaction_data["amount"]
            ).first()
            
            if not existing:
                transaction = Transaction(**transaction_data)
                db.add(transaction)
                synced_count += 1
        
        db.commit()
        return synced_count
    
    def _categorize_transaction(self, description: str) -> str:
        """Simple transaction categorization based on description"""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ["sales", "revenue", "payment", "consulting", "service"]):
            return "Revenue"
        elif any(word in description_lower for word in ["rent", "office"]):
            return "Rent"
        elif any(word in description_lower for word in ["salary", "payroll", "wages"]):
            return "Payroll"
        elif any(word in description_lower for word in ["marketing", "advertising"]):
            return "Marketing"
        elif any(word in description_lower for word in ["software", "subscription", "saas"]):
            return "Software"
        elif any(word in description_lower for word in ["equipment", "hardware"]):
            return "Equipment"
        elif any(word in description_lower for word in ["utilities", "electricity", "internet"]):
            return "Utilities"
        else:
            return "Other"
