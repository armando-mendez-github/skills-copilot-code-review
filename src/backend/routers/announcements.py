"""Announcement management endpoints for the High School Management System API."""

from datetime import date
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..database import announcements_collection, teachers_collection

router = APIRouter(prefix="/announcements", tags=["announcements"])


class AnnouncementPayload(BaseModel):
    """Payload used to create or update announcements."""

    message: str = Field(min_length=1, max_length=280)
    end_date: str
    start_date: Optional[str] = None


def _parse_iso_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _assert_signed_in(username: Optional[str]) -> None:
    if not username:
        raise HTTPException(status_code=401, detail="Authentication required")

    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")


def _validate_dates(start_date_str: Optional[str], end_date_str: str) -> None:
    end_date = _parse_iso_date(end_date_str)
    if end_date is None:
        raise HTTPException(status_code=400, detail="end_date must use YYYY-MM-DD format")

    if start_date_str:
        start_date = _parse_iso_date(start_date_str)
        if start_date is None:
            raise HTTPException(status_code=400, detail="start_date must use YYYY-MM-DD format")
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="start_date cannot be after end_date")


def _normalize_optional_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    normalized = value.strip()
    return normalized or None


def _serialize_announcement(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc.get("_id")),
        "message": doc.get("message", ""),
        "start_date": doc.get("start_date"),
        "end_date": doc.get("end_date"),
    }


def _is_active(doc: Dict[str, Any], today: date) -> bool:
    if not doc.get("message"):
        return False

    start_date = _parse_iso_date(doc.get("start_date"))
    end_date = _parse_iso_date(doc.get("end_date"))

    if end_date is None:
        return False

    return (start_date is None or today >= start_date) and today <= end_date


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def list_announcements(
    manager_username: Optional[str] = Query(None),
) -> List[Dict[str, Any]]:
    """List all announcements for management views."""
    _assert_signed_in(manager_username)
    docs = announcements_collection.find().sort("end_date", 1)
    return [_serialize_announcement(doc) for doc in docs]


@router.get("/active", response_model=Dict[str, Any])
def get_active_announcement() -> Dict[str, Any]:
    """Get the announcement that should be displayed in the public banner."""
    today = date.today()
    active_docs = [
        doc
        for doc in announcements_collection.find()
        if _is_active(doc, today)
    ]

    if not active_docs:
        return {"message": "", "start_date": None, "end_date": None, "is_active": False}

    # Prefer the most recent active announcement by start date, then by end date.
    active_docs.sort(
        key=lambda doc: (
            doc.get("start_date") or "0000-00-00",
            doc.get("end_date") or "0000-00-00",
        ),
        reverse=True,
    )
    selected = active_docs[0]

    return {
        "id": str(selected.get("_id")),
        "message": selected.get("message", ""),
        "start_date": selected.get("start_date"),
        "end_date": selected.get("end_date"),
        "is_active": True,
    }


@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any])
def create_announcement(
    payload: AnnouncementPayload,
    manager_username: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Create a new announcement. Requires a signed-in teacher."""
    _assert_signed_in(manager_username)

    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="message cannot be empty")

    normalized_start_date = _normalize_optional_date(payload.start_date)
    _validate_dates(normalized_start_date, payload.end_date)

    doc = {
        "message": message,
        "start_date": normalized_start_date,
        "end_date": payload.end_date,
    }
    result = announcements_collection.insert_one(doc)
    doc["_id"] = result.inserted_id

    return _serialize_announcement(doc)


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    payload: AnnouncementPayload,
    manager_username: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Update an announcement. Requires a signed-in teacher."""
    _assert_signed_in(manager_username)

    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="message cannot be empty")

    normalized_start_date = _normalize_optional_date(payload.start_date)
    _validate_dates(normalized_start_date, payload.end_date)

    try:
        object_id = ObjectId(announcement_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid announcement id") from exc

    result = announcements_collection.update_one(
        {"_id": object_id},
        {
            "$set": {
                "message": message,
                "start_date": normalized_start_date,
                "end_date": payload.end_date,
            }
        },
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    updated = announcements_collection.find_one({"_id": object_id})
    if not updated:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return _serialize_announcement(updated)


@router.delete("/{announcement_id}", response_model=Dict[str, str])
def delete_announcement(
    announcement_id: str,
    manager_username: Optional[str] = Query(None),
) -> Dict[str, str]:
    """Delete an announcement. Requires a signed-in teacher."""
    _assert_signed_in(manager_username)

    try:
        object_id = ObjectId(announcement_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid announcement id") from exc

    result = announcements_collection.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted"}
