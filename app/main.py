# app/main.py
from fastapi import FastAPI

app = FastAPI(title="Price Tracker API")

@app.get("/")
async def root():
    return {"message": "API is running"}