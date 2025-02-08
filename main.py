from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth.auth import router as auth_router
from contracts.contracts import router as contracts_router
from sensor.sensor import router as sensor_router

origins = [
    "http://localhost",
    "http://localhost:8000",
    # Add other origins as needed
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth")
app.include_router(contracts_router, prefix="/contracts")
app.include_router(sensor_router, prefix="/sensors")

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}