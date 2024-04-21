import os
import logging
import json
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from httpx import AsyncClient
from pydantic import BaseModel, ValidationError

from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from config import Settings

from cornMoistProcessing import CornMoistureProcessor

# Load environment settings
load_dotenv()
settings = Settings()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PredictionRequest(BaseModel):
    sensorid: str
    sensor_temperature: int
    sensor_density: int
    sensor_moisture: int

app = FastAPI()

processor = CornMoistureProcessor()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

limiter = Limiter(key_func=get_remote_address, default_limits=["5/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.on_event("startup")
async def startup_event():
    app.state.http_client = AsyncClient()

@app.on_event("shutdown")
async def shutdown_event():
    await app.state.http_client.aclose()

@app.post("/predict-moisture", status_code=200)
async def moisture_predict(request_data: PredictionRequest, client: AsyncClient = Depends(lambda: app.state.http_client)):
    try:
        logging.info(f'request_data: {request_data}')
        input_data = processor.transform_data(request_data.dict())
        predicted_moisture, result_json = processor.predict_moisture(input_data)
        logging.info(f'Predicted Moisture: {predicted_moisture}')
        logging.info(f'Predicted Moisture: {result_json}')

        if predicted_moisture is None:
            logger.error("Failed to generate prediction output correctly.")
            raise HTTPException(status_code=500, detail='Failed to process prediction.')

        return JSONResponse(status_code=200, content=json.loads(result_json))

    except ValidationError as ve:
        logger.error(f"Validation error: {ve.json()}")
        return JSONResponse(status_code=422, content={"detail": ve.errors()})

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    uvicorn.run("main:app", host=settings.backend_host, port=settings.backend_port)