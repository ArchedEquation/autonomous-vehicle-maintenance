"""
Async Inter-Agent Communication System Demo
Demonstrates event-driven architecture with message passing
"""
import asyncio
import logging
from datetime import datetime

from message_queue import InMemoryMessageQueue, TimeoutHandler
from message_schemas import MessageHeader, MessagePriority, MessageType, VehicleDataMessage
from channel_definitions import Channel, MessageFlow
from async_master_orchestrator import AsyncMasterOrchestrator
from async_data_analysis_agent import AsyncDataAnalysisAgent
from async_customer_engagement_agent import AsyncCustomerEngagementAgent
from async_scheduling_agent import AsyncSchedulingAgent


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """
    Main demo function
    Sets up the async system and demonstrates message flow
    """
    
    print("=" * 80)
    print("ASYNC INTER-AGENT COMMUNICATION SYSTEM DEMO")
    print("Event-Driven Architecture with Message Passing")
    print("=" * 80)
    print()
    
    # Display message flow diagram
    print(MessageFlow.get_workflow_diagram())
    print()
    
    # Initialize message queue and timeout handler
    logger.info("Initializing message queue and timeout handler...")
    message_queue = InMemoryMessageQueue(max_queue_size=10000)
    timeout_handler = TimeoutHandler(default_timeout=30)
    
    await message_queue.start()
    
    # Initialize agents
    logger.info("Initializing agents...")
    orchestrator = AsyncMasterOrchestrator(message_queue, timeout_handler)
    data_analysis_agent = AsyncDataAnalysisAgent(message_queue, timeout_handler)
    customer_engagement_agent = AsyncCustomerEngagementAgent(message_queue, timeout_handler)
    scheduling_agent = AsyncSchedulingAgent(message_queue, timeout_handler)
    
    # Start all agents
    logger.info("Starting all agents...")
    await orchestrator.start()
    await data_analysis_agent.start()
    await customer_engagement_agent.start()
    await scheduling_agent.start()
    
    print("\n" + "=" * 80)
    print("ALL AGENTS STARTED AND SUBSCRIBED TO CHANNELS")
    print("=" * 80)
    print()
    
    # Wait for agents to initialize
    await asyncio.sleep(1)
    
    # Scenario 1: Normal vehicle data with potential issue
    print("\n" + "=" * 80)
    print("SCENARIO 1: Vehicle with Potential Engine Issue")
    print("=" * 80)
    print()
    
    vehicle_data_1 = {
        "vehicle_id": "VEH-12345",
        "customer_id": "CUST-001",
        "timestamp": datetime.utcnow().isoformat(),
        "sensor_data": {
            "engine_temperature": 230,  # High temperature
            "oil_pressure": 35,
            "rpm": 3000,
            "speed": 65
        }
    }
    
    header_1 = MessageHeader(
        sender="external_system",
        receiver="master_orchestrator",
        message_type=MessageType.VEHICLE_DATA.value,
        priority=MessagePriority.NORMAL.value
    )
    
    message_1 = VehicleDataMessage(header=header_1, payload=vehicle_data_1)
    correlation_id_1 = header_1.correlation_id
    
    logger.info(f"Publishing vehicle data message, correlation_id: {correlation_id_1}")
    await message_queue.publish(Channel.VEHICLE_DATA_INPUT.value, message_1.to_dict())
    
    # Wait for workflow to complete
    await asyncio.sleep(6)
    
    # Check workflow status
    workflow_1 = orchestrator.get_workflow_status(correlation_id_1)
    print(f"\nWorkflow 1 Status: {workflow_1}")
    
    # Scenario 2: Vehicle with critical issue
    print("\n" + "=" * 80)
    print("SCENARIO 2: Vehicle with Critical Oil Pressure Issue")
    print("=" * 80)
    print()
    
    vehicle_data_2 = {
        "vehicle_id": "VEH-67890",
        "customer_id": "CUST-002",
        "timestamp": datetime.utcnow().isoformat(),
        "sensor_data": {
            "engine_temperature": 200,
            "oil_pressure": 15,  # Critical low pressure
            "rpm": 2500,
            "speed": 55
        }
    }
    
    header_2 = MessageHeader(
        sender="external_system",
        receiver="master_orchestrator",
        message_type=MessageType.VEHICLE_DATA.value,
        priority=MessagePriority.HIGH.value
    )
    
    message_2 = VehicleDataMessage(header=header_2, payload=vehicle_data_2)
    correlation_id_2 = header_2.correlation_id
    
    logger.info(f"Publishing vehicle data message, correlation_id: {correlation_id_2}")
    await message_queue.publish(Channel.VEHICLE_DATA_INPUT.value, message_2.to_dict())
    
    # Wait for workflow to complete
    await asyncio.sleep(6)
    
    # Check workflow status
    workflow_2 = orchestrator.get_workflow_status(correlation_id_2)
    print(f"\nWorkflow 2 Status: {workflow_2}")
    
    # Scenario 3: Normal vehicle (no issues)
    print("\n" + "=" * 80)
    print("SCENARIO 3: Vehicle with Normal Readings")
    print("=" * 80)
    print()
    
    vehicle_data_3 = {
        "vehicle_id": "VEH-11111",
        "customer_id": "CUST-003",
        "timestamp": datetime.utcnow().isoformat(),
        "sensor_data": {
            "engine_temperature": 190,  # Normal
            "oil_pressure": 40,  # Normal
            "rpm": 2000,
            "speed": 50
        }
    }
    
    header_3 = MessageHeader(
        sender="external_system",
        receiver="master_orchestrator",
        message_type=MessageType.VEHICLE_DATA.value,
        priority=MessagePriority.NORMAL.value
    )
    
    message_3 = VehicleDataMessage(header=header_3, payload=vehicle_data_3)
    correlation_id_3 = header_3.correlation_id
    
    logger.info(f"Publishing vehicle data message, correlation_id: {correlation_id_3}")
    await message_queue.publish(Channel.VEHICLE_DATA_INPUT.value, message_3.to_dict())
    
    # Wait for workflow to complete
    await asyncio.sleep(4)
    
    # Check workflow status
    workflow_3 = orchestrator.get_workflow_status(correlation_id_3)
    print(f"\nWorkflow 3 Status: {workflow_3}")
    
    # Display queue statistics
    print("\n" + "=" * 80)
    print("MESSAGE QUEUE STATISTICS")
    print("=" * 80)
    stats = message_queue.get_queue_stats()
    print(f"\nTotal Channels: {stats['total_channels']}")
    print(f"Total Subscribers: {stats['total_subscribers']}")
    print(f"Total Messages Logged: {stats['total_messages_logged']}")
    print("\nChannel Details:")
    for channel, info in stats['channels'].items():
        print(f"  {channel}:")
        print(f"    Messages: {info['total_messages']}")
        print(f"    Subscribers: {info['subscribers']}")
    
    # Display message log (last 20 messages)
    print("\n" + "=" * 80)
    print("MESSAGE LOG (Last 20 Messages)")
    print("=" * 80)
    message_log = message_queue.get_message_log(limit=20)
    for log_entry in message_log[-20:]:
        print(f"\n{log_entry['timestamp']}")
        print(f"  Channel: {log_entry['channel']}")
        print(f"  Action: {log_entry['action']}")
        print(f"  Type: {log_entry['message_type']}")
        print(f"  {log_entry['sender']} -> {log_entry['receiver']}")
        print(f"  Message ID: {log_entry['message_id']}")
        print(f"  Correlation ID: {log_entry['correlation_id']}")
    
    # Display all workflows
    print("\n" + "=" * 80)
    print("ALL WORKFLOWS SUMMARY")
    print("=" * 80)
    all_workflows = orchestrator.get_all_workflows()
    for corr_id, workflow in all_workflows.items():
        print(f"\nCorrelation ID: {corr_id}")
        print(f"  Vehicle: {workflow.get('vehicle_id')}")
        print(f"  Customer: {workflow.get('customer_id')}")
        print(f"  Current Stage: {workflow.get('current_stage')}")
        print(f"  Stages Completed: {workflow.get('stages_completed')}")
        print(f"  Start Time: {workflow.get('start_time')}")
        if 'end_time' in workflow:
            print(f"  End Time: {workflow.get('end_time')}")
    
    # Cleanup
    print("\n" + "=" * 80)
    print("STOPPING ALL AGENTS")
    print("=" * 80)
    
    await orchestrator.stop()
    await data_analysis_agent.stop()
    await customer_engagement_agent.stop()
    await scheduling_agent.stop()
    await message_queue.stop()
    
    print("\nDemo completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
