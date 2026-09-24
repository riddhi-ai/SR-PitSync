"""SR PITSYNC backend. Start it with:  uvicorn main:app --reload"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import config
import models  # noqa: F401  (makes sure the tables are known)
import timeutil
from database import Base, engine
from routers import attendance, auth, members, tasks, workshop, exports

os.makedirs(config.UPLOAD_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)  # creates the tables the first time
    yield


app = FastAPI(title="SR PITSYNC API", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_credentials=False,
                   allow_methods=["*"], allow_headers=["*"])

for r in (auth, members, attendance, tasks, workshop,exports):
    app.include_router(r.router)

app.mount("/uploads", StaticFiles(directory=config.UPLOAD_DIR), name="uploads")


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "app": config.APP_NAME, "today": timeutil.today(), "timezone": config.TIMEZONE}
