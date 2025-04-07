import asyncio
import json
from typing import Set, Dict, List, Any
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Body
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Float,
    DateTime,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import select
from datetime import datetime
from pydantic import BaseModel, field_validator
from config import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
)

print(f"""
Database connection parameters:
HOST: {POSTGRES_HOST}
PORT: {POSTGRES_PORT}
USER: {POSTGRES_USER}
DB: {POSTGRES_DB}
PASSWORD: {'*' * len(POSTGRES_PASSWORD)}
""")

# FastAPI app setup
app = FastAPI()
# SQLAlchemy setup
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
print(f"Database URL: {DATABASE_URL.replace(POSTGRES_PASSWORD, '*' * len(POSTGRES_PASSWORD))}")

engine = create_engine(DATABASE_URL)
metadata = MetaData()
# Define the ProcessedAgentData table
processed_agent_data = Table(
    "processed_agent_data",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("road_state", String),
    Column("user_id", Integer),
    Column("x", Float),
    Column("y", Float),
    Column("z", Float),
    Column("latitude", Float),
    Column("longitude", Float),
    Column("timestamp", DateTime),
)
SessionLocal = sessionmaker(bind=engine)


# SQLAlchemy model
class ProcessedAgentDataInDB(BaseModel):
    id: int
    road_state: str
    user_id: int
    x: float
    y: float
    z: float
    latitude: float
    longitude: float
    timestamp: datetime


# FastAPI models
class AccelerometerData(BaseModel):
    x: float
    y: float
    z: float


class GpsData(BaseModel):
    latitude: float
    longitude: float


class AgentData(BaseModel):
    user_id: int
    accelerometer: AccelerometerData
    gps: GpsData
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


class ProcessedAgentData(BaseModel):
    road_state: str
    agent_data: AgentData


# WebSocket subscriptions
subscriptions: Dict[int, Set[WebSocket]] = {}


# FastAPI WebSocket endpoint
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    if user_id not in subscriptions:
        subscriptions[user_id] = set()
    subscriptions[user_id].add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        subscriptions[user_id].remove(websocket)


# Function to send data to subscribed users
async def send_data_to_subscribers(user_id: int, data):
    if user_id in subscriptions:
        for websocket in subscriptions[user_id]:
            await websocket.send_json(json.dumps(data))


# FastAPI CRUDL endpoints


@app.post("/processed_agent_data/")
async def create_processed_agent_data(data: List[ProcessedAgentData]):
    db = SessionLocal()
    try:
        created_items = []
        for item in data:
            db_item = {
                "road_state": item.road_state,"user_id": item.agent_data.user_id,
                "x": item.agent_data.accelerometer.x, "y": item.agent_data.accelerometer.y,
                "z": item.agent_data.accelerometer.z, "latitude": item.agent_data.gps.latitude,
                "longitude": item.agent_data.gps.longitude, "timestamp": item.agent_data.timestamp
            }
            
            query = processed_agent_data.insert().values(**db_item)
            result = db.execute(query)
            db.commit()
            
            created_item = {
                "id": result.inserted_primary_key[0],
                **db_item
            }
            created_items.append(created_item)
            
            if item.agent_data.user_id in subscriptions:
                await send_data_to_subscribers(
                    item.agent_data.user_id, {"type": "new_data", "data": created_item}
                )
        
        return {"status": "success","message": f"Успішно створено {len(created_items)} елементів",
            "data": created_items
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Під час створення даних сталася помилка: {str(e)}"
        )
    finally:
        db.close()


@app.get(
    "/processed_agent_data/{processed_agent_data_id}",response_model=ProcessedAgentDataInDB,)
def read_processed_agent_data(processed_agent_data_id: int):
    try:
        db = SessionLocal()
        query = select(processed_agent_data).where(
            processed_agent_data.c.id == processed_agent_data_id
        )
        result = db.execute(query).first()
        
        if result is None:
            raise HTTPException(status_code=404, detail=f"Дані з ID {processed_agent_data_id} не знайдено") 
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Помилка при отриманні даних: {str(e)}"
        )
    finally:
        db.close()


@app.get("/processed_agent_data/", response_model=list[ProcessedAgentDataInDB])
def list_processed_agent_data():
    try:
        db = SessionLocal()
        query = select(processed_agent_data)
        results = db.execute(query).fetchall()
        return results
    
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Помилка при отриманні списку даних: {str(e)}")
    finally:
        db.close()


@app.put(
    "/processed_agent_data/{processed_agent_data_id}",
    response_model=ProcessedAgentDataInDB,
)
def update_processed_agent_data(processed_agent_data_id: int, data: ProcessedAgentData):
    try:
        db = SessionLocal() 
        check_query = select(processed_agent_data).where(
            processed_agent_data.c.id == processed_agent_data_id
        )
        existing_record = db.execute(check_query).first()
        
        if existing_record is None:
            raise HTTPException(status_code=404,detail=f"Дані з ID {processed_agent_data_id} не знайдено")
        update_data = {
            "road_state": data.road_state,"user_id": data.agent_data.user_id,
            "x": data.agent_data.accelerometer.x,"y": data.agent_data.accelerometer.y,
            "z": data.agent_data.accelerometer.z, "latitude": data.agent_data.gps.latitude,
            "longitude": data.agent_data.gps.longitude,"timestamp": data.agent_data.timestamp
        }
        
        query = processed_agent_data.update().where(processed_agent_data.c.id == processed_agent_data_id).values(**update_data)  
        db.execute(query)
        db.commit()
        updated_record = db.execute(check_query).first()
        return updated_record
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Помилка при оновленні даних: {str(e)}"
        )
    finally:
        db.close()


@app.delete(
    "/processed_agent_data/{processed_agent_data_id}",response_model=ProcessedAgentDataInDB,)
def delete_processed_agent_data(processed_agent_data_id: int):
    try:
        db = SessionLocal()
        
        check_query = select(processed_agent_data).where(processed_agent_data.c.id == processed_agent_data_id)
        record_to_delete = db.execute(check_query).first()
        
        if record_to_delete is None:
            raise HTTPException(status_code=404,detail=f"Дані з ID {processed_agent_data_id} не знайдено")
        
        query = processed_agent_data.delete().where(processed_agent_data.c.id == processed_agent_data_id)
        db.execute(query)
        db.commit()
        
        return record_to_delete
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500,detail=f"Помилка при видаленні даних: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
