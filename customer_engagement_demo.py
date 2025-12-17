"""
Customer Engagement Agent - Full Integration Demo
Demonstrates voice/chat capabilities with the complete system
"""

import time
import json
from datetime import datetime

from customer_engagement_agent import (
    CustomerEngagementAgent,
    DiagnosticReport,
    CustomerProfile,
    UrgencyLevel,
    CommunicationChannel,
    create_customer_engagement_handler
)
from master_orchestrator import MasterOrchestrator, AgentType
from data_analysis_agent import DataAnalysisAgent, TelematicsReading


class FullSystemDemo:
    """Complete system demonstration with all agents"""
    
    def __init__(self):
        # Initialize all agents
        self.data_agent = DataAnalysisAgent()
        self.engagement_agent = CustomerEngagementAgent()
        self.orchestrator = MasterOrchestrator(max_workers=10)
        
        # Register agents
        self._register_agents()
        
        print("Full System Demo initialized")
    
    def _register_agents(self):
        """Register all agents with orchestrator"""
        # Data Analysis Agent
        from data_analysis_agent import create_data_analysis_handler
        data_handler = create_data_analysis_handler(self.data_agent)
        self.orchestrator.register_agent(AgentType.DATA_ANALYSIS, data_handler)
        
        # Diagnosis Agent (mock)
        def diagnosis_handler(payload):
            analysis = payload.get('analysis_results', {})
            anomaly_score = analysis.get('anomaly_score', 0)
            
            return {
                'predicted_failures': ['brake_wear', 'battery_degradation'],
                'failure_probability': min(anomaly_score * 2, 0.95),
                'severity_score': min(anomaly_score * 1.5, 0.9),
                'estimated_days_to_failure': max(7, int(90 * (1 - anomaly_score))),
                'recommended_services': ['brake_inspection', 'battery_test'],
                'estimated_cost': 350.0,
                'risk_description': 'potential brake and electrical system issues'
            }
        
        self.orchestrator.register_agent(AgentType.DIAGNOSIS, diagnosis_handler)
        
        # Customer Engagement Agent
        engagement_handler = create_customer_engagement_handler(self.engagement_agent)
        self.orchestrator.register_agent(AgentType.CUSTOMER_ENGAGEMENT, engagement_handler)
        
        # Scheduling Agent (mock)
        def scheduling_handler(payload):
            return {
                'options': [{
                    'datetime': datetime.now(),
                    'service_center': 'Main Center',
                    'estimated_duration': 2,
                    'customer_preference_score': 0.8,
                    'service_center_load': 0.5
                }]
            }
        
        self.orchestrator.register_agent(AgentType.SCHEDULING, scheduling_handler)
    
    def run_scenario(self, scenario_name: str, telemetry: dict, customer_info: dict):
        """Run a complete scenario"""
        print(f"\n{'='*70}")
        print(f" {scenario_name}")
        print(f"{'='*70}\n")
        
        # Start orchestrator
        self.orchestrator.start()
        
        # Process vehicle telemetry
        vehicle_id = telemetry['vehicle_id']
        workflow_id = self.orchestrator.receive_vehicle_telemetry(vehicle_id, telemetry)
        
        print(f"Created workflow: {workflow_id}")
        print(f"Vehicle: {vehicle_id}")
        print(f"Customer: {customer_info['name']}")
        
        # Wait for processing
        time.sleep(2)
        
        # Get workflow status
        status = self.orchestrator.get_workflow_status(workflow_id)
        print(f"\nWorkflow Status: {status['state']}")
        print(f"Priority: {status['priority']}")
        print(f"Urgency Score: {status.get('urgency_score', 'N/A')}")
        
        return workflow_id


