from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database
from pymongo import MongoClient

app = FastAPI()

# Define Pydantic model for user registration
class UserRegistration(BaseModel):
    first_name: str
    email: str
    password: str
    phone: str
    profile_picture: str

# PostgreSQL database setup
DATABASE_URL = "postgresql://postgres:Opensona@123@localhost:5432/template1"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define PostgreSQL User model
class PostgreSQLUser(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    phone = Column(String)

# Create MongoDB connection
mongo_client = MongoClient("mongodb://localhost:27017")
mongo_db = mongo_client["mydb"]
mongo_collection = mongo_db["user_profiles"]

# Endpoint for user registration
@app.post("/register/")
async def register_user(user: UserRegistration):
    async with Database(DATABASE_URL) as database:
        await database.execute(PostgreSQLUser.__table__.insert().values(
            first_name=user.first_name,
            email=user.email,
            password=user.password,
            phone=user.phone,
        ))
    
    # Save profile picture in MongoDB
    profile_data = {
        "user_id": user.email, # You can use a unique user_id
        "profile_picture": user.profile_picture,
    }
    mongo_collection.insert_one(profile_data)

    return {"message": "User registered successfully"}

# Endpoint to get user details
@app.get("/user/{user_id}")
async def get_user(user_id: str):
    # Fetch user details from PostgreSQL
    async with Database(DATABASE_URL) as database:
        user_details = await database.fetch_one(
            PostgreSQLUser.__table__.select().where(PostgreSQLUser.email == user_id)
        )
    
    # Fetch user profile picture from MongoDB
    profile_data = mongo_collection.find_one({"user_id": user_id})

    if not user_details or not profile_data:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user_id,
        "first_name": user_details.first_name,
        "email": user_details.email,
        "phone": user_details.phone,
        "profile_picture": profile_data.get("profile_picture")
    }
