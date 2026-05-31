"""
Authentication endpoints for the High School Management System API
"""

import secrets
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException

from ..database import teachers_collection, verify_password

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

active_sessions: Dict[str, str] = {}


def get_teacher_from_session_token(session_token: Optional[str]) -> Dict[str, Any]:
    """Validate a server-issued session token and return the teacher document."""
    if not session_token:
        raise HTTPException(status_code=401, detail="Authentication required")

    username = active_sessions.get(session_token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid session")

    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        active_sessions.pop(session_token, None)
        raise HTTPException(status_code=401, detail="Invalid session")

    return teacher


@router.post("/login")
def login(username: str, password: str) -> Dict[str, Any]:
    """Login a teacher account"""
    # Find the teacher in the database
    teacher = teachers_collection.find_one({"_id": username})

    # Verify password using Argon2 verifier from database.py
    if not teacher or not verify_password(teacher.get("password", ""), password):
        raise HTTPException(
            status_code=401, detail="Invalid username or password")

    session_token = secrets.token_urlsafe(32)
    active_sessions[session_token] = teacher["username"]

    # Return teacher information (excluding password)
    return {
        "username": teacher["username"],
        "display_name": teacher["display_name"],
        "role": teacher["role"],
        "session_token": session_token,
    }


@router.get("/check-session")
def check_session(
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token")
) -> Dict[str, Any]:
    """Check if a server-issued session token is valid."""
    teacher = get_teacher_from_session_token(x_session_token)

    return {
        "username": teacher["username"],
        "display_name": teacher["display_name"],
        "role": teacher["role"],
        "session_token": x_session_token,
    }
