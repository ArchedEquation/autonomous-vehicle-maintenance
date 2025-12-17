"""
Async Data Analysis Agent
Processes vehicle data analysis requests asynchronously
"""
import asyncio
import logging
from typing import Dict, Any
import numpy as np

from async_agent_base import AsyncAgentBase
from message_schemas import MessageType, MessagePriority, AgentType
from channel_definitions import Channel


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AsyncDataAnalysisAgent(AsyncAgentBase):
    """
    Async Data Analysis Agent
    Subscribes to analysis requests and publishes results
    """
    
    def __init__(self, message_queue, timeout_handler):
        super().__init__(
            agent_name="data_analysis_agent",
            agent_type="data_analysis_agent",
            message_queue=message_queue,
            timeout_handler=timeout_handler,
            default_timeout=60
        )
        
        # Register message handlers
        self.register_message_handler(
            MessageType.ANALYSIS_REQUEST.value,
            self._handle_analysis_request
        )
    
    async def process_message(self, message: Dict[str, Any]):
        """Process messages not handled by specific handlers"""
        header = message.get("header", {})
        logger.info(f"Data Analysis Agent processing message type: {header.get('message_type')}")
    
    async def _handle_analysis_request(self, message: Dict[str, Any]):
        """
        Handle data analysis request
        Performs anomaly detection and failure prediction
        """
        header = message.get("header", {})
        payload = message.get("payload", {})
        correlation_id = header.get("correlation_id")
        
        logger.info(f"Data Analysis Agent processing request, correlation_id: {correlation_id}")
        
        # Simulate analysis processing time
        await asyncio.sleep(2)
        
        # Perform analysis (simplified for demo)
        analysis_result = await self._analyze_vehicle_data(payload)
        
        # Publish result
        await self.publish_message(
            channel=Channel.DATA_ANALYSIS_RESULT.value,
            payload=analysis_result,
            message_type=MessageType.ANALYSIS_RESULT.value,
            receiver=AgentType.MASTER_ORCHESTRATOR.value,
            priority=MessagePriority.HIGH.value if analysis_result.get("anomaly_detected") else MessagePriority.NORMAL.value,
            correlation_id=correlation_id
        )
        
        logger.info(f"Data Analysis Agent published result, correlation_id: {correlation_id}")
    
    async def _analyze_vehicle_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze vehicle data for anomalies and predictions
        This is a simplified version - in production, would use ML models
        """
        # Extract sensor data
        sensor_data = data.get("sensor_data", {})
        
        # Simulate anomaly detection
        anomaly_detected = False
        failure_probability = 0.0
        predicted_failures = []
        
        # Check for anomalies in sensor readings
        if sensor_data:
            # Simplified logic
            engine_temp = sensor_data.get("engine_temperature", 0)
            oil_pressure = sensor_data.get("oil_pressure", 0)
            
            if engine_temp > 220:
                anomaly_detected = True
                failure_probability = 0.8
                predicted_failures.append("engine_overheating")
            
            if oil_pressure < 20:
                anomaly_detected = True
                failure_probability = max(failure_probability, 0.6)
                predicted_failures.append("oil_system_failure")
        
        return {
            "vehicle_id": data.get("vehicle_id"),
            "anomaly_detected": anomaly_detected,
            "failure_probability": failure_probability,
            "predicted_failures": predicted_failures,
            "confidence_score": 0.85,
            "analysis_timestamp": data.get("timestamp", ""),
            "recommendations": self._generate_recommendations(predicted_failures)
        }
    
    def _generate_recommendations(self, failures: list) -> list:
        """Generate recommendations based on predicted failures"""
        recommendations = []
        
        if "engine_overheating" in failures:
            recommendations.append("Check coolant levels and radiator")
        
        if "oil_system_failure" in failures:
            recommendations.append("Inspect oil pump and change oil filter")
        
        return recommendations
