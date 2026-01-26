"""
Integration tests for adoption analytics API endpoints
"""

import unittest
from unittest.mock import Mock, patch
from flask import Flask
import json
from datetime import datetime, timedelta

from ai_agent_connector.app.api import api_bp
from ai_agent_connector.app.utils.adoption_analytics import (
    adoption_analytics,
    FeatureType,
    QueryPatternType
)


class TestAdoptionAnalyticsAPI(unittest.TestCase):
    """Test cases for adoption analytics API endpoints"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Flask(__name__)
        self.app.register_blueprint(api_bp)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Clear analytics state
        adoption_analytics.events.clear()
        adoption_analytics.dau_records.clear()
        adoption_analytics.query_patterns.clear()
        adoption_analytics.feature_usage.clear()
        adoption_analytics.telemetry_opt_in.clear()
        adoption_analytics.telemetry_enabled = True
    
    def test_opt_in_telemetry(self):
        """Test opting in to telemetry"""
        response = self.client.post(
            '/api/analytics/telemetry/opt-in',
            json={'user_id': 'user-123'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['user_id'], 'user-123')
        self.assertIn('message', data)
        
        # Verify user is opted in
        self.assertTrue(adoption_analytics.is_opted_in('user-123'))
    
    def test_opt_in_telemetry_missing_user_id(self):
        """Test opting in without user_id"""
        response = self.client.post(
            '/api/analytics/telemetry/opt-in',
            json={}
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_opt_out_telemetry(self):
        """Test opting out of telemetry"""
        # First opt in
        adoption_analytics.opt_in_telemetry('user-123')
        
        response = self.client.post(
            '/api/analytics/telemetry/opt-out',
            json={'user_id': 'user-123'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['user_id'], 'user-123')
        
        # Verify user is opted out
        self.assertFalse(adoption_analytics.is_opted_in('user-123'))
    
    def test_get_telemetry_status(self):
        """Test getting telemetry status"""
        adoption_analytics.opt_in_telemetry('user-123')
        
        response = self.client.get('/api/analytics/telemetry/status/user-123')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['user_id'], 'user-123')
        self.assertTrue(data['opted_in'])
        self.assertTrue(data['telemetry_enabled'])
    
    def test_track_analytics_event(self):
        """Test tracking an analytics event"""
        response = self.client.post(
            '/api/analytics/events',
            json={
                'feature_type': 'query_execution',
                'user_id': 'user-123',
                'agent_id': 'agent-456',
                'metadata': {'query_type': 'SELECT'}
            }
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('event_id', data)
        self.assertIn('message', data)
    
    def test_track_analytics_event_invalid_feature_type(self):
        """Test tracking event with invalid feature type"""
        response = self.client.post(
            '/api/analytics/events',
            json={
                'feature_type': 'invalid_feature',
                'user_id': 'user-123'
            }
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_track_analytics_event_missing_feature_type(self):
        """Test tracking event without feature_type"""
        response = self.client.post(
            '/api/analytics/events',
            json={'user_id': 'user-123'}
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_get_dau(self):
        """Test getting DAU for a date"""
        # Track some events
        adoption_analytics.track_event(FeatureType.QUERY_EXECUTION, user_id='user-1')
        adoption_analytics.track_event(FeatureType.QUERY_EXECUTION, user_id='user-2')
        
        date = datetime.utcnow().strftime('%Y-%m-%d')
        response = self.client.get(f'/api/analytics/dau?date={date}')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['date'], date)
        self.assertGreaterEqual(data['dau'], 2)
    
    def test_get_dau_default_date(self):
        """Test getting DAU with default date (today)"""
        adoption_analytics.track_event(FeatureType.QUERY_EXECUTION, user_id='user-1')
        
        response = self.client.get('/api/analytics/dau')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('date', data)
        self.assertIn('dau', data)
    
    def test_get_dau_timeseries(self):
        """Test getting DAU timeseries"""
        # Track some events
        adoption_analytics.track_event(FeatureType.QUERY_EXECUTION, user_id='user-1')
        
        start_date = datetime.utcnow().strftime('%Y-%m-%d')
        end_date = datetime.utcnow().strftime('%Y-%m-%d')
        
        response = self.client.get(
            f'/api/analytics/dau/timeseries?start_date={start_date}&end_date={end_date}'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['start_date'], start_date)
        self.assertEqual(data['end_date'], end_date)
        self.assertIn('timeseries', data)
        self.assertGreater(len(data['timeseries']), 0)
    
    def test_get_dau_timeseries_missing_dates(self):
        """Test getting DAU timeseries without dates"""
        response = self.client.get('/api/analytics/dau/timeseries')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_get_query_patterns(self):
        """Test getting query patterns"""
        # Track some query patterns
        adoption_analytics.track_query_pattern(
            QueryPatternType.SELECT,
            user_id='user-1',
            execution_time_ms=100.0,
            success=True
        )
        
        response = self.client.get('/api/analytics/query-patterns')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('patterns', data)
        self.assertIn('SELECT', data['patterns'])
    
    def test_get_feature_usage(self):
        """Test getting feature usage"""
        # Track some feature usage
        adoption_analytics.track_event(FeatureType.QUERY_EXECUTION, user_id='user-1')
        adoption_analytics.track_event(FeatureType.WIDGET_QUERY, user_id='user-2')
        
        response = self.client.get('/api/analytics/features')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('feature_usage', data)
        self.assertGreater(len(data['feature_usage']), 0)
    
    def test_get_feature_usage_filtered(self):
        """Test getting feature usage filtered by type"""
        adoption_analytics.track_event(FeatureType.QUERY_EXECUTION, user_id='user-1')
        adoption_analytics.track_event(FeatureType.WIDGET_QUERY, user_id='user-2')
        
        response = self.client.get(
            '/api/analytics/features?feature_type=query_execution'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('feature_usage', data)
        self.assertIn('query_execution', data['feature_usage'])
        self.assertNotIn('widget_query', data['feature_usage'])
    
    def test_get_top_features(self):
        """Test getting top features"""
        # Track events for different features
        for i in range(5):
            adoption_analytics.track_event(FeatureType.QUERY_EXECUTION, user_id='user-1')
        for i in range(3):
            adoption_analytics.track_event(FeatureType.WIDGET_QUERY, user_id='user-1')
        
        response = self.client.get('/api/analytics/features/top?limit=2')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('top_features', data)
        self.assertEqual(len(data['top_features']), 2)
        # First should be query_execution (5 uses)
        self.assertEqual(data['top_features'][0]['feature_type'], 'query_execution')
        self.assertEqual(data['top_features'][0]['total_uses'], 5)
    
    def test_get_top_features_default_limit(self):
        """Test getting top features with default limit"""
        # Track events for multiple features
        for feature_type in [FeatureType.QUERY_EXECUTION, FeatureType.WIDGET_QUERY, FeatureType.VISUALIZATION]:
            adoption_analytics.track_event(feature_type, user_id='user-1')
        
        response = self.client.get('/api/analytics/features/top')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('top_features', data)
        self.assertLessEqual(len(data['top_features']), 10)  # Default limit is 10
    
    def test_get_adoption_summary(self):
        """Test getting adoption summary"""
        # Track some events
        for i in range(3):
            adoption_analytics.track_event(FeatureType.QUERY_EXECUTION, user_id=f'user-{i}')
        
        start_date = datetime.utcnow().strftime('%Y-%m-%d')
        end_date = datetime.utcnow().strftime('%Y-%m-%d')
        
        response = self.client.get(
            f'/api/analytics/summary?start_date={start_date}&end_date={end_date}'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('summary', data)
        summary = data['summary']
        self.assertIn('period', summary)
        self.assertIn('dau', summary)
        self.assertIn('unique_users', summary)
        self.assertIn('total_events', summary)
        self.assertIn('top_features', summary)
        self.assertIn('feature_adoption', summary)
        self.assertIn('query_patterns', summary)
    
    def test_get_adoption_summary_default_dates(self):
        """Test getting adoption summary with default dates"""
        adoption_analytics.track_event(FeatureType.QUERY_EXECUTION, user_id='user-1')
        
        response = self.client.get('/api/analytics/summary')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('summary', data)
    
    def test_export_analytics_json(self):
        """Test exporting analytics to JSON"""
        # Track some events
        adoption_analytics.track_event(FeatureType.QUERY_EXECUTION, user_id='user-1')
        
        start_date = datetime.utcnow().strftime('%Y-%m-%d')
        end_date = datetime.utcnow().strftime('%Y-%m-%d')
        
        response = self.client.get(
            f'/api/analytics/export?format=json&start_date={start_date}&end_date={end_date}'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        # Should be downloadable
        self.assertIn('attachment', response.headers.get('Content-Disposition', ''))
    
    def test_export_analytics_csv_dau(self):
        """Test exporting DAU data to CSV"""
        adoption_analytics.track_event(FeatureType.QUERY_EXECUTION, user_id='user-1')
        
        start_date = datetime.utcnow().strftime('%Y-%m-%d')
        end_date = datetime.utcnow().strftime('%Y-%m-%d')
        
        response = self.client.get(
            f'/api/analytics/export?format=csv&data_type=dau&start_date={start_date}&end_date={end_date}'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'text/csv')
        self.assertIn('attachment', response.headers.get('Content-Disposition', ''))
    
    def test_export_analytics_csv_features(self):
        """Test exporting feature usage to CSV"""
        adoption_analytics.track_event(FeatureType.QUERY_EXECUTION, user_id='user-1')
        
        response = self.client.get('/api/analytics/export?format=csv&data_type=features')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'text/csv')
    
    def test_export_analytics_csv_patterns(self):
        """Test exporting query patterns to CSV"""
        adoption_analytics.track_query_pattern(QueryPatternType.SELECT, execution_time_ms=100.0)
        
        response = self.client.get('/api/analytics/export?format=csv&data_type=patterns')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'text/csv')
    
    def test_export_analytics_invalid_format(self):
        """Test exporting with invalid format"""
        response = self.client.get('/api/analytics/export?format=xml')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_export_analytics_default_format(self):
        """Test exporting with default format (JSON)"""
        adoption_analytics.track_event(FeatureType.QUERY_EXECUTION, user_id='user-1')
        
        response = self.client.get('/api/analytics/export')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')


if __name__ == '__main__':
    unittest.main()

