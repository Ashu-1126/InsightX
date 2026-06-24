# cameras.py - Camera management endpoints
from fastapi import APIRouter

router = APIRouter()

# Demo camera list with location info for map integration
CAMERAS = [
    {
        "id": 0,
        "name": "Main Entrance",
        "location": {"lat": 28.6139, "lng": 77.2090},
    },
    {
        "id": 1,
        "name": "Warehouse",
        "location": {"lat": 28.6140, "lng": 77.2085},
    },
    {
        "id": 2,
        "name": "Exit Gate",
        "location": {"lat": 28.6135, "lng": 77.2095},
    },
]


@router.get("/cameras")
def get_cameras():
    return CAMERAS
