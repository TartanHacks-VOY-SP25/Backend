from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, Float, TIMESTAMP
import enum

# TODO: REPLACE WITH REAL ENV VARS
DATABASE_URL = (
    "postgresql+asyncpg://myuser:mypassword@host.docker.internal:5432/mydatabase"
)

# DB Models
Base = declarative_base()


class User(Base):
    """
    User model for the database.
    """
    __tablename__ = "users"
    user_id         = Column(String, primary_key=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    wallet_number   = Column(String, nullable=False)
    wallet_address  = Column(String, nullable=False)


class Sensor(Base):
    """
    Sensor model for the database.
    """
    __tablename__ = "user_sensors"
    sensor_id   = Column(String, primary_key=True, nullable=False, index=True)
    owner_id    = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)


class SensorData(Base):
    """'
    Sensor data model for the database.
    """
    __tablename__ = "sensor_data"
    sensor_id = Column(
        String, ForeignKey("user_sensors.sensor_id"), primary_key=True, nullable=False
    )
    drop_alerts     = Column(Integer, nullable=False, index=True)
    overtemp_alerts = Column(Integer, nullable=False, index=True)
    water_events    = Column(Integer, nullable=False, index=True)


class ContractStatus(enum.Enum):
    """
    Contract status enum for the database.
    """
    OPEN = "OPEN"
    FULFILLMENT = "FULFILLMENT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Contract(Base):
    """
    Contract model for the database.
    """
    __tablename__ = "contracts"

    # Contract ID
    contract_id = Column(Integer, primary_key=True, nullable=False, index=True)

    # USER IDs
    proposer_id = Column(
        String, ForeignKey("users.user_id"), nullable=False, index=True
    )
    courier_id = Column(
        String, ForeignKey("users.user_id"), nullable=True, index=True
    )

    # Timestamps and status
    contract_award_time         = Column(TIMESTAMP(timezone=True), nullable=True, index=True)
    contract_completion_time    = Column(TIMESTAMP(timezone=True), nullable=True, index=True)
    contract_confirm_completion = Column(TIMESTAMP(timezone=True), nullable=True, index=True)
    contract_timeout            = Column(TIMESTAMP(timezone=True), index=True)
    contract_status             = Column(String, nullable=False, index=True)

    # Financial details
    required_collateral     = Column(Float, nullable=False)
    base_price              = Column(Float, nullable=False, index=True)
    t1_bonus                = Column(Float, nullable=False, index=True)
    t2_bonus                = Column(Float, nullable=False, index=True)

    # Escrow keys
    base_lock           = Column(String)
    t1_lock             = Column(String)
    t2_lock             = Column(String)
    collateral_lock     = Column(String)
    base_key            = Column(String)
    t1_key              = Column(String)
    t2_key              = Column(String)
    collateral_key      = Column(String)
    base_txn_id         = Column(String)
    t1_txn_id           = Column(String)
    t2_txn_id           = Column(String)
    collateral_txn_id   = Column(String)


    # Sensor
    sensor_id = Column(
        String, ForeignKey("user_sensors.sensor_id"), nullable=True, index=True
    )

    # Contract details
    contract_title         = Column(String, nullable=False)
    contract_description   = Column(String, nullable=False)


# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create session factory
AsyncSessionLocalFactory = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)
