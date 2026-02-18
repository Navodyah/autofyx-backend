from fastapi import APIRouter, status, Body, HTTPException,Request
from controllers.user_controller import create_user_mongo, login_user_mongo
from models.user_models import User, UserLogin
from fastapi.exceptions import RequestValidationError

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def create_user(user: User = Body(...)):
    try:
        created_user = create_user_mongo(user)
        return {
            "message": "User created successfully",
            "user": {
                "user_id": created_user.get("user_id"),
                "user_type": created_user.get("user_type")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", status_code=status.HTTP_200_OK)
def login(credentials: UserLogin = Body(...)):
    login_response = login_user_mongo(credentials)

    if login_response.get("msg") != "Login successful":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=login_response.get("msg", "Invalid credentials")
        )

    return {
        "message": "Login successful",
        "access_token": login_response["access_token"],
        "token_type": login_response["token_type"],
        "user": {
            "user_id": login_response["user_id"],
            "username": login_response["username"],
            "email": login_response["email"],
            "user_type": login_response["user_type"]
        }
    }
