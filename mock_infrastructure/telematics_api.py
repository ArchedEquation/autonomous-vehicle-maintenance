"""
Mock Telematics API
Streams vehicle data every 5 seconds with realistic fluctuations
"""
import asyncio
import json
import random
import math
from datetime import datetime
from typing import Dict, Any, List
from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
import uvicorn


app = FastAPI(title="Vehicle Telematics API", version="1.0.0")

# Global vehicle data storage
vehicles_data = {}


class TelematicsSimulator:
    """Simulates realistic telematics data with time-based variations"""
    
    def __init__(self, vehicle: Dict[str, Any]):
        self.vehicle = vehicle
        self.vin = vehicle["vin"]
        self.telematics = vehicle["telematics"].copy()
        self.failure_scenario = vehicle.get("failure_scenario", {})
        self.time_elapsed = 0
        self.is_driving = False
        self.drive_cycle_time = 0
    
    def update_telematics(self, time_delta: float = 5.0) -> Dict[str, Any]:
        """Update telematics with realistic variations"""
        self.time_elapsed += time_delta
        
        # Simulate driving cycles (drive for 30 min, stop for 60 min)
        if self.time_elapsed % 5400 < 1800:  # Drive for 30 minutes every 90 minutes
            self.is_driving = True
            self.drive_cycle_time += time_delta
        else:
            self.is_driving = False
            self.drive_cycle_time = 0
        
        if self.is_driving:
            self._update_driving_state()
        else:
            self._update_idle_state()
        
        # Apply failure scenario effects
        self._apply_failure_effects()
        
        # Update timestamp
        self.telematics["last_update"] = datetime.utcnow().isoformat()
        
        return self.telematics.copy()
    
    def _update_driving_state(self):
        """Update telematics during driving"""
        # Speed varies between 30-70 mph
        self.telematics["speed"] = 30 + 40 * math.sin(self.drive_cycle_time / 100) + random.uniform(-5, 5)
        self.telematics["speed"] = max(0, min(70, self.telematics["speed"]))
        
        # RPM correlates with speed
        self.telematics["rpm"] = 1500 + self.telematics["speed"] * 30 + random.uniform(-100, 100)
        
        # Engine temperature rises during driving
        target_temp = 205 + random.uniform(-5, 5)
        self.telematics["engine_temperature"] += (target_temp - self.telematics["engine_temperature"]) * 0.1
        
        # Coolant temperature follows engine temp
        self.telematics["coolant_temperature"] = self.telematics["engine_temperature"] - 5 + random.uniform(-2, 2)
        
        # Oil pressure varies with RPM
        self.telematics["oil_pressure"] = 30 + (self.telematics["rpm"] / 100) + random.uniform(-2, 2)
        
        # Battery voltage stable while driving
        self.telematics["battery_voltage"] = 13.8 + random.uniform(-0.2, 0.2)
        
        # Fuel consumption
        self.telematics["fuel_level"] = max(0, self.telematics["fuel_level"] - 0.01)
        
        # Odometer increases
        self.telematics["odometer"] += self.telematics["speed"] / 720  # miles per 5 seconds
    
    def _update_idle_state(self):
        """Update telematics when idle"""
        self.telematics["speed"] = 0
        self.telematics["rpm"] = 0
        
        # Engine temperature cools down
        ambient_temp = 75
        self.telematics["engine_temperature"] += (ambient_temp - self.telematics["engine_temperature"]) * 0.05
        self.telematics["coolant_temperature"] = self.telematics["engine_temperature"]
        
        # Oil pressure drops to zero
        self.telematics["oil_pressure"] = 0
        
        # Battery voltage slowly decreases
        self.telematics["battery_voltage"] = max(11.5, self.telematics["battery_voltage"] - 0.001)
    
    def _apply_failure_effects(self):
        """Apply failure scenario effects to telematics"""
        if not self.failure_scenario.get("has_issue"):
            return
        
        indicators = self.failure_scenario.get("telematics_indicators", {})
        condition = self.failure_scenario.get("current_condition_percent", 100)
        
        # Engine temperature issues
        if "engine_temperature" in indicators:
            if indicators["engine_temperature"] == "increasing":
                self.telematics["engine_temperature"] += random.uniform(0, 2)
        
        # Battery degradation
        if "battery_voltage" in indicators:
            if indicators["battery_voltage"] == "decreasing":
                degradation = (100 - condition) / 100 * 0.5
                self.telematics["battery_voltage"] -= degradation * 0.01
            elif indicators["battery_voltage"] == "fluctuating":
                self.telematics["battery_voltage"] += random.uniform(-0.5, 0.5)
        
        # Brake pad wear
        if "brake_pad_thickness" in indicators:
            if indicators["brake_pad_thickness"] == "critical":
                wear_factor = (100 - condition) / 100
                for position in self.telematics["brake_pad_thickness"]:
                    self.telematics["brake_pad_thickness"][position] = 12.0 * (condition / 100) + random.uniform(-0.5, 0.5)
        
        # Coolant temperature
        if "coolant_temperature" in indicators:
            if indicators["coolant_temperature"] == "high":
                self.telematics["coolant_temperature"] += random.uniform(0, 3)
        
        # Tire pressure imbalance
        if "tire_pressure" in indicators:
            if indicators["tire_pressure"] == "imbalanced":
                self.telematics["tire_pressure"]["front_left"] = 32.0 + random.uniform(-3, 0)
                self.telematics["tire_pressure"]["front_right"] = 32.0 + random.uniform(0, 3)


