from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, resume, history, status
from database import Base, engine
import models  # Import models to ensure tables are created

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ATS Resume Rewriter API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(resume.router, prefix="/resume", tags=["resume"])
app.include_router(history.router, prefix="/history", tags=["history"])
app.include_router(status.router, prefix="", tags=["status"])

import traceback
from fastapi.responses import JSONResponse
from fastapi import Request

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": str(exc), "traceback": traceback.format_exc()}
    )


@app.get("/")
async def root():
    return {"message": "ATS Resume Rewriter API"}