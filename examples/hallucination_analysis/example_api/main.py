from fastapi import FastAPI
from async_create import router as async_router
from decorator import router as decorator_router

app = FastAPI()

app.include_router(decorator_router)
app.include_router(async_router)
