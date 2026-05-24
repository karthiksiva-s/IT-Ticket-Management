# ============================================================
# main.py — Entry point of the FastAPI application
# This file starts the server and links all routes together
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Allows browser to talk to this API
from database import create_tables               # Our DB setup function
from routes import auth, tickets                 # Our route files

# Create the FastAPI app instance
app = FastAPI(title="IT Ticket Management System")

# -------------------------------------------------------
# CORS Middleware
# Without this, the browser will block requests from
# our HTML files to this Python backend.
# -------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Allow all origins (for development)
    allow_methods=["*"],       # Allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],       # Allow all headers including Authorization
)

# -------------------------------------------------------
# Create database tables on startup
# This runs once when the server starts
# -------------------------------------------------------
create_tables()

# -------------------------------------------------------
# Register route groups (like chapters in a book)
# /auth  → login, register
# /tickets → create, view, update tickets
# -------------------------------------------------------
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])

# -------------------------------------------------------
# Root endpoint — just to test if server is running
# -------------------------------------------------------
@app.get("/")
def root():
    return {"message": "IT Ticket System API is running!"}