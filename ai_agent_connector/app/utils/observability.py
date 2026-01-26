"""
Observability integrations for external monitoring tools
Supports Datadog, Grafana, CloudWatch
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
import os


class ObservabilityBackend(Enum):
    """Supported observability backends"""
    DATADOG = "datadog"
    GRAFANA = "grafana"
    CLOUDWATCH = "cloudwatch"
    NONE = "none"  # No integration


@dataclass
class Metric:
    """A metric to send to observability backend"""
    name: str
    value: float
    tags: Dict[str, str]
    timestamp: Optional[float] = None
    metric_type: str = "gauge"  # gauge, counter, histogram


class ObservabilityClient:
    """
    Base class for observability integrations.
    Provides unified interface for sending metrics and logs.
    """
    
    def __init__(self, backend: ObservabilityBackend):
        """
        Initialize observability client.
        
        Args:
            backend: Observability backend type
        """
        self.backend = backend
        self.enabled = backend != ObservabilityBackend.NONE
    
    def send_metric(self, metric: Metric) -> bool:
        """
        Send a metric to the observability backend.
        
        Args:
            metric: Metric to send
            
        Returns:
            bool: True if sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            if self.backend == ObservabilityBackend.DATADOG:
                return self._send_to_datadog(metric)
            elif self.backend == ObservabilityBackend.GRAFANA:
                return self._send_to_grafana(metric)
            elif self.backend == ObservabilityBackend.CLOUDWATCH:
                return self._send_to_cloudwatch(metric)
        except Exception:
            return False
        
        return False
    
    def send_log(self, level: str, message: str, context: Dict[str, Any]) -> bool:
        """
        Send a log entry to the observability backend.
        
        Args:
            level: Log level (info, warning, error)
            message: Log message
            context: Additional context data
            
        Returns:
            bool: True if sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            if self.backend == ObservabilityBackend.DATADOG:
                return self._send_log_to_datadog(level, message, context)
            elif self.backend == ObservabilityBackend.GRAFANA:
                return self._send_log_to_grafana(level, message, context)
            elif self.backend == ObservabilityBackend.CLOUDWATCH:
                return self._send_log_to_cloudwatch(level, message, context)
        except Exception:
            return False
        
        return False
    
    def _send_to_datadog(self, metric: Metric) -> bool:
        """Send metric to Datadog"""
        try:
            from datadog import api, initialize
            
            # Initialize if not already done
            api_key = os.getenv('DATADOG_API_KEY')
            app_key = os.getenv('DATADOG_APP_KEY')
            
            if api_key and app_key:
                initialize(api_key=api_key, app_key=app_key)
                
                # Convert tags to Datadog format
                tags = [f"{k}:{v}" for k, v in metric.tags.items()]
                
                api.Metric.send(
                    metric=metric.name,
                    points=metric.value,
                    tags=tags,
                    type=metric.metric_type
                )
                return True
        except ImportError:
            pass
        except Exception:
            pass
        
        return False
    
    def _send_to_grafana(self, metric: Metric) -> bool:
        """Send metric to Grafana (via Prometheus or Loki)"""
        try:
            # Grafana typically uses Prometheus for metrics
            # This is a simplified implementation
            prometheus_url = os.getenv('PROMETHEUS_PUSHGATEWAY_URL')
            
            if prometheus_url:
                import requests
                import time
                
                # Format as Prometheus metric
                tags_str = ','.join([f'{k}="{v}"' for k, v in metric.tags.items()])
                metric_line = f'{metric.name}{{{tags_str}}} {metric.value}'
                
                # Push to Prometheus Pushgateway
                requests.post(
                    f'{prometheus_url}/metrics/job/ai_agent_connector',
                    data=metric_line
                )
                return True
        except ImportError:
            pass
        except Exception:
            pass
        
        return False
    
    def _send_to_cloudwatch(self, metric: Metric) -> bool:
        """Send metric to AWS CloudWatch"""
        try:
            import boto3
            
            cloudwatch = boto3.client('cloudwatch')
            
            # Convert tags to CloudWatch dimensions
            dimensions = [
                {'Name': k, 'Value': v}
                for k, v in metric.tags.items()
            ]
            
            cloudwatch.put_metric_data(
                Namespace='AIAgentConnector',
                MetricData=[{
                    'MetricName': metric.name,
                    'Value': metric.value,
                    'Dimensions': dimensions,
                    'Timestamp': metric.timestamp or None,
                    'Unit': 'None'
                }]
            )
            return True
        except ImportError:
            pass
        except Exception:
            pass
        
        return False
    
    def _send_log_to_datadog(self, level: str, message: str, context: Dict[str, Any]) -> bool:
        """Send log to Datadog"""
        try:
            from datadog import api, initialize
            
            api_key = os.getenv('DATADOG_API_KEY')
            app_key = os.getenv('DATADOG_APP_KEY')
            
            if api_key and app_key:
                initialize(api_key=api_key, app_key=app_key)
                
                api.Event.create(
                    title=f"[{level.upper()}] {message}",
                    text=json.dumps(context),
                    alert_type=level
                )
                return True
        except ImportError:
            pass
        except Exception:
            pass
        
        return False
    
    def _send_log_to_grafana(self, level: str, message: str, context: Dict[str, Any]) -> bool:
        """Send log to Grafana (via Loki)"""
        try:
            loki_url = os.getenv('GRAFANA_LOKI_URL')
            
            if loki_url:
                import requests
                import time
                
                # Format as Loki log entry
                log_entry = {
                    'streams': [{
                        'stream': {
                            'level': level,
                            'service': 'ai_agent_connector',
                            **context
                        },
                        'values': [[str(int(time.time() * 1e9)), message]]
                    }]
                }
                
                requests.post(
                    f'{loki_url}/loki/api/v1/push',
                    json=log_entry
                )
                return True
        except ImportError:
            pass
        except Exception:
            pass
        
        return False
    
    def _send_log_to_cloudwatch(self, level: str, message: str, context: Dict[str, Any]) -> bool:
        """Send log to AWS CloudWatch Logs"""
        try:
            import boto3
            import time
            
            logs = boto3.client('logs')
            log_group = os.getenv('CLOUDWATCH_LOG_GROUP', 'ai-agent-connector')
            
            log_message = json.dumps({
                'level': level,
                'message': message,
                **context
            })
            
            logs.put_log_events(
                logGroupName=log_group,
                logStreamName='queries',
                logEvents=[{
                    'timestamp': int(time.time() * 1000),
                    'message': log_message
                }]
            )
            return True
        except ImportError:
            pass
        except Exception:
            pass
        
        return False


class ObservabilityManager:
    """
    Manages observability integrations and sends metrics/logs to configured backends.
    """
    
    def __init__(self):
        """Initialize observability manager"""
        backend_str = os.getenv('OBSERVABILITY_BACKEND', 'none').lower()
        try:
            self.backend = ObservabilityBackend(backend_str)
        except ValueError:
            self.backend = ObservabilityBackend.NONE
        
        self.client = ObservabilityClient(self.backend)
    
    def send_query_metric(
        self,
        agent_id: str,
        query_type: str,
        execution_time_ms: float,
        success: bool
    ) -> None:
        """
        Send query execution metric.
        
        Args:
            agent_id: Agent ID
            query_type: Query type
            execution_time_ms: Execution time in milliseconds
            success: Whether query succeeded
        """
        metric = Metric(
            name='query.execution_time',
            value=execution_time_ms,
            tags={
                'agent_id': agent_id,
                'query_type': query_type,
                'status': 'success' if success else 'error'
            }
        )
        self.client.send_metric(metric)
        
        # Also send query count
        count_metric = Metric(
            name='query.count',
            value=1.0,
            tags={
                'agent_id': agent_id,
                'query_type': query_type,
                'status': 'success' if success else 'error'
            },
            metric_type='counter'
        )
        self.client.send_metric(count_metric)
    
    def send_alert_metric(
        self,
        alert_severity: str,
        agent_id: str,
        execution_time_ms: float
    ) -> None:
        """
        Send alert metric.
        
        Args:
            alert_severity: Alert severity
            agent_id: Agent ID
            execution_time_ms: Execution time that triggered alert
        """
        metric = Metric(
            name='query.alert',
            value=1.0,
            tags={
                'agent_id': agent_id,
                'severity': alert_severity,
                'execution_time_ms': str(execution_time_ms)
            },
            metric_type='counter'
        )
        self.client.send_metric(metric)
    
    def send_query_log(
        self,
        level: str,
        message: str,
        agent_id: str,
        query: Optional[str] = None,
        execution_time_ms: Optional[float] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Send query-related log.
        
        Args:
            level: Log level
            message: Log message
            agent_id: Agent ID
            query: Query string
            execution_time_ms: Execution time
            error: Error message if any
        """
        context = {
            'agent_id': agent_id
        }
        
        if query:
            context['query'] = query[:500]  # Truncate long queries
        if execution_time_ms is not None:
            context['execution_time_ms'] = execution_time_ms
        if error:
            context['error'] = error
        
        self.client.send_log(level, message, context)

