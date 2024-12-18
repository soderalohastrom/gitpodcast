from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import generate

app = FastAPI()

# Allow requests from your frontend (adjust frontend URL if needed)
origins = [
    "http://localhost:3000",  # Example frontend
    "https://gitdiagram.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(generate.router)

# Root route


@app.get("/")
async def hello():
    return {"message": "Welcome to the GitDiagram API!"}
