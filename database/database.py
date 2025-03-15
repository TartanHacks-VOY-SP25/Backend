from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Float
import enum

# TODO: REPLACE WITH REAL ENV VARS
DATABASE_URL = "postgresql+asyncpg://myuser:mypassword@host.docker.internal:5432/mydatabase"

# DB Models
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    user_id =         Column(String, primary_key=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    wallet_number =   Column(String, nullable=False)
    wallet_address =  Column(String, nullable=False)
    
class Sensor(Base):
    __tablename__ = "user_sensors"
    sensor_id = Column(String, primary_key=True, nullable=False, index=True)
    owner_id =  Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    
class SensorData(Base):
    __tablename__ = "sensor_data"
    sensor_id =       Column(String, ForeignKey("user_sensors.sensor_id"), primary_key=True, nullable=False)
    drop_alerts =     Column(Integer, nullable=False, index=True)
    overtemp_alerts = Column(Integer, nullable=False, index=True)
    water_events =    Column(Integer, nullable=False, index=True)

class ContractStatus(enum.Enum):
    OPEN = "OPEN"
    FULFILLMENT = "FULFILLMENT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Contract(Base):
    __tablename__ = "contracts"
    contract_id =              Column(Integer, primary_key=True, nullable=False, index=True)
    proposer_id =              Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    courier_id =               Column(String, ForeignKey("users.user_id"), nullable=True, index=True)
    contract_award_time =      Column(DateTime, nullable=True, index=True)
    contract_completion_time = Column(DateTime, nullable=True, index=True)
    # contract_status can be OPEN, FULFILLMENT, COMPLETED, or FAILED
    contract_status =          Column(Enum(ContractStatus), nullable=False, index=True)
    required_collateral =      Column(Float, nullable=False)
    base_price =               Column(Float, nullable=False, index=True)
    t1_bonus =                 Column(Float, nullable=False, index=True)
    t2_bonus =                 Column(Float, nullable=False, index=True)
    base_lock =                Column(String, nullable=False)
    t1_lock =                  Column(String, nullable=False)
    t2_lock =                  Column(String, nullable=False)
    collateral_lock =          Column(String, nullable=False)
    base_key =                 Column(String, nullable=False)
    t1_key =                   Column(String, nullable=False)
    t2_key =                   Column(String, nullable=False)
    collateral_key =           Column(String, nullable=False)
    origin =                   Column(String, nullable=False, index=True)
    destination =              Column(String, nullable=False, index=True)
    contract_timeout =         Column(DateTime, nullable=True, index=True)
    sensor_id =                Column(String, ForeignKey("user_sensors.sensor_id"), nullable=True, index=True)

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create session factory
AsyncSessionLocalFactory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
