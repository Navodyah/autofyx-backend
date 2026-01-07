from datetime import datetime, timezone
from config.mongodb import get_database
from models.user_models import User, UserLogin
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

pwd_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return pwd_hasher.hash(password)


def create_user_mongo(user: User):
    db = get_database()
    users_collection = db["users"]

    hashed_pw = hash_password(user.password)

    user_doc = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_pw,
        "user_type": user.user_type if user.user_type else "user",
        "created_at": datetime.now(timezone.utc)

    }

    result = users_collection.insert_one(user_doc)

    return {
        "msg": "User created successfully",
        "user_id": str(result.inserted_id),
        "user_type": user.user_type
    }

def login_user_mongo(credentials: UserLogin):
    db = get_database()
    users_collection = db["users"]

    # Find user by email only
    user_doc = users_collection.find_one({"email": credentials.email})

    if not user_doc:
        return {"msg": "User not found"}

    try:
        pwd_hasher.verify(user_doc["hashed_password"], credentials.password)
    except VerifyMismatchError:
        return {"msg": "Incorrect password"}

    return {
        "msg": "Login successful",
        "user_id": str(user_doc["_id"]),
        "username": user_doc["username"],
        "email": user_doc["email"],
        "user_type": user_doc.get("user_type", "user")  # Retrieve from database
    }