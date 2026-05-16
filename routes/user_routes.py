from fastapi import APIRouter, status, Body, HTTPException, Request
from controllers.user_controller import (
    create_user_mongo, 
    login_user_mongo,
    get_user_by_id,
    update_user_by_id,
    logout_user,
    change_user_password,
    delete_user_account,
)
from models.user_models import User, UserLogin
from fastapi.exceptions import RequestValidationError
from config.mongodb import get_database

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/all", status_code=status.HTTP_200_OK)
async def get_all_users():
    """Admin: fetch all users from MongoDB."""
    try:
        db = get_database()
        users_cursor = db["users"].find({}, {
            "_id": 1, "username": 1, "email": 1,
            "user_type": 1, "created_at": 1,
            "appwrite_id": 1, "is_banned": 1,
            "profile_image_url": 1,
        })
        users = []
        for u in users_cursor:
            u["_id"] = str(u["_id"])
            if u.get("created_at"):
                u["created_at"] = str(u["created_at"])
            users.append(u)
        return {"users": users, "total": len(users)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/ban/{user_id}", status_code=status.HTTP_200_OK)
async def toggle_ban_user(user_id: str, body: dict = Body(...)):
    """Admin: ban or unban a user."""
    try:
        from bson import ObjectId
        db = get_database()
        banned = body.get("is_banned", True)
        db["users"].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_banned": banned}}
        )
        return {"message": f"User {'banned' if banned else 'unbanned'} successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity/{user_id}", status_code=status.HTTP_200_OK)
async def get_user_activity(user_id: str):
    """Admin: get a user's recent activity."""
    try:
        db = get_database()
        searches = list(db["search_history"].find({"user_id": user_id}).sort("timestamp", -1).limit(10))
        comparisons = list(db["comparisons"].find({"user_id": user_id}).sort("created_at", -1).limit(10))
        logins = list(db["login_history"].find({"user_id": user_id}).sort("timestamp", -1).limit(10))
        for doc in searches + comparisons + logins:
            doc["_id"] = str(doc["_id"])
            for key in ["timestamp", "created_at"]:
                if doc.get(key):
                    doc[key] = str(doc[key])
        return {"searches": searches, "comparisons": comparisons, "logins": logins}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



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


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(body: dict = Body(...)):
    """
    Change user password after verifying the current one.
    Requires: appwrite_id, email, current_password, new_password
    """
    try:
        appwrite_id    = body.get("appwrite_id", "")
        email          = body.get("email", "")
        current_pw     = body.get("current_password", "")
        new_pw         = body.get("new_password", "")

        if not all([appwrite_id, email, current_pw, new_pw]):
            raise HTTPException(status_code=400, detail="appwrite_id, email, current_password and new_password are required.")
        if len(new_pw) < 8:
            raise HTTPException(status_code=400, detail="New password must be at least 8 characters.")

        result = change_user_password(appwrite_id, email, current_pw, new_pw)
        if not result.get("success"):
            error = result.get("error", "")
            status_code = 401 if error == "WRONG_PASSWORD" else 400
            raise HTTPException(status_code=status_code, detail=result.get("message", "Password change failed."))

        return {"message": result["message"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete", status_code=status.HTTP_200_OK)
async def delete_account(body: dict = Body(...)):
    """
    Permanently delete a user account from Appwrite and MongoDB.
    Requires: appwrite_id, user_id (MongoDB ObjectId string)
    """
    try:
        appwrite_id = body.get("appwrite_id", "")
        user_id     = body.get("user_id", "")

        if not appwrite_id:
            raise HTTPException(status_code=400, detail="appwrite_id is required.")

        result = delete_user_account(appwrite_id, user_id)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message", "Delete failed."))

        return {"message": result["message"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
