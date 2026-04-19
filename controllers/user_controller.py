from datetime import datetime, timezone
from config.mongodb import get_database
from models.user_models import User, UserLogin
from services.appwrite_service import (
    register_user_appwrite, 
    login_user_appwrite,
    get_user_profile,
    update_user_profile,
    logout_user_appwrite
)


def create_user_mongo(user: User):
    """
    Register a new user using Appwrite with MongoDB storage
    
    Args:
        user: User object with registration details
        
    Returns:
        Dictionary with registration response
    """
    return register_user_appwrite(user)


def login_user_mongo(credentials: UserLogin):
    """
    Login user using Appwrite authentication
    
    Args:
        credentials: UserLogin object with email and password
        
    Returns:
        Dictionary with login response and session data
    """
    return login_user_appwrite(credentials)


def get_user_by_id(user_id: str):
    """
    Get user profile by ID
    
    Args:
        user_id: MongoDB user ID
        
    Returns:
        Dictionary with user profile
    """
    return get_user_profile(user_id)


def update_user_by_id(user_id: str, update_data: dict):
    """
    Update user profile
    
    Args:
        user_id: MongoDB user ID
        update_data: Dictionary with fields to update
        
    Returns:
        Dictionary with update response
    """
    return update_user_profile(user_id, update_data)


def logout_user(session_id: str):
    """
    Logout user by deleting session
    
    Args:
        session_id: Appwrite session ID
        
    Returns:
        Dictionary with logout response
    """
    return logout_user_appwrite(session_id)

