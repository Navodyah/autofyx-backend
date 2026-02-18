# controllers/user_profile_controller.py (Updated for sync)
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from bson import ObjectId
from config.mongodb import get_database  # Use your existing sync DB

def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user profile by user_id (sync version)"""
    db = get_database()

    user = db["users"].find_one({"_id": ObjectId(user_id)})
    if not user:
        return None

    profile = db["user_profiles"].find_one({"user_id": user_id})

    return {
        "_id": str(user["_id"]),
        "username": user.get("username"),
        "email": user.get("email"),
        "user_type": user.get("user_type", "user"),
        "created_at": user.get("created_at"),
        "profile": profile if profile else {}
    }

def update_user_profile(user_id: str, profile_data: Dict[str, Any]) -> Dict[str, str]:
    """Update or create user profile (sync version)"""
    db = get_database()

    user = db["users"].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise ValueError("User not found")

    profile_doc = {
        "user_id": user_id,
        **profile_data,
        "updated_at": datetime.now(timezone.utc)
    }

    result = db["user_profiles"].update_one(
        {"user_id": user_id},
        {"$set": profile_doc, "$setOnInsert": {"created_at": datetime.now(timezone.utc)}},
        upsert=True
    )

    return {"msg": "Profile updated successfully", "modified_count": result.modified_count}

def update_basic_info(user_id: str, username: str = None, email: str = None) -> Dict[str, str]:
    """Update basic user information (sync version)"""
    db = get_database()

    update_fields = {}
    if username:
        existing = db["users"].find_one({"username": username, "_id": {"$ne": ObjectId(user_id)}})
        if existing:
            raise ValueError("Username already taken")
        update_fields["username"] = username

    if email:
        existing = db["users"].find_one({"email": email, "_id": {"$ne": ObjectId(user_id)}})
        if existing:
            raise ValueError("Email already taken")
        update_fields["email"] = email

    if update_fields:
        db["users"].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_fields}
        )

    return {"msg": "Basic information updated successfully"}

def change_password(user_id: str, current_password: str, new_password: str) -> Dict[str, str]:
    """Change user password (sync version)"""
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError

    db = get_database()
    pwd_hasher = PasswordHasher()

    user = db["users"].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise ValueError("User not found")

    try:
        pwd_hasher.verify(user["hashed_password"], current_password)
    except VerifyMismatchError:
        raise ValueError("Current password is incorrect")

    new_hashed_password = pwd_hasher.hash(new_password)

    db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"hashed_password": new_hashed_password}}
    )

    return {"msg": "Password changed successfully"}

def get_user_statistics(user_id: str) -> Dict[str, Any]:
    """Get user statistics (sync version)"""
    db = get_database()

    stats = {
        "total_comparisons": db["comparisons"].count_documents({"user_id": user_id}),
        "total_favorites": db["favorites"].count_documents({"user_id": user_id}),
        "total_searches": db["search_history"].count_documents({"user_id": user_id}),
        "profile_completeness": 0
    }

    profile = db["user_profiles"].find_one({"user_id": user_id})
    if profile:
        fields = ["monthly_income", "purpose", "area", "fuel_pref", "transmission_pref"]
        filled = sum(1 for field in fields if profile.get(field))
        stats["profile_completeness"] = int((filled / len(fields)) * 100)

    return stats
