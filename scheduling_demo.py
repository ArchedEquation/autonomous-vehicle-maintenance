"""
Scheduling Agent - Comprehensive Demo
Demonstrates all scheduling features including emergency handling
"""

import time
import json
from datetime import datetime, timedelta

from scheduling_agent import (
    SchedulingAgent,
    BookingRequest,
    UrgencyLevel,
    create_scheduling_handler
)


def demo_emergency_override():
    """Demo: Emergency booking with override logic"""
    print("\n" + "="*70)
    print(" DEMO: EMERGENCY OVERRIDE")
    print("="*70)
    
    agent = SchedulingAgent()
    
    # Create emergency request
    request = BookingRequest(
        request_id="EMERG001",
        vehicle_id="VEH_EMERGENCY",
        customer_id="CUST_EMERGENCY",
        urgency_level=UrgencyLevel.EMERGENCY,
        services_required=['brake_system_failure', 'emergency_repair'],
        estimated_duration=2.5,
        diagnostic_details={
            'issue': 'complete_brake_failure',
            'severity': 'critical',
            'safety_risk': True,
            'description': 'Total brake system failure - vehicle unsafe to drive'
        },
        customer_preferences={'preferred_time': 'immediate'},
        parts_needed=['brake_pads', 'brake_fluid'],
        required_expertise='brakes',
        customer_location={'lat': 40.7128, 'lon': -74.0060}
    )
    
    print("\n📋 Emergency Request Details:")
    print(f"   Vehicle: {request.vehicle_id}")
    print(f"   Issue: {request.diagnostic_details['issue']}")
    print(f"   Safety Risk: {request.diagnostic_details['safety_risk']}")
    print(f"   Urgency: {request.urgency_level.name}")
    
    # Schedule
    result = agent.schedule_appointment(request)
    
    print("\n✅ Scheduling Result:")
    print(f"   Success: {result.success}")
    
    if result.appointment:
        apt = result.appointment
        print(f"   Appointment ID: {apt.appointment_id}")
        print(f"   Center: {apt.center_name}")
        print(f"   Scheduled Time: {apt.slot.start_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Time Until Service: {(apt.slot.start_time - datetime.now()).total_seconds() / 60:.0f} minutes")
        print(f"   Technician: {apt.technician_assigned}")
        print(f"   Status: {apt.status.value}")
        print(f"   ⚠️  Notes: {apt.notes}")
    else:
        print(f"   ❌ Reason: {result.reason}")


def demo_load_balancing():
    """Demo: Load balancing across service centers"""
    print("\n" + "="*70)
    print(" DEMO: LOAD BALANCING")
    print("="*70)
    
    agent = SchedulingAgent()
    
    print("\n📊 Initial Service Center Loads:")
    for center_id in ['SC001', 'SC002', 'SC003']:
        status = agent.get_center_status(center_id)
        print(f"   {status['name']}: {status['current_load']:.1%} load")
    
    # Create multiple booking requests
    print("\n📝 Creating 5 booking requests...")
    
    results = []
    for i in range(5):
        request = BookingRequest(
            request_id=f"REQ_LB_{i+1}",
            vehicle_id=f"VEH_LB_{i+1}",
            customer_id=f"CUST_LB_{i+1}",
            urgency_level=UrgencyLevel.NORMAL,
            services_required=['maintenance', 'inspection'],
            estimated_duration=1.5,
            diagnostic_details={'issue': 'routine_maintenance'},
            customer_preferences={'preferred_time': 'morning'},
            parts_needed=[],
            customer_location={'lat': 40.7128 + i*0.01, 'lon': -74.0060}
        )
        
        result = agent.schedule_appointment(request)
        results.append(result)
        
        if result.success:
            print(f"   ✓ Request {i+1}: Scheduled at {result.appointment.center_name}")
    
    print("\n📊 Final Service Center Loads:")
    for center_id in ['SC001', 'SC002', 'SC003']:
        status = agent.get_center_status(center_id)
        print(f"   {status['name']}: {status['current_load']:.1%} load "
              f"({status['upcoming_appointments']} appointments)")


