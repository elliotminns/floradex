from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.auth import routes as auth_routes
from app.users import routes as user_routes
from app.plants import routes as plant_routes
from app.identification import routes as identification_routes
from app.plants import species_routes
from app.plants import species

import os

app = FastAPI(title="Floradex API")

os.makedirs("static/uploads/plants", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure CORS to allow requests from your frontend
origins = [
    "http://localhost:8081",        # Expo web
    "exp://172.20.10.7:8081"        #UWE Mobile Address
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(user_routes.router, prefix="/api/users", tags=["Users"])
app.include_router(plant_routes.router, prefix="/api/plants", tags=["Plants"])
app.include_router(identification_routes.router, prefix="/api/identify", tags=["Identification"])
app.include_router(
    species_routes.router,
    prefix="/species",  # New endpoint for plant species
    tags=["species"]
)
app.include_router(
    species.router,
    prefix="/api/plant-species",
    tags=["plant-species"]
)

@app.get("/")
async def root():
    return {"message": "Welcome to Floradex API"}