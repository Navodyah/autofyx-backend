"""
Recommendation History & Vehicle Score Tracking Service
- Saves top-15 recommended vehicles per user (capped sliding window)
- Tracks top-3 vehicles in a global score collection (increment per recommendation)
"""
from datetime import datetime, timezone
from typing import Any, Dict, List

from bson import ObjectId
from config.mongodb import get_database

MAX_HISTORY = 15   # Max vehicles stored in a user's recommendation history


def save_recommendation_history(user_id: str, vehicles: List[Dict[str, Any]]) -> Dict:
    """
    Persist the top-N recommended vehicles (up to MAX_HISTORY) under the user's record.
    Each call replaces the stored list with the newest recommendations prepended,
    trimming to MAX_HISTORY total entries.

    Collection: recommendation_history
    Document shape:
      {
        user_id: str,
        vehicles: [ { vehicle_id, model, brand, score, recommended_at, ... } ],
        updated_at: datetime
      }
    """
    if not user_id or not vehicles:
        return {"message": "Nothing to save."}

    db = get_database()
    col = db["recommendation_history"]

    # Build the new batch (cap at MAX_HISTORY)
    new_batch = []
    for v in vehicles[:MAX_HISTORY]:
        entry = {
            "vehicle_id": v.get("vehicle_id") or v.get("_id"),
            "model":      v.get("model") or v.get("Model"),
            "brand":      v.get("brand") or v.get("Brand"),
            "year":       v.get("year") or v.get("Year"),
            "score":      v.get("score") or v.get("predicted_score") or v.get("composite_score"),
            "fuel_type":  v.get("fuel_type") or v.get("fuel"),
            "vehicle_class": v.get("vehicle_class") or v.get("Class"),
            "min_price":  v.get("minimum_price"),
            "max_price":  v.get("max_price"),
            "recommended_at": datetime.now(timezone.utc).isoformat(),
        }
        new_batch.append({k: val for k, val in entry.items() if val is not None})

    # Fetch existing history and prepend new, trim to MAX_HISTORY
    existing_doc = col.find_one({"user_id": user_id})
    existing_vehicles = existing_doc.get("vehicles", []) if existing_doc else []

    merged = new_batch + existing_vehicles
    trimmed = merged[:MAX_HISTORY]

    col.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "user_id":    user_id,
                "vehicles":   trimmed,
                "updated_at": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )

    return {
        "message": f"Saved {len(new_batch)} vehicles. History now has {len(trimmed)} entries.",
        "total": len(trimmed),
    }


def track_top3_vehicle_scores(vehicles: List[Dict[str, Any]]) -> Dict:
    """
    Increment recommendation_count by 1 for each of the top-3 vehicles.
    Uses upsert so the first sighting creates the document.

    Collection: vehicle_recommendation_scores
    Document shape:
      {
        vehicle_id: str,
        model: str,
        brand: str,
        year: ...,
        fuel_type: str,
        vehicle_class: str,
        recommendation_count: int,   # incremented each run
        last_recommended_at: datetime,
        first_recommended_at: datetime,  # set only on insert
      }
    """
    if not vehicles:
        return {"message": "No vehicles to track."}

    db = get_database()
    col = db["vehicle_recommendation_scores"]

    top3 = vehicles[:3]
    now = datetime.now(timezone.utc)

    updated = 0
    for v in top3:
        vid = str(v.get("vehicle_id") or v.get("_id") or "")
        if not vid:
            continue

        col.update_one(
            {"vehicle_id": vid},
            {
                "$inc": {"recommendation_count": 1},
                "$set": {
                    "model":               v.get("model") or v.get("Model"),
                    "brand":               v.get("brand") or v.get("Brand"),
                    "year":                v.get("year") or v.get("Year"),
                    "fuel_type":           v.get("fuel_type") or v.get("fuel"),
                    "vehicle_class":       v.get("vehicle_class") or v.get("Class"),
                    "last_recommended_at": now,
                },
                "$setOnInsert": {
                    "first_recommended_at": now,
                },
            },
            upsert=True,
        )
        updated += 1

    return {"message": f"Scores updated for {updated} vehicle(s)."}


def get_recommendation_history(user_id: str) -> Dict:
    """Fetch the stored recommendation history for a user."""
    db = get_database()
    col = db["recommendation_history"]
    doc = col.find_one({"user_id": user_id}, {"_id": 0})
    if not doc:
        return {"user_id": user_id, "vehicles": [], "total": 0}
    return {
        "user_id":    doc.get("user_id"),
        "vehicles":   doc.get("vehicles", []),
        "total":      len(doc.get("vehicles", [])),
        "updated_at": str(doc.get("updated_at", "")),
    }


def get_vehicle_leaderboard(limit: int = 20) -> Dict:
    """Return the top vehicles ranked by recommendation_count (for analytics)."""
    db = get_database()
    col = db["vehicle_recommendation_scores"]
    cursor = col.find({}, {"_id": 0}).sort("recommendation_count", -1).limit(limit)
    leaderboard = list(cursor)
    for doc in leaderboard:
        for key in ["last_recommended_at", "first_recommended_at"]:
            if doc.get(key):
                doc[key] = str(doc[key])
    return {"leaderboard": leaderboard, "total": len(leaderboard)}


def get_global_recommendation_timeline() -> Dict:
    """Aggregate recommendation history across all users to provide a time-series of recommendation activity."""
    db = get_database()
    col = db["recommendation_history"]
    
    pipeline = [
        {"$unwind": "$vehicles"},
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d", 
                        "date": {"$toDate": "$vehicles.recommended_at"}
                    }
                },
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    
    results = list(col.aggregate(pipeline))
    timeline = [{"date": r["_id"], "count": r["count"]} for r in results]
    return {"timeline": timeline}
