"""
Scheduled query system
Allows scheduling recurring queries (daily reports, etc.)
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import uuid
import json


class ScheduleFrequency(Enum):
    """Schedule frequency"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"  # Cron expression


@dataclass
class ScheduledQuery:
    """A scheduled query"""
    schedule_id: str
    agent_id: str
    query: str
    query_type: str
    schedule_frequency: ScheduleFrequency
    schedule_config: Dict[str, Any]  # time, day_of_week, etc.
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    notification_config: Optional[Dict[str, Any]] = None  # email, webhook, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'schedule_id': self.schedule_id,
            'agent_id': self.agent_id,
            'query': self.query,
            'query_type': self.query_type,
            'schedule_frequency': self.schedule_frequency.value,
            'schedule_config': self.schedule_config,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'last_run_at': self.last_run_at,
            'next_run_at': self.next_run_at,
            'run_count': self.run_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'notification_config': self.notification_config,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduledQuery':
        """Create from dictionary"""
        return cls(
            schedule_id=data['schedule_id'],
            agent_id=data['agent_id'],
            query=data['query'],
            query_type=data['query_type'],
            schedule_frequency=ScheduleFrequency(data['schedule_frequency']),
            schedule_config=data['schedule_config'],
            is_active=data.get('is_active', True),
            created_at=data.get('created_at', datetime.utcnow().isoformat()),
            last_run_at=data.get('last_run_at'),
            next_run_at=data.get('next_run_at'),
            run_count=data.get('run_count', 0),
            success_count=data.get('success_count', 0),
            failure_count=data.get('failure_count', 0),
            notification_config=data.get('notification_config'),
            metadata=data.get('metadata', {})
        )


