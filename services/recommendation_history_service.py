"""
Recommendation History & Vehicle Score Tracking Service

NEW SESSION MODEL (v2):
- Each recommendation run creates a NEW document in `recommendation_history`
- Each document = one session: { user_id, session_id, vehicles: [...], saved_at, vehicle_count }
- Users can accumulate multiple sessions over time
- A user is capped at MAX_SESSIONS total sessions (oldest are pruned)
- Tracks top-3 vehicles in a global score collection (increment per recommendation)
"""
from datetime import datetime, timezone
from typing import Any, Dict, List
import uuid

from bson import ObjectId
from config.mongodb import get_database

MAX_SESSIONS   = 20   # Max recommendation sessions stored per user
MAX_VEHICLES   = 10   # Max vehicles stored per session


def save_recommendation_history(user_id: str, vehicles: List[Dict[str, Any]]) -> Dict:
    """
    Save a new recommendation SESSION for the user.

    Each call to this function creates a brand-new document in the
    `recommendation_history` collection representing one recommendation run.

    Collection: recommendation_history
    Document shape:
      {
        user_id:       str,
        session_id:    str,          # uuid4 — unique per run
        vehicles:      [ { vehicle_id, model, brand, score, fuel_type, ... } ],
        vehicle_count: int,
        saved_at:      datetime (UTC),
      }

    Old sessions beyond MAX_SESSIONS are deleted (oldest first).
    """
    if not user_id or not vehicles:
        return {"message": "Nothing to save."}

    db  = get_database()
    col = db["recommendation_history"]

    now        = datetime.now(timezone.utc)
    session_id = str(uuid.uuid4())

    # Build the vehicle list for this session (cap at MAX_VEHICLES)
    session_vehicles = []
    for v in vehicles[:MAX_VEHICLES]:
        score_val = v.get("score") or v.get("Compatibility_Score") or v.get("composite_score") or v.get("predicted_score")
        entry = {
            "vehicle_id":    v.get("vehicle_id") or v.get("_id"),
            "model":         v.get("model") or v.get("Model"),
            "brand":         v.get("brand") or v.get("Brand") or v.get("Make"),
            "year":          v.get("year") or v.get("Year") or v.get("YEAR"),
            "score":         float(score_val) if score_val is not None else None,
            "fuel_type":     v.get("fuel_type") or v.get("fuel_type_name") or v.get("FUEL"),
            "vehicle_class": v.get("vehicle_class") or v.get("VEHICLE CLASS"),
            "min_price":     v.get("min_price") or v.get("minimum_price"),
            "max_price":     v.get("max_price"),
            "image_url":     v.get("image_url"),
            "monthly_emi":   v.get("monthly_emi"),
            "recommended_at": now.isoformat(),  # stamped per vehicle from session time
        }
        session_vehicles.append({k: val for k, val in entry.items() if val is not None})

    # Insert the new session document
    col.insert_one({
        "user_id":       user_id,
        "session_id":    session_id,
        "vehicles":      session_vehicles,
        "vehicle_count": len(session_vehicles),
        "saved_at":      now,
    })

    # Prune oldest sessions beyond MAX_SESSIONS
    all_sessions = list(
        col.find({"user_id": user_id}, {"_id": 1, "saved_at": 1})
           .sort("saved_at", -1)
    )
    if len(all_sessions) > MAX_SESSIONS:
        ids_to_delete = [s["_id"] for s in all_sessions[MAX_SESSIONS:]]
        col.delete_many({"_id": {"$in": ids_to_delete}})

    return {
        "message":       f"New session saved with {len(session_vehicles)} vehicles.",
        "session_id":    session_id,
        "vehicle_count": len(session_vehicles),
    }


def track_top3_vehicle_scores(vehicles: List[Dict[str, Any]]) -> Dict:
    """
    Increment recommendation_count by 1 for each of the top-3 vehicles.
    Uses upsert so the first sighting creates the document.

    Collection: vehicle_recommendation_scores
    """
    if not vehicles:
        return {"message": "No vehicles to track."}

    db  = get_database()
    col = db["vehicle_recommendation_scores"]

    top3 = vehicles[:3]
    now  = datetime.now(timezone.utc)

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
                    "brand":               v.get("brand") or v.get("Brand") or v.get("Make"),
                    "year":                v.get("year") or v.get("Year") or v.get("YEAR"),
                    "fuel_type":           v.get("fuel_type") or v.get("fuel_type_name") or v.get("FUEL"),
                    "vehicle_class":       v.get("vehicle_class") or v.get("VEHICLE CLASS"),
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
    """
    Return ALL recommendation sessions for a user, sorted newest first.

    Response shape:
    {
      "user_id": "...",
      "sessions": [
        {
          "session_id": "uuid",
          "vehicle_count": 10,
          "saved_at": "ISO string",
          "vehicles": [ { vehicle_id, model, brand, score, ... } ]
        },
        ...
      ],
      "total_sessions": N,
      "total_vehicles":  M,
    }
    """
    db  = get_database()
    col = db["recommendation_history"]

    cursor = (
        col.find({"user_id": user_id}, {"_id": 0})
           .sort("saved_at", -1)
           .limit(MAX_SESSIONS)
    )
    sessions = []
    total_vehicles = 0
    for doc in cursor:
        saved_at = doc.get("saved_at")
        saved_at_iso = saved_at.isoformat() if hasattr(saved_at, "isoformat") else str(saved_at)
        vehicles = doc.get("vehicles", [])
        # Inject recommended_at from session saved_at into each vehicle
        for veh in vehicles:
            if not veh.get("recommended_at"):
                veh["recommended_at"] = saved_at_iso
        sessions.append({
            "session_id":    doc.get("session_id", ""),
            "vehicle_count": doc.get("vehicle_count", len(vehicles)),
            "saved_at":      saved_at_iso,
            "vehicles":      vehicles,
        })
        total_vehicles += doc.get("vehicle_count", len(vehicles))

    return {
        "user_id":        user_id,
        "sessions":       sessions,
        "total_sessions": len(sessions),
        "total_vehicles": total_vehicles,
    }


def get_vehicle_leaderboard(limit: int = 20) -> Dict:
    """Return the top vehicles ranked by recommendation_count (for analytics)."""
    db  = get_database()
    col = db["vehicle_recommendation_scores"]
    cursor    = col.find({}, {"_id": 0}).sort("recommendation_count", -1).limit(limit)
    leaderboard = list(cursor)
    for doc in leaderboard:
        for key in ["last_recommended_at", "first_recommended_at"]:
            if doc.get(key):
                doc[key] = str(doc[key])
    return {"leaderboard": leaderboard, "total": len(leaderboard)}


def get_global_recommendation_timeline() -> Dict:
    """Aggregate recommendation history across all users to provide a time-series."""
    db  = get_database()
    col = db["recommendation_history"]

    pipeline = [
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date":   "$saved_at",
                    }
                },
                "count": {"$sum": "$vehicle_count"},
            }
        },
        {"$sort": {"_id": 1}},
    ]

    results  = list(col.aggregate(pipeline))
    timeline = [{"date": r["_id"], "count": r["count"]} for r in results]
    return {"timeline": timeline}
