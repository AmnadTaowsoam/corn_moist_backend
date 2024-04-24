from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List
import httpx
import joblib
import pandas as pd
import numpy as np
import json

app = FastAPI()

# Load the model at the start of the application
model = joblib.load("linear_moisture_model.pkl")

class JSONData(BaseModel):
    data: List[float]
    sensorId: str = Field(default="default_id", example="sensor_001")

async def predict(data: List[float]) -> float:
    # Convert data to the format expected by the model
    df = pd.DataFrame([data], columns=model.feature_names_in_)
    prediction = model.predict(df)
    return prediction[0]

async def forward_data_to_port_8002(data: JSONData, prediction: float):
    async with httpx.AsyncClient() as client:
        url = "http://127.0.0.1:8002/upload/json"
        try:
            # Modify the payload to match the expected format of the second application
            payload = {"value": [prediction]}  # Assuming prediction is a single float value
            print(f"Sending payload to port 8002: {payload}")  # Print the payload being sent
            response = await client.post(url, json=payload)
            response.raise_for_status()
            print(f"Data forwarded to port 8002: {data.data}, Prediction: {prediction}, Sensor ID: {data.sensorId}")
        except httpx.HTTPError as e:
            print(f"Error forwarding data to port 8002: {e}")

@app.post("/upload/json")
async def receive_and_forward_data(background_tasks: BackgroundTasks, json_data: JSONData):
    print(f"Data received on port 8001: {json_data.data}, Sensor ID: {json_data.sensorId}")
    # Predict the value before forwarding
    prediction = await predict(json_data.data)
    # Schedule the data to be forwarded with the prediction and the sensorId
    background_tasks.add_task(forward_data_to_port_8002, json_data, prediction)
    return {"message": "Data received and is being forwarded to port 8002", "prediction": prediction, "sensorId": json_data.sensorId}