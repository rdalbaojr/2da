from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String
# ... rest of your imports ...

# 1. Database Setup
DATABASE_URL = "sqlite:///./2da.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Define the SQLAlchemy Database Model
class RideRequest(Base):
    __tablename__ = "ride_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    passenger_name = Column(String, index=True)
    pickup_location = Column(String)
    dropoff_location = Column(String)
    status = Column(String, default="pending")

# 3. Define the Pydantic Schema (Data Validation)
class RideRequestCreate(BaseModel):
    passenger_name: str
    pickup_location: str
    dropoff_location: str

# 4. Initialize Database and App
Base.metadata.create_all(bind=engine)
app = FastAPI(title="2DA Tricycle Ride-Hailing API")

# NEW: Tell FastAPI to serve your HTML files from the current directory
app.mount("/web", StaticFiles(directory=".", html=True), name="web")

# 5. API Endpoints
@app.get("/")
def read_root():
    return {"message": "Welcome to the 2DA API. The database is active!"}

# NEW: Endpoint to create a ride request
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
