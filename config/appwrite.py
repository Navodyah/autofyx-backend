"""
Appwrite configuration and service initialization
"""
import os
from appwrite.client import Client
from appwrite.services.users import Users
from appwrite.services.account import Account

# Environment variables for Appwrite
# Support both backend and NEXT_PUBLIC variable names to reduce setup mistakes.
APPWRITE_ENDPOINT = os.getenv("APPWRITE_ENDPOINT") or os.getenv("NEXT_PUBLIC_APPWRITE_ENDPOINT") or "http://localhost:80/v1"
APPWRITE_PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID") or os.getenv("NEXT_PUBLIC_APPWRITE_PROJECT_ID") or ""
APPWRITE_API_KEY = os.getenv("APPWRITE_API_KEY", "")
APPWRITE_DATABASE_ID = os.getenv("APPWRITE_DATABASE_ID", "users")


def _clean_env(value: str) -> str:
    """Normalize .env values that may include extra spaces or quotes."""
    return value.strip().strip('"').strip("'") if isinstance(value, str) else value

def get_appwrite_client():
    """Create and return Appwrite client"""
    endpoint = _clean_env(APPWRITE_ENDPOINT)
    project_id = _clean_env(APPWRITE_PROJECT_ID)

    if not endpoint:
        raise ValueError("APPWRITE_ENDPOINT is not configured")
    if not project_id:
        raise ValueError("APPWRITE_PROJECT_ID is not configured")

    client = Client()
    client.set_endpoint(endpoint)
    client.set_project(project_id)

    api_key = _clean_env(APPWRITE_API_KEY)
    if api_key:
        client.set_key(api_key)

    return client

def get_users_service():
    """Get Appwrite Users service"""
    if not _clean_env(APPWRITE_API_KEY):
        raise ValueError("APPWRITE_API_KEY is required for server-side user registration")
    client = get_appwrite_client()
    return Users(client)

def get_account_service():
    """Get Appwrite Account service for client-side authentication"""
    client = get_appwrite_client()
    return Account(client)
