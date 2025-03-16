from fastapi import APIRouter, Response, Request, Depends
from database import database
from sqlalchemy.future import select
from sqlalchemy import DateTime
from datetime import datetime
from datetime import timezone
from fastapi.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from starlette import status

from auth import auth
from database import database

router = APIRouter()

@router.post("/register_sensor", tags=["Sensor"])
async def register_sensor(
    sensor: str, 
    _user: None = Depends(auth.get_current_user), 
    _auth: None = Depends(auth.check_and_renew_access_token)
):
    async with database.AsyncSessionLocalFactory() as session:
        new_sensor = database.Sensor(
            sensor_id=sensor,
            owner_id=_user['sub'],
        )
        session.add(new_sensor)
        try:
            await session.commit()
        except IntegrityError:
            raise HTTPException(status_code=400, detail="Invalid sensor ID")
    return {'registered_sensor_id': sensor, 'registered_owner': _user['sub']}


# Define a Pydantic model matching the sensor's POST payload.
class SensorPayload(BaseModel):
    uid: int       # sensor identifier (will be converted to string)
    long: float    # longitude
    lat: float     # latitude
    fall: int      # fall (drop) events
    temp: int      # temperature events
    hum: int       # water/humidity events

@router.post("/sensor_data", tags=["Sensor"])
async def sensor_data(payload: SensorPayload):
    sensor_id_str = str(payload.uid)
    
    async with database.AsyncSessionLocalFactory() as session:
        # Check if the sensor is registered in user_sensors.
        result = await session.execute(
            select(database.Sensor).filter_by(sensor_id=sensor_id_str)
        )
        user_sensor_record = result.scalar_one_or_none()

        if not user_sensor_record:
            raise HTTPException(status_code=400, detail="Sensor not registered. Please call register_sensor first.")
        
        # Check if the sensor is associated with an open contract.
        result = await session.execute(
            select(database.Contract).where(
                database.Sensor.sensor_id == sensor_id_str &
                database.Contract.contract_status == database.ContractStatus.FULFILLMENT 
            )
        )
        in_progress_contract = result.scalars().all()
        if not in_progress_contract:
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail="Sensor not associated with an in progress contract."
            )

        # Next, try to retrieve an existing sensor_data record.
        result = await session.execute(
            select(database.SensorData).filter_by(sensor_id=sensor_id_str)
        )
        sensor_data_record = result.scalar_one_or_none()

        if sensor_data_record:
            # Sensor data exists: update its counters and location.
            sensor_data_record.drop_alerts += payload.fall
            sensor_data_record.overtemp_alerts += payload.temp
            sensor_data_record.water_events += payload.hum
            sensor_data_record.longitude = payload.long
            sensor_data_record.latitude = payload.lat
        else:
            # Sensor data does not exist; create a new record.
            new_sensor_data = database.SensorData(
                sensor_id=sensor_id_str,
                drop_alerts=payload.fall,
                overtemp_alerts=payload.temp,
                water_events=payload.hum,
                longitude=payload.long,
                latitude=payload.lat,
            )
            session.add(new_sensor_data)

        try:
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=400, detail=f"Error updating sensor data: {str(e)}")
        
    return {"status": "success", "sensor_id": sensor_id_str}
