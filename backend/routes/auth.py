# ============================================================
# routes/auth.py — Authentication Routes
# Handles: Register new users, Login existing users
# ============================================================

from fastapi import APIRouter, HTTPException
from database import get_connection
from models import RegisterRequest, LoginRequest
from auth_utils import create_token

# APIRouter is like a mini-app; we attach it to the main app in main.py
router = APIRouter()


# -------------------------------------------------------
# POST /auth/register
# Creates a new user account
# -------------------------------------------------------
@router.post("/register")
def register(data: RegisterRequest):
    """
    Registers a new user.
    - Checks if username already exists
    - Stores the user in the database
    - Returns a success message
    
    NOTE: In production, always hash passwords! (e.g., using bcrypt)
    We store plain text here for simplicity.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Check if username is already taken
    cursor.execute("SELECT id FROM users WHERE username = ?", (data.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists.")

    # Insert the new user
    cursor.execute(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        (data.username, data.password, data.role)
    )
    conn.commit()
    conn.close()

    return {"message": "User registered successfully!"}


# -------------------------------------------------------
# POST /auth/login
# Verifies credentials and returns a JWT token
# -------------------------------------------------------
@router.post("/login")
def login(data: LoginRequest):
    """
    Logs in a user.
    - Checks if username/password match
    - Returns a JWT token + user role
    
    The frontend stores this token and sends it with every request.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Look up user by username and password
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (data.username, data.password)
    )
    user = cursor.fetchone()
    conn.close()

    # If no match found → wrong credentials
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    # Generate a JWT token for this user
    token = create_token(user["id"], user["username"], user["role"])

    return {
        "token": token,
        "role": user["role"],
        "username": user["username"],
        "message": "Login successful!"
    }