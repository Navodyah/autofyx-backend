from datetime import datetime, timezone
from typing import Dict, List, Optional
from config.mongodb import get_database
from bson import ObjectId

def create_application(app_data: dict) -> Dict:
    db = get_database()
    collection = db["researcher_applications"]
    
    doc = {
        "name": app_data.get("name"),
        "email": app_data.get("email"),
        "academic_role": app_data.get("academic_role"),
        "comment": app_data.get("comment"),
        "appwrite_id": app_data.get("appwrite_id"),
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    # Check if a pending application already exists for this appwrite_id
    existing = collection.find_one({"appwrite_id": doc["appwrite_id"], "status": "pending"})
    if existing:
        return {"success": False, "message": "You already have a pending application."}

    result = collection.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return {"success": True, "application": doc}

def get_pending_applications() -> List[Dict]:
    db = get_database()
    collection = db["researcher_applications"]
    cursor = collection.find({"status": "pending"}).sort("created_at", -1)
    
    apps = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        apps.append(doc)
    return apps

def update_application_status(app_id: str, status: str) -> Dict:
    db = get_database()
    collection = db["researcher_applications"]
    
    try:
        obj_id = ObjectId(app_id)
    except Exception:
        return {"success": False, "message": "Invalid application ID"}
        
    app_doc = collection.find_one({"_id": obj_id})
    if not app_doc:
        return {"success": False, "message": "Application not found"}
        
    collection.update_one(
        {"_id": obj_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc)}}
    )
    
    # If approved, update user's role in the DB to "researcher"
    if status == "approved":
        users_collection = db["users"]
        appwrite_id = app_doc.get("appwrite_id")
        if appwrite_id:
            users_collection.update_one(
                {"appwrite_id": appwrite_id},
                {"$set": {"user_type": "researcher"}}
            )
            try:
                from config.appwrite import get_users_service
                users_service = get_users_service()
                # Appwrite labels replace existing ones, so we just set it to 'researcher'
                users_service.update_labels(appwrite_id, ["researcher"])
            except Exception as e:
                print(f"Failed to update Appwrite labels for {appwrite_id}: {e}")
            
    return {"success": True, "message": f"Application {status} successfully."}
