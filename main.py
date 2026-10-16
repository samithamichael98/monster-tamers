
from fastapi import FastAPI
from app.routers.monsters import router as monsters_router

app = FastAPI(title="Monster Tamers API")

app.include_router(monsters_router)


@app.get("/")
def home():
    return {"message": "Welcome to Monster Tamers!"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