# Initialize simulators
simulators = {}


def load_vehicles():
    """Load vehicles from synthetic data"""
    global vehicles_data, simulators
    
    import os
    
    # Try multiple possible paths
    possible_paths = [
        "synthetic_vehicles.json",  # Running from mock_infrastructure
        "mock_infrastructure/synthetic_vehicles.json",  # Running from root
        os.path.join(os.path.dirname(__file__), "synthetic_vehicles.json")  # Relative to this file
    ]
    
    vehicles = None
    for filepath in possible_paths:
        try:
            with open(filepath, 'r') as f:
                vehicles = json.load(f)
                print(f"Loaded vehicles from: {filepath}")
                break
        except FileNotFoundError:
            continue
    
    if vehicles is None:
        print("="*80)
        print("ERROR: Synthetic vehicles file not found!")
        print("Please run: python synthetic_vehicle_data.py")
        print("(from the mock_infrastructure directory)")
        print("="*80)
        return
    
    for vehicle in vehicles:
        vin = vehicle["vin"]
        vehicles_data[vin] = vehicle
        simulators[vin] = TelematicsSimulator(vehicle)
        
    print(f"Loaded {len(vehicles)} vehicles")


@app.on_event("startup")
async def startup_event():
    """Load vehicles on startup"""
    load_vehicles()
    # Start background telemetry updates
    asyncio.create_task(update_telemetry_loop())


async def update_telemetry_loop():
    """Background task to update telemetry every 5 seconds"""
    while True:
        for vin, simulator in simulators.items():
            vehicles_data[vin]["telematics"] = simulator.update_telematics()
        await asyncio.sleep(5)


@app.get("/")
async def root():
    """API root"""
    return {
        "service": "Vehicle Telematics API",
        "version": "1.0.0",
        "endpoints": {
            "vehicles": "/api/vehicles",
            "telemetry": "/api/telemetry/{vin}",
            "stream": "/api/stream/{vin}",
            "all_telemetry": "/api/telemetry/all"
        }
    }


@app.get("/api/vehicles")
async def get_vehicles():
    """Get list of all vehicles"""
    return {
        "count": len(vehicles_data),
        "vehicles": [
            {
                "vin": v["vin"],
                "model": v["model"],
                "year": v["year"],
                "mileage": v["current_mileage"],
                "owner": v["owner"]["name"]
            }
            for v in vehicles_data.values()
        ]
    }


@app.get("/api/telemetry/{vin}")
async def get_telemetry(vin: str):
    """Get current telemetry for a vehicle"""
    if vin not in vehicles_data:
        return JSONResponse(
            status_code=404,
            content={"error": f"Vehicle {vin} not found"}
        )
    
    vehicle = vehicles_data[vin]
    return {
        "vin": vin,
        "model": f"{vehicle['year']} {vehicle['model']}",
        "telemetry": vehicle["telematics"],
        "failure_scenario": vehicle.get("failure_scenario", {})
    }


@app.get("/api/telemetry/all")
async def get_all_telemetry():
    """Get telemetry for all vehicles"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "count": len(vehicles_data),
        "vehicles": [
            {
                "vin": vin,
                "model": f"{v['year']} {v['model']}",
                "telemetry": v["telematics"]
            }
            for vin, v in vehicles_data.items()
        ]
    }


@app.websocket("/api/stream/{vin}")
async def stream_telemetry(websocket: WebSocket, vin: str):
    """Stream telemetry data via WebSocket"""
    await websocket.accept()
    
    if vin not in vehicles_data:
        await websocket.send_json({"error": f"Vehicle {vin} not found"})
        await websocket.close()
        return
    
    try:
        while True:
            vehicle = vehicles_data[vin]
            data = {
                "vin": vin,
                "timestamp": datetime.utcnow().isoformat(),
                "telemetry": vehicle["telematics"]
            }
            await websocket.send_json(data)
            await asyncio.sleep(5)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


if __name__ == "__main__":
    print("="*80)
    print("STARTING TELEMATICS API SERVER")
    print("="*80)
    print("\nEndpoints:")
    print("  GET  http://localhost:8000/")
    print("  GET  http://localhost:8000/api/vehicles")
    print("  GET  http://localhost:8000/api/telemetry/{vin}")
    print("  GET  http://localhost:8000/api/telemetry/all")
    print("  WS   ws://localhost:8000/api/stream/{vin}")
    print("\nStreaming telemetry every 5 seconds...")
    print("="*80)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
