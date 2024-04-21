import pandas as pd
import joblib
import logging
import json
import random

class CornMoistureProcessor:
    def __init__(self) -> None:
        self.model = None
        self.load_model()
    
    def load_model(self):
        try:
            self.model = joblib.load('./linear_moisture_model.pkl')
        except Exception as e:
            logging.error(f"Failed to load model: {e}")

    def transform_data(self, json_data):
        fields = ['sensorid', 'sensor_temperature', 'sensor_density', 'sensor_moisture']
        data_subset = {f'sensor_{field.capitalize()}': json_data.get(field, 0) for field in fields}
        df = pd.DataFrame([data_subset])
        df = df.apply(pd.to_numeric, errors='coerce')
        return df

    def predict_moisture(self, df):
        if not self.model:
            logging.error("Model is not loaded.")
            return None, json.dumps({"error": "Model is not loaded"})
        
        try:
            predictions = random.uniform(10.0, 20.0)  # Simulating model prediction
            result_json = json.dumps({"predicted_moisture": predictions})
            return predictions, result_json
        except Exception as e:
            logging.error(f"Error during model prediction: {e}")
            return None, json.dumps({"error": str(e)})