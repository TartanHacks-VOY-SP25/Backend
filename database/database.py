from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, String
import enum

# TODO: REPLACE WITH REAL ENV VARS
DATABASE_URL = "postgresql+asyncpg://myuser:mypassword@host.docker.internal:5432/mydatabase"


# DB Models
# Base class for models
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    userID                          = Column(String, primary_key=True, nullable=False, index=True)
    hashed_password                 = Column(String, nullable=False)
    # TODO: XRP wallet details
    # email: str
    # full_name: str
    # disabled: bool

class Sensor(Base):
    __tablename__ = "user_sensors"
    sensorID                       = Column(String, primary_key=True,           nullable=False, index=True)
    ownerID                        = Column(String, ForeignKey("users.userID"), nullable=False, index=True)
    # sensorType                     = Column(String, nullable=False, index=True)
    # sensorLocation                 = Column(String, nullable=False, index=True)
    # sensorStatus                   = Column(String, nullable=False, index=True)
    # sensorDetails                  = Column(String, nullable=False, index=True)

class SensorData(Base):
    __tablename__ = "sensor_data"
    sensorID                      = Column(String, ForeignKey("user_sensors.sensorID"),  primary_key=True, nullable=False)
    timestamp                     = Column(DateTime, nullable=False)
    drop_alerts                   = Column(Integer,  nullable=False, index=True)
    overtemp_alerts               = Column(Integer,  nullable=False, index=True)
    water_events                  = Column(Integer,  nullable=False, index=True)


class ContractStatus(str, enum.Enum):
    OPEN = "open"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class Contract(Base):
    __tablename__ = "contracts"
    contractID                    = Column(Integer, primary_key=True, index=True)
    proposerID                    = Column(String, ForeignKey("users.userID"),   index=True)
    biddingExpiryTime             = Column(DateTime,             nullable=False, index=True)
    biddingSelectionExpiryTime    = Column(DateTime,             nullable=False, index=True)
    contractAwardTime             = Column(DateTime,             nullable=True,  index=True)
    contractCompletionTime        = Column(DateTime,             nullable=True,  index=True)
    contractStatus                = Column(String,               nullable=False, index=True)
    title                         = Column(String,               nullable=False, index=True)
    description                   = Column(String,               nullable=False, index=True)
    # TODO: Add fields as necessary for XRP integration

class BidStatus(str, enum.Enum):
    OPEN = "open"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class Bid(Base):
    __tablename__ = "bids"
    bidID                         = Column(Integer, primary_key=True,                   index=True, nullable=False)
    bidderID                      = Column(String,  ForeignKey("users.userID"),         index=True, nullable=False)
    contractID                    = Column(Integer, ForeignKey("contracts.contractID"), index=True, nullable=False)
    bidFloorPrice                 = Column(Integer,                                     index=True, nullable=False)
    incentives                    = Column(String,                                      index=True, nullable=False)
    bidStatus                     = Column(String,                                      index=True, nullable=False)
    bidTime                       = Column(DateTime,                                    index=True, nullable=False)   
    sensorID                      = Column(String, ForeignKey("user_sensors.sensorID"), index=True, nullable=False)

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create session factory
AsyncSessionLocalFactory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)