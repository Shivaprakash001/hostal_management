from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import httpx
from .config import settings

# Utility: shared async client factory
class HttpClient:
    _client: Optional[httpx.AsyncClient] = None

    @classmethod
    def client(cls) -> httpx.AsyncClient:
        if cls._client is None:
            cls._client = httpx.AsyncClient(timeout=settings.http_timeout)
        return cls._client

# ---------- Students ----------
class FindStudentByNameInput(BaseModel):
    name: str = Field(..., description="Partial or full name of the student")

async def find_student_by_name(name: str) -> List[Dict[str, Any]]:
    """Return students whose name matches (ilike)."""
    url = f"{settings.hms_api_base}/students/?name={name}"
    client = HttpClient.client()
    r = await client.get(url)
    r.raise_for_status()
    return r.json()

class CreateStudentInput(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    room_no: Optional[str] = None

async def create_student(**payload) -> Dict[str, Any]:
    url = f"{settings.hms_api_base}/students/"
    client = HttpClient.client()
    r = await client.post(url, json=payload)
    r.raise_for_status()
    return r.json()

class UpdateStudentInput(BaseModel):
    student_id: int
    data: Dict[str, Any]

async def update_student(student_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{settings.hms_api_base}/students/{student_id}"
    client = HttpClient.client()
    r = await client.put(url, json=data)
    r.raise_for_status()
    return r.json()

class DeleteStudentInput(BaseModel):
    student_id: int
    confirm: bool = Field(default=False, description="Must be true to execute deletion")

async def delete_student(student_id: int, confirm: bool = False) -> Dict[str, Any]:
    client = HttpClient.client()
    # Fetch details for potential undo and to validate existence
    get_url = f"{settings.hms_api_base}/students/{student_id}"
    get_resp = await client.get(get_url)
    if get_resp.status_code == 404:
        return {"summary": f"Student {student_id} not found.", "data": []}
    get_resp.raise_for_status()
    student_info = get_resp.json()
    if not confirm:
        return {
            "summary": f"Confirm delete student id {student_id}?",
            "data": [{"confirm": True, "student_id": student_id}],
        }
    del_url = f"{settings.hms_api_base}/students/{student_id}"
    del_resp = await client.delete(del_url)
    del_resp.raise_for_status()
    undo_payload = {
        "type": "recreate_student",
        "payload": {
            "name": student_info.get("name"),
            "room_no": student_info.get("room_no") if student_info.get("room_no") != "Unassigned" else None,
        },
    }
    return {
        "summary": f"Deleted student {student_id}.",
        "data": [{"deleted_id": student_id, "undo": undo_payload}],
    }

class ListStudentsInput(BaseModel):
    room_no: Optional[str] = Field(None, description="Filter by room number")

async def list_students(room_no: Optional[str] = None) -> List[Dict[str, Any]]:
    params = {}
    if room_no:
        params["room_no"] = room_no
    url = f"{settings.hms_api_base}/students/"
    client = HttpClient.client()
    r = await client.get(url, params=params)
    r.raise_for_status()
    return r.json()

class AssignRoomInput(BaseModel):
    student_id: int
    room_no: str

async def assign_room(student_id: int, room_no: str) -> Dict[str, Any]:
    # You may already have a dedicated endpoint. If not, treat it as update.
    return await update_student(student_id, {"room_no": room_no})

# Convenience tool: assign by student name
class AssignRoomByNameInput(BaseModel):
    student_name: str
    room_no: str

async def assign_room_by_name(student_name: str, room_no: str) -> Dict[str, Any]:
    matches = await find_student_by_name(student_name)
    if not matches:
        return {
            "summary": f"No student found for '{student_name}'.",
            "data": [],
        }
    if len(matches) > 1:
        choices = [
            {
                "id": m.get("id") or m.get("student_id"),
                "name": m.get("name"),
                "room_no": m.get("room_no") or m.get("room") or "Unassigned",
            }
            for m in matches
        ]
        return {
            "summary": f"Found {len(matches)} students named '{student_name}'. Please specify the student id to assign room {room_no}.",
            "data": choices,
        }
    student_id = matches[0].get("id") or matches[0].get("student_id")
    if not isinstance(student_id, int):
        return {
            "summary": "Matched student has no valid id.",
            "data": [],
        }
    result = await assign_room(student_id, room_no)
    return {
        "summary": f"Assigned room {room_no} to student id {student_id}.",
        "data": [result],
    }

# ---------- Rooms ----------
class CreateRoomInput(BaseModel):
    room_no: str
    capacity: int
    status: Optional[str] = Field(default="available")

async def create_room(**payload) -> Dict[str, Any]:
    url = f"{settings.hms_api_base}/rooms/"
    client = HttpClient.client()
    r = await client.post(url, json=payload)
    r.raise_for_status()
    return r.json()

class DeleteRoomInput(BaseModel):
    room_no: str
    confirm: bool = Field(default=False, description="Must be true to execute deletion")

async def delete_room(room_no: str, confirm: bool = False) -> Dict[str, Any]:
    client = HttpClient.client()
    # Fetch room for undo
    get_url = f"{settings.hms_api_base}/rooms/{room_no}"
    get_resp = await client.get(get_url)
    if get_resp.status_code == 404:
        return {"summary": f"Room {room_no} not found.", "data": []}
    get_resp.raise_for_status()
    room_info = get_resp.json()
    if not confirm:
        return {
            "summary": f"Confirm delete room {room_no}?",
            "data": [{"confirm": True, "room_no": room_no}],
        }
    del_url = f"{settings.hms_api_base}/rooms/"
    del_resp = await client.request("DELETE", del_url, json={"room_no": room_no})
    del_resp.raise_for_status()
    undo_payload = {
        "type": "recreate_room",
        "payload": {
            "room_no": room_info.get("room_no"),
            "capacity": room_info.get("capacity"),
            "price": room_info.get("price"),
        },
    }
    return {
        "summary": f"Deleted room {room_no}.",
        "data": [{"deleted_room": room_no, "undo": undo_payload}],
    }

class ListRoomsInput(BaseModel):
    status: Optional[str] = None

async def list_rooms(status: Optional[str] = None) -> List[Dict[str, Any]]:
    params = {}
    if status:
        params["status"] = status
    url = f"{settings.hms_api_base}/rooms/"
    client = HttpClient.client()
    r = await client.get(url, params=params)
    r.raise_for_status()
    return r.json()

class UpdateRoomInput(BaseModel):
    room_no: str
    data: Dict[str, Any]

async def update_room(room_no: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update room fields via PUT /rooms/{room_no}.
    Accepts keys: new_room_no, price, capacity.
    """
    url = f"{settings.hms_api_base}/rooms/{room_no}"
    client = HttpClient.client()
    r = await client.put(url, json=data)
    r.raise_for_status()
    return r.json()

# ---------- Payments ----------
class CreatePaymentInput(BaseModel):
    student_id: int
    amount: float
    due_date: Optional[str] = None  # ISO yyyy-mm-dd
    status: Optional[str] = Field(default="pending")

async def create_payment(**payload) -> Dict[str, Any]:
    url = f"{settings.hms_api_base}/payments/"
    client = HttpClient.client()
    r = await client.post(url, json=payload)
    r.raise_for_status()
    created = r.json()
    student_id = created.get("student_id")
    # Best-effort fetch current payments to compute insights
    summary = "Payment created."
    data = [created]
    try:
        if isinstance(student_id, int):
            all_for_student = await list_payments(student_id=student_id)
            s = _payment_insights_summary(all_for_student, student_name=None)
            if s:
                summary = f"{summary} {s}"
    except Exception:
        pass
    return {"summary": summary, "data": data}

class UpdatePaymentInput(BaseModel):
    payment_id: int
    data: Dict[str, Any]

async def update_payment(payment_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{settings.hms_api_base}/payments/{payment_id}"
    client = HttpClient.client()
    r = await client.put(url, json=data)
    r.raise_for_status()
    updated = r.json()
    student_id = updated.get("student_id")
    summary = "Payment updated."
    data_out = [updated]
    try:
        if isinstance(student_id, int):
            all_for_student = await list_payments(student_id=student_id)
            s = _payment_insights_summary(all_for_student, student_name=None)
            if s:
                summary = f"{summary} {s}"
    except Exception:
        pass
    return {"summary": summary, "data": data_out}

class DeletePaymentInput(BaseModel):
    payment_id: int

async def delete_payment(payment_id: int) -> Dict[str, Any]:
    url = f"{settings.hms_api_base}/payments/{payment_id}"
    client = HttpClient.client()
    r = await client.delete(url)
    r.raise_for_status()
    return {"ok": True, "deleted_id": payment_id}

class ListPaymentsInput(BaseModel):
    status: Optional[str] = None  # pending/paid/overdue
    student_id: Optional[int] = None

async def list_payments(status: Optional[str] = None, student_id: Optional[int] = None) -> List[Dict[str, Any]]:
    params = {}
    if status:
        params["status"] = status
    if student_id:
        params["student_id"] = student_id
    url = f"{settings.hms_api_base}/payments/"
    client = HttpClient.client()
    r = await client.get(url, params=params)
    r.raise_for_status()
    return r.json()

# Convenience: payments by student name
class PaymentsByNameInput(BaseModel):
    student_name: str

async def payments_by_name(student_name: str) -> List[Dict[str, Any]]:
    # Try direct endpoint first (exact name match)
    client = HttpClient.client()
    try:
        url = f"{settings.hms_api_base}/payments/student/{student_name}"
        r = await client.get(url)
        r.raise_for_status()
        payments = r.json()
        summary = _payment_insights_summary(payments, student_name=student_name)
        return {"summary": summary, "data": payments}
    except httpx.HTTPStatusError as e:
        if e.response is None or e.response.status_code != 404:
            raise
        # Fallback: disambiguate by ilike search and fetch by student_id
        matches = await find_student_by_name(student_name)
        if not matches:
            return {"summary": f"No student found for '{student_name}'.", "data": []}
        if len(matches) > 1:
            choices = [
                {
                    "id": m.get("id") or m.get("student_id"),
                    "name": m.get("name"),
                    "room_no": m.get("room_no") or m.get("room") or "Unassigned",
                }
                for m in matches
            ]
            return {
                "summary": f"Found {len(matches)} students matching '{student_name}'. Please specify the student id to view payments.",
                "data": choices,
            }
        sid = matches[0].get("id") or matches[0].get("student_id")
        exact_name = matches[0].get("name") or student_name
        if not isinstance(sid, int):
            return {"summary": "Matched student has no valid id.", "data": []}
        payments = await list_payments(student_id=sid)
        summary = _payment_insights_summary(payments, student_name=exact_name)
        return {"summary": summary, "data": payments}

def _payment_insights_summary(payments: List[Dict[str, Any]], student_name: Optional[str]) -> str:
    try:
        total_count = len(payments)
        paid = [p for p in payments if (p.get("status") or "").lower() == "paid"]
        pending = [p for p in payments if (p.get("status") or "").lower() == "pending"]
        overdue = [p for p in payments if (p.get("status") or "").lower() == "overdue"]
        sum_paid = sum(float(p.get("amount") or 0) for p in paid)
        sum_pending = sum(float(p.get("amount") or 0) for p in pending)
        sum_overdue = sum(float(p.get("amount") or 0) for p in overdue)
        total_amount = sum(float(p.get("amount") or 0) for p in payments)
        name_part = f"{student_name} has " if student_name else ""
        return (
            f"{name_part}{total_count} payment(s): "
            f"{len(paid)} paid (₹{int(sum_paid)}), "
            f"{len(pending)} pending (₹{int(sum_pending)}), "
            f"{len(overdue)} overdue (₹{int(sum_overdue)}). "
            f"Total ₹{int(total_amount)}."
        )
    except Exception:
        return ""

# Convenience: assign any empty room to student by name
class AssignAnyEmptyRoomByNameInput(BaseModel):
    student_name: str

async def assign_any_empty_room_by_name(student_name: str) -> Dict[str, Any]:
    matches = await find_student_by_name(student_name)
    if not matches:
        return {"summary": f"No student found for '{student_name}'.", "data": []}
    if len(matches) > 1:
        choices = [
            {
                "id": m.get("id") or m.get("student_id"),
                "name": m.get("name"),
                "room_no": m.get("room_no") or m.get("room") or "Unassigned",
            }
            for m in matches
        ]
        return {
            "summary": f"Found {len(matches)} students named '{student_name}'. Please specify the student id for room assignment.",
            "data": choices,
        }
    sid = matches[0].get("id") or matches[0].get("student_id")
    if not isinstance(sid, int):
        return {"summary": "Matched student has no valid id.", "data": []}
    rooms = await list_rooms()
    candidates: List[Dict[str, Any]] = []
    for room in rooms:
        try:
            capacity = int(room.get("capacity") or 0)
            students = room.get("students") or []
            if isinstance(students, dict):
                students = list(students.values())
            available = capacity - len(students)
            if available > 0:
                candidates.append({"room_no": room.get("room_no"), "available": available})
        except Exception:
            continue
    if not candidates:
        return {
            "summary": "No empty rooms available. Try updating capacity or freeing a room.",
            "data": [],
        }
    best = sorted(candidates, key=lambda r: r["available"], reverse=True)[0]
    result = await assign_room(sid, best["room_no"])
    return {
        "summary": f"Assigned room {best['room_no']} to student id {sid}.",
        "data": [result],
    }

# Convenience: create payment by student name
class CreatePaymentByNameInput(BaseModel):
    student_name: str
    amount: float
    status: Optional[str] = None

async def create_payment_by_name(student_name: str, amount: float, status: Optional[str] = None) -> Dict[str, Any]:
    from datetime import datetime
    url = f"{settings.hms_api_base}/payments/by-name/{student_name}"
    now = datetime.now()
    payload = {
        "amount": amount,
        "month": now.month,
        "year": now.year,
        "payment_method": "Cash"
    }
    if status:
        payload["status"] = status
    client = HttpClient.client()
    r = await client.post(url, json=payload)
    r.raise_for_status()
    created = r.json()
    # Fetch all payments for insights
    try:
        all_p = await payments_by_name(student_name)
        # payments_by_name now returns envelope
        if isinstance(all_p, dict) and "summary" in all_p:
            return {"summary": f"Payment created. {all_p['summary']}", "data": [created]}
    except Exception:
        pass
    return {"summary": "Payment created.", "data": [created]}

# Convenience: set payment status by student name (optionally one payment_id)
class SetPaymentsStatusByNameInput(BaseModel):
    student_name: str
    status: str
    payment_id: Optional[int] = None

async def set_payments_status_by_name(student_name: str, status: str, payment_id: Optional[int] = None) -> Dict[str, Any]:
    payments = await payments_by_name(student_name)
    if isinstance(payments, dict):
        # Extract list if envelope
        payments_list = payments.get("data") or []
    else:
        payments_list = payments
    if not payments_list:
        return {"summary": f"No payments found for '{student_name}'.", "data": []}
    updated: List[Dict[str, Any]] = []
    targets = [p for p in payments_list if payment_id is None or p.get("id") == payment_id]
    for p in targets:
        pid = p.get("id")
        amount = p.get("amount", 0)
        # Backend expects both amount and status in PUT
        res = await update_payment(pid, {"amount": amount, "status": status})
        updated.append(res)
    # After updates, recompute insights
    try:
        latest = await payments_by_name(student_name)
        if isinstance(latest, dict) and "summary" in latest:
            return {"summary": f"Updated {len(updated)} payment(s) to '{status}'. {latest['summary']}", "data": updated}
    except Exception:
        pass
    return {"summary": f"Updated {len(updated)} payment(s) to '{status}'.", "data": updated}

# Convenience tool: delete by student name
class DeleteStudentByNameInput(BaseModel):
    student_name: str
    confirm: bool = Field(default=False, description="Must be true to execute deletion")

async def delete_student_by_name(student_name: str, confirm: bool = False) -> Dict[str, Any]:
    matches = await find_student_by_name(student_name)
    if not matches:
        return {"summary": f"No student found for '{student_name}'.", "data": []}
    if len(matches) > 1:
        choices = [
            {
                "id": m.get("id") or m.get("student_id"),
                "name": m.get("name"),
                "room_no": m.get("room_no") or m.get("room") or "Unassigned",
            }
            for m in matches
        ]
        return {
            "summary": f"Found {len(matches)} students named '{student_name}'. Please specify the student id for deletion.",
            "data": choices,
        }
    student_id = matches[0].get("id") or matches[0].get("student_id")
    if not isinstance(student_id, int):
        return {"summary": "Matched student has no valid id.", "data": []}
    
    # Now call the regular delete_student function
    return await delete_student(student_id, confirm)