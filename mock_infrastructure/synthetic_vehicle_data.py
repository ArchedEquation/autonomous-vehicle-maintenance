"""
Synthetic Vehicle Dataset Generator
Creates realistic vehicle data with telematics, maintenance history, and failure scenarios
"""
import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import math


class SyntheticVehicleGenerator:
    """Generate synthetic vehicle data with realistic patterns"""
    
    MODELS = [
        {"name": "Sedan Pro", "year_range": (2020, 2024), "base_mileage": 15000},
        {"name": "SUV Elite", "year_range": (2019, 2024), "base_mileage": 18000},
        {"name": "Truck Max", "year_range": (2018, 2023), "base_mileage": 25000},
        {"name": "Compact City", "year_range": (2021, 2024), "base_mileage": 12000},
        {"name": "Hybrid Eco", "year_range": (2020, 2024), "base_mileage": 10000}
    ]
    
    FIRST_NAMES = ["John", "Sarah", "Michael", "Emma", "David", "Lisa", "James", "Maria", "Robert", "Jennifer"]
    LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    
    CITIES = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]
    
    def __init__(self, num_vehicles: int = 10):
        self.num_vehicles = num_vehicles
        self.vehicles = []
        self.current_time = datetime.utcnow()
    
    def generate_vin(self, index: int) -> str:
        """Generate realistic VIN"""
        return f"1HGBH41JXMN{index:06d}"
    
    def generate_vehicle(self, index: int) -> Dict[str, Any]:
        """Generate a single vehicle with complete data"""
        model_info = random.choice(self.MODELS)
        year = random.randint(*model_info["year_range"])
        
        # Calculate age-based mileage
        vehicle_age = self.current_time.year - year
        base_mileage = model_info["base_mileage"] * vehicle_age
        mileage_variance = random.randint(-5000, 10000)
        current_mileage = max(0, base_mileage + mileage_variance)
        
        # Generate owner info
        owner = {
            "name": f"{random.choice(self.FIRST_NAMES)} {random.choice(self.LAST_NAMES)}",
            "email": f"owner{index}@example.com",
            "phone": f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "address": {
                "street": f"{random.randint(100, 9999)} Main St",
                "city": random.choice(self.CITIES),
                "state": "CA",
                "zip": f"{random.randint(10000, 99999)}"
            }
        }
        
        vehicle = {
            "vin": self.generate_vin(index),
            "model": model_info["name"],
            "year": year,
            "manufacturing_date": f"{year}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "manufacturing_batch": f"BATCH-{year}-{random.randint(1, 12):02d}",
            "current_mileage": current_mileage,
            "owner": owner,
            "registration": {
                "plate": f"{random.choice(['ABC', 'XYZ', 'DEF'])}{random.randint(1000, 9999)}",
                "state": "CA",
                "expiry": f"{self.current_time.year + 1}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
            },
            "insurance": {
                "provider": random.choice(["StateFarm", "Geico", "Progressive", "Allstate"]),
                "policy_number": f"POL-{random.randint(100000, 999999)}",
                "expiry": f"{self.current_time.year + 1}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
            }
        }
        
        return vehicle
    
    def generate_maintenance_history(self, vehicle: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate maintenance history for a vehicle"""
        history = []
        mileage = vehicle["current_mileage"]
        
        # Generate service records based on mileage
        service_intervals = [5000, 10000, 15000, 20000, 25000, 30000, 40000, 50000, 60000, 75000]
        
        for interval in service_intervals:
            if mileage > interval:
                service_date = self.current_time - timedelta(days=random.randint(30, 365))
                
                services = []
                if interval % 10000 == 0:
                    services.extend(["Oil Change", "Filter Replacement", "Fluid Check"])
                if interval % 20000 == 0:
                    services.extend(["Tire Rotation", "Brake Inspection"])
                if interval % 30000 == 0:
                    services.extend(["Transmission Service", "Coolant Flush"])
                
                history.append({
                    "date": service_date.isoformat(),
                    "mileage": interval,
                    "service_type": "Scheduled Maintenance",
                    "services_performed": services,
                    "parts_replaced": self._get_parts_for_services(services),
                    "cost": random.randint(100, 500),
                    "service_center": f"Service Center {random.randint(1, 5)}",
                    "technician": f"Tech-{random.randint(100, 999)}"
                })
        
        return sorted(history, key=lambda x: x["date"])
    
    def _get_parts_for_services(self, services: List[str]) -> List[str]:
        """Get parts replaced for services"""
        parts = []
        if "Oil Change" in services:
            parts.extend(["Oil Filter", "Engine Oil"])
        if "Filter Replacement" in services:
            parts.extend(["Air Filter", "Cabin Filter"])
        if "Brake Inspection" in services and random.random() < 0.3:
            parts.extend(["Brake Pads"])
        return parts
    
    def generate_all_vehicles(self) -> List[Dict[str, Any]]:
        """Generate all vehicles with complete data"""
        vehicles = []
        
        for i in range(self.num_vehicles):
            vehicle = self.generate_vehicle(i)
            vehicle["maintenance_history"] = self.generate_maintenance_history(vehicle)
            vehicle["telematics"] = self.initialize_telematics(vehicle)
            vehicle["failure_scenario"] = self.generate_failure_scenario(vehicle, i)
            
            vehicles.append(vehicle)
        
        self.vehicles = vehicles
        return vehicles
    
    def initialize_telematics(self, vehicle: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize telematics baseline for a vehicle"""
        return {
            "engine_temperature": 195.0,  # Normal operating temp
            "oil_pressure": 40.0,  # PSI
            "battery_voltage": 12.6,  # Volts
            "coolant_temperature": 190.0,
            "rpm": 0,
            "speed": 0,
            "fuel_level": random.randint(20, 100),
            "tire_pressure": {
                "front_left": 32.0,
                "front_right": 32.0,
                "rear_left": 32.0,
                "rear_right": 32.0
            },
            "brake_pad_thickness": {
                "front_left": random.uniform(8.0, 12.0),
                "front_right": random.uniform(8.0, 12.0),
                "rear_left": random.uniform(8.0, 12.0),
                "rear_right": random.uniform(8.0, 12.0)
            },
            "odometer": vehicle["current_mileage"],
            "last_update": self.current_time.isoformat()
        }


    
    def generate_failure_scenario(self, vehicle: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Generate realistic failure scenario for a vehicle"""
        scenarios = [
            {
                "vehicle_index": 0,
                "component": "Engine",
                "issue": "Coolant leak developing",
                "severity": "MEDIUM",
                "current_condition": 75,
                "predicted_failure_days": 21,
                "symptoms": ["Temperature fluctuations", "Coolant level dropping"],
                "telematics_indicators": {"engine_temperature": "increasing", "coolant_temperature": "high"}
            },
            {
                "vehicle_index": 1,
                "component": "Battery",
                "issue": "Battery degradation",
                "severity": "LOW",
                "current_condition": 60,
                "predicted_failure_days": 45,
                "symptoms": ["Slow cranking", "Voltage drops"],
                "telematics_indicators": {"battery_voltage": "decreasing"}
            },
            {
                "vehicle_index": 2,
                "component": "Brake System",
                "issue": "Brake pads worn at 85%",
                "severity": "HIGH",
                "current_condition": 15,
                "predicted_failure_days": 14,
                "symptoms": ["Squealing noise", "Reduced braking performance"],
                "telematics_indicators": {"brake_pad_thickness": "critical"}
            },
            {
                "vehicle_index": 3,
                "component": "Transmission",
                "issue": "Transmission fluid degradation",
                "severity": "MEDIUM",
                "current_condition": 50,
                "predicted_failure_days": 30,
                "symptoms": ["Hard shifting", "Delayed engagement"],
                "telematics_indicators": {"transmission_temp": "elevated"}
            },
            {
                "vehicle_index": 4,
                "component": "Tire",
                "issue": "Uneven tire wear",
                "severity": "LOW",
                "current_condition": 40,
                "predicted_failure_days": 60,
                "symptoms": ["Vibration", "Pulling to one side"],
                "telematics_indicators": {"tire_pressure": "imbalanced"}
            },
            {
                "vehicle_index": 5,
                "component": "Electrical System",
                "issue": "Alternator bearing wear",
                "severity": "MEDIUM",
                "current_condition": 55,
                "predicted_failure_days": 25,
                "symptoms": ["Whining noise", "Dimming lights"],
                "telematics_indicators": {"battery_voltage": "fluctuating"}
            },
            {
                "vehicle_index": 6,
                "component": "Suspension",
                "issue": "Strut deterioration",
                "severity": "LOW",
                "current_condition": 45,
                "predicted_failure_days": 50,
                "symptoms": ["Bouncing", "Uneven tire wear"],
                "telematics_indicators": {"ride_quality": "degraded"}
            },
            {
                "vehicle_index": 7,
                "component": "Fuel System",
                "issue": "Fuel pump efficiency declining",
                "severity": "MEDIUM",
                "current_condition": 65,
                "predicted_failure_days": 35,
                "symptoms": ["Engine hesitation", "Difficulty starting"],
                "telematics_indicators": {"fuel_pressure": "low"}
            },
            {
                "vehicle_index": 8,
                "component": "Cooling System",
                "issue": "Radiator clogging",
                "severity": "HIGH",
                "current_condition": 30,
                "predicted_failure_days": 18,
                "symptoms": ["Overheating", "Poor heater performance"],
                "telematics_indicators": {"coolant_temperature": "high"}
            },
            {
                "vehicle_index": 9,
                "component": "Brake System",
                "issue": "Brake fluid contamination",
                "severity": "MEDIUM",
                "current_condition": 50,
                "predicted_failure_days": 28,
                "symptoms": ["Spongy brake pedal", "Reduced braking"],
                "telematics_indicators": {"brake_fluid_level": "low"}
            }
        ]
        
        # Find scenario for this vehicle
        scenario = next((s for s in scenarios if s["vehicle_index"] == index), scenarios[0])
        
        return {
            "has_issue": True,
            "component": scenario["component"],
            "issue_description": scenario["issue"],
            "severity": scenario["severity"],
            "current_condition_percent": scenario["current_condition"],
            "predicted_failure_date": (self.current_time + timedelta(days=scenario["predicted_failure_days"])).isoformat(),
            "predicted_failure_days": scenario["predicted_failure_days"],
            "symptoms": scenario["symptoms"],
            "telematics_indicators": scenario["telematics_indicators"],
            "recommended_action": f"Schedule {scenario['component']} inspection within {scenario['predicted_failure_days']} days"
        }
    
    def save_to_json(self, filepath: str = "synthetic_vehicles.json"):
        """Save vehicles to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.vehicles, f, indent=2)
        print(f"Saved {len(self.vehicles)} vehicles to {filepath}")
    
    def get_vehicle_by_vin(self, vin: str) -> Dict[str, Any]:
        """Get vehicle by VIN"""
        return next((v for v in self.vehicles if v["vin"] == vin), None)
    
    def get_all_vehicles(self) -> List[Dict[str, Any]]:
        """Get all vehicles"""
        return self.vehicles


if __name__ == "__main__":
    # Generate synthetic vehicles
    generator = SyntheticVehicleGenerator(num_vehicles=10)
    vehicles = generator.generate_all_vehicles()
    
    # Save to file
    generator.save_to_json("mock_infrastructure/synthetic_vehicles.json")
    
    # Print summary
    print("\n" + "="*80)
    print("SYNTHETIC VEHICLE DATASET GENERATED")
    print("="*80)
    
    for i, vehicle in enumerate(vehicles):
        print(f"\nVehicle {i+1}:")
        print(f"  VIN: {vehicle['vin']}")
        print(f"  Model: {vehicle['year']} {vehicle['model']}")
        print(f"  Mileage: {vehicle['current_mileage']:,} miles")
        print(f"  Owner: {vehicle['owner']['name']}")
        print(f"  Maintenance Records: {len(vehicle['maintenance_history'])}")
        
        if vehicle['failure_scenario']['has_issue']:
            scenario = vehicle['failure_scenario']
            print(f"  ⚠️  FAILURE SCENARIO:")
            print(f"      Component: {scenario['component']}")
            print(f"      Issue: {scenario['issue_description']}")
            print(f"      Severity: {scenario['severity']}")
            print(f"      Condition: {scenario['current_condition_percent']}%")
            print(f"      Predicted Failure: {scenario['predicted_failure_days']} days")
