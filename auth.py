import os
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, APIRouter, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import httpx
from pydantic import BaseModel
from config import settings

import logging

# Logging and Configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

class Token(BaseModel):
    accessToken: str
    refreshToken: str
    token_type: str = "bearer"

class Login(BaseModel):
    username: str

class TokenData(BaseModel):
    username: str
    machine_ip: str = None  # Optional: default to None if not included in the token
    port: str = None 

async def username_exists(username: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(settings.user_exist_endpoint, params={"username": username})
        if response.status_code == 200:
            data = response.json()
            exists = data.get("exists", False)
            return {"exists": exists}
        else:
            return {"exists": False}
    
async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode token โดยใช้ค่าจาก settings
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        machine_ip: str = payload.get("machine_ip")
        port: str = payload.get("port")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, machine_ip=machine_ip, port=port)
    except JWTError:
        raise credentials_exception
    return token_data

def create_token(data: dict, expires_delta: timedelta, token_type: str) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({
        "exp": expire,
        "type": token_type,
        "machine_ip": data.get("machine_ip", ""),  # Storing IP in the token
        "port": data.get("port", "")               # Storing port in the token
    })
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

@router.post("/login", response_model=Token)
async def login_for_access_token(data: Login):
    if not await username_exists(data.username):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    accessToken = create_token(
        data={"sub": data.username},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        token_type="access"
    )
    logging.info(f'accessToken={accessToken}')
    refreshToken = create_token(
        data={"sub": data.username},
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        token_type="refresh"
    )
    logging.info(f'refreshToken={refreshToken}')
    return {"accessToken": accessToken, "refreshToken": refreshToken, "token_type": "bearer"}