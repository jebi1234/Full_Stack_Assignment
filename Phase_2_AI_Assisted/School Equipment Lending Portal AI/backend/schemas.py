# File: backend/schemas.py

from pydantic import BaseModel
from typing import Optional
from datetime import date # Make sure this is imported

# --- User Schemas ---

class UserCreate(BaseModel):
    username: str
    password: str
    role: str  # 'student', 'staff', or 'admin'

class User(BaseModel):
    user_id: int
    username: str
    role: str

    class Config:
        from_attributes = True

# --- Auth Schemas ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- Equipment Schemas ---

class EquipmentBase(BaseModel):
    name: str
    category: str
    condition: str
    total_quantity: int
    status: Optional[str] = "available"

class EquipmentCreate(EquipmentBase):
    pass 

class Equipment(EquipmentBase):
    equipment_id: int
    available_quantity: int 

    class Config:
        from_attributes = True

# --- Repair Schemas ---

class RepairBase(BaseModel):
    equipment_id: int
    description: str

class RepairCreate(RepairBase):
    pass

class Repair(RepairBase):
    repair_id: int
    reported_by_user_id: int
    report_date: date
    repair_status: str
    completed_date: Optional[date] = None

    class Config:
        from_attributes = True

# --- Request Schemas ---

class RequestBase(BaseModel):
    equipment_id: int
    borrow_date: date
    expected_return_date: date

class RequestCreate(RequestBase):
    pass  

class Request(RequestBase):
    request_id: int
    user_id: int
    status: str
    request_date: date
    actual_return_date: Optional[date] = None
    approved_by_user_id: Optional[int] = None

    class Config:
        from_attributes = True

# --- Analytics Schemas ---

class UsageAnalytics(BaseModel):
    equipment_id: int
    name: str
    request_count: int

    class Config:
        from_attributes = True


class RequestApprove(BaseModel):
    # Admin must provide the official return date
    expected_return_date: date