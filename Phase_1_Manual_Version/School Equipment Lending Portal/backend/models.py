# File: backend/models.py

from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from database import Base

# 1. Users Table Model
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, index=True) # 'student', 'staff', 'admin'

    # --- THIS IS THE CORRECT AND FINAL FIX ---
    # We use 'primaryjoin' to explicitly state the join condition
    # for each relationship, using strings to avoid errors.
    
    requests = relationship(
        "Request", 
        back_populates="user",
        # Join when this User's user_id matches the Request's user_id
        primaryjoin="User.user_id == Request.user_id"
    )
    
    approved_requests = relationship(
        "Request", 
        back_populates="approver",
        # Join when this User's user_id matches the Request's approved_by_user_id
        primaryjoin="User.user_id == Request.approved_by_user_id"
    )
    # --- END FIX ---

    repairs_reported = relationship("Repair", back_populates="reporter")


# 2. Equipment Table Model
class Equipment(Base):
    __tablename__ = "equipment"

    equipment_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String, index=True)
    condition = Column(String)
    total_quantity = Column(Integer)
    available_quantity = Column(Integer)
    status = Column(String, default="available") # 'available', 'on_loan', 'under_repair'

    requests = relationship("Request", back_populates="equipment")
    repairs = relationship("Repair", back_populates="equipment")


# 3. Requests Table Model
class Request(Base):
    __tablename__ = "requests"

    request_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    equipment_id = Column(Integer, ForeignKey("equipment.equipment_id"))
    
    status = Column(String, index=True, default="pending") # 'pending', 'approved', 'rejected', 'returned', 'overdue'
    request_date = Column(Date)
    borrow_date = Column(Date)
    expected_return_date = Column(Date)
    actual_return_date = Column(Date, nullable=True) 
    
    approved_by_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    
    # This side has always been correct.
    # We still need foreign_keys here to link back.
    user = relationship("User", back_populates="requests", foreign_keys=[user_id])
    
    equipment = relationship("Equipment", back_populates="requests")

    approver = relationship(
        "User", 
        back_populates="approved_requests", 
        foreign_keys=[approved_by_user_id]
    )


# 4. Repairs Table Model
class Repair(Base):
    __tablename__ = "repairs"

    repair_id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.equipment_id"))
    reported_by_user_id = Column(Integer, ForeignKey("users.user_id"))
    
    description = Column(Text)
    report_date = Column(Date)
    repair_status = Column(String, default="pending") # 'pending', 'in_progress', 'completed'
    completed_date = Column(Date, nullable=True)

    equipment = relationship("Equipment", back_populates="repairs")
    reporter = relationship("User", back_populates="repairs_reported")