from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import init_db, get_db
from models import User, UserRole
from auth import get_password_hash
from routes import auth_routes, admin_routes, candidate_routes
import os

# Initialize FastAPI app
app = FastAPI(
    title="Interview System API",
    description="Offline interview management system with PDF processing and auto-grading",
    version="1.0.0"
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router)
app.include_router(admin_routes.router)
app.include_router(candidate_routes.router)

# Serve uploaded files
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.on_event("startup")
def startup_event():
    """Initialize database and create default admin user"""
    # Initialize database tables
    init_db()
    
    # Create default admin user if doesn't exist
    from sqlalchemy.orm import Session
    db = next(get_db())
    
    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.ADMIN
            )
            db.add(admin_user)
            db.commit()
            print("✅ Default admin user created (username: admin, password: admin123)")
        else:
            print("✅ Admin user already exists")
    finally:
        db.close()

@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "Interview System API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
