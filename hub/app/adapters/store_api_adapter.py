import json
import logging
from typing import List

import pydantic_core
import requests

from app.entities.processed_agent_data import ProcessedAgentData
from app.interfaces.store_gateway import StoreGateway


class StoreApiAdapter(StoreGateway):
    def __init__(self, api_base_url):
        self.api_base_url = api_base_url

    def save_data(self, processed_agent_data_batch: List[ProcessedAgentData]):
        """
        Save the processed road data to the Store API.
        Parameters:
            processed_agent_data_batch (dict): Processed road data to be saved.
        Returns:
            bool: True if the data is successfully saved, False otherwise.
        """
        try:
            # Перетворити дані на формат, придатний для API
            payload = [data.to_dict() for data in processed_agent_data_batch]
            
            # Надіслати дані до API
            response = requests.post(
                f"{self.api_base_url}/store/data",
                json=payload
            )
            
            # Перевірити відповідь
            if response.status_code in (200, 201):
                return True
            else:
                print(f"Error saving data: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Exception when saving data: {str(e)}")
            return False
