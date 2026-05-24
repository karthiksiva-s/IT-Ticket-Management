# ============================================================
# routes/tickets.py — All Ticket-Related Routes
# Handles: Create, View, Update, Cancel tickets
# ============================================================

from fastapi import APIRouter, HTTPException, Depends
from database import get_connection
from models import CreateTicketRequest, UpdateTicketRequest, CancelTicketRequest
from auth_utils import get_current_user, require_admin
from datetime import date

router = APIRouter()


def generate_ticket_id(cursor) -> str:
    """
    Auto-generates a unique Ticket ID in the format: TKT-YYYYMMDD-XXXX
    Example: TKT-20240615-0042
    
    We count today's tickets and increment by 1.
    """
    today = date.today().strftime("%Y%m%d")   # e.g., "20240615"
    prefix = f"TKT-{today}-"

    # Count how many tickets already exist today
    cursor.execute("SELECT COUNT(*) as cnt FROM tickets WHERE ticket_id LIKE ?", (f"{prefix}%",))
    count = cursor.fetchone()["cnt"]

    # Format as 4-digit number: 0001, 0002, ...
    ticket_id = f"{prefix}{str(count + 1).zfill(4)}"
    return ticket_id


# -------------------------------------------------------
# POST /tickets/create
# Creates a new ticket (User only)
# -------------------------------------------------------
@router.post("/create")
def create_ticket(data: CreateTicketRequest, user: dict = Depends(get_current_user)):
    """
    Creates a new support ticket.
    - Auto-generates: Ticket ID, Created Date
    - Default Status: Open
    - Linked to the logged-in user
    """
    conn = get_connection()
    cursor = conn.cursor()

    ticket_id = generate_ticket_id(cursor)
    created_date = date.today().isoformat()   # e.g., "2024-06-15"

    cursor.execute("""
        INSERT INTO tickets 
        (ticket_id, employee_name, employee_id, asset_id, category, subject,
         description, priority, status, created_date, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Open', ?, ?)
    """, (
        ticket_id,
        data.employee_name,
        data.employee_id,
        data.asset_id,
        data.category,
        data.subject,
        data.description,
        data.priority,
        created_date,
        user["user_id"]
    ))

    conn.commit()
    conn.close()

    return {
        "message": "Ticket created successfully!",
        "ticket_id": ticket_id
    }


# -------------------------------------------------------
# GET /tickets/my
# Returns all tickets created by the logged-in user
# -------------------------------------------------------
@router.get("/my")
def get_my_tickets(user: dict = Depends(get_current_user)):
    """
    Returns all tickets belonging to the current user.
    Used in: User Dashboard + View All Tickets page
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM tickets 
        WHERE created_by = ? 
        ORDER BY created_date DESC
    """, (user["user_id"],))

    tickets = [dict(row) for row in cursor.fetchall()]   # Convert rows to dicts
    conn.close()

    return tickets


# -------------------------------------------------------
# GET /tickets/my/stats
# Returns ticket counts for User Dashboard counters
# -------------------------------------------------------
@router.get("/my/stats")
def get_my_stats(user: dict = Depends(get_current_user)):
    """
    Returns summary statistics for the dashboard cards.
    Total / Open / Closed tickets count.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as cnt FROM tickets WHERE created_by = ?", (user["user_id"],))
    total = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM tickets WHERE created_by = ? AND status = 'Open'", (user["user_id"],))
    open_count = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM tickets WHERE created_by = ? AND status IN ('Closed','Canceled')", (user["user_id"],))
    closed_count = cursor.fetchone()["cnt"]

    conn.close()

    return {"total": total, "open": open_count, "closed": closed_count}


# -------------------------------------------------------
# PUT /tickets/{ticket_id}/cancel
# User cancels their own Open ticket
# -------------------------------------------------------
@router.put("/{ticket_id}/cancel")
def cancel_ticket(ticket_id: str, data: CancelTicketRequest, user: dict = Depends(get_current_user)):
    """
    Cancels a ticket.
    - Only the owner can cancel
    - Only Open tickets can be canceled
    - Must provide a cancel reason
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Fetch the ticket to validate ownership and status
    cursor.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,))
    ticket = cursor.fetchone()

    if not ticket:
        conn.close()
        raise HTTPException(status_code=404, detail="Ticket not found.")

    if ticket["created_by"] != user["user_id"]:
        conn.close()
        raise HTTPException(status_code=403, detail="You can only cancel your own tickets.")

    if ticket["status"] != "Open":
        conn.close()
        raise HTTPException(status_code=400, detail="Only Open tickets can be canceled.")

    # Update the ticket status and store the reason
    cursor.execute("""
        UPDATE tickets 
        SET status = 'Canceled', cancel_reason = ? 
        WHERE ticket_id = ?
    """, (data.cancel_reason, ticket_id))

    conn.commit()
    conn.close()

    return {"message": "Ticket canceled successfully."}


