from fastapi import FastAPI
from log import router as log_router
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

app = FastAPI()

app.title = "QuotientAI Logger Testing"
app.description = "A simple API for testing logging and detection with QuotientAI"

app.include_router(log_router)
