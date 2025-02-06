from fastapi import FastAPI
from async_create import router as async_router

app = FastAPI()

app.include_router(async_router)
