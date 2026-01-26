"""
Unit tests for adoption analytics system
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from ai_agent_connector.app.utils.adoption_analytics import (
    AdoptionAnalytics,
    TelemetryEvent,
    DailyActiveUser,
    QueryPattern,
    FeatureUsage,
    FeatureType,
    QueryPatternType
)


class TestTelemetryEvent(unittest.TestCase):
    """Test cases for TelemetryEvent"""
    
    def test_create_telemetry_event(self):
        """Test creating a telemetry event"""
        event = TelemetryEvent(
            event_id="event-123",
            event_type="query_execution",
            timestamp=datetime.utcnow().isoformat(),
            anonymous_user_id="user-hash",
            anonymous_agent_id="agent-hash",
            session_id="session-123"
        )
        
        self.assertEqual(event.event_id, "event-123")
        self.assertEqual(event.event_type, "query_execution")
        self.assertEqual(event.anonymous_user_id, "user-hash")
        self.assertIsNotNone(event.timestamp)
    
    def test_telemetry_event_to_dict(self):
        """Test converting telemetry event to dictionary"""
        event = TelemetryEvent(
            event_id="event-123",
            event_type="query_execution",
            timestamp="2024-01-01T00:00:00",
            metadata={"key": "value"}
        )
        
        event_dict = event.to_dict()
        self.assertIn("event_id", event_dict)
        self.assertIn("event_type", event_dict)
        self.assertEqual(event_dict["metadata"]["key"], "value")


class TestAdoptionAnalytics(unittest.TestCase):
    """Test cases for AdoptionAnalytics"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analytics = AdoptionAnalytics(telemetry_enabled=True, anonymize_ids=True)
    
    def test_init_defaults(self):
        """Test initialization with defaults"""
        analytics = AdoptionAnalytics()
        self.assertTrue(analytics.telemetry_enabled)
        self.assertTrue(analytics.anonymize_ids)
    
    def test_init_with_options(self):
        """Test initialization with custom options"""
        analytics = AdoptionAnalytics(telemetry_enabled=False, anonymize_ids=False)
        self.assertFalse(analytics.telemetry_enabled)
        self.assertFalse(analytics.anonymize_ids)
    
    def test_anonymize_id(self):
        """Test ID anonymization"""
        original_id = "user-123"
        anonymized = self.analytics._anonymize_id(original_id)
        
        self.assertNotEqual(original_id, anonymized)
        self.assertEqual(len(anonymized), 16)  # First 16 chars of hash
        # Same ID should produce same hash
        anonymized2 = self.analytics._anonymize_id(original_id)
        self.assertEqual(anonymized, anonymized2)
    
    def test_anonymize_id_disabled(self):
        """Test ID anonymization when disabled"""
        analytics = AdoptionAnalytics(anonymize_ids=False)
        original_id = "user-123"
        anonymized = analytics._anonymize_id(original_id)
        
        self.assertEqual(original_id, anonymized)
    
    def test_opt_in_telemetry(self):
        """Test opting in to telemetry"""
        user_id = "user-123"
        self.analytics.opt_in_telemetry(user_id)
        
        self.assertTrue(self.analytics.is_opted_in(user_id))
    
    def test_opt_out_telemetry(self):
        """Test opting out of telemetry"""
        user_id = "user-123"
        self.analytics.opt_in_telemetry(user_id)
        self.analytics.opt_out_telemetry(user_id)
        
        self.assertFalse(self.analytics.is_opted_in(user_id))
    
    def test_is_opted_in_default(self):
        """Test that users are opted-in by default"""
        user_id = "user-123"
        # User not explicitly set should default to opted-in
        self.assertTrue(self.analytics.is_opted_in(user_id))
    
    def test_track_event_telemetry_disabled(self):
        """Test tracking event when telemetry is disabled"""
        analytics = AdoptionAnalytics(telemetry_enabled=False)
        event = analytics.track_event(
            FeatureType.QUERY_EXECUTION,
            user_id="user-123"
        )
        
        self.assertIsNone(event)
        self.assertEqual(len(analytics.events), 0)
    
    def test_track_event_user_opted_out(self):
        """Test tracking event when user has opted out"""
        user_id = "user-123"
        self.analytics.opt_out_telemetry(user_id)
        
        event = self.analytics.track_event(
            FeatureType.QUERY_EXECUTION,
            user_id=user_id
        )
        
        self.assertIsNone(event)
        self.assertEqual(len(self.analytics.events), 0)
    
    def test_track_event_success(self):
        """Test successfully tracking an event"""
        event = self.analytics.track_event(
            FeatureType.QUERY_EXECUTION,
            user_id="user-123",
            agent_id="agent-456",
            metadata={"key": "value"}
        )
        
        self.assertIsNotNone(event)
        self.assertEqual(len(self.analytics.events), 1)
        self.assertEqual(event.event_type, FeatureType.QUERY_EXECUTION.value)
        self.assertIsNotNone(event.anonymous_user_id)
        self.assertIsNotNone(event.anonymous_agent_id)
        self.assertEqual(event.metadata["key"], "value")
    
    def test_track_event_anonymizes_ids(self):
        """Test that event tracking anonymizes user/agent IDs"""
        event = self.analytics.track_event(
            FeatureType.QUERY_EXECUTION,
            user_id="user-123",
            agent_id="agent-456"
        )
        
        self.assertNotEqual(event.anonymous_user_id, "user-123")
        self.assertNotEqual(event.anonymous_agent_id, "agent-456")
    
    def test_track_event_generates_session_id(self):
        """Test that event tracking generates session ID if not provided"""
        event = self.analytics.track_event(
            FeatureType.QUERY_EXECUTION,
            user_id="user-123"
        )
        
        self.assertIsNotNone(event.session_id)
    
    def test_track_event_max_events_limit(self):
        """Test that events are limited to max_events"""
        self.analytics.max_events = 10
        
        # Add 15 events
        for i in range(15):
            self.analytics.track_event(
                FeatureType.QUERY_EXECUTION,
                user_id=f"user-{i}"
            )
        
        # Should only keep last 10 events
        self.assertEqual(len(self.analytics.events), 10)
        # First event should be removed (oldest)
        self.assertEqual(self.analytics.events[0].user_id, f"user-5")
    
    def test_track_event_updates_dau(self):
        """Test that tracking event updates DAU"""
        self.analytics.track_event(
            FeatureType.QUERY_EXECUTION,
            user_id="user-123"
        )
        
        date = datetime.utcnow().strftime('%Y-%m-%d')
        self.assertIn(date, self.analytics.dau_records)
        self.assertGreater(len(self.analytics.dau_records[date]), 0)
    
    def test_track_event_updates_feature_usage(self):
        """Test that tracking event updates feature usage"""
        self.analytics.track_event(
            FeatureType.QUERY_EXECUTION,
            user_id="user-123"
        )
        
        feature_type = FeatureType.QUERY_EXECUTION.value
        self.assertIn(feature_type, self.analytics.feature_usage)
        self.assertEqual(self.analytics.feature_usage[feature_type].total_uses, 1)
    
    def test_get_dau(self):
        """Test getting DAU for a date"""
        date = datetime.utcnow().strftime('%Y-%m-%d')
        
        # Track events for 3 users
        for i in range(3):
            self.analytics.track_event(
                FeatureType.QUERY_EXECUTION,
                user_id=f"user-{i}"
            )
        
        dau = self.analytics.get_dau(date)
        self.assertEqual(dau, 3)
    
    def test_get_dau_empty_date(self):
        """Test getting DAU for date with no activity"""
        date = "2024-01-01"
        dau = self.analytics.get_dau(date)
        self.assertEqual(dau, 0)
    
    def test_get_dau_timeseries(self):
        """Test getting DAU timeseries"""
        start_date = "2024-01-01"
        end_date = "2024-01-03"
        
        timeseries = self.analytics.get_dau_timeseries(start_date, end_date)
        
        self.assertEqual(len(timeseries), 3)
        self.assertEqual(timeseries[0]["date"], "2024-01-01")
        self.assertEqual(timeseries[0]["dau"], 0)
        self.assertEqual(timeseries[2]["date"], "2024-01-03")
    
    def test_track_query_pattern(self):
        """Test tracking query pattern"""
        self.analytics.track_query_pattern(
            QueryPatternType.SELECT,
            user_id="user-123",
            agent_id="agent-456",
            execution_time_ms=145.5,
            success=True
        )
        
        pattern_key = QueryPatternType.SELECT.value
        self.assertIn(pattern_key, self.analytics.query_patterns)
        pattern = self.analytics.query_patterns[pattern_key]
        self.assertEqual(pattern.count, 1)
        self.assertEqual(pattern.avg_execution_time_ms, 145.5)
        self.assertEqual(pattern.success_rate, 1.0)
    
    def test_track_query_pattern_telemetry_disabled(self):
        """Test tracking query pattern when telemetry is disabled"""
        analytics = AdoptionAnalytics(telemetry_enabled=False)
        analytics.track_query_pattern(
            QueryPatternType.SELECT,
            user_id="user-123"
        )
        
        self.assertEqual(len(analytics.query_patterns), 0)
    
    def test_track_query_pattern_user_opted_out(self):
        """Test tracking query pattern when user opted out"""
        user_id = "user-123"
        self.analytics.opt_out_telemetry(user_id)
        
        self.analytics.track_query_pattern(
            QueryPatternType.SELECT,
            user_id=user_id
        )
        
        self.assertEqual(len(self.analytics.query_patterns), 0)
    
    def test_track_query_pattern_updates_average(self):
        """Test that query pattern tracking updates average execution time"""
        # Track multiple patterns
        self.analytics.track_query_pattern(
            QueryPatternType.SELECT,
            execution_time_ms=100.0,
            success=True
        )
        self.analytics.track_query_pattern(
            QueryPatternType.SELECT,
            execution_time_ms=200.0,
            success=True
        )
        
        pattern = self.analytics.query_patterns[QueryPatternType.SELECT.value]
        self.assertEqual(pattern.avg_execution_time_ms, 150.0)
        self.assertEqual(pattern.count, 2)
    
    def test_track_query_pattern_updates_success_rate(self):
        """Test that query pattern tracking updates success rate"""
        # Track 3 successful and 1 failed
        for _ in range(3):
            self.analytics.track_query_pattern(
                QueryPatternType.SELECT,
                success=True
            )
        self.analytics.track_query_pattern(
            QueryPatternType.SELECT,
            success=False
        )
        
        pattern = self.analytics.query_patterns[QueryPatternType.SELECT.value]
        self.assertEqual(pattern.success_rate, 0.75)
    
    def test_track_query_pattern_tracks_unique_users(self):
        """Test that query pattern tracks unique users"""
        for i in range(3):
            self.analytics.track_query_pattern(
                QueryPatternType.SELECT,
                user_id=f"user-{i}"
            )
        
        pattern = self.analytics.query_patterns[QueryPatternType.SELECT.value]
        self.assertEqual(len(pattern.unique_users), 3)
    
    def test_get_query_patterns(self):
        """Test getting query patterns"""
        self.analytics.track_query_pattern(QueryPatternType.SELECT, execution_time_ms=100.0)
        self.analytics.track_query_pattern(QueryPatternType.INSERT, execution_time_ms=200.0)
        
        patterns = self.analytics.get_query_patterns()
        
        self.assertEqual(len(patterns), 2)
        self.assertIn(QueryPatternType.SELECT.value, patterns)
        self.assertIn(QueryPatternType.INSERT.value, patterns)
    
    def test_get_feature_usage(self):
        """Test getting feature usage"""
        self.analytics.track_event(FeatureType.QUERY_EXECUTION, user_id="user-1")
        self.analytics.track_event(FeatureType.WIDGET_QUERY, user_id="user-2")
        
        usage = self.analytics.get_feature_usage()
        
        self.assertGreaterEqual(len(usage), 2)
        self.assertIn(FeatureType.QUERY_EXECUTION.value, usage)
        self.assertIn(FeatureType.WIDGET_QUERY.value, usage)
    
    def test_get_feature_usage_filtered(self):
        """Test getting feature usage filtered by type"""
        self.analytics.track_event(FeatureType.QUERY_EXECUTION, user_id="user-1")
        self.analytics.track_event(FeatureType.WIDGET_QUERY, user_id="user-2")
        
        usage = self.analytics.get_feature_usage(feature_type=FeatureType.QUERY_EXECUTION.value)
        
        self.assertEqual(len(usage), 1)
        self.assertIn(FeatureType.QUERY_EXECUTION.value, usage)
    
    def test_get_top_features(self):
        """Test getting top features"""
        # Track events for different features
        for i in range(10):
            self.analytics.track_event(FeatureType.QUERY_EXECUTION, user_id="user-1")
        for i in range(5):
            self.analytics.track_event(FeatureType.WIDGET_QUERY, user_id="user-1")
        for i in range(3):
            self.analytics.track_event(FeatureType.VISUALIZATION, user_id="user-1")
        
        top_features = self.analytics.get_top_features(limit=2)
        
        self.assertEqual(len(top_features), 2)
        self.assertEqual(top_features[0]["feature_type"], FeatureType.QUERY_EXECUTION.value)
        self.assertEqual(top_features[0]["total_uses"], 10)
        self.assertEqual(top_features[1]["feature_type"], FeatureType.WIDGET_QUERY.value)
        self.assertEqual(top_features[1]["total_uses"], 5)
    
    def test_get_adoption_summary(self):
        """Test getting adoption summary"""
        # Track some events
        for i in range(5):
            self.analytics.track_event(
                FeatureType.QUERY_EXECUTION,
                user_id=f"user-{i}"
            )
        
        start_date = datetime.utcnow().strftime('%Y-%m-%d')
        end_date = datetime.utcnow().strftime('%Y-%m-%d')
        
        summary = self.analytics.get_adoption_summary(start_date, end_date)
        
        self.assertIn("period", summary)
        self.assertIn("dau", summary)
        self.assertIn("unique_users", summary)
        self.assertIn("total_events", summary)
        self.assertIn("top_features", summary)
        self.assertIn("feature_adoption", summary)
        self.assertIn("query_patterns", summary)
    
    def test_get_adoption_summary_default_dates(self):
        """Test getting adoption summary with default dates"""
        summary = self.analytics.get_adoption_summary()
        
        self.assertIn("period", summary)
        self.assertIn("dau", summary)
    
    def test_feature_usage_tracks_unique_users(self):
        """Test that feature usage tracks unique users"""
        # Track events for same feature from different users
        for i in range(5):
            self.analytics.track_event(
                FeatureType.QUERY_EXECUTION,
                user_id=f"user-{i}"
            )
        
        usage = self.analytics.feature_usage[FeatureType.QUERY_EXECUTION.value]
        self.assertEqual(len(usage.unique_users), 5)
    
    def test_feature_usage_tracks_unique_agents(self):
        """Test that feature usage tracks unique agents"""
        # Track events for same feature from different agents
        for i in range(3):
            self.analytics.track_event(
                FeatureType.QUERY_EXECUTION,
                agent_id=f"agent-{i}"
            )
        
        usage = self.analytics.feature_usage[FeatureType.QUERY_EXECUTION.value]
        self.assertEqual(len(usage.unique_agents), 3)
    
    def test_feature_usage_tracks_daily_usage(self):
        """Test that feature usage tracks daily usage"""
        self.analytics.track_event(FeatureType.QUERY_EXECUTION, user_id="user-1")
        self.analytics.track_event(FeatureType.QUERY_EXECUTION, user_id="user-1")
        
        date = datetime.utcnow().strftime('%Y-%m-%d')
        usage = self.analytics.feature_usage[FeatureType.QUERY_EXECUTION.value]
        self.assertEqual(usage.daily_usage[date], 2)
    
    def test_export_to_json(self):
        """Test exporting to JSON"""
        import tempfile
        import os
        import json
        
        # Track some events
        self.analytics.track_event(FeatureType.QUERY_EXECUTION, user_id="user-1")
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            start_date = datetime.utcnow().strftime('%Y-%m-%d')
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
            self.analytics.export_to_json(temp_path, start_date, end_date)
            
            # Verify file was created and contains data
            self.assertTrue(os.path.exists(temp_path))
            with open(temp_path, 'r') as f:
                data = json.load(f)
                self.assertIn("summary", data)
                self.assertIn("dau_timeseries", data)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_export_to_csv_dau(self):
        """Test exporting DAU to CSV"""
        import tempfile
        import os
        import csv
        
        # Track some events
        self.analytics.track_event(FeatureType.QUERY_EXECUTION, user_id="user-1")
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_path = f.name
        
        try:
            start_date = datetime.utcnow().strftime('%Y-%m-%d')
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
            self.analytics.export_to_csv(temp_path, 'dau', start_date, end_date)
            
            # Verify file was created
            self.assertTrue(os.path.exists(temp_path))
            with open(temp_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                self.assertGreater(len(rows), 0)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_export_to_csv_features(self):
        """Test exporting features to CSV"""
        import tempfile
        import os
        import csv
        
        self.analytics.track_event(FeatureType.QUERY_EXECUTION, user_id="user-1")
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_path = f.name
        
        try:
            self.analytics.export_to_csv(temp_path, 'features')
            
            self.assertTrue(os.path.exists(temp_path))
            with open(temp_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                self.assertGreater(len(rows), 0)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_export_to_csv_patterns(self):
        """Test exporting patterns to CSV"""
        import tempfile
        import os
        import csv
        
        self.analytics.track_query_pattern(QueryPatternType.SELECT, execution_time_ms=100.0)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_path = f.name
        
        try:
            self.analytics.export_to_csv(temp_path, 'patterns')
            
            self.assertTrue(os.path.exists(temp_path))
            with open(temp_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                self.assertGreater(len(rows), 0)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_dau_records_query_count(self):
        """Test that DAU records track query count"""
        # Track query execution events
        self.analytics.track_event(FeatureType.QUERY_EXECUTION, user_id="user-1")
        self.analytics.track_event(FeatureType.NATURAL_LANGUAGE_QUERY, user_id="user-1")
        # Track non-query event
        self.analytics.track_event(FeatureType.VISUALIZATION, user_id="user-1")
        
        date = datetime.utcnow().strftime('%Y-%m-%d')
        anonymous_user_id = self.analytics._anonymize_id("user-1")
        dau = self.analytics.dau_records[date][anonymous_user_id]
        
        self.assertEqual(dau.query_count, 2)  # Only query events count
        self.assertEqual(dau.feature_count, 3)  # All events count
    
    def test_multiple_dates_dau(self):
        """Test DAU tracking across multiple dates"""
        # Simulate tracking events on different dates
        # Note: In real usage, dates are determined by current time
        # This test verifies that DAU is tracked per date
        
        user_id = "user-1"
        self.analytics.track_event(FeatureType.QUERY_EXECUTION, user_id=user_id)
        
        date = datetime.utcnow().strftime('%Y-%m-%d')
        dau_today = self.analytics.get_dau(date)
        self.assertGreater(dau_today, 0)
        
        # Get DAU for a different date (should be 0)
        different_date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
        dau_yesterday = self.analytics.get_dau(different_date)
        self.assertEqual(dau_yesterday, 0)


if __name__ == '__main__':
    unittest.main()