def demo_critical_scenario():
    """Demo: Critical engine overheating"""
    print("\n" + "="*70)
    print(" DEMO: CRITICAL ENGINE OVERHEATING")
    print("="*70)
    
    agent = CustomerEngagementAgent()
    
    # Critical diagnostic report
    report = DiagnosticReport(
        vehicle_id='VEH001',
        customer_id='CUST001',
        urgency_level=UrgencyLevel.CRITICAL,
        issues_detected=['engine overheating', 'coolant leak', 'thermostat failure'],
        recommended_services=['cooling_system_repair', 'thermostat_replacement', 'coolant_flush'],
        estimated_cost=950.00,
        risk_description='immediate engine damage risk and potential safety hazard',
        time_to_failure_days=0,
        safety_critical=True
    )
    
    # Customer profile
    customer = CustomerProfile(
        customer_id='CUST001',
        name='Michael Chen',
        phone='+1-555-0201',
        email='michael.chen@example.com',
        preferred_channel=CommunicationChannel.PHONE_CALL,
        preferred_time='morning',
        communication_style='formal'
    )
    
    # Engage customer
    result = agent.engage_customer(report, customer)
    
    # Display conversation
    print("\n" + "-"*70)
    print(" CONVERSATION TRANSCRIPT")
    print("-"*70)
    
    for msg in result.conversation_transcript:
        role = msg['role'].upper()
        timestamp = msg['timestamp']
        message = msg['message']
        
        if role == 'AGENT':
            print(f"\n🤖 AGENT [{timestamp}]:")
            print(f"   {message}")
        elif role == 'CUSTOMER':
            print(f"\n👤 CUSTOMER [{timestamp}]:")
            print(f"   {message}")
        else:
            print(f"\n📋 {role} [{timestamp}]:")
            print(f"   {message}")
    
    # Display results
    print("\n" + "-"*70)
    print(" ENGAGEMENT RESULTS")
    print("-"*70)
    
    print(f"\n✓ Outcome: {result.outcome.value.upper()}")
    print(f"✓ Appointment Scheduled: {'YES' if result.appointment_scheduled else 'NO'}")
    print(f"✓ Sentiment Score: {result.sentiment_score:.2f} ({_sentiment_label(result.sentiment_score)})")
    print(f"✓ Escalated to Human: {'YES' if result.escalated_to_human else 'NO'}")
    
    if result.appointment_details:
        print(f"\n📅 APPOINTMENT DETAILS:")
        print(f"   Date: {result.appointment_details['date']}")
        print(f"   Time: {result.appointment_details['time']}")
        print(f"   Location: {result.appointment_details['location']}")
        print(f"   Services: {', '.join(result.appointment_details['services'])}")
        print(f"   Estimated Cost: ${result.appointment_details['estimated_cost']:.2f}")
        print(f"   Duration: {result.appointment_details['estimated_duration']}")
        print(f"   Loaner Vehicle: {'YES' if result.appointment_details['loaner_vehicle'] else 'NO'}")


def demo_preventive_scenario():
    """Demo: Preventive maintenance with objections"""
    print("\n" + "="*70)
    print(" DEMO: PREVENTIVE MAINTENANCE (WITH OBJECTIONS)")
    print("="*70)
    
    agent = CustomerEngagementAgent()
    
    # Preventive diagnostic report
    report = DiagnosticReport(
        vehicle_id='VEH002',
        customer_id='CUST002',
        urgency_level=UrgencyLevel.PREVENTIVE,
        issues_detected=['brake_pad_wear', 'battery_degradation'],
        recommended_services=['brake_inspection', 'brake_pad_replacement', 'battery_test'],
        estimated_cost=450.00,
        risk_description='potential brake failure and starting issues',
        time_to_failure_days=45,
        safety_critical=False
    )
    
    # Customer profile
    customer = CustomerProfile(
        customer_id='CUST002',
        name='Jennifer Martinez',
        phone='+1-555-0202',
        email='j.martinez@example.com',
        preferred_channel=CommunicationChannel.SMS,
        preferred_time='afternoon',
        communication_style='casual'
    )
    
    # Engage customer
    result = agent.engage_customer(report, customer)
    
    # Display conversation
    print("\n" + "-"*70)
    print(" CONVERSATION TRANSCRIPT")
    print("-"*70)
    
    for msg in result.conversation_transcript:
        role = msg['role'].upper()
        message = msg['message']
        
        if role == 'AGENT':
            print(f"\n🤖 AGENT: {message}")
        elif role == 'CUSTOMER':
            print(f"\n👤 CUSTOMER: {message}")
        else:
            print(f"\n📋 {role}: {message}")
    
    # Display results
    print("\n" + "-"*70)
    print(" ENGAGEMENT RESULTS")
    print("-"*70)
    
    print(f"\n✓ Outcome: {result.outcome.value.upper()}")
    print(f"✓ Appointment Scheduled: {'YES' if result.appointment_scheduled else 'NO'}")
    print(f"✓ Sentiment Score: {result.sentiment_score:.2f}")
    
    if result.appointment_details:
        print(f"\n📅 Appointment: {result.appointment_details['date']} at {result.appointment_details['time']}")