def demo_optimization_factors():
    """Demo: Multi-factor optimization"""
    print("\n" + "="*70)
    print(" DEMO: MULTI-FACTOR OPTIMIZATION")
    print("="*70)
    
    agent = SchedulingAgent()
    
    # Request with specific requirements
    request = BookingRequest(
        request_id="REQ_OPT",
        vehicle_id="VEH_OPT",
        customer_id="CUST_OPT",
        urgency_level=UrgencyLevel.HIGH,
        services_required=['transmission_repair', 'diagnostic'],
        estimated_duration=4.0,
        diagnostic_details={
            'issue': 'transmission_slipping',
            'severity': 'high',
            'complexity': 'high'
        },
        customer_preferences={
            'preferred_time': 'morning',
            'preferred_center': 'SC003'
        },
        parts_needed=['transmission_fluid'],
        required_expertise='transmission',
        preferred_date=datetime.now() + timedelta(days=2),
        customer_location={'lat': 40.6782, 'lon': -73.9442}
    )
    
    print("\n📋 Request Requirements:")
    print(f"   Services: {', '.join(request.services_required)}")
    print(f"   Duration: {request.estimated_duration} hours")
    print(f"   Expertise: {request.required_expertise}")
    print(f"   Parts: {', '.join(request.parts_needed)}")
    print(f"   Preferred Center: {request.preferred_center}")
    print(f"   Preferred Time: {request.preferred_time}")
    
    result = agent.schedule_appointment(request)
    
    print("\n✅ Optimization Result:")
    print(f"   Success: {result.success}")
    print(f"   Optimization Score: {result.optimization_score:.3f}")
    
    if result.appointment:
        apt = result.appointment
        print(f"\n🎯 Best Match:")
        print(f"   Center: {apt.center_name}")
        print(f"   Time: {apt.slot.start_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Technician: {apt.technician_assigned} ({apt.slot.technician_expertise})")
        print(f"   Cost: ${apt.estimated_cost:.2f}")
        
        if result.alternatives:
            print(f"\n📋 Alternative Options ({len(result.alternatives)}):")
            for i, alt in enumerate(result.alternatives[:3], 1):
                print(f"   {i}. {alt.center_name} at {alt.slot.start_time.strftime('%Y-%m-%d %H:%M')}")


def demo_rescheduling():
    """Demo: Rescheduling appointments"""
    print("\n" + "="*70)
    print(" DEMO: RESCHEDULING")
    print("="*70)
    
    agent = SchedulingAgent()
    
    # Create initial appointment
    request = BookingRequest(
        request_id="REQ_RESCHED",
        vehicle_id="VEH_RESCHED",
        customer_id="CUST_RESCHED",
        urgency_level=UrgencyLevel.NORMAL,
        services_required=['oil_change'],
        estimated_duration=1.0,
        diagnostic_details={'issue': 'routine_maintenance'},
        customer_preferences={'preferred_time': 'morning'},
        parts_needed=['oil_filter'],
        customer_location={'lat': 40.7128, 'lon': -74.0060}
    )
    
    print("\n📅 Creating initial appointment...")
    result = agent.schedule_appointment(request)
    
    if result.success:
        original_apt = result.appointment
        print(f"   ✓ Original: {original_apt.center_name} at {original_apt.slot.start_time.strftime('%Y-%m-%d %H:%M')}")
        
        # Reschedule
        print("\n🔄 Rescheduling appointment...")
        new_date = datetime.now() + timedelta(days=5)
        reschedule_result = agent.reschedule_appointment(
            original_apt.appointment_id,
            new_preferred_date=new_date,
            reason="Customer requested different date"
        )
        
        if reschedule_result.success:
            new_apt = reschedule_result.appointment
            print(f"   ✓ Rescheduled: {new_apt.center_name} at {new_apt.slot.start_time.strftime('%Y-%m-%d %H:%M')}")
            print(f"   📝 Notes: {new_apt.notes}")
        else:
            print(f"   ❌ Failed: {reschedule_result.reason}")


