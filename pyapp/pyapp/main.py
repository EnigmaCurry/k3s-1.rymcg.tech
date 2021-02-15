from fastapi import FastAPI
import model
import logging

logging.basicConfig(level=logging.DEBUG)

app = FastAPI()
@app.get("/")
async def root():
    return {"message": "Hello World"}
