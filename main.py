from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

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
