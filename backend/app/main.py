from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import routes as auth_routes
from app.users import routes as user_routes
from app.plants import routes as plant_routes
from app.identification import routes as identification_routes
from app.plants import species_routes

app = FastAPI(title="Floradex API")

# Configure CORS to allow requests from your frontend
origins = [
    "http://localhost:8081",        # Expo web
    "http://localhost:19006",       # Another possible Expo web port
    "http://localhost:3000",        # In case you use another port
    "http://127.0.0.1:8081",        # Using IP instead of localhost
    "exp://localhost:19000",        # Expo mobile
    "exp://127.0.0.1:19000",        # Expo mobile with IP
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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

@app.get("/")
async def root():
    return {"message": "Welcome to Floradex API"}