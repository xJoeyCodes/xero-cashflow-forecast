from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import os
from jose import JWTError, jwt
from passlib.context import CryptContext

from ..models.database import get_db, User
from ..services.xero_service import XeroService

router = APIRouter()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserCreate(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    xero_tenant_id: Optional[str]
    last_sync_at: Optional[datetime]

    class Config:
        from_attributes = True

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/login", response_model=Token)
async def login_user(user: UserCreate, db: Session = Depends(get_db)):
    """Login user and return access token"""
    db_user = db.query(User).filter(User.email == user.email).first()
    
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.get("/xero/connect")
async def connect_xero():
    """Initiate Xero OAuth2 connection"""
    try:
        xero_service = XeroService()
        authorization_url = xero_service.get_authorization_url()
        return {"authorization_url": authorization_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to Xero: {str(e)}")

@router.get("/xero/callback")
async def xero_callback(
    code: str,
    state: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Handle Xero OAuth2 callback"""
    try:
        xero_service = XeroService()
        tokens = await xero_service.exchange_code_for_tokens(code)
        
        # Update user with Xero tokens
        current_user.xero_access_token = tokens["access_token"]
        current_user.xero_refresh_token = tokens["refresh_token"]
        current_user.xero_token_expires_at = datetime.utcnow() + timedelta(seconds=tokens["expires_in"])
        current_user.xero_tenant_id = tokens.get("tenant_id")
        
        db.commit()
        
        return {"message": "Successfully connected to Xero", "tenant_id": tokens.get("tenant_id")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete Xero connection: {str(e)}")

@router.post("/xero/disconnect")
async def disconnect_xero(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect from Xero"""
    current_user.xero_access_token = None
    current_user.xero_refresh_token = None
    current_user.xero_token_expires_at = None
    current_user.xero_tenant_id = None
    
    db.commit()
    
    return {"message": "Successfully disconnected from Xero"}

@router.get("/xero/status")
async def xero_connection_status(current_user: User = Depends(get_current_user)):
    """Check Xero connection status"""
    is_connected = bool(current_user.xero_access_token and current_user.xero_tenant_id)
    token_expires_at = current_user.xero_token_expires_at
    is_token_valid = token_expires_at and token_expires_at > datetime.utcnow() if token_expires_at else False
    
    return {
        "is_connected": is_connected,
        "tenant_id": current_user.xero_tenant_id,
        "token_expires_at": token_expires_at,
        "is_token_valid": is_token_valid,
        "last_sync_at": current_user.last_sync_at
    }
