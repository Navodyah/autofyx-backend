# config/settings.py
import os

JWT_SECRET = os.getenv("JWT_SECRET","CHANGE_THIS_SUPER_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "120"))
