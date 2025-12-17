"""
Setup Mock Data - Helper Script
Generates synthetic vehicle data for the mock infrastructure
"""
import os
import sys

# Add mock_infrastructure to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mock_infrastructure'))

from synthetic_vehicle_data import SyntheticVehicleGenerator

if __name__ == "__main__":
    print("="*80)
    print("SETTING UP MOCK DATA")
    print("="*80)
    
    # Generate synthetic vehicles
    print("\nGenerating 10 synthetic vehicles...")
    generator = SyntheticVehicleGenerator(num_vehicles=10)
    vehicles = generator.generate_all_vehicles()
    
    # Save to file
    filepath = "mock_infrastructure/synthetic_vehicles.json"
    generator.save_to_json(filepath)
    
    print(f"\n✓ Generated {len(vehicles)} vehicles")
    print(f"✓ Saved to: {os.path.abspath(filepath)}")
    
    # Print summary
    print("\n" + "="*80)
    print("VEHICLE SUMMARY")
    print("="*80)
    
    for i, vehicle in enumerate(vehicles[:3]):  # Show first 3
        print(f"\nVehicle {i+1}:")
        print(f"  VIN: {vehicle['vin']}")
        print(f"  Model: {vehicle['year']} {vehicle['model']}")
        print(f"  Mileage: {vehicle['current_mileage']:,} miles")
        print(f"  Owner: {vehicle['owner']['name']}")
        
        if vehicle['failure_scenario']['has_issue']:
            scenario = vehicle['failure_scenario']
            print(f"  ⚠️  Issue: {scenario['component']}")
    
    if len(vehicles) > 3:
        print(f"\n... and {len(vehicles) - 3} more vehicles")
    
    print("\n" + "="*80)
    print("✓ SETUP COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Start telematics API: python mock_infrastructure/telematics_api.py")
    print("2. Start scheduler API: python mock_infrastructure/service_scheduler_api.py")
    print("3. Run demo: python main_orchestration_demo.py")
    print("="*80)
