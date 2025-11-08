# File: backend/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

# --- 1. IMPORT THE CORS MIDDLEWARE ---
from fastapi.middleware.cors import CORSMiddleware

# Import all our different modules
import models, schemas, crud, auth
from database import SessionLocal, engine, get_db

# Create all database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- 2. DEFINE YOUR ORIGINS (THE WEBSITES YOU TRUST) ---
origins = [
    "http://localhost:3000",
]

# --- 3. ADD THE MIDDLEWARE TO YOUR APP ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow your React app
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Welcome to the School Equipment Lending Portal API!"}


# --- Auth Endpoints ---

@app.post("/register/", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)


@app.post("/token", response_model=schemas.Token)
def login_for_access_token(
    db: Session = Depends(get_db), 
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


# --- Equipment Endpoints ---

@app.post("/equipment/", response_model=schemas.Equipment)
def create_new_equipment(
    equipment: schemas.EquipmentCreate, 
    db: Session = Depends(get_db), 
    admin_user: models.User = Depends(auth.get_current_admin_user)
):
    return crud.create_equipment(db=db, equipment=equipment)


@app.put("/equipment/{equipment_id}", response_model=schemas.Equipment)
def update_existing_equipment(
    equipment_id: int,
    equipment_update: schemas.EquipmentCreate,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(auth.get_current_admin_user)
):
    db_equipment = crud.update_equipment(db, equipment_id, equipment_update)
    if db_equipment is None:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return db_equipment


@app.delete("/equipment/{equipment_id}", response_model=dict)
def delete_existing_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(auth.get_current_admin_user)
):
    if not crud.delete_equipment(db, equipment_id):
        raise HTTPException(status_code=404, detail="Equipment not found")
    return {"message": "Equipment deleted successfully"}


@app.get("/equipment/", response_model=List[schemas.Equipment])
def read_all_equipment(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    equipments = crud.get_all_equipment(db, skip=skip, limit=limit)
    return equipments


@app.get("/equipment/{equipment_id}", response_model=schemas.Equipment)
def read_single_equipment(
    equipment_id: int, 
    db: Session = Depends(get_db)
):
    db_equipment = crud.get_equipment_by_id(db, equipment_id)
    if db_equipment is None:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return db_equipment


# --- Request Endpoints ---

@app.post("/requests/", response_model=schemas.Request)
def create_new_request(
    request: schemas.RequestCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_request = crud.create_equipment_request(db, request, current_user.user_id)
    if db_request is None:
        raise HTTPException(status_code=400, detail="Equipment not available or not found")
    return db_request


@app.get("/requests/my/", response_model=List[schemas.Request])
def get_my_requests(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return crud.get_requests_by_user(db, user_id=current_user.user_id)


@app.get("/requests/pending/", response_model=List[schemas.Request])
def get_pending_requests(
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(auth.get_current_admin_user)
):
    return crud.get_all_pending_requests(db)


# File: backend/main.py
# ... (find and replace this endpoint function) ...

# --- MODIFIED ENDPOINT ---
@app.post("/requests/{request_id}/approve", response_model=schemas.Request)
def approve_pending_request(
    request_id: int,
    # --- NEW: It now requires a JSON body with the approval data ---
    approval_data: schemas.RequestApprove,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(auth.get_current_admin_user)
):
    """
    Approve a borrow request. (Admin Only)
    The admin must provide the official return date.
    """
    # --- UPDATED: Pass the new data to the crud function ---
    db_request = crud.approve_request(db, request_id, admin_user.user_id, approval_data)
    
    if db_request is None:
        raise HTTPException(status_code=404, detail="Request not found, not pending, or equipment unavailable")
    return db_request

# ... (keep all your other endpoints) ...


@app.post("/requests/{request_id}/reject", response_model=schemas.Request)
def reject_pending_request(
    request_id: int,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(auth.get_current_admin_user)
):
    db_request = crud.reject_request(db, request_id, admin_user.user_id)
    if db_request is None:
        raise HTTPException(status_code=404, detail="Request not found or not pending")
    return db_request


@app.post("/requests/{request_id}/return", response_model=schemas.Request)
def return_approved_equipment(
    request_id: int,
    db: Session = Depends(get_db),
    # --- CHANGE: We get the current_user, NOT just the admin ---
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Mark an approved item as returned.
    Accessible by Admins OR the user who made the request.
    """
    db_request = crud.get_request_by_id(db, request_id)

    if not db_request:
        raise HTTPException(status_code=404, detail="Request not found")

    # --- NEW SECURITY CHECK ---
    # Allow if user is an admin OR if the user_id on the request matches the logged-in user
    if current_user.role != "admin" and db_request.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to return this item")

    # Call the crud function (which is already correct)
    updated_request = crud.return_equipment(db, request_id)
    
    if updated_request is None:
        raise HTTPException(status_code=400, detail="Request not in 'approved' state")
    
    return updated_request


# --- Repair Log Endpoints ---

@app.post("/equipment/{equipment_id}/report-damage", response_model=schemas.Repair)
def report_equipment_damage(
    equipment_id: int,
    report: schemas.RepairCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if report.equipment_id != equipment_id:
        raise HTTPException(status_code=400, detail="Equipment ID in URL and body do not match")
        
    db_report = crud.create_repair_report(db, report, current_user.user_id)
    if db_report is None:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return db_report


@app.get("/repairs/", response_model=List[schemas.Repair])
def get_all_repair_reports(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(auth.get_current_admin_user)
):
    return crud.get_all_repairs(db, skip=skip, limit=limit)


@app.post("/repairs/{repair_id}/complete", response_model=schemas.Repair)
def complete_repair_report(
    repair_id: int,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(auth.get_current_admin_user)
):
    db_report = crud.complete_repair(db, repair_id)
    if db_report is None:
        raise HTTPException(status_code=404, detail="Repair report not found or not pending")
    return db_report


# --- History & Analytics Endpoints ---

@app.get("/users/{user_id}/requests", response_model=List[schemas.Request])
def read_user_requests(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(auth.get_current_admin_user)
):
    requests = crud.get_requests_by_user_admin(db, user_id=user_id)
    if requests is None:
        raise HTTPException(status_code=404, detail="User not found")
    return requests


@app.get("/analytics/usage", response_model=List[schemas.UsageAnalytics])
def get_equipment_usage_analytics(
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(auth.get_current_admin_user)
):
    return crud.get_usage_analytics(db)


# --- Overdue Tracking Endpoints ---

@app.get("/requests/overdue/", response_model=List[schemas.Request])
def get_overdue_requests(
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(auth.get_current_admin_user)
):
    return crud.get_all_overdue_items(db)


@app.post("/requests/check-overdue/", response_model=List[schemas.Request])
def trigger_overdue_check(
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(auth.get_current_admin_user)
):
    return crud.check_for_overdue_items(db)

