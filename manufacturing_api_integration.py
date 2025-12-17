"""
Manufacturing API Integration
Sends CAPA reports and quality insights to manufacturing teams
"""
import asyncio
import logging
from typing import Dict, Any, Optional
import json


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ManufacturingAPIClient:
    """
    Client for sending reports to manufacturing systems
    Supports REST API, webhook, and dashboard integration
    """
    
    def __init__(
        self,
        api_base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        webhook_url: Optional[str] = None
    ):
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.webhook_url = webhook_url
        self.dashboard_data: Dict[str, Any] = {}
    
    async def send_capa_report(self, report: Dict[str, Any]) -> bool:
        """
        Send CAPA report to manufacturing team
        
        Args:
            report: CAPA report dictionary
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Sending CAPA report {report['report_id']} to manufacturing team")
            
            # Simulate API call (in production, use aiohttp)
            if self.api_base_url:
                await self._send_via_api(report)
            
            # Send via webhook
            if self.webhook_url:
                await self._send_via_webhook(report)
            
            # Update dashboard
            await self._update_dashboard(report)
            
            logger.info(f"Successfully sent CAPA report {report['report_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending CAPA report: {e}")
            return False


    
    async def _send_via_api(self, report: Dict[str, Any]):
        """Send report via REST API"""
        # In production, use aiohttp:
        # async with aiohttp.ClientSession() as session:
        #     headers = {"Authorization": f"Bearer {self.api_key}"}
        #     async with session.post(
        #         f"{self.api_base_url}/capa-reports",
        #         json=report,
        #         headers=headers
        #     ) as response:
        #         response.raise_for_status()
        
        logger.info(f"[API] Sent report to {self.api_base_url}/capa-reports")
    
    async def _send_via_webhook(self, report: Dict[str, Any]):
        """Send report via webhook"""
        # In production, use aiohttp:
        # async with aiohttp.ClientSession() as session:
        #     async with session.post(
        #         self.webhook_url,
        #         json=report
        #     ) as response:
        #         response.raise_for_status()
        
        logger.info(f"[Webhook] Sent report to {self.webhook_url}")
    
    async def _update_dashboard(self, report: Dict[str, Any]):
        """Update dashboard with new report"""
        report_id = report['report_id']
        self.dashboard_data[report_id] = {
            "report": report,
            "updated": report['created_date']
        }
        
        logger.info(f"[Dashboard] Updated with report {report_id}")
    
    async def send_urgent_alert(
        self,
        component: str,
        failure_mode: str,
        failure_count: int
    ) -> bool:
        """
        Send urgent alert to manufacturing team
        
        Args:
            component: Component name
            failure_mode: Failure mode
            failure_count: Number of failures
            
        Returns:
            bool: Success status
        """
        try:
            alert = {
                "alert_type": "URGENT_QUALITY_ISSUE",
                "component": component,
                "failure_mode": failure_mode,
                "failure_count": failure_count,
                "timestamp": asyncio.get_event_loop().time(),
                "priority": "CRITICAL"
            }
            
            logger.critical(
                f"URGENT ALERT: {component}/{failure_mode} - {failure_count} failures"
            )
            
            if self.webhook_url:
                await self._send_via_webhook(alert)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending urgent alert: {e}")
            return False


    
    async def send_summary_report(self, summary: Dict[str, Any]) -> bool:
        """
        Send summary report to manufacturing team
        
        Args:
            summary: Summary report dictionary
            
        Returns:
            bool: Success status
        """
        try:
            logger.info("Sending summary report to manufacturing team")
            
            if self.api_base_url:
                await self._send_via_api(summary)
            
            if self.webhook_url:
                await self._send_via_webhook(summary)
            
            logger.info("Successfully sent summary report")
            return True
            
        except Exception as e:
            logger.error(f"Error sending summary report: {e}")
            return False
    
    async def send_impact_measurement(self, impact: Dict[str, Any]) -> bool:
        """
        Send impact measurement to manufacturing team
        
        Args:
            impact: Impact measurement dictionary
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Sending impact measurement for {impact['report_id']}")
            
            if self.api_base_url:
                await self._send_via_api(impact)
            
            logger.info("Successfully sent impact measurement")
            return True
            
        except Exception as e:
            logger.error(f"Error sending impact measurement: {e}")
            return False
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data"""
        return {
            "total_reports": len(self.dashboard_data),
            "reports": list(self.dashboard_data.values())
        }
    
    def clear_dashboard(self):
        """Clear dashboard data"""
        self.dashboard_data.clear()
        logger.info("Dashboard data cleared")
