from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import auth, resume, history
from .database import Base, engine
import models  # Import models to ensure tables are created

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ATS Resume Rewriter API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(resume.router, prefix="/resume", tags=["resume"])
app.include_router(history.router, prefix="/history", tags=["history"])

@app.get("/")
async def root():
    return {"message": "ATS Resume Rewriter API"}