"""
Appwrite authentication service
Handles user registration, login, and profile management with MongoDB storage
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from config.mongodb import get_database
from models.user_models import User, UserLogin
from config.appwrite import get_users_service, get_appwrite_client
from appwrite.exception import AppwriteException

_USER_INDEXES_READY = False


def _normalize_email(value: str) -> str:
    return value.strip().lower()

def _extract_value(source: Any, keys: list[str]) -> str:
    if source is None:
        return ""

    if isinstance(source, dict):
        for key in keys:
            value = source.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()

    source_dict = getattr(source, "__dict__", {}) or {}
    if isinstance(source_dict, dict):
        for key in keys:
            value = source_dict.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()

    for key in keys:
        value = getattr(source, key, None)
        if value is not None and str(value).strip():
            return str(value).strip()

    return ""


def _extract_id(value: Any) -> str:
    """Support both dict and model-object responses from Appwrite SDK."""
    return _extract_value(value, ["$id", "id"])


def _extract_session_user_id(value: Any) -> str:
    return _extract_value(value, ["userId", "user_id", "$userId"])


def _ensure_user_indexes(users_collection) -> None:
    global _USER_INDEXES_READY
    if _USER_INDEXES_READY:
        return

    # Non-unique indexes avoid migration failures when legacy duplicate docs exist.
    users_collection.create_index("email")
    users_collection.create_index("appwrite_id")
    users_collection.create_index("identity_key")
    _USER_INDEXES_READY = True


def _find_mongo_user(users_collection, email: str, appwrite_id: str = "") -> Optional[Dict]:
    if appwrite_id:
        user_doc = users_collection.find_one({"appwrite_id": appwrite_id})
        if user_doc:
            return user_doc
    return users_collection.find_one({"email": email})


def _find_appwrite_user_id_by_email(email: str) -> str:
    try:
        users_service = get_users_service()
        result = users_service.list(search=email)
        users = []

        if isinstance(result, dict):
            users = result.get("users") or []
        else:
            result_dict = getattr(result, "__dict__", {}) or {}
            users = result_dict.get("users") or getattr(result, "users", []) or []

        target_email = _normalize_email(email)
        for user_item in users:
            candidate_email = _normalize_email(_extract_value(user_item, ["email"]))
            if candidate_email == target_email:
                candidate_id = _extract_id(user_item)
                if candidate_id:
                    return candidate_id
    except Exception:
        return ""
    return ""


def _upsert_mongo_user(
    *,
    email: str,
    username: str,
    user_type: str = "user",
    appwrite_id: str = "",
) -> Dict:
    """Create or update MongoDB profile for an Appwrite-authenticated user."""
    db = get_database()
    users_collection = db["users"]
    _ensure_user_indexes(users_collection)

    normalized_email = _normalize_email(email)
    normalized_appwrite_id = appwrite_id.strip()
    normalized_user_type = (user_type or "user").strip().lower()
    normalized_username = (username or normalized_email.split("@")[0]).strip() or normalized_email

    now = datetime.now(timezone.utc)
    selector = {"email": normalized_email}
    if normalized_appwrite_id:
        selector = {"$or": [{"appwrite_id": normalized_appwrite_id}, {"email": normalized_email}]}

    set_payload = {
        "updated_at": now,
        "username": normalized_username,
        "email": normalized_email,
        "user_type": normalized_user_type,
        "auth_provider": "appwrite",
        "identity_key": normalized_appwrite_id or normalized_email,
    }
    if normalized_appwrite_id:
        set_payload["appwrite_id"] = normalized_appwrite_id

    users_collection.update_one(
        selector,
        {
            "$set": set_payload,
            "$setOnInsert": {
                "profile_completed": False,
                "preferences": {},
                "created_at": now,
            },
        },
        upsert=True,
    )

    user_doc = _find_mongo_user(
        users_collection=users_collection,
        email=normalized_email,
        appwrite_id=normalized_appwrite_id,
    )
    mongo_id = str(user_doc["_id"]) if user_doc and "_id" in user_doc else ""

    return {"mongo_id": mongo_id, "user_doc": user_doc}


def register_user_appwrite(user: User) -> Dict:
    """
    Register a new user with Appwrite and store profile in MongoDB
    
    Args:
        user: User object with username, email, password, user_type
        
    Returns:
        Dict with registration status and user details
    """
    try:
        normalized_email = _normalize_email(str(user.email))
        appwrite_id = (user.appwrite_id or "").strip()

        # If appwrite_id is already known from OTP flow, reuse it and skip duplicate create.
        if not appwrite_id:
            users_service = get_users_service()
            appwrite_user = users_service.create(
                user_id="unique()",
                email=normalized_email,
                password=user.password,
                name=user.username,
            )
            appwrite_id = _extract_id(appwrite_user)

        # Store user profile in MongoDB (idempotent and appwrite_id-aware)
        mongo_profile = _upsert_mongo_user(
            email=normalized_email,
            username=user.username,
            user_type=user.user_type,
            appwrite_id=appwrite_id,
        )

        return {
            "success": True,
            "message": "User registered successfully",
            "user_id": mongo_profile["mongo_id"],
            "appwrite_id": appwrite_id,
            "email": normalized_email,
            "username": user.username,
            "user_type": user.user_type
        }

    except AppwriteException as e:
        error_msg = str(e)
        if "already exists" in error_msg.lower() or "already registered" in error_msg.lower():
            # Reconcile MongoDB profile if Appwrite user already exists.
            resolved_appwrite_id = (user.appwrite_id or "").strip() or _find_appwrite_user_id_by_email(str(user.email))
            mongo_profile = _upsert_mongo_user(
                email=str(user.email),
                username=user.username,
                user_type=user.user_type,
                appwrite_id=resolved_appwrite_id,
            )
            return {
                "success": True,
                "message": "User already exists in Appwrite. MongoDB profile synchronized.",
                "user_id": mongo_profile["mongo_id"],
                "appwrite_id": resolved_appwrite_id,
                "email": _normalize_email(str(user.email)),
                "username": user.username,
                "user_type": user.user_type if user.user_type else "user"
            }
        return {
            "success": False,
            "message": error_msg,
            "error": "APPWRITE_ERROR"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Registration failed: {str(e)}",
            "error": "SERVER_ERROR"
        }


def login_user_appwrite(credentials: UserLogin) -> Dict:
    """
    Authenticate user with Appwrite using email and password
    Returns user data from MongoDB
    
    Args:
        credentials: UserLogin object with email and password
        
    Returns:
        Dict with authentication token and user details
    """
    try:
        normalized_email = _normalize_email(str(credentials.email))

        # Authenticate against Appwrite first.
        client = get_appwrite_client()
        from appwrite.services.account import Account
        account = Account(client)

        session = account.create_email_password_session(
            email=normalized_email,
            password=credentials.password
        )
        session_id = _extract_id(session)
        appwrite_id = _extract_session_user_id(session)

        db = get_database()
        users_collection = db["users"]
        _ensure_user_indexes(users_collection)

        user_doc = _find_mongo_user(
            users_collection=users_collection,
            email=normalized_email,
            appwrite_id=appwrite_id,
        )

        # Auto-reconcile Mongo user profile for users authenticated directly by Appwrite.
        if not user_doc:
            mongo_profile = _upsert_mongo_user(
                email=normalized_email,
                username=normalized_email.split("@")[0],
                user_type="user",
                appwrite_id=appwrite_id,
            )
            user_doc = mongo_profile.get("user_doc")

        if not user_doc:
            return {
                "success": False,
                "message": "User profile could not be synchronized",
                "error": "USER_SYNC_FAILED"
            }

        now = datetime.now(timezone.utc)

        if appwrite_id and user_doc.get("appwrite_id") != appwrite_id:
            users_collection.update_one(
                {"_id": user_doc["_id"]},
                {
                    "$set": {
                        "appwrite_id": appwrite_id,
                        "identity_key": appwrite_id,
                        "updated_at": now,
                    }
                }
            )
            user_doc["appwrite_id"] = appwrite_id
            user_doc["identity_key"] = appwrite_id

        users_collection.update_one(
            {"_id": user_doc["_id"]},
            {
                "$set": {
                    "last_login": now,
                    "updated_at": now
                }
            }
        )

        return {
            "success": True,
            "message": "Login successful",
            "session_id": session_id,
            "user": {
                "user_id": str(user_doc["_id"]),
                "appwrite_id": user_doc.get("appwrite_id", appwrite_id),
                "email": user_doc.get("email", normalized_email),
                "username": user_doc.get("username", normalized_email.split("@")[0]),
                "user_type": user_doc.get("user_type", "user")
            }
        }

    except AppwriteException as e:
        error_msg = str(e)
        if "invalid password" in error_msg.lower():
            return {
                "success": False,
                "message": "Invalid email or password",
                "error": "INVALID_CREDENTIALS"
            }
        return {
            "success": False,
            "message": error_msg,
            "error": "APPWRITE_ERROR"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Login failed: {str(e)}",
            "error": "SERVER_ERROR"
        }


def get_user_profile(user_id: str) -> Dict:
    """
    Get user profile from MongoDB
    
    Args:
        user_id: MongoDB user ID
        
    Returns:
        Dict with user profile data
    """
    try:
        from bson import ObjectId
        db = get_database()
        users_collection = db["users"]
        
        user_doc = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user_doc:
            return {
                "success": False,
                "message": "User not found",
                "error": "USER_NOT_FOUND"
            }
        
        # Remove sensitive data
        user_doc.pop("_id", None)
        
        return {
            "success": True,
            "user": user_doc
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to fetch profile: {str(e)}",
            "error": "SERVER_ERROR"
        }


def update_user_profile(user_id: str, update_data: Dict) -> Dict:
    """
    Update user profile in MongoDB
    
    Args:
        user_id: MongoDB user ID
        update_data: Dictionary with fields to update
        
    Returns:
        Dict with update status
    """
    try:
        from bson import ObjectId
        db = get_database()
        users_collection = db["users"]
        
        # Add update timestamp
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        result = users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            return {
                "success": False,
                "message": "User not found",
                "error": "USER_NOT_FOUND"
            }
        
        return {
            "success": True,
            "message": "Profile updated successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to update profile: {str(e)}",
            "error": "SERVER_ERROR"
        }


def logout_user_appwrite(session_id: str) -> Dict:
    """
    Logout user and delete session
    
    Args:
        session_id: Appwrite session ID
        
    Returns:
        Dict with logout status
    """
    try:
        client = get_appwrite_client()
        from appwrite.services.account import Account
        account = Account(client)
        
        account.delete_session(session_id)
        
        return {
            "success": True,
            "message": "Logged out successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Logout failed: {str(e)}",
            "error": "SERVER_ERROR"
        }