def demo_parts_availability():
    """Demo: Parts availability checking"""
    print("\n" + "="*70)
    print(" DEMO: PARTS AVAILABILITY")
    print("="*70)
    
    agent = SchedulingAgent()
    
    # Request with specific parts
    request = BookingRequest(
        request_id="REQ_PARTS",
        vehicle_id="VEH_PARTS",
        customer_id="CUST_PARTS",
        urgency_level=UrgencyLevel.HIGH,
        services_required=['suspension_repair'],
        estimated_duration=3.0,
        diagnostic_details={'issue': 'worn_suspension'},
        customer_preferences={'preferred_time': 'afternoon'},
        parts_needed=['suspension_parts', 'brake_pads'],  # suspension_parts only at SC003
        customer_location={'lat': 40.7128, 'lon': -74.0060}
    )
    
    print("\n📦 Required Parts:")
    for part in request.parts_needed:
        print(f"   • {part}")
    
    print("\n🏪 Parts Inventory by Center:")
    for center_id in ['SC001', 'SC002', 'SC003']:
        center = agent.scheduler_api.service_centers[center_id]
        print(f"\n   {center.name}:")
        for part in request.parts_needed:
            available = center.parts_inventory.get(part, 0)
            status = "✓" if available > 0 else "✗"
            print(f"      {status} {part}: {available}")
    
    result = agent.schedule_appointment(request)
    
    print("\n✅ Scheduling Result:")
    if result.success:
        print(f"   Scheduled at: {result.appointment.center_name}")
        print(f"   Parts Reserved: {', '.join(result.appointment.parts_reserved)}")
    else:
        print(f"   ❌ Failed: {result.reason}")


def demo_expertise_matching():
    """Demo: Technician expertise matching"""
    print("\n" + "="*70)
    print(" DEMO: EXPERTISE MATCHING")
    print("="*70)
    
    agent = SchedulingAgent()
    
    # Complex repair requiring master technician
    request = BookingRequest(
        request_id="REQ_EXPERT",
        vehicle_id="VEH_EXPERT",
        customer_id="CUST_EXPERT",
        urgency_level=UrgencyLevel.HIGH,
        services_required=['engine_rebuild', 'transmission_overhaul'],
        estimated_duration=8.0,
        diagnostic_details={
            'issue': 'major_engine_failure',
            'complexity': 'very_high',
            'requires_master_tech': True
        },
        customer_preferences={'preferred_time': 'morning'},
        parts_needed=['engine_parts'],
        required_expertise='engine',
        customer_location={'lat': 40.7128, 'lon': -74.0060}
    )
    
    print("\n👨‍🔧 Expertise Requirements:")
    print(f"   Required: {request.required_expertise}")
    print(f"   Complexity: {request.diagnostic_details['complexity']}")
    print(f"   Duration: {request.estimated_duration} hours")
    
    print("\n🏪 Available Technicians:")
    for center_id in ['SC001', 'SC002', 'SC003']:
        center = agent.scheduler_api.service_centers[center_id]
        print(f"\n   {center.name}:")
        for tech in center.technicians:
            print(f"      • {tech['name']} ({tech['expertise']}) - {', '.join(tech['specializations'])}")
    
    result = agent.schedule_appointment(request)
    
    print("\n✅ Matching Result:")
    if result.success:
        apt = result.appointment
        tech = next(
            t for t in agent.scheduler_api.service_centers[apt.center_id].technicians
            if t['id'] == apt.technician_assigned
        )
        print(f"   Center: {apt.center_name}")
        print(f"   Technician: {tech['name']}")
        print(f"   Expertise: {tech['expertise']}")
        print(f"   Specializations: {', '.join(tech['specializations'])}")


def run_all_demos():
    """Run all demonstration scenarios"""
    print("\n" + "="*70)
    print(" SCHEDULING AGENT - COMPREHENSIVE DEMO")
    print("="*70)
    
    demos = [
        ("Emergency Override", demo_emergency_override),
        ("Load Balancing", demo_load_balancing),
        ("Multi-Factor Optimization", demo_optimization_factors),
        ("Rescheduling", demo_rescheduling),
        ("Parts Availability", demo_parts_availability),
        ("Expertise Matching", demo_expertise_matching),
    ]
    
    for name, demo_func in demos:
        try:
            demo_func()
            time.sleep(1)
        except Exception as e:
            print(f"\n❌ Error in {name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print(" ALL DEMOS COMPLETED")
    print("="*70)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        demo_type = sys.argv[1].lower()
        
        if demo_type == 'emergency':
            demo_emergency_override()
        elif demo_type == 'loadbalance':
            demo_load_balancing()
        elif demo_type == 'optimization':
            demo_optimization_factors()
        elif demo_type == 'reschedule':
            demo_rescheduling()
        elif demo_type == 'parts':
            demo_parts_availability()
        elif demo_type == 'expertise':
            demo_expertise_matching()
        else:
            print(f"Unknown demo type: {demo_type}")
            print("Available: emergency, loadbalance, optimization, reschedule, parts, expertise")
    else:
        # Run all demos
        run_all_demos()
