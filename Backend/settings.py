# settings.py - Detection sensitivity and app settings endpoints
from fastapi import APIRouter, Body, Depends, HTTPException
import sqlite3
from database import get_db

router = APIRouter()


@router.get("/settings/sensitivity")
def get_sensitivity(db: sqlite3.Connection = Depends(get_db)):
    c = db.cursor()
    c.execute(
        "SELECT value FROM settings WHERE key=?", ("detection_sensitivity",)
    )
    row = c.fetchone()
    return {"sensitivity": int(row[0]) if row else 50}


@router.post("/settings/sensitivity")
def set_sensitivity(
    data: dict = Body(...), db: sqlite3.Connection = Depends(get_db)
):
    try:
        value = int(data.get("value", 50))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=400, detail="Sensitivity must be an integer"
        )
    if value < 0 or value > 100:
        raise HTTPException(
            status_code=400, detail="Sensitivity must be between 0 and 100"
        )
    c = db.cursor()
    c.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        ("detection_sensitivity", str(value)),
    )
    db.commit()
    return {"message": "Sensitivity updated.", "sensitivity": value}
