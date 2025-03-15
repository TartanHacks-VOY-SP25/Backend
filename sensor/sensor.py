from fastapi import APIRouter, Response, Request, Depends
from database import database
from sqlalchemy.future import select
from sqlalchemy import DateTime
from datetime import datetime
from datetime import timezone
from fastapi.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

from auth import auth
from database import database

router = APIRouter()

@router.post("/register_sensor", tags=["Sensor"])
async def register_sensor(
    sensor: str, 
    _user: None=Depends(auth.get_current_user), 
    _auth: None=Depends(auth.check_and_renew_access_token)
    ):
    async with database.AsyncSessionLocalFactory() as session:
        new_sensor = database.Sensor(
            sensorID=sensor,
            ownerID=_user['sub'],
        )
        session.add(new_sensor)
        try:
            await session.commit()
        except IntegrityError:
            raise HTTPException(status_code=400, detail="Invalid sensor ID")
    return {'registered_sensor_id': sensor, 'registered_owner': _user['sub']}




class SensorData(BaseModel):
    uid: str
    fall: str
    temp: str
    hum: str

@router.post("/sensor_data", tags=["Sensor"])
async def sensor_data(data: SensorData, request: Request):
    async with database.AsyncSessionLocalFactory() as session:
        # just format the data and upload, no authentication needed.
        sensor_data = database.SensorData(
            sensorID=data.uid,
            timestamp=datetime.now(),
            drop_alerts=int(data.fall),
            overtemp_alerts=int(data.temp),
            water_events=int(data.hum),
        )
        try:
            session.add(sensor_data)
            await session.commit()
            await session.refresh(sensor_data)
        except Exception:
            raise HTTPException(status_code=400, detail="Unknown error occurred.")
    
    return {"status": "success"}

        # write the sensor data into the database, and gracefully handle and report any errors 
        