class QueryScheduler:
    """
    Manages scheduled queries.
    """
    
    def __init__(self):
        """Initialize query scheduler"""
        # schedule_id -> ScheduledQuery
        self._schedules: Dict[str, ScheduledQuery] = {}
        # agent_id -> list of schedule_ids
        self._agent_schedules: Dict[str, List[str]] = {}
    
    def create_schedule(
        self,
        agent_id: str,
        query: str,
        query_type: str,
        frequency: ScheduleFrequency,
        schedule_config: Dict[str, Any],
        notification_config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ScheduledQuery:
        """
        Create a scheduled query.
        
        Args:
            agent_id: Agent ID
            query: Query to execute
            query_type: Type of query
            frequency: Schedule frequency
            schedule_config: Schedule configuration (time, day_of_week, etc.)
            notification_config: Notification configuration
            metadata: Additional metadata
            
        Returns:
            ScheduledQuery object
        """
        schedule_id = str(uuid.uuid4())
        
        # Calculate next run time
        next_run_at = self._calculate_next_run(frequency, schedule_config)
        
        schedule = ScheduledQuery(
            schedule_id=schedule_id,
            agent_id=agent_id,
            query=query,
            query_type=query_type,
            schedule_frequency=frequency,
            schedule_config=schedule_config,
            next_run_at=next_run_at.isoformat() if next_run_at else None,
            notification_config=notification_config,
            metadata=metadata or {}
        )
        
        self._schedules[schedule_id] = schedule
        
        # Track by agent
        if agent_id not in self._agent_schedules:
            self._agent_schedules[agent_id] = []
        self._agent_schedules[agent_id].append(schedule_id)
        
        return schedule
    
    def get_schedule(self, schedule_id: str) -> Optional[ScheduledQuery]:
        """Get a scheduled query"""
        return self._schedules.get(schedule_id)
    
    def list_schedules(
        self,
        agent_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[ScheduledQuery]:
        """
        List scheduled queries.
        
        Args:
            agent_id: Filter by agent ID
            is_active: Filter by active status
            
        Returns:
            List of ScheduledQuery objects
        """
        schedules = list(self._schedules.values())
        
        if agent_id:
            schedules = [s for s in schedules if s.agent_id == agent_id]
        
        if is_active is not None:
            schedules = [s for s in schedules if s.is_active == is_active]
        
        return schedules
    
    def update_schedule(
        self,
        schedule_id: str,
        query: Optional[str] = None,
        frequency: Optional[ScheduleFrequency] = None,
        schedule_config: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None,
        notification_config: Optional[Dict[str, Any]] = None
    ) -> Optional[ScheduledQuery]:
        """
        Update a scheduled query.
        
        Args:
            schedule_id: Schedule ID
            query: New query
            frequency: New frequency
            schedule_config: New schedule config
            is_active: Active status
            notification_config: New notification config
            
        Returns:
            Updated ScheduledQuery or None if not found
        """
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return None
        
        if query is not None:
            schedule.query = query
        
        if frequency is not None:
            schedule.schedule_frequency = frequency
        
        if schedule_config is not None:
            schedule.schedule_config = schedule_config
            # Recalculate next run
            next_run = self._calculate_next_run(schedule.schedule_frequency, schedule.schedule_config)
            schedule.next_run_at = next_run.isoformat() if next_run else None
        
        if is_active is not None:
            schedule.is_active = is_active
        
        if notification_config is not None:
            schedule.notification_config = notification_config
        
        return schedule
    
    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a scheduled query"""
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return False
        
        # Remove from agent tracking
        if schedule.agent_id in self._agent_schedules:
            self._agent_schedules[schedule.agent_id] = [
                sid for sid in self._agent_schedules[schedule.agent_id] if sid != schedule_id
            ]
        
        del self._schedules[schedule_id]
        return True
    
    def get_due_schedules(self) -> List[ScheduledQuery]:
        """
        Get schedules that are due to run.
        
        Returns:
            List of ScheduledQuery objects that are due
        """
        now = datetime.utcnow()
        due = []
        
        for schedule in self._schedules.values():
            if not schedule.is_active:
                continue
            
            if schedule.next_run_at:
                next_run = datetime.fromisoformat(schedule.next_run_at.replace('Z', '+00:00'))
                if next_run <= now:
                    due.append(schedule)
        
        return due
    
    def mark_run(
        self,
        schedule_id: str,
        success: bool,
        result: Optional[Any] = None
    ) -> None:
        """
        Mark a schedule as run.
        
        Args:
            schedule_id: Schedule ID
            success: Whether the run was successful
            result: Optional result data
        """
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return
        
        schedule.last_run_at = datetime.utcnow().isoformat()
        schedule.run_count += 1
        
        if success:
            schedule.success_count += 1
        else:
            schedule.failure_count += 1
        
        # Calculate next run
        next_run = self._calculate_next_run(
            schedule.schedule_frequency,
            schedule.schedule_config
        )
        schedule.next_run_at = next_run.isoformat() if next_run else None
    
    def _calculate_next_run(
        self,
        frequency: ScheduleFrequency,
        config: Dict[str, Any]
    ) -> Optional[datetime]:
        """Calculate next run time"""
        now = datetime.utcnow()
        
        if frequency == ScheduleFrequency.HOURLY:
            return now + timedelta(hours=1)
        
        elif frequency == ScheduleFrequency.DAILY:
            time_str = config.get('time', '00:00')
            hour, minute = map(int, time_str.split(':'))
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run
        
        elif frequency == ScheduleFrequency.WEEKLY:
            day_of_week = config.get('day_of_week', 0)  # 0 = Monday
            time_str = config.get('time', '00:00')
            hour, minute = map(int, time_str.split(':'))
            
            days_ahead = day_of_week - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return next_run
        
        elif frequency == ScheduleFrequency.MONTHLY:
            day = config.get('day', 1)
            time_str = config.get('time', '00:00')
            hour, minute = map(int, time_str.split(':'))
            
            next_run = now.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                # Move to next month
                if next_run.month == 12:
                    next_run = next_run.replace(year=next_run.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=next_run.month + 1)
            
            return next_run
        
        # CUSTOM (cron) - simplified implementation
        elif frequency == ScheduleFrequency.CUSTOM:
            # For now, just add 1 day
            # Full cron parsing would require a library like croniter
            return now + timedelta(days=1)
        
        return None

