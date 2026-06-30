import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import settings
from database import engine
from models.app import Base
from routers import api, apps, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.APK_STORAGE_PATH, exist_ok=True)
    os.makedirs(settings.ICON_STORAGE_PATH, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="techkev-Appstore", version="1.0.0", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(auth.router)
app.include_router(apps.router)
app.include_router(api.router)


@app.get("/health")
def health():
    return {"status": "ok"}
