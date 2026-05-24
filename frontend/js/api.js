// ============================================================
// js/api.js — Shared API helper
// All pages import this file to talk to the backend.
// It automatically adds the JWT token to every request.
// ============================================================

const API_BASE = "https://it-ticket-management-imd8.onrender.com";  // Backend server address

// -------------------------------------------------------
// getToken() — Reads the JWT token from localStorage
// The token is saved there after login
// -------------------------------------------------------
function getToken() {
    return localStorage.getItem("token");
}

// -------------------------------------------------------
// getUser() — Reads the logged-in user's info
// Returns: { token, role, username }
// -------------------------------------------------------
function getUser() {
    const user = localStorage.getItem("user");
    return user ? JSON.parse(user) : null;
}

// -------------------------------------------------------
// requireAuth(role) — Guards a page
// Call this at the top of every protected page.
// If not logged in → redirect to login
// If wrong role → redirect to their correct dashboard
// -------------------------------------------------------
function requireAuth(requiredRole = null) {
    const user = getUser();
    if (!user) {
        window.location.href = "/index.html";
        return null;
    }
    if (requiredRole && user.role !== requiredRole) {
        // Redirect to their own dashboard
        if (user.role === "admin") {
            window.location.href = "admin-dashboard.html";
        } else {
            window.location.href = "user-dashboard.html";
        }
        return null;
    }
    return user;
}

// -------------------------------------------------------
// logout() — Clears storage and sends user to login
// -------------------------------------------------------
function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "/index.html";
}

// -------------------------------------------------------
// apiFetch(endpoint, options) — The main HTTP helper
// Automatically:
//   - Adds Authorization header with the JWT token
//   - Sets Content-Type to JSON
//   - Returns parsed JSON response
//   - Throws an error if response is not OK (4xx/5xx)
// -------------------------------------------------------
async function apiFetch(endpoint, options = {}) {
    const token = getToken();

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(token ? { "Authorization": `Bearer ${token}` } : {}),
            ...(options.headers || {})
        }
    });

    const data = await response.json();

    // If the server returned an error, throw it so we can show the user
    if (!response.ok) {
        throw new Error(data.detail || "Something went wrong.");
    }

    return data;
}

// -------------------------------------------------------
// showToast(message, type) — Shows a temporary notification
// type: 'success' (green) or 'error' (red)
// -------------------------------------------------------
function showToast(message, type = "success") {
    // Remove any existing toast
    const existing = document.getElementById("toast");
    if (existing) existing.remove();

    const toast = document.createElement("div");
    toast.id = "toast";
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    // Animate in, then out
    setTimeout(() => toast.classList.add("show"), 10);
    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 400);
    }, 3000);
}

// -------------------------------------------------------
// getPriorityBadge(priority) — Returns colored HTML badge
// Used in tables to show priority visually
// -------------------------------------------------------
function getPriorityBadge(priority) {
    const colors = {
        High: "badge-high",
        Medium: "badge-medium",
        Low: "badge-low"
    };
    return `<span class="badge ${colors[priority] || ''}">${priority}</span>`;
}

// -------------------------------------------------------
// getStatusBadge(status) — Returns colored HTML badge
// -------------------------------------------------------
function getStatusBadge(status) {
    const colors = {
        Open: "badge-open",
        "In Progress": "badge-inprogress",
        Closed: "badge-closed",
        Canceled: "badge-canceled"
    };
    return `<span class="badge ${colors[status] || ''}">${status}</span>`;
}