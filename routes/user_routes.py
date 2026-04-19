from fastapi import APIRouter, status, Body, HTTPException, Request
from controllers.user_controller import (
    create_user_mongo, 
    login_user_mongo,
    get_user_by_id,
    update_user_by_id,
    logout_user
)
from models.user_models import User, UserLogin
from fastapi.exceptions import RequestValidationError

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: User = Body(...)):
    """
    Register a new user with Appwrite authentication and MongoDB storage
    
    Args:
        user: User object with username, email, password, user_type
        
    Returns:
        Response with user details and status
    """
    try:
        result = create_user_mongo(user)
        
        if not result.get("success", False):
            status_code = status.HTTP_409_CONFLICT if result.get("error") == "USER_ALREADY_EXISTS" else status.HTTP_400_BAD_REQUEST
            raise HTTPException(
                status_code=status_code,
                detail=result.get("message", "Registration failed")
            )
        
        return {
            "message": "User registered successfully",
            "user": {
                "user_id": result.get("user_id"),
                "appwrite_id": result.get("appwrite_id"),
                "email": result.get("email"),
                "username": result.get("username"),
                "user_type": result.get("user_type")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", status_code=status.HTTP_200_OK)
async def login_user(credentials: UserLogin = Body(...)):
    """
    Authenticate user with Appwrite
    
    Args:
        credentials: UserLogin object with email and password
        
    Returns:
        Response with session data and user information
    """
    try:
        result = login_user_mongo(credentials)
        
        if not result.get("success", False):
            error = result.get("error")
            if error in ["INVALID_CREDENTIALS", "USER_NOT_FOUND"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=result.get("message", "Invalid credentials")
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Login failed")
            )
        
        return {
            "message": "Login successful",
            "session_id": result.get("session_id"),
            "user": result.get("user")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/{user_id}", status_code=status.HTTP_200_OK)
async def get_user_profile(user_id: str):
    """
    Get user profile by ID
    
    Args:
        user_id: MongoDB user ID
        
    Returns:
        User profile data
    """
    try:
        result = get_user_by_id(user_id)
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("message", "User not found")
            )
        
        return result.get("user")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile/{user_id}", status_code=status.HTTP_200_OK)
async def update_user_profile(user_id: str, update_data: dict = Body(...)):
    """
    Update user profile
    
    Args:
        user_id: MongoDB user ID
        update_data: Dictionary with fields to update
        
    Returns:
        Update confirmation
    """
    try:
        result = update_user_by_id(user_id, update_data)
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Update failed")
            )
        
        return {
            "message": result.get("message"),
            "user_id": user_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(session_data: dict = Body(...)):
    """
    Logout user and delete session
    
    Args:
        session_data: Dictionary with session_id
        
    Returns:
        Logout confirmation
    """
    try:
        session_id = session_data.get("session_id")
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="session_id is required"
            )
        
        result = logout_user(session_id)
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Logout failed")
            )
        
        return {
            "message": result.get("message")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

