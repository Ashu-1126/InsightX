from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import sqlite3
from database import get_db
from auth import get_current_user

router = APIRouter()


class PersonIn(BaseModel):
    name: str
    extra: str = None
    admin: bool = False


@router.post("/people/")
def add_person(person: PersonIn, db: sqlite3.Connection = Depends(get_db)):
    c = db.cursor()
    c.execute(
        "INSERT INTO people (name, extra, admin) VALUES (?, ?, ?)",
        (person.name, person.extra, person.admin),
    )
    db.commit()
    person_id = c.lastrowid
    return {"id": person_id, "admin": person.admin}


@router.get("/people/")
def get_people(db: sqlite3.Connection = Depends(get_db)):
    c = db.cursor()
    c.execute("SELECT id, name, extra, admin FROM people")
    return [
        {"id": row[0], "name": row[1], "extra": row[2], "admin": bool(row[3])}
        for row in c.fetchall()
    ]


@router.get("/people/{person_id}")
def get_person(person_id: int, db: sqlite3.Connection = Depends(get_db)):
    c = db.cursor()
    c.execute(
        "SELECT id, name, extra, admin FROM people WHERE id=?", (person_id,)
    )
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Person not found.")
    return {
        "id": row[0],
        "name": row[1],
        "extra": row[2],
        "admin": bool(row[3]),
    }


@router.post("/people/{person_id}/set_admin")
def set_admin(
    person_id: int,
    db: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    c = db.cursor()
    c.execute("SELECT id FROM people WHERE id=?", (person_id,))
    if not c.fetchone():
        raise HTTPException(status_code=404, detail="Person not found.")
    c.execute("UPDATE people SET admin=1 WHERE id=?", (person_id,))
    db.commit()
    return {"id": person_id, "admin": True}


@router.post("/people/{person_id}/unset_admin")
def unset_admin(
    person_id: int,
    db: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    c = db.cursor()
    c.execute("SELECT id FROM people WHERE id=?", (person_id,))
    if not c.fetchone():
        raise HTTPException(status_code=404, detail="Person not found.")
    c.execute("UPDATE people SET admin=0 WHERE id=?", (person_id,))
    db.commit()
    return {"id": person_id, "admin": False}
