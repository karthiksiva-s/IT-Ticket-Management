# ============================================================
# models.py — Data shapes (like blueprints / contracts)
# Pydantic checks that incoming JSON matches these shapes
# If something is missing or wrong type → automatic 422 error
# ============================================================

from pydantic import BaseModel
from typing import Optional


# -------------------------------------------------------
# AUTH MODELS
# -------------------------------------------------------

class RegisterRequest(BaseModel):
    """Data needed to register a new user"""
    username: str
    password: str
    role: str = "user"          # Default role is 'user'; can be 'admin'


class LoginRequest(BaseModel):
    """Data needed to log in"""
    username: str
    password: str


# -------------------------------------------------------
# TICKET MODELS
# -------------------------------------------------------

class CreateTicketRequest(BaseModel):
    """Data the user sends when creating a new ticket"""
    employee_name: str
    employee_id: str
    asset_id: str
    category: str               # e.g., Hardware, Software, Network, etc.
    subject: str
    description: str
    priority: str               # Low, Medium, or High


class UpdateTicketRequest(BaseModel):
    """
    Data the ADMIN sends when updating a ticket.
    All fields are Optional — admin may update just status, just response, or both.
    """
    status: Optional[str] = None            # Open, In Progress, Closed
    admin_response: Optional[str] = None    # Admin's reply to the user


class CancelTicketRequest(BaseModel):
    """Data the USER sends when canceling their own ticket"""
    cancel_reason: str          # User must provide a reason