"""
Integrated Mock Infrastructure Demo
Demonstrates all components working together
"""
import asyncio
import json
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mock_infrastructure.synthetic_vehicle_data import SyntheticVehicleGenerator
from mock_infrastructure.maintenance_database import MaintenanceDatabase
from mock_infrastructure.customer_interaction_simulator import CustomerInteractionSimulator


async def demo_complete_workflow():
    """Demonstrate complete workflow with all components"""
    
    print("="*80)
    print("INTEGRATED MOCK INFRASTRUCTURE DEMO")
    print("Complete Vehicle Maintenance System Simulation")
    print("="*80)
    
    # Step 1: Generate Synthetic Vehicles
    print("\n" + "="*80)
    print("STEP 1: GENERATING SYNTHETIC VEHICLE DATASET")
    print("="*80)
    
    generator = SyntheticVehicleGenerator(num_vehicles=10)
    vehicles = generator.generate_all_vehicles()
    generator.save_to_json("mock_infrastructure/synthetic_vehicles.json")
    
    print(f"\n✓ Generated {len(vehicles)} vehicles with:")
    print("  - VIN, model, year, mileage")
    print("  - Owner contact information")
    print("  - Maintenance history")
    print("  - Simulated telematics")
    print("  - Realistic failure scenarios")
    
    # Show sample vehicle
    sample_vehicle = vehicles[2]  # Vehicle with brake issue
    print(f"\nSample Vehicle (VIN: {sample_vehicle['vin']}):")
    print(f"  Model: {sample_vehicle['year']} {sample_vehicle['model']}")
    print(f"  Mileage: {sample_vehicle['current_mileage']:,} miles")
    print(f"  Owner: {sample_vehicle['owner']['name']}")
    print(f"  Email: {sample_vehicle['owner']['email']}")
    print(f"  Phone: {sample_vehicle['owner']['phone']}")
    
    # Show failure scenario
    scenario = sample_vehicle['failure_scenario']
    print(f"\n  ⚠️  FAILURE SCENARIO:")
    print(f"      Component: {scenario['component']}")
    print(f"      Issue: {scenario['issue_description']}")
    print(f"      Severity: {scenario['severity']}")
    print(f"      Condition: {scenario['current_condition_percent']}%")
    print(f"      Predicted Failure: {scenario['predicted_failure_days']} days")
    print(f"      Symptoms: {', '.join(scenario['symptoms'])}")
    
    # Step 2: Initialize Maintenance Database
    print("\n" + "="*80)
    print("STEP 2: INITIALIZING MAINTENANCE RECORDS DATABASE")
    print("="*80)
    
    db = MaintenanceDatabase()
    db.initialize_schema()
    db.import_synthetic_data()
    
    print("\n✓ Database initialized with:")
    print(f"  - {len(vehicles)} vehicles")
    print("  - Complete maintenance history")
    print("  - Service records with parts and costs")
    
    # Query sample maintenance history
    history = db.get_service_history(sample_vehicle['vin'])
    print(f"\nMaintenance History for {sample_vehicle['vin']}:")
    for record in history[:3]:
        print(f"  {record['service_date'][:10]} @ {record['mileage']:,} miles:")
        print(f"    Services: {', '.join(record['services_performed'])}")
        print(f"    Cost: ${record['cost']:.2f}")
    
    db.close()
    
    # Step 3: Simulate Telematics Data
    print("\n" + "="*80)
    print("STEP 3: SIMULATING TELEMATICS DATA STREAM")
    print("="*80)
    
    print("\n✓ Telematics API would stream data every 5 seconds")
    print("  Endpoints:")
    print("    GET  /api/vehicles - List all vehicles")
    print("    GET  /api/telemetry/{vin} - Get current telemetry")
    print("    WS   /api/stream/{vin} - Stream telemetry")
    
    # Show current telemetry
    telemetry = sample_vehicle['telematics']
    print(f"\nCurrent Telemetry for {sample_vehicle['vin']}:")
    print(f"  Engine Temp: {telemetry['engine_temperature']:.1f}°F")
    print(f"  Oil Pressure: {telemetry['oil_pressure']:.1f} PSI")
    print(f"  Battery: {telemetry['battery_voltage']:.1f}V")
    print(f"  Speed: {telemetry['speed']:.0f} mph")
    print(f"  Odometer: {telemetry['odometer']:,} miles")
    
    # Show brake pad thickness (critical for this vehicle)
    print(f"\n  Brake Pad Thickness:")
    for position, thickness in telemetry['brake_pad_thickness'].items():
        status = "⚠️ CRITICAL" if thickness < 3.0 else "✓ OK"
        print(f"    {position}: {thickness:.1f}mm {status}")
    
    # Step 4: Service Scheduler
    print("\n" + "="*80)
    print("STEP 4: SERVICE SCHEDULER API")
    print("="*80)
    
    print("\n✓ Service Scheduler API provides:")
    print("  - 3 service centers with availability")
    print("  - Hourly appointment slots")
    print("  - Booking and confirmation")
    
    print("\nAvailable Service Centers:")
    centers = [
        {"id": "SC001", "name": "Downtown Service Center", "city": "New York"},
        {"id": "SC002", "name": "Westside Auto Care", "city": "Los Angeles"},
        {"id": "SC003", "name": "North Point Service", "city": "Chicago"}
    ]
    
    for center in centers:
        print(f"  {center['id']}: {center['name']} ({center['city']})")
    
    # Simulate finding available slots
    print(f"\nAvailable Slots for Next Week:")
    tomorrow = datetime.utcnow() + timedelta(days=1)
    for i in range(3):
        slot_date = tomorrow + timedelta(days=i)
        print(f"  {slot_date.strftime('%Y-%m-%d')} 9:00 AM - Downtown Service Center")
        print(f"  {slot_date.strftime('%Y-%m-%d')} 2:00 PM - Westside Auto Care")
    
    # Step 5: Customer Interaction
    print("\n" + "="*80)
    print("STEP 5: CUSTOMER INTERACTION SIMULATION")
    print("="*80)
    
    # Create customer simulator
    customer = CustomerInteractionSimulator(
        customer_name=sample_vehicle['owner']['name'],
        personality="cooperative"
    )
    
    # Send notification about brake issue
    notification_message = (
        f"Hello {customer.customer_name}, our analysis shows your "
        f"{sample_vehicle['year']} {sample_vehicle['model']}'s brake pads are at "
        f"{scenario['current_condition_percent']}% remaining. We recommend scheduling "
        f"service within {scenario['predicted_failure_days']} days to ensure your safety."
    )
    
    print(f"\nSending Notification:")
    print(f"  To: {customer.customer_name}")
    print(f"  Message: {notification_message}")
    print(f"  Urgency: {scenario['severity']}")
    
    response = customer.receive_notification(
        notification_type="maintenance_alert",
        message=notification_message,
        urgency=scenario['severity'].lower()
    )
    
    print(f"\nCustomer Response:")
    if response["responded"]:
        print(f"  Responded in: {response['response_time_minutes']} minutes")
        print(f"  Decision: {response['response']['decision'].upper()}")
        print(f"  Response: \"{response['response']['text']}\"")
        print(f"  Sentiment: {response['response']['sentiment']}")
        
        if response['response']['decision'] == 'accepted':
            print(f"  Preferred: {', '.join(response['response']['preferred_dates'])}")
            print(f"  Time: {response['response']['preferred_time']}")
    else:
        print("  No response received")
    
    # Simulate chat conversation
    print(f"\n{'-'*80}")
    print("CHAT CONVERSATION SIMULATION")
    print(f"{'-'*80}")
    
    conversation = customer.simulate_chat_conversation(
        "Hello! We've detected that your brake pads need attention soon."
    )
    
    for msg in conversation:
        role = "AGENT" if msg["role"] == "agent" else "CUSTOMER"
        print(f"\n{role}: {msg['message']}")
    
    # Step 6: Complete Workflow Summary
    print("\n" + "="*80)
    print("COMPLETE WORKFLOW SUMMARY")
    print("="*80)
    
    print("\n1. ✓ Vehicle Data Generated")
    print("   - 10 vehicles with complete profiles")
    print("   - Realistic failure scenarios")
    
    print("\n2. ✓ Telematics Streaming")
    print("   - Real-time sensor data")
    print("   - Failure indicators detected")
    
    print("\n3. ✓ Maintenance Database")
    print("   - Historical service records")
    print("   - Parts and cost tracking")
    
    print("\n4. ✓ Predictive Analysis")
    print(f"   - Identified: {scenario['component']} issue")
    print(f"   - Severity: {scenario['severity']}")
    print(f"   - Predicted failure: {scenario['predicted_failure_days']} days")
    
    print("\n5. ✓ Customer Engagement")
    print(f"   - Notification sent to {customer.customer_name}")
    print(f"   - Customer {response['response']['decision']}")
    
    if response['response']['decision'] == 'accepted':
        print("\n6. ✓ Appointment Scheduling")
        print("   - Available slots identified")
        print("   - Booking confirmed")
        print("   - Service center notified")
    
    print("\n" + "="*80)
    print("DEMO COMPLETE")
    print("="*80)
    
    print("\nTo start the APIs:")
    print("  1. Telematics API:  python mock_infrastructure/telematics_api.py")
    print("  2. Scheduler API:   python mock_infrastructure/service_scheduler_api.py")
    
    print("\nTo access the data:")
    print("  - Vehicles: mock_infrastructure/synthetic_vehicles.json")
    print("  - Database: mock_infrastructure/maintenance_records.db")


if __name__ == "__main__":
    asyncio.run(demo_complete_workflow())