def demo_routine_scenario():
    """Demo: Routine maintenance"""
    print("\n" + "="*70)
    print(" DEMO: ROUTINE MAINTENANCE")
    print("="*70)
    
    agent = CustomerEngagementAgent()
    
    # Routine diagnostic report
    report = DiagnosticReport(
        vehicle_id='VEH003',
        customer_id='CUST003',
        urgency_level=UrgencyLevel.ROUTINE,
        issues_detected=['scheduled_maintenance_due'],
        recommended_services=['oil_change', 'tire_rotation', 'multi_point_inspection'],
        estimated_cost=120.00,
        risk_description='maintain optimal vehicle performance',
        time_to_failure_days=None,
        safety_critical=False
    )
    
    # Customer profile
    customer = CustomerProfile(
        customer_id='CUST003',
        name='David Thompson',
        phone='+1-555-0203',
        email='d.thompson@example.com',
        preferred_channel=CommunicationChannel.EMAIL,
        preferred_time='evening',
        communication_style='casual'
    )
    
    # Engage customer
    result = agent.engage_customer(report, customer)
    
    # Display conversation (abbreviated)
    print("\n" + "-"*70)
    print(" CONVERSATION SUMMARY")
    print("-"*70)
    
    print(f"\nChannel: {customer.preferred_channel.value}")
    print(f"Communication Style: {customer.communication_style}")
    print(f"Messages Exchanged: {len(result.conversation_transcript)}")
    
    # Display results
    print("\n" + "-"*70)
    print(" ENGAGEMENT RESULTS")
    print("-"*70)
    
    print(f"\n✓ Outcome: {result.outcome.value.upper()}")
    print(f"✓ Appointment Scheduled: {'YES' if result.appointment_scheduled else 'NO'}")
    
    if result.appointment_details:
        print(f"\n📅 Appointment: {result.appointment_details['date']} at {result.appointment_details['time']}")
        print(f"💰 Cost: ${result.appointment_details['estimated_cost']:.2f}")


def demo_multi_channel():
    """Demo: Multi-channel communication"""
    print("\n" + "="*70)
    print(" DEMO: MULTI-CHANNEL COMMUNICATION")
    print("="*70)
    
    agent = CustomerEngagementAgent()
    
    channels = [
        (CommunicationChannel.PHONE_CALL, "Phone Call"),
        (CommunicationChannel.SMS, "SMS"),
        (CommunicationChannel.EMAIL, "Email"),
        (CommunicationChannel.APP_NOTIFICATION, "App Notification")
    ]
    
    report = DiagnosticReport(
        vehicle_id='VEH004',
        customer_id='CUST004',
        urgency_level=UrgencyLevel.URGENT,
        issues_detected=['battery_failure_imminent'],
        recommended_services=['battery_replacement'],
        estimated_cost=200.00,
        risk_description='vehicle may not start',
        time_to_failure_days=3,
        safety_critical=False
    )
    
    print("\nTesting different communication channels:\n")
    
    for channel, channel_name in channels:
        customer = CustomerProfile(
            customer_id='CUST004',
            name='Test Customer',
            phone='+1-555-0204',
            email='test@example.com',
            preferred_channel=channel,
            preferred_time='morning',
            communication_style='formal'
        )
        
        result = agent.engage_customer(report, customer)
        
        print(f"✓ {channel_name:20} - Outcome: {result.outcome.value:12} - Scheduled: {'YES' if result.appointment_scheduled else 'NO'}")


def demo_sentiment_analysis():
    """Demo: Sentiment analysis and escalation"""
    print("\n" + "="*70)
    print(" DEMO: SENTIMENT ANALYSIS & ESCALATION")
    print("="*70)
    
    agent = CustomerEngagementAgent()
    
    # Test different sentiment scenarios
    test_messages = [
        ("Yes, that sounds great! Let's schedule it.", "Positive"),
        ("I'm not sure about this. Can you explain more?", "Neutral"),
        ("This is too expensive. I can't afford it right now.", "Negative"),
        ("I'm really frustrated. You keep calling me about this!", "Very Negative"),
    ]
    
    print("\nAnalyzing customer sentiment:\n")
    
    for message, expected in test_messages:
        sentiment = agent._analyze_sentiment(message)
        label = _sentiment_label(sentiment)
        
        print(f"Message: \"{message}\"")
        print(f"  Sentiment Score: {sentiment:+.2f}")
        print(f"  Label: {label}")
        print(f"  Expected: {expected}")
        print()


def _sentiment_label(score: float) -> str:
    """Convert sentiment score to label"""
    if score > 0.5:
        return "Very Positive"
    elif score > 0.2:
        return "Positive"
    elif score > -0.2:
        return "Neutral"
    elif score > -0.5:
        return "Negative"
    else:
        return "Very Negative"


def run_all_demos():
    """Run all demonstration scenarios"""
    print("\n" + "="*70)
    print(" CUSTOMER ENGAGEMENT AGENT - COMPREHENSIVE DEMO")
    print("="*70)
    
    demos = [
        ("Critical Scenario", demo_critical_scenario),
        ("Preventive Scenario", demo_preventive_scenario),
        ("Routine Scenario", demo_routine_scenario),
        ("Multi-Channel", demo_multi_channel),
        ("Sentiment Analysis", demo_sentiment_analysis),
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
        
        if demo_type == 'critical':
            demo_critical_scenario()
        elif demo_type == 'preventive':
            demo_preventive_scenario()
        elif demo_type == 'routine':
            demo_routine_scenario()
        elif demo_type == 'multichannel':
            demo_multi_channel()
        elif demo_type == 'sentiment':
            demo_sentiment_analysis()
        else:
            print(f"Unknown demo type: {demo_type}")
            print("Available: critical, preventive, routine, multichannel, sentiment")
    else:
        # Run all demos
        run_all_demos()
