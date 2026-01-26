"""
Adoption Analytics System
Tracks DAU, query patterns, and feature usage with opt-in anonymous telemetry
"""

import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
import json


class FeatureType(Enum):
    """Types of features to track"""
    QUERY_EXECUTION = "query_execution"
    NATURAL_LANGUAGE_QUERY = "natural_language_query"
    WIDGET_QUERY = "widget_query"
    QUERY_OPTIMIZATION = "query_optimization"
    MULTI_AGENT_COLLABORATION = "multi_agent_collaboration"
    SCHEDULED_QUERY = "scheduled_query"
    QUERY_SHARING = "query_sharing"
    VISUALIZATION = "visualization"
    EXPORT = "export"
    PROMPT_STUDIO = "prompt_studio"
    SSO_LOGIN = "sso_login"
    AGENT_REGISTRATION = "agent_registration"
    DATABASE_CONNECTION = "database_connection"


class QueryPatternType(Enum):
    """Types of query patterns"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE_TABLE = "CREATE_TABLE"
    ALTER_TABLE = "ALTER_TABLE"
    DROP_TABLE = "DROP_TABLE"
    JOIN = "JOIN"
    AGGREGATION = "AGGREGATION"
    SUBQUERY = "SUBQUERY"
    CTE = "CTE"
    NATURAL_LANGUAGE = "NATURAL_LANGUAGE"


@dataclass
class TelemetryEvent:
    """Anonymous telemetry event"""
    event_id: str
    event_type: str  # FeatureType value
    timestamp: str
    anonymous_user_id: Optional[str] = None  # Hashed/anonymized user ID
    anonymous_agent_id: Optional[str] = None  # Hashed/anonymized agent ID
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class DailyActiveUser:
    """Daily active user record"""
    date: str  # YYYY-MM-DD format
    anonymous_user_id: str
    anonymous_agent_id: Optional[str] = None
    feature_count: int = 0
    query_count: int = 0
    last_activity: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class QueryPattern:
    """Query pattern analysis"""
    pattern_type: str  # QueryPatternType value
    count: int = 0
    avg_execution_time_ms: float = 0.0
    success_rate: float = 0.0
    unique_users: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['unique_users'] = list(self.unique_users)
        return result


@dataclass
class FeatureUsage:
    """Feature usage statistics"""
    feature_type: str  # FeatureType value
    total_uses: int = 0
    unique_users: Set[str] = field(default_factory=set)
    unique_agents: Set[str] = field(default_factory=set)
    last_used: Optional[str] = None
    daily_usage: Dict[str, int] = field(default_factory=dict)  # date -> count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['unique_users'] = list(self.unique_users)
        result['unique_agents'] = list(self.unique_agents)
        return result


class AdoptionAnalytics:
    """Manages adoption analytics and telemetry"""
    
    def __init__(self, telemetry_enabled: bool = True, anonymize_ids: bool = True):
        """
        Initialize adoption analytics
        
        Args:
            telemetry_enabled: Whether telemetry is enabled (opt-in)
            anonymize_ids: Whether to anonymize user/agent IDs
        """
        self.telemetry_enabled = telemetry_enabled
        self.anonymize_ids = anonymize_ids
        
        # Storage for telemetry events (in-memory, should use database in production)
        self.events: List[TelemetryEvent] = []
        self.max_events = 100000  # Maximum events to keep in memory
        
        # Daily active users tracking
        self.dau_records: Dict[str, Dict[str, DailyActiveUser]] = {}  # date -> {anonymous_user_id -> DAU}
        
        # Query patterns tracking
        self.query_patterns: Dict[str, QueryPattern] = {}  # pattern_type -> QueryPattern
        
        # Feature usage tracking
        self.feature_usage: Dict[str, FeatureUsage] = {}  # feature_type -> FeatureUsage
        
        # Session tracking
        self.user_sessions: Dict[str, Dict[str, Any]] = {}  # session_id -> session data
        
        # Opt-in status (user_id -> enabled)
        self.telemetry_opt_in: Dict[str, bool] = {}
    
    def _anonymize_id(self, identifier: str) -> str:
        """Anonymize an identifier using SHA256 hash"""
        if not self.anonymize_ids:
            return identifier
        
        # Use SHA256 with a salt (in production, use a secret salt)
        salt = "analytics_salt"  # Should be from environment variable in production
        hash_input = f"{salt}:{identifier}".encode('utf-8')
        hash_value = hashlib.sha256(hash_input).hexdigest()
        return hash_value[:16]  # Use first 16 chars for shorter IDs
    
    def opt_in_telemetry(self, user_id: str) -> None:
        """Opt-in a user to telemetry"""
        self.telemetry_opt_in[user_id] = True
    
    def opt_out_telemetry(self, user_id: str) -> None:
        """Opt-out a user from telemetry"""
        self.telemetry_opt_in[user_id] = False
        # Remove existing events for this user
        if not self.anonymize_ids:
            self.events = [e for e in self.events if e.anonymous_user_id != user_id]
    
    def is_opted_in(self, user_id: str) -> bool:
        """Check if user has opted in to telemetry"""
        # Default to opted-in if not explicitly set
        return self.telemetry_opt_in.get(user_id, True)
    
    def track_event(
        self,
        feature_type: FeatureType,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[TelemetryEvent]:
        """
        Track a telemetry event
        
        Args:
            feature_type: Type of feature being used
            user_id: User ID (will be anonymized)
            agent_id: Agent ID (will be anonymized)
            session_id: Session ID
            metadata: Additional metadata
            
        Returns:
            TelemetryEvent if tracked, None if telemetry disabled or user opted out
        """
        if not self.telemetry_enabled:
            return None
        
        # Check opt-in status
        if user_id and not self.is_opted_in(user_id):
            return None
        
        # Anonymize IDs
        anonymous_user_id = self._anonymize_id(user_id) if user_id else None
        anonymous_agent_id = self._anonymize_id(agent_id) if agent_id else None
        
        # Create event
        event = TelemetryEvent(
            event_id=str(uuid.uuid4()),
            event_type=feature_type.value,
            timestamp=datetime.utcnow().isoformat(),
            anonymous_user_id=anonymous_user_id,
            anonymous_agent_id=anonymous_agent_id,
            session_id=session_id or str(uuid.uuid4()),
            metadata=metadata or {}
        )
        
        # Store event
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events.pop(0)  # Remove oldest event
        
        # Update DAU tracking
        self._update_dau(event)
        
        # Update feature usage
        self._update_feature_usage(event)
        
        return event
    
    def _update_dau(self, event: TelemetryEvent) -> None:
        """Update daily active user tracking"""
        date = datetime.utcnow().strftime('%Y-%m-%d')
        
        if date not in self.dau_records:
            self.dau_records[date] = {}
        
        if event.anonymous_user_id:
            if event.anonymous_user_id not in self.dau_records[date]:
                self.dau_records[date][event.anonymous_user_id] = DailyActiveUser(
                    date=date,
                    anonymous_user_id=event.anonymous_user_id,
                    anonymous_agent_id=event.anonymous_agent_id,
                    feature_count=0,
                    query_count=0,
                    last_activity=event.timestamp
                )
            
            dau = self.dau_records[date][event.anonymous_user_id]
            dau.feature_count += 1
            dau.last_activity = event.timestamp
            
            if event.event_type in [FeatureType.QUERY_EXECUTION.value, FeatureType.NATURAL_LANGUAGE_QUERY.value]:
                dau.query_count += 1
    
    def _update_feature_usage(self, event: TelemetryEvent) -> None:
        """Update feature usage tracking"""
        feature_type = event.event_type
        
        if feature_type not in self.feature_usage:
            self.feature_usage[feature_type] = FeatureUsage(
                feature_type=feature_type,
                total_uses=0,
                unique_users=set(),
                unique_agents=set(),
                last_used=None,
                daily_usage={}
            )
        
        usage = self.feature_usage[feature_type]
        usage.total_uses += 1
        usage.last_used = event.timestamp
        
        if event.anonymous_user_id:
            usage.unique_users.add(event.anonymous_user_id)
        
        if event.anonymous_agent_id:
            usage.unique_agents.add(event.anonymous_agent_id)
        
        # Update daily usage
        date = datetime.utcnow().strftime('%Y-%m-%d')
        usage.daily_usage[date] = usage.daily_usage.get(date, 0) + 1
    
    def track_query_pattern(
        self,
        pattern_type: QueryPatternType,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        execution_time_ms: float = 0.0,
        success: bool = True
    ) -> None:
        """
        Track a query pattern
        
        Args:
            pattern_type: Type of query pattern
            user_id: User ID (will be anonymized)
            agent_id: Agent ID (will be anonymized)
            execution_time_ms: Query execution time in milliseconds
            success: Whether query was successful
        """
        if not self.telemetry_enabled:
            return
        
        # Check opt-in status
        if user_id and not self.is_opted_in(user_id):
            return
        
        pattern_key = pattern_type.value
        
        if pattern_key not in self.query_patterns:
            self.query_patterns[pattern_key] = QueryPattern(
                pattern_type=pattern_key,
                count=0,
                avg_execution_time_ms=0.0,
                success_rate=0.0,
                unique_users=set()
            )
        
        pattern = self.query_patterns[pattern_key]
        pattern.count += 1
        
        # Update average execution time
        total_time = pattern.avg_execution_time_ms * (pattern.count - 1) + execution_time_ms
        pattern.avg_execution_time_ms = total_time / pattern.count
        
        # Update success rate
        total_successes = pattern.success_rate * (pattern.count - 1) + (1.0 if success else 0.0)
        pattern.success_rate = total_successes / pattern.count
        
        # Track unique users
        if user_id:
            anonymous_user_id = self._anonymize_id(user_id)
            pattern.unique_users.add(anonymous_user_id)
    
    def get_dau(self, date: Optional[str] = None) -> int:
        """
        Get daily active users for a date
        
        Args:
            date: Date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Number of daily active users
        """
        if date is None:
            date = datetime.utcnow().strftime('%Y-%m-%d')
        
        if date not in self.dau_records:
            return 0
        
        return len(self.dau_records[date])
    
    def get_dau_timeseries(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Get DAU timeseries data
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            List of {date, dau} dictionaries
        """
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        timeseries = []
        current = start
        
        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            dau = self.get_dau(date_str)
            timeseries.append({
                'date': date_str,
                'dau': dau
            })
            current += timedelta(days=1)
        
        return timeseries
    
    def get_query_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Get query pattern statistics"""
        return {
            pattern_type: pattern.to_dict()
            for pattern_type, pattern in self.query_patterns.items()
        }
    
    def get_feature_usage(self, feature_type: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get feature usage statistics
        
        Args:
            feature_type: Optional feature type to filter by
            
        Returns:
            Dictionary of feature usage statistics
        """
        if feature_type:
            if feature_type in self.feature_usage:
                return {feature_type: self.feature_usage[feature_type].to_dict()}
            return {}
        
        return {
            ft: usage.to_dict()
            for ft, usage in self.feature_usage.items()
        }
    
    def get_top_features(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top used features
        
        Args:
            limit: Maximum number of features to return
            
        Returns:
            List of feature usage statistics sorted by total_uses
        """
        features = list(self.feature_usage.values())
        features.sort(key=lambda x: x.total_uses, reverse=True)
        
        return [f.to_dict() for f in features[:limit]]
    
    def get_adoption_summary(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get adoption analytics summary
        
        Args:
            start_date: Optional start date in YYYY-MM-DD format
            end_date: Optional end date in YYYY-MM-DD format
            
        Returns:
            Dictionary with adoption metrics
        """
        if start_date is None:
            start_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
        if end_date is None:
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
        
        # Calculate unique users across period
        unique_users = set()
        for date, users in self.dau_records.items():
            if start_date <= date <= end_date:
                unique_users.update(users.keys())
        
        # Calculate total events in period
        period_events = [
            e for e in self.events
            if start_date <= e.timestamp[:10] <= end_date
        ]
        
        # Calculate feature adoption
        feature_adoption = {}
        for feature_type, usage in self.feature_usage.items():
            period_usage = sum(
                count for date, count in usage.daily_usage.items()
                if start_date <= date <= end_date
            )
            if period_usage > 0:
                feature_adoption[feature_type] = {
                    'total_uses': period_usage,
                    'unique_users': len([
                        u for u in usage.unique_users
                        if any(start_date <= date <= end_date for date in self.dau_records.keys())
                    ])
                }
        
        return {
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'dau': {
                'current': self.get_dau(end_date),
                'timeseries': self.get_dau_timeseries(start_date, end_date)
            },
            'unique_users': len(unique_users),
            'total_events': len(period_events),
            'top_features': self.get_top_features(10),
            'feature_adoption': feature_adoption,
            'query_patterns': {
                pattern_type: {
                    'count': pattern.count,
                    'avg_execution_time_ms': pattern.avg_execution_time_ms,
                    'success_rate': pattern.success_rate,
                    'unique_users': len(pattern.unique_users)
                }
                for pattern_type, pattern in self.query_patterns.items()
            }
        }
    
    def export_to_json(self, file_path: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> None:
        """
        Export analytics data to JSON file
        
        Args:
            file_path: Path to output JSON file
            start_date: Optional start date filter
            end_date: Optional end date filter
        """
        export_data = {
            'exported_at': datetime.utcnow().isoformat(),
            'summary': self.get_adoption_summary(start_date, end_date),
            'dau_timeseries': self.get_dau_timeseries(
                start_date or (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d'),
                end_date or datetime.utcnow().strftime('%Y-%m-%d')
            ),
            'query_patterns': self.get_query_patterns(),
            'feature_usage': self.get_feature_usage()
        }
        
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def export_to_csv(self, file_path: str, data_type: str = 'summary', start_date: Optional[str] = None, end_date: Optional[str] = None) -> None:
        """
        Export analytics data to CSV file
        
        Args:
            file_path: Path to output CSV file
            data_type: Type of data to export ('dau', 'features', 'patterns', 'summary')
            start_date: Optional start date filter
            end_date: Optional end date filter
        """
        import csv
        
        if start_date is None:
            start_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
        if end_date is None:
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
        
        with open(file_path, 'w', newline='') as f:
            if data_type == 'dau':
                writer = csv.DictWriter(f, fieldnames=['date', 'dau'])
                writer.writeheader()
                for row in self.get_dau_timeseries(start_date, end_date):
                    writer.writerow(row)
            
            elif data_type == 'features':
                writer = csv.DictWriter(f, fieldnames=['feature_type', 'total_uses', 'unique_users', 'unique_agents', 'last_used'])
                writer.writeheader()
                for feature_type, usage in self.get_feature_usage().items():
                    writer.writerow({
                        'feature_type': feature_type,
                        'total_uses': usage['total_uses'],
                        'unique_users': len(usage['unique_users']),
                        'unique_agents': len(usage['unique_agents']),
                        'last_used': usage.get('last_used', '')
                    })
            
            elif data_type == 'patterns':
                writer = csv.DictWriter(f, fieldnames=['pattern_type', 'count', 'avg_execution_time_ms', 'success_rate', 'unique_users'])
                writer.writeheader()
                for pattern_type, pattern in self.get_query_patterns().items():
                    writer.writerow({
                        'pattern_type': pattern_type,
                        'count': pattern['count'],
                        'avg_execution_time_ms': pattern['avg_execution_time_ms'],
                        'success_rate': pattern['success_rate'],
                        'unique_users': len(pattern['unique_users'])
                    })
            
            elif data_type == 'summary':
                summary = self.get_adoption_summary(start_date, end_date)
                # Export as flat CSV
                writer = csv.DictWriter(f, fieldnames=['metric', 'value'])
                writer.writeheader()
                writer.writerow({'metric': 'unique_users', 'value': summary['unique_users']})
                writer.writerow({'metric': 'total_events', 'value': summary['total_events']})
                writer.writerow({'metric': 'current_dau', 'value': summary['dau']['current']})


# Global instance
adoption_analytics = AdoptionAnalytics()

