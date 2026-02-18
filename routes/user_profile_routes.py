# routes/user_profile_routes.py (Updated for sync)
from fastapi import APIRouter, Depends, HTTPException
from dependencies.auth import get_current_user
from controllers.user_profile_controller import (
    get_user_profile,
    update_user_profile,
    update_basic_info,
    change_password,
    get_user_statistics
)
from models.profile_models import UserProfileUpdate, BasicInfoUpdate, PasswordChange

router = APIRouter(prefix="/user-profile", tags=["User Profile"])

@router.get("/me")
def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's profile"""
    user_id = current_user["sub"]
    profile = get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.put("/me")
def update_my_profile(
    profile_data: UserProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update current user's profile"""
    user_id = current_user["sub"]
    result = update_user_profile(user_id, profile_data.model_dump(exclude_unset=True))
    return result

@router.put("/basic-info")
def update_my_basic_info(
    basic_info: BasicInfoUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update username or email"""
    user_id = current_user["sub"]
    try:
        result = update_basic_info(
            user_id,
            username=basic_info.username,
            email=basic_info.email
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/change-password")
def change_my_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_user)
):
    """Change user password"""
    user_id = current_user["sub"]
    try:
        result = change_password(
            user_id,
            password_data.current_password,
            password_data.new_password
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/statistics")
def get_my_statistics(current_user: dict = Depends(get_current_user)):
    """Get user statistics"""
    user_id = current_user["sub"]
    stats = get_user_statistics(user_id)
    return stats
