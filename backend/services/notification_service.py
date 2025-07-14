"""
Notification Service

Handles clinical alerts, notifications, and communication with medical staff.
Supports multiple notification channels including email, SMS, and in-app alerts.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import json

from config import settings

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class NotificationService:
    """
    Comprehensive notification service for clinical alerts and communication
    """
    
    def __init__(self):
        """Initialize notification service"""
        self.notification_history: List[Dict[str, Any]] = []
        self.alert_rules = self._load_alert_rules()
        self.notification_channels = self._setup_notification_channels()
        
        logger.info("Notification Service initialized")
    
    async def send_clinical_alert(
        self,
        call_session_id: str,
        alert_type: str,
        severity: str,
        message: str,
        data: Dict[str, Any],
        patient_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send clinical alert to appropriate medical staff
        
        Args:
            call_session_id: Associated call session
            alert_type: Type of alert (high_pain_level, patient_concerns, etc.)
            severity: Alert severity level
            message: Alert message
            data: Additional alert data
            patient_id: Patient identifier
            
        Returns:
            Notification result
        """
        try:
            # Create alert record
            alert_record = {
                'id': f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{call_session_id}",
                'call_session_id': call_session_id,
                'patient_id': patient_id,
                'alert_type': alert_type,
                'severity': severity,
                'message': message,
                'data': data,
                'timestamp': datetime.now(),
                'status': 'pending',
                'notifications_sent': []
            }
            
            # Determine notification channels based on severity
            channels = self._get_channels_for_severity(severity)
            
            # Get recipient list
            recipients = await self._get_alert_recipients(alert_type, severity)
            
            # Send notifications through each channel
            for channel in channels:
                try:
                    if channel == NotificationChannel.EMAIL:
                        result = await self._send_email_alert(alert_record, recipients)
                        alert_record['notifications_sent'].append({
                            'channel': 'email',
                            'result': result,
                            'timestamp': datetime.now()
                        })
                    
                    elif channel == NotificationChannel.SMS:
                        result = await self._send_sms_alert(alert_record, recipients)
                        alert_record['notifications_sent'].append({
                            'channel': 'sms',
                            'result': result,
                            'timestamp': datetime.now()
                        })
                    
                    elif channel == NotificationChannel.IN_APP:
                        result = await self._send_in_app_alert(alert_record, recipients)
                        alert_record['notifications_sent'].append({
                            'channel': 'in_app',
                            'result': result,
                            'timestamp': datetime.now()
                        })
                    
                    elif channel == NotificationChannel.WEBHOOK:
                        result = await self._send_webhook_alert(alert_record, recipients)
                        alert_record['notifications_sent'].append({
                            'channel': 'webhook',
                            'result': result,
                            'timestamp': datetime.now()
                        })
                        
                except Exception as e:
                    logger.error(f"Error sending {channel.value} notification: {e}")
                    alert_record['notifications_sent'].append({
                        'channel': channel.value,
                        'result': {'error': str(e)},
                        'timestamp': datetime.now()
                    })
            
            # Update alert status
            alert_record['status'] = 'sent' if alert_record['notifications_sent'] else 'failed'
            
            # Store alert history
            self.notification_history.append(alert_record)
            
            logger.info(f"Clinical alert sent: {alert_record['id']}")
            
            return {
                'alert_id': alert_record['id'],
                'status': alert_record['status'],
                'channels_used': [notif['channel'] for notif in alert_record['notifications_sent']],
                'recipients_count': len(recipients)
            }
            
        except Exception as e:
            logger.error(f"Error sending clinical alert: {e}")
            raise
    
    async def send_call_summary_notification(
        self,
        call_session_id: str,
        patient_id: str,
        summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send call summary notification to care team
        """
        try:
            # Create summary notification
            notification_data = {
                'type': 'call_summary',
                'call_session_id': call_session_id,
                'patient_id': patient_id,
                'summary': summary,
                'timestamp': datetime.now()
            }
            
            # Get care team recipients
            recipients = await self._get_care_team_recipients(patient_id)
            
            # Send via email (primary channel for summaries)
            result = await self._send_email_summary(notification_data, recipients)
            
            return {
                'status': 'sent',
                'recipients_count': len(recipients),
                'notification_id': f"summary_{call_session_id}"
            }
            
        except Exception as e:
            logger.error(f"Error sending call summary: {e}")
            raise
    
    async def send_system_notification(
        self,
        notification_type: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send system-level notifications (errors, maintenance, etc.)
        """
        try:
            notification_data = {
                'type': notification_type,
                'message': message,
                'data': data or {},
                'timestamp': datetime.now()
            }
            
            # Send to system administrators
            admin_recipients = await self._get_admin_recipients()
            
            # Use multiple channels for system notifications
            results = []
            
            # Email
            email_result = await self._send_system_email(notification_data, admin_recipients)
            results.append({'channel': 'email', 'result': email_result})
            
            # In-app notification
            app_result = await self._send_system_in_app(notification_data, admin_recipients)
            results.append({'channel': 'in_app', 'result': app_result})
            
            return {
                'status': 'sent',
                'channels': results,
                'notification_id': f"system_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
        except Exception as e:
            logger.error(f"Error sending system notification: {e}")
            raise
    
    def get_notification_history(
        self,
        limit: int = 100,
        severity: Optional[str] = None,
        alert_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get notification history with optional filtering
        """
        filtered_history = self.notification_history
        
        if severity:
            filtered_history = [
                alert for alert in filtered_history 
                if alert.get('severity') == severity
            ]
        
        if alert_type:
            filtered_history = [
                alert for alert in filtered_history 
                if alert.get('alert_type') == alert_type
            ]
        
        # Sort by timestamp (newest first) and limit
        filtered_history.sort(key=lambda x: x['timestamp'], reverse=True)
        return filtered_history[:limit]
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """
        Get alert statistics and metrics
        """
        total_alerts = len(self.notification_history)
        
        if total_alerts == 0:
            return {
                'total_alerts': 0,
                'by_severity': {},
                'by_type': {},
                'by_status': {},
                'average_response_time': 0
            }
        
        # Group by severity
        by_severity = {}
        for alert in self.notification_history:
            severity = alert.get('severity', 'unknown')
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # Group by type
        by_type = {}
        for alert in self.notification_history:
            alert_type = alert.get('alert_type', 'unknown')
            by_type[alert_type] = by_type.get(alert_type, 0) + 1
        
        # Group by status
        by_status = {}
        for alert in self.notification_history:
            status = alert.get('status', 'unknown')
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            'total_alerts': total_alerts,
            'by_severity': by_severity,
            'by_type': by_type,
            'by_status': by_status,
            'last_24_hours': len([
                alert for alert in self.notification_history
                if (datetime.now() - alert['timestamp']).total_seconds() < 86400
            ])
        }
    
    def _get_channels_for_severity(self, severity: str) -> List[NotificationChannel]:
        """Get notification channels based on alert severity"""
        severity_channels = {
            'low': [NotificationChannel.IN_APP],
            'moderate': [NotificationChannel.EMAIL, NotificationChannel.IN_APP],
            'high': [NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.IN_APP],
            'urgent': [NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.IN_APP, NotificationChannel.WEBHOOK],
            'critical': [NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.IN_APP, NotificationChannel.WEBHOOK]
        }
        
        return severity_channels.get(severity, [NotificationChannel.EMAIL])
    
    async def _get_alert_recipients(self, alert_type: str, severity: str) -> List[Dict[str, Any]]:
        """Get recipient list based on alert type and severity"""
        # This would typically query a database for care team members
        # For now, return mock recipients
        
        base_recipients = [
            {
                'id': 'nurse_1',
                'name': 'Nurse Johnson',
                'email': 'nurse.johnson@hospital.com',
                'phone': '+1234567890',
                'role': 'nurse'
            }
        ]
        
        # Add more recipients for high severity alerts
        if severity in ['urgent', 'critical']:
            base_recipients.extend([
                {
                    'id': 'doctor_1',
                    'name': 'Dr. Smith',
                    'email': 'dr.smith@hospital.com',
                    'phone': '+1234567891',
                    'role': 'physician'
                },
                {
                    'id': 'supervisor_1',
                    'name': 'Supervisor Brown',
                    'email': 'supervisor.brown@hospital.com',
                    'phone': '+1234567892',
                    'role': 'supervisor'
                }
            ])
        
        return base_recipients
    
    async def _get_care_team_recipients(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get care team recipients for a specific patient"""
        # This would query the database for the patient's care team
        # For now, return mock recipients
        return [
            {
                'id': 'care_coordinator_1',
                'name': 'Care Coordinator Davis',
                'email': 'coordinator.davis@hospital.com',
                'role': 'care_coordinator'
            }
        ]
    
    async def _get_admin_recipients(self) -> List[Dict[str, Any]]:
        """Get system administrator recipients"""
        return [
            {
                'id': 'admin_1',
                'name': 'System Admin',
                'email': 'admin@hospital.com',
                'role': 'admin'
            }
        ]
    
    async def _send_email_alert(self, alert_record: Dict[str, Any], recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send email alert notification"""
        try:
            # In production, this would use an email service (SMTP, SendGrid, etc.)
            # For now, just log the action
            
            subject = f"Clinical Alert: {alert_record['alert_type']} - {alert_record['severity'].upper()}"
            body = self._format_email_alert_body(alert_record)
            
            logger.info(f"EMAIL ALERT sent to {len(recipients)} recipients")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body: {body[:200]}...")
            
            return {
                'status': 'sent',
                'recipients_count': len(recipients),
                'method': 'email'
            }
            
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def _send_sms_alert(self, alert_record: Dict[str, Any], recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send SMS alert notification"""
        try:
            # In production, this would use Twilio SMS or similar service
            # For now, just log the action
            
            message = self._format_sms_alert_message(alert_record)
            
            logger.info(f"SMS ALERT sent to {len(recipients)} recipients")
            logger.info(f"Message: {message}")
            
            return {
                'status': 'sent',
                'recipients_count': len(recipients),
                'method': 'sms'
            }
            
        except Exception as e:
            logger.error(f"Error sending SMS alert: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def _send_in_app_alert(self, alert_record: Dict[str, Any], recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send in-app notification"""
        try:
            # In production, this would push to a real-time notification system
            # For now, just log the action
            
            logger.info(f"IN-APP ALERT sent to {len(recipients)} recipients")
            logger.info(f"Alert: {alert_record['message']}")
            
            return {
                'status': 'sent',
                'recipients_count': len(recipients),
                'method': 'in_app'
            }
            
        except Exception as e:
            logger.error(f"Error sending in-app alert: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def _send_webhook_alert(self, alert_record: Dict[str, Any], recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send webhook notification to external systems"""
        try:
            # In production, this would make HTTP requests to external systems
            # For now, just log the action
            
            webhook_payload = {
                'alert_id': alert_record['id'],
                'alert_type': alert_record['alert_type'],
                'severity': alert_record['severity'],
                'message': alert_record['message'],
                'timestamp': alert_record['timestamp'].isoformat(),
                'data': alert_record['data']
            }
            
            logger.info(f"WEBHOOK ALERT sent")
            logger.info(f"Payload: {json.dumps(webhook_payload, default=str)}")
            
            return {
                'status': 'sent',
                'webhook_urls_count': 1,
                'method': 'webhook'
            }
            
        except Exception as e:
            logger.error(f"Error sending webhook alert: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def _send_email_summary(self, notification_data: Dict[str, Any], recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send call summary via email"""
        try:
            subject = f"Call Summary - Patient Follow-up"
            body = self._format_email_summary_body(notification_data)
            
            logger.info(f"EMAIL SUMMARY sent to {len(recipients)} recipients")
            logger.info(f"Subject: {subject}")
            
            return {
                'status': 'sent',
                'recipients_count': len(recipients),
                'method': 'email'
            }
            
        except Exception as e:
            logger.error(f"Error sending email summary: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def _send_system_email(self, notification_data: Dict[str, Any], recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send system notification via email"""
        try:
            subject = f"System Notification: {notification_data['type']}"
            body = f"Message: {notification_data['message']}\n\nTimestamp: {notification_data['timestamp']}\n\nData: {json.dumps(notification_data.get('data', {}), indent=2)}"
            
            logger.info(f"SYSTEM EMAIL sent to {len(recipients)} recipients")
            logger.info(f"Subject: {subject}")
            
            return {'status': 'sent', 'recipients_count': len(recipients)}
            
        except Exception as e:
            logger.error(f"Error sending system email: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def _send_system_in_app(self, notification_data: Dict[str, Any], recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send system notification via in-app"""
        try:
            logger.info(f"SYSTEM IN-APP notification sent to {len(recipients)} recipients")
            logger.info(f"Message: {notification_data['message']}")
            
            return {'status': 'sent', 'recipients_count': len(recipients)}
            
        except Exception as e:
            logger.error(f"Error sending system in-app notification: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def _format_email_alert_body(self, alert_record: Dict[str, Any]) -> str:
        """Format email body for clinical alerts"""
        return f"""
Clinical Alert Notification

Alert ID: {alert_record['id']}
Severity: {alert_record['severity'].upper()}
Type: {alert_record['alert_type']}
Call Session: {alert_record['call_session_id']}
Patient ID: {alert_record.get('patient_id', 'N/A')}

Message: {alert_record['message']}

Timestamp: {alert_record['timestamp']}

Additional Data:
{json.dumps(alert_record['data'], indent=2)}

Please review this alert and take appropriate action.
"""
    
    def _format_sms_alert_message(self, alert_record: Dict[str, Any]) -> str:
        """Format SMS message for clinical alerts"""
        return f"ALERT: {alert_record['severity'].upper()} - {alert_record['message']} (Call: {alert_record['call_session_id'][:8]})"
    
    def _format_email_summary_body(self, notification_data: Dict[str, Any]) -> str:
        """Format email body for call summaries"""
        summary = notification_data['summary']
        return f"""
Patient Call Summary

Call Session: {notification_data['call_session_id']}
Patient ID: {notification_data['patient_id']}
Timestamp: {notification_data['timestamp']}

Summary:
{json.dumps(summary, indent=2)}

This is an automated summary of the patient follow-up call.
"""
    
    def _load_alert_rules(self) -> Dict[str, Any]:
        """Load alert rules and configurations"""
        # In production, this would load from database or config file
        return {
            'high_pain_level': {
                'threshold': 7,
                'severity': 'urgent',
                'auto_escalate': True
            },
            'patient_concerns': {
                'severity': 'moderate',
                'require_response': True
            }
        }
    
    def _setup_notification_channels(self) -> Dict[str, Any]:
        """Setup notification channel configurations"""
        return {
            'email': {
                'enabled': True,
                'smtp_host': getattr(settings, 'SMTP_SERVER', 'localhost'),
                'smtp_port': getattr(settings, 'SMTP_PORT', 587)
            },
            'sms': {
                'enabled': True,
                'provider': 'twilio'
            },
            'in_app': {
                'enabled': True,
                'websocket_endpoint': '/ws/notifications'
            },
            'webhook': {
                'enabled': True,
                'endpoints': []
            }
        }


# Global service instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get global notification service instance"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service 