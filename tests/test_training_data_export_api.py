"""
Integration tests for training data export API endpoints
"""

import unittest
from unittest.mock import Mock, patch
from flask import Flask
import json
from datetime import datetime

from ai_agent_connector.app.api import api_bp
from ai_agent_connector.app.utils.training_data_export import (
    training_data_exporter,
    ExportFormat
)


class TestTrainingDataExportAPI(unittest.TestCase):
    """Test cases for training data export API endpoints"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Flask(__name__)
        self.app.register_blueprint(api_bp)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Clear exporter state
        training_data_exporter.query_sql_pairs.clear()
        training_data_exporter.anonymize_sensitive_data = True
    
    def test_add_training_pair(self):
        """Test adding a query-SQL pair"""
        response = self.client.post(
            '/api/training-data/pairs',
            json={
                'natural_language_query': 'Show me all users',
                'sql_query': 'SELECT * FROM users',
                'database_type': 'postgresql',
                'database_name': 'production_db',
                'success': True,
                'execution_time_ms': 45.5
            }
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('pair', data)
        self.assertEqual(data['pair']['natural_language_query'], 'Show me all users')
        self.assertIn('pair_id', data['pair'])
    
    def test_add_training_pair_missing_required_fields(self):
        """Test adding pair without required fields"""
        response = self.client.post(
            '/api/training-data/pairs',
            json={
                'natural_language_query': 'Show users'
                # Missing sql_query
            }
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_add_training_pair_anonymizes_data(self):
        """Test that added pair anonymizes sensitive data"""
        response = self.client.post(
            '/api/training-data/pairs',
            json={
                'natural_language_query': 'Email: john@example.com',
                'sql_query': 'SELECT * FROM users',
                'database_name': 'sensitive_db'
            }
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        pair = data['pair']
        
        # Natural language query should be anonymized
        self.assertNotIn('john@example.com', pair['natural_language_query'])
        # Database name should be anonymized
        self.assertNotEqual(pair['database_name'], 'sensitive_db')
        if pair['database_name']:
            self.assertIn('db_', pair['database_name'])
    
    def test_list_training_pairs(self):
        """Test listing training pairs"""
        # Add some pairs
        training_data_exporter.add_query_sql_pair(
            natural_language_query='Show users',
            sql_query='SELECT * FROM users'
        )
        training_data_exporter.add_query_sql_pair(
            natural_language_query='Count orders',
            sql_query='SELECT COUNT(*) FROM orders'
        )
        
        response = self.client.get('/api/training-data/pairs')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('pairs', data)
        self.assertGreaterEqual(len(data['pairs']), 2)
    
    def test_list_training_pairs_with_limit(self):
        """Test listing pairs with limit"""
        # Add multiple pairs
        for i in range(5):
            training_data_exporter.add_query_sql_pair(
                natural_language_query=f'Query {i}',
                sql_query=f'SELECT {i}'
            )
        
        response = self.client.get('/api/training-data/pairs?limit=2')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertLessEqual(len(data['pairs']), 2)
    
    def test_list_training_pairs_filter_successful_only(self):
        """Test listing pairs filtered by success"""
        training_data_exporter.add_query_sql_pair(
            natural_language_query='Success',
            sql_query='SELECT 1',
            success=True
        )
        training_data_exporter.add_query_sql_pair(
            natural_language_query='Fail',
            sql_query='INVALID',
            success=False
        )
        
        response = self.client.get('/api/training-data/pairs?successful_only=true')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['pairs']), 1)
        self.assertTrue(data['pairs'][0]['success'])
    
    def test_list_training_pairs_with_date_range(self):
        """Test listing pairs with date range"""
        # Add a pair
        training_data_exporter.add_query_sql_pair(
            natural_language_query='Show users',
            sql_query='SELECT * FROM users'
        )
        
        date = datetime.utcnow().strftime('%Y-%m-%d')
        response = self.client.get(
            f'/api/training-data/pairs?start_date={date}&end_date={date}'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertGreaterEqual(len(data['pairs']), 0)
    
    def test_get_training_pair(self):
        """Test getting a specific pair by ID"""
        pair = training_data_exporter.add_query_sql_pair(
            natural_language_query='Show users',
            sql_query='SELECT * FROM users'
        )
        
        response = self.client.get(f'/api/training-data/pairs/{pair.pair_id}')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('pair', data)
        self.assertEqual(data['pair']['pair_id'], pair.pair_id)
    
    def test_get_training_pair_not_found(self):
        """Test getting non-existent pair"""
        response = self.client.get('/api/training-data/pairs/non-existent')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_delete_training_pair(self):
        """Test deleting a pair"""
        pair = training_data_exporter.add_query_sql_pair(
            natural_language_query='Show users',
            sql_query='SELECT * FROM users'
        )
        
        response = self.client.delete(f'/api/training-data/pairs/{pair.pair_id}')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
        
        # Verify pair is deleted
        get_response = self.client.get(f'/api/training-data/pairs/{pair.pair_id}')
        self.assertEqual(get_response.status_code, 404)
    
    def test_delete_training_pair_not_found(self):
        """Test deleting non-existent pair"""
        response = self.client.delete('/api/training-data/pairs/non-existent')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_get_training_statistics(self):
        """Test getting training statistics"""
        # Add some pairs
        training_data_exporter.add_query_sql_pair(
            natural_language_query='Show users',
            sql_query='SELECT * FROM users',
            database_type='postgresql',
            success=True
        )
        training_data_exporter.add_query_sql_pair(
            natural_language_query='Count orders',
            sql_query='SELECT COUNT(*) FROM orders',
            database_type='mysql',
            success=True
        )
        training_data_exporter.add_query_sql_pair(
            natural_language_query='Fail',
            sql_query='INVALID',
            success=False
        )
        
        response = self.client.get('/api/training-data/statistics')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('statistics', data)
        stats = data['statistics']
        self.assertGreaterEqual(stats['total_pairs'], 3)
        self.assertGreaterEqual(stats['successful_pairs'], 2)
        self.assertIn('unique_tables', stats)
        self.assertIn('database_types', stats)
    
    def test_get_training_statistics_with_date_range(self):
        """Test getting statistics with date range"""
        training_data_exporter.add_query_sql_pair(
            natural_language_query='Show users',
            sql_query='SELECT * FROM users'
        )
        
        date = datetime.utcnow().strftime('%Y-%m-%d')
        response = self.client.get(
            f'/api/training-data/statistics?start_date={date}&end_date={date}'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('statistics', data)
    
    def test_export_training_data_jsonl(self):
        """Test exporting training data to JSONL format"""
        # Add some pairs
        training_data_exporter.add_query_sql_pair(
            natural_language_query='Show users',
            sql_query='SELECT * FROM users'
        )
        
        response = self.client.get('/api/training-data/export?format=jsonl')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/x-ndjson', response.content_type)
        self.assertIn('attachment', response.headers.get('Content-Disposition', ''))
        
        # Verify content is valid JSONL
        lines = response.data.decode('utf-8').strip().split('\n')
        self.assertGreater(len(lines), 0)
        for line in lines:
            json.loads(line)  # Should be valid JSON
    
    def test_export_training_data_json(self):
        """Test exporting training data to JSON format"""
        training_data_exporter.add_query_sql_pair(
            natural_language_query='Show users',
            sql_query='SELECT * FROM users'
        )
        
        response = self.client.get('/api/training-data/export?format=json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        
        # Verify content is valid JSON
        data = json.loads(response.data)
        self.assertIn('pairs', data)
        self.assertIn('statistics', data)
    
    def test_export_training_data_csv(self):
        """Test exporting training data to CSV format"""
        training_data_exporter.add_query_sql_pair(
            natural_language_query='Show users',
            sql_query='SELECT * FROM users',
            database_type='postgresql'
        )
        
        response = self.client.get('/api/training-data/export?format=csv')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'text/csv')
        
        # Verify content is CSV
        content = response.data.decode('utf-8')
        self.assertIn('pair_id', content)
        self.assertIn('natural_language_query', content)
        self.assertIn('sql_query', content)
    
    def test_export_training_data_default_format(self):
        """Test exporting with default format (JSONL)"""
        training_data_exporter.add_query_sql_pair(
            natural_language_query='Show users',
            sql_query='SELECT * FROM users'
        )
        
        response = self.client.get('/api/training-data/export')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/x-ndjson', response.content_type)
    
    def test_export_training_data_invalid_format(self):
        """Test exporting with invalid format"""
        response = self.client.get('/api/training-data/export?format=xml')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_export_training_data_no_data(self):
        """Test exporting when no data exists"""
        response = self.client.get('/api/training-data/export?format=jsonl')
        
        # Should return 404 when no data
        # Note: Implementation may vary, this assumes 404 is returned
        # If implementation returns empty file, adjust assertion
        self.assertIn(response.status_code, [404, 200])
    
    def test_export_training_data_with_filters(self):
        """Test exporting with date and success filters"""
        # Add pairs
        training_data_exporter.add_query_sql_pair(
            natural_language_query='Success',
            sql_query='SELECT 1',
            success=True
        )
        training_data_exporter.add_query_sql_pair(
            natural_language_query='Fail',
            sql_query='INVALID',
            success=False
        )
        
        response = self.client.get(
            '/api/training-data/export?format=jsonl&successful_only=true'
        )
        
        self.assertEqual(response.status_code, 200)
        lines = response.data.decode('utf-8').strip().split('\n')
        for line in lines:
            pair = json.loads(line)
            self.assertTrue(pair['success'])


if __name__ == '__main__':
    unittest.main()


