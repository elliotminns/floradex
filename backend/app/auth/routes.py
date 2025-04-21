# app/auth/routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from bson.objectid import ObjectId
from typing import Optional

from app.config import db, ACCESS_TOKEN_EXPIRE_MINUTES
from app.auth.utils import authenticate_user, create_access_token, get_password_hash
from app.users.models import UserCreate, User

router = APIRouter()

@router.post("/register", response_model=dict)
async def register(
    request: Request,
    username: Optional[str] = Form(None),
    password: Optional[str] = Form(None)
):
    # Try to get data from form
    if not username or not password:
        # Try to get data from JSON body
        try:
            data = await request.json()
            username = data.get("username")
            password = data.get("password")
        except:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not parse username and password from request"
            )
    
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username and password are required"
        )
        
    # Check if user exists
    db_user = db.users.find_one({"username": username})
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Create new user
    hashed_password = get_password_hash(password)
    user_data = {
        "username": username,
        "hashed_password": hashed_password,
        "plants": []
    }
    
    # Insert into database
    result = db.users.insert_one(user_data)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    
    return {
        "_id": str(result.inserted_id),
        "username": username,
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/login", response_model=dict)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Convert ObjectId to string if needed
    user_id = user.id
    if isinstance(user_id, ObjectId):
        user_id = str(user_id)
    
    return {
        "_id": user_id,
        "username": user.username,
        "access_token": access_token,
        "token_type": "bearer"
    }