import os
import shutil
from fastapi import FastAPI, Depends, Form, HTTPException, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# ==========================================
# 1. INITIALIZE APP & FOLDERS
# ==========================================
os.makedirs("uploads", exist_ok=True)

app = FastAPI(title="2DA Tricycle Ride-Hailing API")
app.mount("/web", StaticFiles(directory=".", html=True), name="web")

# ==========================================
# 2. DATABASE SETUP
# ==========================================
DATABASE_URL = "sqlite:///./2da.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String)  # 'passenger' or 'driver'
    full_name = Column(String)
    address = Column(String)
    whatsapp_number = Column(String)
    toda_number = Column(String, nullable=True)
    gcash_account = Column(String, nullable=True)
    toda_id_path = Column(String, nullable=True)

class RideRequest(Base):
    __tablename__ = "ride_requests"
    id = Column(Integer, primary_key=True, index=True)
    passenger_name = Column(String, index=True)
    pickup_location = Column(String)
    dropoff_location = Column(String)
    service_type = Column(String, nullable=True) 
    fare = Column(String, nullable=True)         
    status = Column(String, default="pending")
    driver_name = Column(String, nullable=True)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 4. PYDANTIC SCHEMAS
# ==========================================
class RideRequestCreate(BaseModel):
    passenger_name: str
    pickup_location: str
    dropoff_location: str
    service_type: str = "PASSENGER"
    fare: str = "₱0.00"

class AcceptRideSchema(BaseModel):
    driver_name: str

# ==========================================
# 5. API ENDPOINTS
# ==========================================
@app.get("/")
def read_root():
    # Redirect immediately to login
    return RedirectResponse(url="/web/login.html", status_code=303)

# --- ONE COMBINED LOGIN ROUTE ---
@app.post("/login")
def login_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # 1. Check for Master Admin FIRST
    if username == "masterom" and password == "qZ82118@@":
        response = RedirectResponse(url="/web/admin_dashboard.html", status_code=303)
        response.set_cookie(key="admin_session", value="masterom_active")
        return response

    # 2. Check Database for Passenger or Driver
    user = db.query(User).filter(User.username == username, User.password == password).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    # 3. Route to the correct Dashboard
    if user.role == "driver":
        response = RedirectResponse(url="/web/driver_dashboard.html", status_code=303)
    else:
        # If it's a passenger, go directly to booking!
        response = RedirectResponse(url="/web/booking.html", status_code=303)
        
    # 4. Set frontend Cookies
    display_name = user.full_name if user.full_name else user.username
    response.set_cookie(key="passenger_name", value=display_name)
    if user.role == "driver":
        response.set_cookie(key="driver_name", value=display_name)
    
    return response

@app.post("/register-account/")
def register_account(
    role: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    address: str = Form(...),
    whatsapp_number: str = Form(...),
    toda_number: str = Form(None),
    gcash_account: str = Form(None),
    toda_id: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    file_path = None
    if role == "driver" and toda_id:
        file_path = f"uploads/{username}_{toda_id.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(toda_id.file, buffer)

    new_user = User(
        username=username, 
        password=password, 
        role=role, 
        full_name=full_name,
        address=address,
        whatsapp_number=whatsapp_number,
        toda_number=toda_number,
        gcash_account=gcash_account,
        toda_id_path=file_path
    )
    db.add(new_user)
    db.commit()
    
    return RedirectResponse(url="/web/login.html", status_code=303)

# --- Ride Management ---
@app.post("/request-ride/")
def create_ride_request(request: RideRequestCreate, db: Session = Depends(get_db)):
    new_ride = RideRequest(
        passenger_name=request.passenger_name,
        pickup_location=request.pickup_location,
        dropoff_location=request.dropoff_location,
        service_type=request.service_type,
        fare=request.fare,
        status="pending"
    )
    db.add(new_ride)
    db.commit()
    db.refresh(new_ride)
    return {"message": "Ride requested successfully", "id": new_ride.id}

@app.post("/accept-ride/{ride_id}")
def accept_ride(ride_id: int, request: AcceptRideSchema, db: Session = Depends(get_db)):
    ride = db.query(RideRequest).filter(RideRequest.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    ride.status = "accepted"
    ride.driver_name = request.driver_name
    db.commit()
    db.refresh(ride)
    return {"message": "Ride accepted successfully!", "ride_id": ride.id}

@app.post("/complete-ride/{ride_id}")
def complete_ride(ride_id: int, db: Session = Depends(get_db)):
    ride = db.query(RideRequest).filter(RideRequest.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    ride.status = "completed"
    db.commit()
    return {"message": "Ride completed successfully", "id": ride.id}

@app.post("/pay-ride/{ride_id}")
def pay_ride(ride_id: int, db: Session = Depends(get_db)):
    ride = db.query(RideRequest).filter(RideRequest.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    ride.status = "paid"
    db.commit()
    return {"message": "Payment confirmed", "id": ride.id}

@app.get("/ride-status/{ride_id}")
def check_ride_status(ride_id: int, db: Session = Depends(get_db)):
    ride = db.query(RideRequest).filter(RideRequest.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    return {"status": ride.status, "driver_name": ride.driver_name}

@app.get("/pending-rides/")
def get_pending_rides(db: Session = Depends(get_db)):
    return db.query(RideRequest).all()

@app.get("/api/rides")
def get_available_rides(db: Session = Depends(get_db)):
    return db.query(RideRequest).all()
