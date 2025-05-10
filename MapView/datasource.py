import asyncio
import json
from datetime import datetime
import websockets
from kivy import Logger
from pydantic import BaseModel, field_validator
from config import STORE_HOST, STORE_PORT
import paho.mqtt.client as mqtt


# Pydantic models
class ProcessedAgentData(BaseModel):
    road_state: str
    user_id: int
    x: float
    y: float
    z: float
    latitude: float
    longitude: float
    timestamp: datetime

    @classmethod
    @field_validator("timestamp", mode="before")
    def check_timestamp(cls, value):
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            raise ValueError(
                "Invalid timestamp format. Expected ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)."
            )


class Datasource:
    def __init__(self, user_id: int):
        self.index = 0
        self.user_id = user_id
        self.connection_status = None
        self._new_points = []
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        asyncio.ensure_future(self.connect_to_server())

    def get_new_points(self):
        Logger.debug(self._new_points)
        points = self._new_points
        self._new_points = []
        return points

    async def connect_to_server(self):
        while True:
            Logger.debug("CONNECT TO SERVER")
            try:
                self.client.connect(STORE_HOST, STORE_PORT, 60)
                self.connection_status = "Connected"
                self.client.loop_start()
              
                while self.connection_status == "Connected":
                    await asyncio.sleep(1)
            except Exception as e:
                Logger.debug(f"Connection error: {e}")
                self.connection_status = "Disconnected"
                Logger.debug("SERVER DISCONNECT")
                await asyncio.sleep(5) 

    def on_connect(self, client, userdata, flags, rc):
        Logger.debug(f"Connected with result code {rc}")
        self.client.subscribe("processed_agent_data")

    def on_message(self, client, userdata, msg):
        try:
            data = msg.payload.decode()
            parsed_data = json.loads(data)
            self.handle_received_data(parsed_data)
        except Exception as e:
            Logger.debug(f"Error processing message: {e}")

    def handle_received_data(self, data):
        Logger.debug(f"Received data: {data}")
        
        if isinstance(data, str):
            data = json.loads(data)
        
        if "road_state" in data and "agent_data" in data:
            agent_data = data["agent_data"]
            gps_data = agent_data.get("gps", {})
            new_point = (
                gps_data.get("latitude"),
                gps_data.get("longitude"),
                data.get("road_state")
            ) 
            if None not in new_point:
                self._new_points.append(new_point)
            else:
                Logger.warning(f"Incomplete data received: {data}")