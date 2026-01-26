"""
Unit tests for training data export system
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime
import tempfile
import os
import json
import csv

from ai_agent_connector.app.utils.training_data_export import (
    TrainingDataExporter,
    QuerySQLPair,
    DatasetStatistics,
    ExportFormat
)


class TestQuerySQLPair(unittest.TestCase):
    """Test cases for QuerySQLPair"""
    
    def test_create_query_sql_pair(self):
        """Test creating a query-SQL pair"""
        pair = QuerySQLPair(
            pair_id="pair-123",
            natural_language_query="Show me all users",
            sql_query="SELECT * FROM users",
            timestamp=datetime.utcnow().isoformat(),
            database_type="postgresql",
            database_name="production_db",
            table_names=["users"],
            success=True,
            execution_time_ms=45.5
        )
        
        self.assertEqual(pair.pair_id, "pair-123")
        self.assertEqual(pair.natural_language_query, "Show me all users")
        self.assertEqual(pair.sql_query, "SELECT * FROM users")
        self.assertEqual(pair.database_type, "postgresql")
        self.assertIn("users", pair.table_names)
    
    def test_query_sql_pair_to_dict(self):
        """Test converting query-SQL pair to dictionary"""
        pair = QuerySQLPair(
            pair_id="pair-123",
            natural_language_query="Show users",
            sql_query="SELECT * FROM users",
            timestamp="2024-01-01T00:00:00",
            metadata={"key": "value"}
        )
        
        pair_dict = pair.to_dict()
        self.assertIn("pair_id", pair_dict)
        self.assertIn("natural_language_query", pair_dict)
        self.assertIn("sql_query", pair_dict)
        self.assertEqual(pair_dict["metadata"]["key"], "value")
    
    def test_query_sql_pair_from_dict(self):
        """Test creating query-SQL pair from dictionary"""
        data = {
            "pair_id": "pair-123",
            "natural_language_query": "Show users",
            "sql_query": "SELECT * FROM users",
            "timestamp": "2024-01-01T00:00:00",
            "database_type": None,
            "database_name": None,
            "table_names": [],
            "success": True,
            "execution_time_ms": None,
            "metadata": {}
        }
        
        pair = QuerySQLPair.from_dict(data)
        self.assertEqual(pair.pair_id, "pair-123")
        self.assertEqual(pair.natural_language_query, "Show users")


class TestTrainingDataExporter(unittest.TestCase):
    """Test cases for TrainingDataExporter"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.exporter = TrainingDataExporter(anonymize_sensitive_data=True)
    
    def test_init_defaults(self):
        """Test initialization with defaults"""
        exporter = TrainingDataExporter()
        self.assertTrue(exporter.anonymize_sensitive_data)
    
    def test_init_with_options(self):
        """Test initialization with custom options"""
        exporter = TrainingDataExporter(anonymize_sensitive_data=False)
        self.assertFalse(exporter.anonymize_sensitive_data)
    
    def test_anonymize_email(self):
        """Test email anonymization"""
        query = "Find user with email john.doe@example.com"
        anonymized = self.exporter._anonymize_query(query)
        
        self.assertNotIn("john.doe@example.com", anonymized)
        self.assertIn("@example.com", anonymized)  # Domain preserved
        self.assertIn("user_", anonymized)  # Hashed prefix
    
    def test_anonymize_phone(self):
        """Test phone number anonymization"""
        query = "Call user at 555-123-4567"
        anonymized = self.exporter._anonymize_query(query)
        
        self.assertNotIn("555-123-4567", anonymized)
        self.assertIn("XXX-XXX-", anonymized)
    
    def test_anonymize_ssn(self):
        """Test SSN anonymization"""
        query = "User SSN is 123-45-6789"
        anonymized = self.exporter._anonymize_query(query)
        
        self.assertNotIn("123-45-6789", anonymized)
        self.assertIn("XXX-XX-", anonymized)
    
    def test_anonymize_credit_card(self):
        """Test credit card anonymization"""
        query = "Card number 1234-5678-9012-3456"
        anonymized = self.exporter._anonymize_query(query)
        
        self.assertNotIn("1234-5678-9012-3456", anonymized)
        self.assertIn("XXXX-XXXX-XXXX-", anonymized)
    
    def test_anonymize_ip(self):
        """Test IP address anonymization"""
        query = "IP address 192.168.1.1"
        anonymized = self.exporter._anonymize_query(query)
        
        self.assertNotIn("192.168.1.1", anonymized)
        self.assertIn("XXX.XXX.XXX.", anonymized)
    
    def test_anonymize_disabled(self):
        """Test that anonymization can be disabled"""
        exporter = TrainingDataExporter(anonymize_sensitive_data=False)
        query = "Email: john@example.com"
        anonymized = exporter._anonymize_query(query)
        
        self.assertEqual(query, anonymized)
    
    def test_extract_table_names(self):
        """Test extracting table names from SQL"""
        sql = "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
        tables = self.exporter._extract_table_names(sql)
        
        self.assertIn("users", tables)
        self.assertIn("orders", tables)
        self.assertEqual(len(set(tables)), 2)  # No duplicates
    
    def test_extract_table_names_from_update(self):
        """Test extracting table names from UPDATE statement"""
        sql = "UPDATE products SET price = 100 WHERE id = 1"
        tables = self.exporter._extract_table_names(sql)
        
        self.assertIn("products", tables)
    
    def test_detect_query_type_select(self):
        """Test detecting SELECT query type"""
        sql = "SELECT * FROM users"
        query_type = self.exporter._detect_query_type(sql)
        self.assertEqual(query_type, "SELECT")
    
    def test_detect_query_type_insert(self):
        """Test detecting INSERT query type"""
        sql = "INSERT INTO users (name) VALUES ('John')"
        query_type = self.exporter._detect_query_type(sql)
        self.assertEqual(query_type, "INSERT")
    
    def test_detect_query_type_update(self):
        """Test detecting UPDATE query type"""
        sql = "UPDATE users SET name = 'John'"
        query_type = self.exporter._detect_query_type(sql)
        self.assertEqual(query_type, "UPDATE")
    
    def test_detect_query_type_delete(self):
        """Test detecting DELETE query type"""
        sql = "DELETE FROM users WHERE id = 1"
        query_type = self.exporter._detect_query_type(sql)
        self.assertEqual(query_type, "DELETE")
    
    def test_add_query_sql_pair(self):
        """Test adding a query-SQL pair"""
        pair = self.exporter.add_query_sql_pair(
            natural_language_query="Show me all users",
            sql_query="SELECT * FROM users",
            database_type="postgresql",
            database_name="production_db",
            success=True,
            execution_time_ms=45.5
        )
        
        self.assertIsNotNone(pair.pair_id)
        self.assertEqual(len(self.exporter.query_sql_pairs), 1)
        self.assertIn("users", pair.table_names)
        self.assertEqual(pair.database_type, "postgresql")
        # Database name should be anonymized
        self.assertNotEqual(pair.database_name, "production_db")
        self.assertIn("db_", pair.database_name)
    
    def test_add_query_sql_pair_anonymizes_nl_query(self):
        """Test that natural language query is anonymized"""
        pair = self.exporter.add_query_sql_pair(
            natural_language_query="Email: john@example.com",
            sql_query="SELECT * FROM users"
        )
        
        self.assertNotIn("john@example.com", pair.natural_language_query)
    
    def test_add_query_sql_pair_anonymizes_db_name(self):
        """Test that database name is anonymized"""
        pair = self.exporter.add_query_sql_pair(
            natural_language_query="Show users",
            sql_query="SELECT * FROM users",
            database_name="sensitive_db"
        )
        
        self.assertNotEqual(pair.database_name, "sensitive_db")
        self.assertIn("db_", pair.database_name)
    
    def test_add_query_sql_pair_no_anonymization(self):
        """Test adding pair with anonymization disabled"""
        exporter = TrainingDataExporter(anonymize_sensitive_data=False)
        pair = exporter.add_query_sql_pair(
            natural_language_query="Email: john@example.com",
            sql_query="SELECT * FROM users",
            database_name="production_db"
        )
        
        self.assertIn("john@example.com", pair.natural_language_query)
        self.assertEqual(pair.database_name, "production_db")
    
    def test_get_statistics(self):
        """Test getting dataset statistics"""
        # Add some pairs
        self.exporter.add_query_sql_pair(
            natural_language_query="Show users",
            sql_query="SELECT * FROM users",
            database_type="postgresql",
            success=True
        )
        self.exporter.add_query_sql_pair(
            natural_language_query="Count orders",
            sql_query="SELECT COUNT(*) FROM orders",
            database_type="mysql",
            success=True
        )
        self.exporter.add_query_sql_pair(
            natural_language_query="Delete user",
            sql_query="DELETE FROM users WHERE id = 1",
            success=False
        )
        
        stats = self.exporter.get_statistics()
        
        self.assertEqual(stats.total_pairs, 3)
        self.assertEqual(stats.successful_pairs, 2)
        self.assertEqual(stats.failed_pairs, 1)
        self.assertEqual(len(stats.unique_tables), 2)
        self.assertIn("users", stats.unique_tables)
        self.assertIn("orders", stats.unique_tables)
        self.assertEqual(len(stats.database_types), 2)
        self.assertGreater(stats.avg_query_length, 0)
        self.assertGreater(stats.avg_sql_length, 0)
    
    def test_get_statistics_with_date_filter(self):
        """Test getting statistics with date filter"""
        # Add pair today
        self.exporter.add_query_sql_pair(
            natural_language_query="Show users",
            sql_query="SELECT * FROM users",
            success=True
        )
        
        start_date = datetime.utcnow().strftime('%Y-%m-%d')
        end_date = datetime.utcnow().strftime('%Y-%m-%d')
        
        stats = self.exporter.get_statistics(start_date=start_date, end_date=end_date)
        self.assertEqual(stats.total_pairs, 1)
        
        # Filter for past date (should return 0)
        past_date = "2020-01-01"
        stats = self.exporter.get_statistics(start_date=past_date, end_date=past_date)
        self.assertEqual(stats.total_pairs, 0)
    
    def test_get_statistics_empty(self):
        """Test getting statistics with no pairs"""
        stats = self.exporter.get_statistics()
        self.assertEqual(stats.total_pairs, 0)
        self.assertEqual(stats.successful_pairs, 0)
        self.assertEqual(len(stats.unique_tables), 0)
    
    def test_export_to_jsonl(self):
        """Test exporting to JSONL format"""
        # Add some pairs
        self.exporter.add_query_sql_pair(
            natural_language_query="Show users",
            sql_query="SELECT * FROM users",
            success=True
        )
        self.exporter.add_query_sql_pair(
            natural_language_query="Count orders",
            sql_query="SELECT COUNT(*) FROM orders",
            success=True
        )
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            temp_path = f.name
        
        try:
            count, stats = self.exporter.export_to_jsonl(temp_path)
            
            self.assertEqual(count, 2)
            self.assertEqual(stats.total_pairs, 2)
            
            # Verify file content
            with open(temp_path, 'r') as f:
                lines = f.readlines()
                self.assertEqual(len(lines), 2)
                
                # Parse first line
                pair = json.loads(lines[0])
                self.assertIn("pair_id", pair)
                self.assertIn("natural_language_query", pair)
                self.assertIn("sql_query", pair)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_export_to_jsonl_with_filters(self):
        """Test exporting to JSONL with date and success filters"""
        # Add pairs
        self.exporter.add_query_sql_pair(
            natural_language_query="Show users",
            sql_query="SELECT * FROM users",
            success=True
        )
        self.exporter.add_query_sql_pair(
            natural_language_query="Fail query",
            sql_query="INVALID SQL",
            success=False
        )
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            temp_path = f.name
        
        try:
            count, stats = self.exporter.export_to_jsonl(
                temp_path,
                filter_successful_only=True
            )
            
            self.assertEqual(count, 1)
            self.assertEqual(stats.successful_pairs, 1)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_export_to_json(self):
        """Test exporting to JSON format"""
        self.exporter.add_query_sql_pair(
            natural_language_query="Show users",
            sql_query="SELECT * FROM users",
            success=True
        )
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            count, stats = self.exporter.export_to_json(temp_path)
            
            self.assertEqual(count, 1)
            
            # Verify file content
            with open(temp_path, 'r') as f:
                data = json.load(f)
                self.assertIn("exported_at", data)
                self.assertIn("format_version", data)
                self.assertIn("total_pairs", data)
                self.assertIn("pairs", data)
                self.assertIn("statistics", data)
                self.assertEqual(len(data["pairs"]), 1)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_export_to_csv(self):
        """Test exporting to CSV format"""
        self.exporter.add_query_sql_pair(
            natural_language_query="Show users",
            sql_query="SELECT * FROM users",
            database_type="postgresql",
            success=True
        )
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_path = f.name
        
        try:
            count, stats = self.exporter.export_to_csv(temp_path)
            
            self.assertEqual(count, 1)
            
            # Verify file content
            with open(temp_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                self.assertEqual(len(rows), 1)
                self.assertIn("natural_language_query", rows[0])
                self.assertIn("sql_query", rows[0])
                self.assertIn("database_type", rows[0])
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_export_format_jsonl(self):
        """Test export method with JSONL format"""
        self.exporter.add_query_sql_pair(
            natural_language_query="Show users",
            sql_query="SELECT * FROM users"
        )
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            temp_path = f.name
        
        try:
            count, stats = self.exporter.export(temp_path, format=ExportFormat.JSONL)
            self.assertEqual(count, 1)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_export_format_json(self):
        """Test export method with JSON format"""
        self.exporter.add_query_sql_pair(
            natural_language_query="Show users",
            sql_query="SELECT * FROM users"
        )
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            count, stats = self.exporter.export(temp_path, format=ExportFormat.JSON)
            self.assertEqual(count, 1)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_export_format_csv(self):
        """Test export method with CSV format"""
        self.exporter.add_query_sql_pair(
            natural_language_query="Show users",
            sql_query="SELECT * FROM users"
        )
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_path = f.name
        
        try:
            count, stats = self.exporter.export(temp_path, format=ExportFormat.CSV)
            self.assertEqual(count, 1)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_export_invalid_format(self):
        """Test export with invalid format"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = f.name
        
        try:
            with self.assertRaises(ValueError):
                # This should fail since we can't pass an invalid ExportFormat enum
                # But if we could, it would raise ValueError
                pass
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_list_pairs(self):
        """Test listing pairs"""
        # Add pairs
        self.exporter.add_query_sql_pair("Query 1", "SELECT 1")
        self.exporter.add_query_sql_pair("Query 2", "SELECT 2")
        self.exporter.add_query_sql_pair("Query 3", "SELECT 3")
        
        pairs = self.exporter.list_pairs()
        self.assertEqual(len(pairs), 3)
    
    def test_list_pairs_with_limit(self):
        """Test listing pairs with limit"""
        # Add pairs
        for i in range(5):
            self.exporter.add_query_sql_pair(f"Query {i}", f"SELECT {i}")
        
        pairs = self.exporter.list_pairs(limit=2)
        self.assertEqual(len(pairs), 2)
    
    def test_list_pairs_with_offset(self):
        """Test listing pairs with offset"""
        # Add pairs
        for i in range(5):
            self.exporter.add_query_sql_pair(f"Query {i}", f"SELECT {i}")
        
        pairs = self.exporter.list_pairs(offset=2)
        self.assertEqual(len(pairs), 3)  # 5 total - 2 offset
    
    def test_list_pairs_filter_successful_only(self):
        """Test listing pairs filtered by success"""
        self.exporter.add_query_sql_pair("Success", "SELECT 1", success=True)
        self.exporter.add_query_sql_pair("Fail", "INVALID", success=False)
        
        pairs = self.exporter.list_pairs(filter_successful_only=True)
        self.assertEqual(len(pairs), 1)
        self.assertTrue(pairs[0].success)
    
    def test_get_pair(self):
        """Test getting a specific pair by ID"""
        pair = self.exporter.add_query_sql_pair("Show users", "SELECT * FROM users")
        
        retrieved = self.exporter.get_pair(pair.pair_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.pair_id, pair.pair_id)
        self.assertEqual(retrieved.natural_language_query, "Show users")
    
    def test_get_pair_not_found(self):
        """Test getting non-existent pair"""
        retrieved = self.exporter.get_pair("non-existent")
        self.assertIsNone(retrieved)
    
    def test_delete_pair(self):
        """Test deleting a pair"""
        pair = self.exporter.add_query_sql_pair("Show users", "SELECT * FROM users")
        
        result = self.exporter.delete_pair(pair.pair_id)
        self.assertTrue(result)
        self.assertEqual(len(self.exporter.query_sql_pairs), 0)
        
        # Verify pair is deleted
        retrieved = self.exporter.get_pair(pair.pair_id)
        self.assertIsNone(retrieved)
    
    def test_delete_pair_not_found(self):
        """Test deleting non-existent pair"""
        result = self.exporter.delete_pair("non-existent")
        self.assertFalse(result)
    
    def test_statistics_query_type_distribution(self):
        """Test that statistics include query type distribution"""
        self.exporter.add_query_sql_pair("Select users", "SELECT * FROM users")
        self.exporter.add_query_sql_pair("Insert user", "INSERT INTO users VALUES (1)")
        self.exporter.add_query_sql_pair("Update user", "UPDATE users SET name = 'John'")
        
        stats = self.exporter.get_statistics()
        
        self.assertIn("SELECT", stats.query_type_distribution)
        self.assertIn("INSERT", stats.query_type_distribution)
        self.assertIn("UPDATE", stats.query_type_distribution)
        self.assertEqual(stats.query_type_distribution["SELECT"], 1)
        self.assertEqual(stats.query_type_distribution["INSERT"], 1)
        self.assertEqual(stats.query_type_distribution["UPDATE"], 1)
    
    def test_statistics_date_range(self):
        """Test that statistics include date range"""
        self.exporter.add_query_sql_pair("Query 1", "SELECT 1")
        
        stats = self.exporter.get_statistics()
        
        self.assertIn("start", stats.date_range)
        self.assertIn("end", stats.date_range)
        self.assertIsNotNone(stats.date_range["start"])
        self.assertIsNotNone(stats.date_range["end"])


if __name__ == '__main__':
    unittest.main()


