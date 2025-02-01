import requests
from fastapi import HTTPException
from io import BytesIO
import pandas as pd
import certifi
from io import StringIO
import json

class Utils:
    # Helper function to process API requests
    def fetch_data(endpoint):
        try:
            response = requests.get(endpoint)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Error fetching data: {e}")
        
    def fetch_image(url):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            return BytesIO(response.content)
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Error fetching image: {e}")
        
    def load_newline_delimited_json(file_url: str):
        response = requests.get(file_url, verify=False)
        response.raise_for_status()  # Check for HTTP errors
        return pd.read_json(StringIO(response.text), lines=True)
    
    def process_endpoint_url(endpoint_url, pop_key=None):
        """
        Fetches data from a URL, parses JSON, and optionally pops a key.

        Args:
            endpoint_url: The URL to fetch data from.
            pop_key: The key to pop from the JSON data (optional, defaults to None).

        Returns:
            A pandas DataFrame containing the processed data
        """
        json_result = requests.get(endpoint_url).content

        data = json.loads(json_result)

        # if pop_key is provided, pop key and normalize nested fields
        if pop_key:
            df_result = pd.json_normalize(data.pop(pop_key), sep = '_')
        # if pop_key is not provided, normalize entire json
        else:
            df_result = pd.json_normalize(data)

        return df_result
