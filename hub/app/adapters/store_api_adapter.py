import json
import logging
from typing import List
from datetime import datetime

import pydantic_core
import requests

from app.entities.processed_agent_data import ProcessedAgentData
from app.interfaces.store_gateway import StoreGateway


# Додаємо кастомний JSON-енкодер
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class StoreApiAdapter(StoreGateway):
    def __init__(self, api_base_url):
        self.api_base_url = api_base_url

    def save_data(self, processed_agent_data_batch: List[ProcessedAgentData]):
        try:
            # Конвертуємо дані в JSON формат з обробкою datetime
            data = []
            for item in processed_agent_data_batch:
                item_dict = item.model_dump()
                # Конвертуємо datetime в рядок
                if 'agent_data' in item_dict and 'timestamp' in item_dict['agent_data']:
                    if isinstance(item_dict['agent_data']['timestamp'], datetime):
                        item_dict['agent_data']['timestamp'] = item_dict['agent_data']['timestamp'].isoformat()
                data.append(item_dict)
            
            # Відправляємо POST запит до API
            response = requests.post(
                f"{self.api_base_url}/processed_agent_data/",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            # Перевіряємо статус відповіді
            response.raise_for_status()
            
            logging.info(f"Successfully saved {len(processed_agent_data_batch)} records")
            return True
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to save data: {str(e)}")
            return False
        
