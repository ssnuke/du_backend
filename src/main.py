from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.events import router as evnet_router
import os 

app = FastAPI(title="DU Backend App", version="1.0.0")

app.include_router(evnet_router,prefix="/api")
app.add_middleware(CORSMiddleware,
                   allow_origins=["*"],
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"],
                   )

@app.get("/")
def hello():
    return {"message":" Hello world "}

@app.get("/healthz")
def read_api_health():
    return {"status": "ok"}