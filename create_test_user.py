#!/usr/bin/env python
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database import SessionLocal, engine
from models.user import User
from passlib.context import CryptContext

# Create tables if they don't exist
from database import Base
Base.metadata.create_all(bind=engine)

# Password hashing (same as in auth.py)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_test_user():
    # Create database session
    db = SessionLocal()
    
    try:
        # Test user details
        test_username = "testuser"
        test_email = "test@example.com"
        test_password = "TestPassword123!"
        
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == test_username) | (User.email == test_email)
        ).first()
        
        if existing_user:
            print(f'User with username {test_username} or email {test_email} already exists')
            print(f'Existing user ID: {existing_user.id}')
            return existing_user.id
        
        # Hash password and create user
        hashed_password = pwd_context.hash(test_password)
        db_user = User(
            username=test_username,
            email=test_email,
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        print(f'Test user created successfully!')
        print(f'Username: {test_username}')
        print(f'Email: {test_email}')
        print(f'Password: {test_password}')
        print(f'User ID: {db_user.id}')
        
        return db_user.id
        
    except Exception as e:
        print(f'Error creating user: {e}')
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()