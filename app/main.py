from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    announcements,
    attendance,
    auth,
    events,
    lifegroups,
    ministries,
    reports,
    users,
)
from app.core.config import settings

app = FastAPI(title="Hills of Glory MIS API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(ministries.router)
app.include_router(lifegroups.router)
app.include_router(events.router)
app.include_router(attendance.router)
app.include_router(announcements.router)
app.include_router(reports.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