# -------------------------------------------------------
# GET /tickets/all  (Admin only)
# Returns all tickets with optional search/sort
# -------------------------------------------------------
@router.get("/all")
def get_all_tickets(
    search: str = "",
    sort_by: str = "date",
    admin: dict = Depends(require_admin)
):
    """
    Admin-only: Returns ALL tickets in the system.
    
    search   → filter by ticket_id, employee_name, or asset_id
    sort_by  → 'date' (newest first) or 'priority' (High → Low)
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Build search filter
    search_filter = f"%{search}%"

    # Sort logic
    if sort_by == "priority":
        # Sort High → Medium → Low using CASE
        order_clause = "CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 WHEN 'Low' THEN 3 END"
    else:
        order_clause = "created_date DESC"   # Default: newest first

    cursor.execute(f"""
        SELECT * FROM tickets 
        WHERE ticket_id LIKE ? OR employee_name LIKE ? OR asset_id LIKE ?
        ORDER BY {order_clause}
    """, (search_filter, search_filter, search_filter))

    tickets = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return tickets


# -------------------------------------------------------
# GET /tickets/admin/stats  (Admin only)
# Returns admin dashboard statistics
# -------------------------------------------------------
@router.get("/admin/stats")
def get_admin_stats(admin: dict = Depends(require_admin)):
    """
    Admin dashboard counters:
    Total / Open / Closed / High Priority tickets
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as cnt FROM tickets")
    total = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM tickets WHERE status = 'Open'")
    open_count = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM tickets WHERE status IN ('Closed','Canceled')")
    closed_count = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM tickets WHERE priority = 'High'")
    high_priority = cursor.fetchone()["cnt"]

    # Fetch high priority tickets for the dashboard table
    cursor.execute("""
        SELECT * FROM tickets 
        WHERE priority = 'High' 
        ORDER BY created_date DESC 
        LIMIT 10
    """)
    high_priority_tickets = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "total": total,
        "open": open_count,
        "closed": closed_count,
        "high_priority": high_priority,
        "high_priority_tickets": high_priority_tickets
    }


# -------------------------------------------------------
# PUT /tickets/{ticket_id}/update  (Admin only)
# Admin updates status and/or adds a response
# -------------------------------------------------------
@router.put("/{ticket_id}/update")
def update_ticket(ticket_id: str, data: UpdateTicketRequest, admin: dict = Depends(require_admin)):
    """
    Admin updates a ticket.
    - Can change: status (Open → In Progress → Closed)
    - Can add: admin_response (reply to user)
    - Cannot edit Closed or Canceled tickets
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,))
    ticket = cursor.fetchone()

    if not ticket:
        conn.close()
        raise HTTPException(status_code=404, detail="Ticket not found.")

    if ticket["status"] in ("Closed", "Canceled"):
        conn.close()
        raise HTTPException(status_code=400, detail="Cannot update a Closed or Canceled ticket.")

    # Build dynamic update — only update fields that were provided
    fields = []
    values = []

    if data.status:
        fields.append("status = ?")
        values.append(data.status)

    if data.admin_response:
        fields.append("admin_response = ?")
        values.append(data.admin_response)

    if not fields:
        conn.close()
        raise HTTPException(status_code=400, detail="Nothing to update.")

    values.append(ticket_id)   # For the WHERE clause

    cursor.execute(f"UPDATE tickets SET {', '.join(fields)} WHERE ticket_id = ?", values)
    conn.commit()
    conn.close()

    return {"message": "Ticket updated successfully."}


# -------------------------------------------------------
# GET /tickets/{ticket_id}
# Get a single ticket by ID (both user and admin)
# -------------------------------------------------------
@router.get("/{ticket_id}")
def get_ticket(ticket_id: str, user: dict = Depends(get_current_user)):
    """
    Returns full details of a single ticket.
    Used when opening the View Details popup/modal.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,))
    ticket = cursor.fetchone()
    conn.close()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")

    # Users can only view their own tickets; admins can view any
    if user["role"] != "admin" and ticket["created_by"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied.")

    return dict(ticket)