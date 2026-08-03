from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi import FastAPI, Depends, Form, HTTPException

# 1. Initialize App
app = FastAPI(title="2DA Tricycle Ride-Hailing API")

# Serve HTML files from the current directory under the "/web" path
app.mount("/web", StaticFiles(directory=".", html=True), name="web")

# 2. Database Setup
DATABASE_URL = "sqlite:///./2da.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# You MUST define Base before using it in any class!
Base = declarative_base()


# 3. Define the SQLAlchemy Database Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String)  # 'passenger' or 'driver'
    mobile = Column(String)

class RideRequest(Base):
    __tablename__ = "ride_requests"
    id = Column(Integer, primary_key=True, index=True)
    passenger_name = Column(String)
    pickup_location = Column(String)
    dropoff_location = Column(String)


# 4. Define the Pydantic Schema (Data Validation)
class RideRequestCreate(BaseModel):
    passenger_name: str
    pickup_location: str
    dropoff_location: str


# Initialize Database (Creates tables based on models above)
Base.metadata.create_all(bind=engine)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 5. API Endpoints
@app.get("/")
def read_root():
    # Force all new visitors to the login screen
    return RedirectResponse(url="/web/login.html")

@app.post("/register")
def register_user(
    role: str = Form(...),
    username: str = Form(...),
    mobile: str = Form(...),
    otp: str = Form(...), # Simulating OTP for now
    password: str = Form(...),
    db: Session = Depends(get_db)
):
@app.get("/api/rides")
def get_available_rides(db: Session = Depends(get_db)):
    # Fetch all ride requests from the SQLite database
    rides = db.query(RideRequest).all()
    return rides  
    # 1. Check if username already exists
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # 2. Create the new user in the database
    new_user = User(username=username, password=password, role=role, mobile=mobile)
    db.add(new_user)
    db.commit()
    
    # 3. Redirect back to login screen after successful registration
    return RedirectResponse(url="/web/login.html", status_code=303)


@app.post("/login")
def login_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # 1. Check if the user exists and the password matches
    user = db.query(User).filter(User.username == username, User.password == password).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    # 2. If login is successful, redirect to the booking page!
    return RedirectResponse(url="/web/booking.html", status_code=303)


@app.post("/request-ride/")
def create_ride_request(ride: RideRequestCreate, db: Session = Depends(get_db)):
    # Create a new database record using the data sent by the user
    new_ride = RideRequest(
        passenger_name=ride.passenger_name,
        pickup_location=ride.pickup_location,
        dropoff_location=ride.dropoff_location
    )
    # Save it to the SQLite database
    db.add(new_ride)
    db.commit()
    db.refresh(new_ride)
    
    return {"message": "Ride requested successfully!", "ride_id": new_ride.id}
