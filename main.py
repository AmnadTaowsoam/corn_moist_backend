from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import uvicorn
import jwt
from jwt import PyJWTError, ExpiredSignatureError
import datetime
import configparser

app = FastAPI()

config = configparser.ConfigParser()
config.read('config.ini')
server_config = config['ServerCredentials']

USERNAME = server_config['username']
PASSWORD = server_config['password']
SECRET_KEY = server_config['SECRET_KEY']

security = HTTPBearer()

class LoginData(BaseModel):
    username: str
    password: str

class MoistureData(BaseModel):
    sensor_id: str
    moisture: int

def create_token(data: dict, expires_delta: datetime.timedelta = None):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (expires_delta if expires_delta else datetime.timedelta(minutes=30))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid token")

@app.post("/login")
async def login(login_data: LoginData):
    if login_data.username == USERNAME and login_data.password == PASSWORD:
        token_data = {"sub": login_data.username}
        token = create_token(token_data)
        return {"access_token": token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

@app.post("/refresh_token")
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
    username = payload.get('sub')
    new_token = create_token({"sub": username})
    return {"access_token": new_token, "token_type": "bearer"}

@app.post("/data")
async def receive_data(data: MoistureData, token: str = Depends(verify_token)):
    print(f"Received data: {data}")
    return {"status": "Data received successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008)
