"""
Webhook Performance Monitor
Real-time monitoring of webhook performance and error rates
"""

import asyncio
import logging
import time
import json
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional
import threading
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("webhook_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WebhookMonitor:
    """Monitor webhook performance and errors"""
    
    def __init__(self, window_minutes: int = 5):
        self.window_minutes = window_minutes
        self.metrics = defaultdict(lambda: {
            'requests': deque(),
            'errors': deque(),
            'response_times': deque(),
            'last_success': None,
            'last_error': None
        })
        self.running = False
        self.monitor_thread = None
        
    def record_request(self, endpoint: str, duration: float, success: bool = True, error: str = None):
        """Record a webhook request"""
        now = datetime.utcnow()
        
        # Add to metrics
        self.metrics[endpoint]['requests'].append({
            'timestamp': now,
            'duration': duration,
            'success': success,
            'error': error
        })
        
        self.metrics[endpoint]['response_times'].append({
            'timestamp': now,
            'duration': duration
        })
        
        if success:
            self.metrics[endpoint]['last_success'] = now
        else:
            self.metrics[endpoint]['errors'].append({
                'timestamp': now,
                'error': error
            })
            self.metrics[endpoint]['last_error'] = now
            
        # Clean old data
        self._cleanup_old_data(endpoint)
        
        # Log significant events
        if duration > 10:
            logger.warning(f"Slow request to {endpoint}: {duration:.2f}s")
        if not success:
            logger.error(f"Failed request to {endpoint}: {error}")
    
    def _cleanup_old_data(self, endpoint: str):
        """Remove data older than the window"""
        cutoff = datetime.utcnow() - timedelta(minutes=self.window_minutes)
        
        for metric_type in ['requests', 'errors', 'response_times']:
            while (self.metrics[endpoint][metric_type] and 
                   self.metrics[endpoint][metric_type][0]['timestamp'] < cutoff):
                self.metrics[endpoint][metric_type].popleft()
    
    def get_stats(self, endpoint: str) -> Dict:
        """Get current statistics for an endpoint"""
        data = self.metrics[endpoint]
        
        # Calculate stats
        total_requests = len(data['requests'])
        total_errors = len(data['errors'])
        success_rate = (total_requests - total_errors) / total_requests * 100 if total_requests > 0 else 0
        
        response_times = [r['duration'] for r in data['response_times']]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        
        return {
            'endpoint': endpoint,
            'window_minutes': self.window_minutes,
            'total_requests': total_requests,
            'total_errors': total_errors,
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'max_response_time': max_response_time,
            'last_success': data['last_success'],
            'last_error': data['last_error']
        }
    
    def start_monitoring(self):
        """Start the monitoring thread"""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            logger.info("Webhook monitoring started")
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("Webhook monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Generate periodic reports
                self._generate_report()
                time.sleep(60)  # Report every minute
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                time.sleep(5)
    
    def _generate_report(self):
        """Generate and log a monitoring report"""
        report = []
        report.append("=" * 60)
        report.append(f"WEBHOOK MONITOR REPORT - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)
        
        for endpoint in self.metrics:
            stats = self.get_stats(endpoint)
            report.append(f"\nEndpoint: {endpoint}")
            report.append(f"  Requests: {stats['total_requests']}")
            report.append(f"  Errors: {stats['total_errors']}")
            report.append(f"  Success Rate: {stats['success_rate']:.1f}%")
            report.append(f"  Avg Response Time: {stats['avg_response_time']:.2f}s")
            report.append(f"  Max Response Time: {stats['max_response_time']:.2f}s")
            
            # Alert conditions
            if stats['success_rate'] < 95:
                report.append(f"  🚨 LOW SUCCESS RATE: {stats['success_rate']:.1f}%")
            
            if stats['avg_response_time'] > 5:
                report.append(f"  ⚠️ SLOW RESPONSE: {stats['avg_response_time']:.2f}s avg")
            
            if stats['max_response_time'] > 12:
                report.append(f"  🚨 TIMEOUT RISK: {stats['max_response_time']:.2f}s max")
        
        report.append("=" * 60)
        
        # Log the report
        for line in report:
            logger.info(line)
    
    def save_metrics(self, filename: str = "webhook_metrics.json"):
        """Save current metrics to file"""
        try:
            # Convert metrics to JSON-serializable format
            serializable_metrics = {}
            for endpoint, data in self.metrics.items():
                serializable_metrics[endpoint] = {
                    'requests': [
                        {
                            'timestamp': req['timestamp'].isoformat(),
                            'duration': req['duration'],
                            'success': req['success'],
                            'error': req['error']
                        }
                        for req in data['requests']
                    ],
                    'last_success': data['last_success'].isoformat() if data['last_success'] else None,
                    'last_error': data['last_error'].isoformat() if data['last_error'] else None
                }
            
            with open(filename, 'w') as f:
                json.dump(serializable_metrics, f, indent=2)
            
            logger.info(f"Metrics saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

# Global monitor instance
webhook_monitor = WebhookMonitor()

# Decorator to automatically monitor webhook functions
def monitor_webhook(endpoint_name: str):
    """Decorator to automatically monitor webhook performance"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                webhook_monitor.record_request(endpoint_name, duration, success=True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                webhook_monitor.record_request(endpoint_name, duration, success=False, error=str(e))
                raise
        return wrapper
    return decorator

# Example usage functions
def demo_usage():
    """Demonstrate how to use the monitor"""
    
    # Start monitoring
    webhook_monitor.start_monitoring()
    
    # Simulate some requests
    webhook_monitor.record_request("/twilio/voice", 1.5, success=True)
    webhook_monitor.record_request("/twilio/voice", 2.1, success=True)
    webhook_monitor.record_request("/twilio/voice", 0.8, success=True)
    webhook_monitor.record_request("/twilio/voice", 15.2, success=False, error="Timeout")
    
    # Get stats
    stats = webhook_monitor.get_stats("/twilio/voice")
    print(json.dumps(stats, indent=2, default=str))
    
    # Save metrics
    webhook_monitor.save_metrics()
    
    # Stop monitoring
    time.sleep(2)
    webhook_monitor.stop_monitoring()

if __name__ == "__main__":
    demo_usage()
