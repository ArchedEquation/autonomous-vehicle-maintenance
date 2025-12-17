"""
Service Scheduler API
Mock endpoint that returns available appointment slots based on date/location
"""
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random
import uvicorn


app = FastAPI(title="Service Scheduler API", version="1.0.0")


# Service centers
SERVICE_CENTERS = [
    {
        "id": "SC001",
        "name": "Downtown Service Center",
        "address": "123 Main St, New York, NY 10001",
        "phone": "+1-555-100-1000",
        "hours": "Mon-Fri: 8AM-6PM, Sat: 9AM-4PM",
        "capacity_per_hour": 4
    },
    {
        "id": "SC002",
        "name": "Westside Auto Care",
        "address": "456 West Ave, Los Angeles, CA 90001",
        "phone": "+1-555-200-2000",
        "hours": "Mon-Sat: 7AM-7PM",
        "capacity_per_hour": 6
    },
    {
        "id": "SC003",
        "name": "North Point Service",
        "address": "789 North Blvd, Chicago, IL 60601",
        "phone": "+1-555-300-3000",
        "hours": "Mon-Fri: 8AM-5PM",
        "capacity_per_hour": 3
    }
]


# Existing appointments (simulated)
appointments = {}


def generate_available_slots(
    center_id: str,
    start_date: datetime,
    end_date: datetime
) -> List[Dict[str, Any]]:
    """Generate available appointment slots"""
    center = next((c for c in SERVICE_CENTERS if c["id"] == center_id), None)
    if not center:
        return []
    
    slots = []
    current_date = start_date
    
    while current_date <= end_date:
        # Skip weekends for some centers
        if current_date.weekday() >= 5 and center_id == "SC003":
            current_date += timedelta(days=1)
            continue
        
        # Generate hourly slots
        for hour in range(8, 17):  # 8 AM to 5 PM
            slot_time = current_date.replace(hour=hour, minute=0, second=0)
            
            # Check if slot is already booked
            slot_key = f"{center_id}_{slot_time.isoformat()}"
            booked_count = appointments.get(slot_key, 0)
            
            available = center["capacity_per_hour"] - booked_count
            
            if available > 0:
                slots.append({
                    "center_id": center_id,
                    "center_name": center["name"],
                    "datetime": slot_time.isoformat(),
                    "available_slots": available,
                    "duration_minutes": 60
                })
        
        current_date += timedelta(days=1)
    
    return slots



@app.get("/")
async def root():
    """API root"""
    return {
        "service": "Service Scheduler API",
        "version": "1.0.0",
        "endpoints": {
            "centers": "/api/centers",
            "availability": "/api/availability",
            "book": "/api/book",
            "appointments": "/api/appointments/{vin}"
        }
    }


@app.get("/api/centers")
async def get_service_centers(city: Optional[str] = None):
    """Get list of service centers"""
    centers = SERVICE_CENTERS
    
    if city:
        centers = [c for c in centers if city.lower() in c["address"].lower()]
    
    return {
        "count": len(centers),
        "centers": centers
    }


@app.get("/api/availability")
async def get_availability(
    center_id: Optional[str] = Query(None, description="Service center ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    city: Optional[str] = Query(None, description="City name")
):
    """Get available appointment slots"""
    
    # Default date range: next 14 days
    if not start_date:
        start = datetime.utcnow() + timedelta(days=1)
    else:
        start = datetime.fromisoformat(start_date)
    
    if not end_date:
        end = start + timedelta(days=14)
    else:
        end = datetime.fromisoformat(end_date)
    
    # Get centers to check
    centers_to_check = SERVICE_CENTERS
    if center_id:
        centers_to_check = [c for c in SERVICE_CENTERS if c["id"] == center_id]
    elif city:
        centers_to_check = [c for c in SERVICE_CENTERS if city.lower() in c["address"].lower()]
    
    # Generate slots for each center
    all_slots = []
    for center in centers_to_check:
        slots = generate_available_slots(center["id"], start, end)
        all_slots.extend(slots)
    
    return {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "total_slots": len(all_slots),
        "slots": all_slots[:50]  # Limit to 50 slots
    }


@app.post("/api/book")
async def book_appointment(booking: Dict[str, Any]):
    """Book an appointment"""
    required_fields = ["vin", "center_id", "datetime", "service_type"]
    
    for field in required_fields:
        if field not in booking:
            return JSONResponse(
                status_code=400,
                content={"error": f"Missing required field: {field}"}
            )
    
    vin = booking["vin"]
    center_id = booking["center_id"]
    slot_time = booking["datetime"]
    service_type = booking["service_type"]
    
    # Check if slot is available
    slot_key = f"{center_id}_{slot_time}"
    center = next((c for c in SERVICE_CENTERS if c["id"] == center_id), None)
    
    if not center:
        return JSONResponse(
            status_code=404,
            content={"error": "Service center not found"}
        )
    
    booked_count = appointments.get(slot_key, 0)
    
    if booked_count >= center["capacity_per_hour"]:
        return JSONResponse(
            status_code=409,
            content={"error": "Slot is fully booked"}
        )
    
    # Book the appointment
    appointments[slot_key] = booked_count + 1
    
    appointment_id = f"APT-{random.randint(100000, 999999)}"
    
    appointment_data = {
        "appointment_id": appointment_id,
        "vin": vin,
        "center_id": center_id,
        "center_name": center["name"],
        "datetime": slot_time,
        "service_type": service_type,
        "status": "confirmed",
        "created_at": datetime.utcnow().isoformat()
    }
    
    return appointment_data


@app.get("/api/appointments/{vin}")
async def get_appointments(vin: str):
    """Get appointments for a vehicle"""
    # In a real system, this would query a database
    # For demo, return mock data
    return {
        "vin": vin,
        "appointments": [
            {
                "appointment_id": f"APT-{random.randint(100000, 999999)}",
                "center_name": random.choice(SERVICE_CENTERS)["name"],
                "datetime": (datetime.utcnow() + timedelta(days=random.randint(1, 14))).isoformat(),
                "service_type": random.choice(["Oil Change", "Brake Inspection", "General Maintenance"]),
                "status": "confirmed"
            }
        ]
    }


if __name__ == "__main__":
    print("="*80)
    print("STARTING SERVICE SCHEDULER API SERVER")
    print("="*80)
    print("\nEndpoints:")
    print("  GET  http://localhost:8001/")
    print("  GET  http://localhost:8001/api/centers")
    print("  GET  http://localhost:8001/api/availability")
    print("  POST http://localhost:8001/api/book")
    print("  GET  http://localhost:8001/api/appointments/{vin}")
    print("\nService Centers:")
    for center in SERVICE_CENTERS:
        print(f"  {center['id']}: {center['name']}")
    print("="*80)
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
