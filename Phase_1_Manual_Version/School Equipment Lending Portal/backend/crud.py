# File: backend/crud.py

from sqlalchemy.orm import Session
from sqlalchemy import func # Import func
import models, schemas, auth
from datetime import date # Import date

# --- User CRUD Functions ---

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username, 
        hashed_password=hashed_password, 
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Equipment CRUD Functions ---

def create_equipment(db: Session, equipment: schemas.EquipmentCreate):
    db_equipment = models.Equipment(
        **equipment.model_dump(),
        available_quantity=equipment.total_quantity 
    )
    db.add(db_equipment)
    db.commit()
    db.refresh(db_equipment)
    return db_equipment

def get_equipment_by_id(db: Session, equipment_id: int):
    return db.query(models.Equipment).filter(models.Equipment.equipment_id == equipment_id).first()

def get_all_equipment(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Equipment).offset(skip).limit(limit).all()

def update_equipment(db: Session, equipment_id: int, equipment_update: schemas.EquipmentCreate):
    db_equipment = get_equipment_by_id(db, equipment_id)
    if not db_equipment:
        return None
    
    update_data = equipment_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_equipment, key, value)
    
    if "total_quantity" in update_data:
        on_loan = db_equipment.total_quantity - db_equipment.available_quantity
        db_equipment.available_quantity = db_equipment.total_quantity - on_loan
    
    db.commit()
    db.refresh(db_equipment)
    return db_equipment

def delete_equipment(db: Session, equipment_id: int):
    db_equipment = get_equipment_by_id(db, equipment_id)
    if db_equipment:
        db.delete(db_equipment)
        db.commit()
        return True
    return False

# --- Request CRUD Functions ---

def create_equipment_request(db: Session, request: schemas.RequestCreate, user_id: int):
    db_equipment = get_equipment_by_id(db, request.equipment_id)
    if not db_equipment or db_equipment.available_quantity <= 0:
        return None  

    db_request = models.Request(
        **request.model_dump(),
        user_id=user_id,
        request_date=date.today(), 
        status="pending"
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

def get_request_by_id(db: Session, request_id: int):
    return db.query(models.Request).filter(models.Request.request_id == request_id).first()

def get_requests_by_user(db: Session, user_id: int):
    return db.query(models.Request).filter(models.Request.user_id == user_id).all()

def get_all_pending_requests(db: Session):
    return db.query(models.Request).filter(models.Request.status == "pending").all()

# File: backend/crud.py
# ... (find and replace this function) ...

# --- MODIFIED FUNCTION ---
def approve_request(db: Session, request_id: int, admin_user_id: int, approval_data: schemas.RequestApprove):
    """
    Approves a pending request.
    - Updates request status to 'approved'.
    - Updates who approved it.
    - SETS THE OFFICIAL RETURN DATE from the admin.
    - Decrements the available_quantity of the equipment.
    """
    db_request = get_request_by_id(db, request_id)
    if not db_request or db_request.status != "pending":
        return None  # Request not found or not pending
    
    db_equipment = get_equipment_by_id(db, db_request.equipment_id)
    if not db_equipment or db_equipment.available_quantity <= 0:
        return None # Equipment not found or none available
    
    # Approve the request
    db_request.status = "approved"
    db_request.approved_by_user_id = admin_user_id
    
    # --- NEW: Set the return date from the admin's input ---
    db_request.expected_return_date = approval_data.expected_return_date
    
    # Update equipment quantity
    db_equipment.available_quantity -= 1
    
    db.commit()
    db.refresh(db_request)
    return db_request

# ... (keep all your other functions) ...

def reject_request(db: Session, request_id: int, admin_user_id: int):
    db_request = get_request_by_id(db, request_id)
    if not db_request or db_request.status != "pending":
        return None 
    
    db_request.status = "rejected"
    db_request.approved_by_user_id = admin_user_id 
    
    db.commit()
    db.refresh(db_request)
    return db_request

def return_equipment(db: Session, request_id: int):
    db_request = get_request_by_id(db, request_id)
    
    if not db_request or db_request.status != "approved":
        return None  
    
    db_equipment = get_equipment_by_id(db, db_request.equipment_id)
    if not db_equipment:
        return None 
    
    db_request.status = "returned"
    db_request.actual_return_date = date.today()
    db_equipment.available_quantity += 1
    
    db.commit()
    db.refresh(db_request)
    return db_request

# --- Repair Log CRUD Functions ---

def create_repair_report(db: Session, report: schemas.RepairCreate, user_id: int):
    db_equipment = get_equipment_by_id(db, report.equipment_id)
    if not db_equipment:
        return None  

    db_report = models.Repair(
        equipment_id=report.equipment_id,
        description=report.description,
        reported_by_user_id=user_id,
        report_date=date.today(),
        repair_status="pending"
    )
    
    db_equipment.status = "under_repair"
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

def get_all_repairs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Repair).offset(skip).limit(limit).all()

def complete_repair(db: Session, repair_id: int):
    db_report = db.query(models.Repair).filter(models.Repair.repair_id == repair_id).first()
    if not db_report or db_report.repair_status != "pending":
        return None 
    
    db_equipment = get_equipment_by_id(db, db_report.equipment_id)
    if not db_equipment:
        return None

    db_report.repair_status = "completed"
    db_report.completed_date = date.today()
    db_equipment.status = "available"
    
    db.commit()
    db.refresh(db_report)
    return db_report

# --- History & Analytics CRUD ---

def get_requests_by_user_admin(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        return None 
    
    return db.query(models.Request).filter(models.Request.user_id == user_id).all()


def get_usage_analytics(db: Session):
    return db.query(
        models.Equipment.equipment_id,
        models.Equipment.name,
        func.count(models.Request.request_id).label("request_count")
    ).join(
        models.Request, models.Equipment.equipment_id == models.Request.equipment_id
    ).group_by(
        models.Equipment.equipment_id, models.Equipment.name
    ).order_by(
        func.count(models.Request.request_id).desc()
    ).all()

# --- Due Date & Overdue Tracking ---

def check_for_overdue_items(db: Session):
    today = date.today()
    
    overdue_requests = db.query(models.Request).filter(
        models.Request.status == "approved",
        models.Request.expected_return_date < today
    ).all()
    
    if not overdue_requests:
        return [] 

    for request in overdue_requests:
        request.status = "overdue"
    
    db.commit()
    return overdue_requests

def get_all_overdue_items(db: Session):
    return db.query(models.Request).filter(models.Request.status == "overdue").all()
