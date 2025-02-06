from fastapi import FastAPI
import uvicorn
from background_create import router as background_router
from decorator import router as decorator_router

app = FastAPI()

app.include_router(decorator_router)
app.include_router(background_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
