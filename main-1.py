import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import dashboard

load_dotenv()

app = FastAPI(title="Admin Document Management Portal API")

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://127.0.0.1:5500")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin, "http://localhost:5500", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "admin-portal-api"}
