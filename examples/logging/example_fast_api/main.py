from fastapi import FastAPI
from log import router as log_router

app = FastAPI()

app.include_router(log_router)
