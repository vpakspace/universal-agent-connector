"""
Test cases for Query Optimization feature
"""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from ai_agent_connector.app.utils.query_optimizer import (
    QueryOptimizer, ExplainAnalysis, IndexRecommendation,
    QueryRewrite, OptimizationReport, OptimizationLevel
)
from ai_agent_connector.app.utils.optimization_storage import (
    OptimizationStorage, OptimizationMetric
)
from ai_agent_connector.app.db import DatabaseConnector


class TestExplainAnalysis:
    """Test EXPLAIN analysis functionality"""
    
    @pytest.fixture
    def mock_connector(self):
        """Mock database connector"""
        connector = Mock(spec=DatabaseConnector)
        connector.is_connected = False
        return connector
    
    @pytest.fixture
    def optimizer(self, mock_connector):
        """Create optimizer with mock connector"""
        return QueryOptimizer(mock_connector)
    
    def test_analyze_query_simple_explain(self, optimizer, mock_connector):
        """Test analyzing query with simple EXPLAIN"""
        # Mock EXPLAIN result
        explain_result = [
            ([json.dumps([{
                'Plan': {
                    'Node Type': 'Seq Scan',
                    'Relation Name': 'users',
                    'Total Cost': 1250.5,
                    'Plan Rows': 10000,
                    'Actual Rows': 150,
                    'Actual Total Time': 45.2
                }
            }])],)
        ]
        
        mock_connector.execute_query.return_value = explain_result
        mock_connector.is_connected = False
        
        analysis = optimizer.analyze_query("SELECT * FROM users WHERE age > 25")
        
        assert analysis.query == "SELECT * FROM users WHERE age > 25"
        assert analysis.total_cost == 1250.5
        assert analysis.execution_time == 45.2
        assert analysis.rows_examined == 10000
        assert analysis.rows_returned == 150
        assert 'users' in analysis.sequential_scans
    
    def test_analyze_query_with_index_usage(self, optimizer, mock_connector):
        """Test analyzing query that uses an index"""
        explain_result = [
            ([json.dumps([{
                'Plan': {
                    'Node Type': 'Index Scan',
                    'Index Name': 'idx_users_email',
                    'Relation Name': 'users',
                    'Total Cost': 25.5,
                    'Plan Rows': 1,
                    'Actual Rows': 1,
                    'Actual Total Time': 2.1
                }
            }])],)
        ]
        
        mock_connector.execute_query.return_value = explain_result
        mock_connector.is_connected = False
        
        analysis = optimizer.analyze_query("SELECT * FROM users WHERE email = 'test@example.com'")
        
        assert 'idx_users_email' in analysis.index_usage
        assert len(analysis.sequential_scans) == 0
        assert analysis.total_cost == 25.5
    
    def test_analyze_query_with_error(self, optimizer, mock_connector):
        """Test handling errors in EXPLAIN analysis"""
        mock_connector.execute_query.side_effect = Exception("Connection failed")
        mock_connector.is_connected = False
        
        analysis = optimizer.analyze_query("SELECT * FROM users")
        
        assert len(analysis.warnings) > 0
        assert analysis.total_cost is None
        assert analysis.execution_time is None
    
    def test_analyze_query_nested_plan(self, optimizer, mock_connector):
        """Test analyzing query with nested plan nodes"""
        explain_result = [
            ([json.dumps([{
                'Plan': {
                    'Node Type': 'Hash Join',
                    'Total Cost': 2500.0,
                    'Plans': [
                        {
                            'Node Type': 'Seq Scan',
                            'Relation Name': 'users'
                        },
                        {
                            'Node Type': 'Seq Scan',
                            'Relation Name': 'orders'
                        }
                    ]
                }
            }])],)
        ]
        
        mock_connector.execute_query.return_value = explain_result
        mock_connector.is_connected = False
        
        analysis = optimizer.analyze_query("SELECT * FROM users JOIN orders ON users.id = orders.user_id")
        
        assert 'users' in analysis.sequential_scans
        assert 'orders' in analysis.sequential_scans
        assert len(analysis.sequential_scans) == 2


class TestIndexRecommendations:
    """Test index recommendation functionality"""
    
    @pytest.fixture
    def mock_connector(self):
        connector = Mock(spec=DatabaseConnector)
        connector.is_connected = False
        return connector
    
    @pytest.fixture
    def optimizer(self, mock_connector):
        return QueryOptimizer(mock_connector)
    
    @pytest.fixture
    def explain_analysis_with_seq_scan(self):
        """Create EXPLAIN analysis with sequential scan"""
        return ExplainAnalysis(
            query="SELECT * FROM users WHERE age > 25",
            plan={},
            total_cost=1250.5,
            execution_time=45.2,
            rows_examined=10000,
            rows_returned=150,
            index_usage=[],
            sequential_scans=['users'],
            warnings=["Sequential scan on users"]
        )
    
    def test_recommend_indexes_where_clause(self, optimizer, explain_analysis_with_seq_scan):
        """Test index recommendation for WHERE clause"""
        query = "SELECT * FROM users WHERE age > 25"
        
        recommendations = optimizer.recommend_indexes(query, explain_analysis_with_seq_scan)
        
        assert len(recommendations) > 0
        age_rec = next((r for r in recommendations if 'age' in r.columns), None)
        assert age_rec is not None
        assert age_rec.table == 'users'
        assert age_rec.index_type == 'btree'
        assert age_rec.priority == OptimizationLevel.CRITICAL
        assert 'CREATE INDEX' in age_rec.sql
    
    def test_recommend_indexes_join_condition(self, optimizer):
        """Test index recommendation for JOIN conditions"""
        explain_analysis = ExplainAnalysis(
            query="SELECT * FROM users JOIN orders ON users.id = orders.user_id",
            plan={},
            total_cost=2500.0,
            execution_time=None,
            rows_examined=None,
            rows_returned=None,
            index_usage=[],
            sequential_scans=['users', 'orders'],
            warnings=[]
        )
        
        query = "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
        recommendations = optimizer.recommend_indexes(query, explain_analysis)
        
        assert len(recommendations) > 0
        # Should recommend index on join columns
        join_recs = [r for r in recommendations if 'JOIN' in r.reason or 'id' in r.columns]
        assert len(join_recs) > 0
    
    def test_recommend_indexes_order_by(self, optimizer):
        """Test index recommendation for ORDER BY"""
        explain_analysis = ExplainAnalysis(
            query="SELECT * FROM users ORDER BY created_at DESC",
            plan={},
            total_cost=1500.0,
            execution_time=None,
            rows_examined=None,
            rows_returned=None,
            index_usage=[],
            sequential_scans=['users'],
            warnings=[]
        )
        
        query = "SELECT * FROM users ORDER BY created_at DESC"
        recommendations = optimizer.recommend_indexes(query, explain_analysis)
        
        order_by_recs = [r for r in recommendations if 'ORDER BY' in r.reason or 'created_at' in r.columns]
        assert len(order_by_recs) > 0
    
    def test_recommend_indexes_no_duplicates(self, optimizer, explain_analysis_with_seq_scan):
        """Test that duplicate recommendations are removed"""
        query = "SELECT * FROM users WHERE age > 25 AND age < 50"
        
        recommendations = optimizer.recommend_indexes(query, explain_analysis_with_seq_scan)
        
        # Check for duplicates
        seen = set()
        for rec in recommendations:
            key = (rec.table, tuple(rec.columns))
            assert key not in seen, "Duplicate recommendation found"
            seen.add(key)
    
    def test_index_recommendation_to_dict(self):
        """Test index recommendation serialization"""
        rec = IndexRecommendation(
            table="users",
            columns=["age"],
            index_type="btree",
            reason="WHERE clause filters on age",
            estimated_improvement="50-90% faster",
            priority=OptimizationLevel.CRITICAL,
            sql="CREATE INDEX idx_users_age ON users (age);"
        )
        
        data = rec.to_dict()
        assert data['table'] == "users"
        assert data['columns'] == ["age"]
        assert data['priority'] == "critical"


class TestQueryRewrites:
    """Test query rewrite suggestions"""
    
    @pytest.fixture
    def mock_connector(self):
        connector = Mock(spec=DatabaseConnector)
        connector.is_connected = False
        return connector
    
    @pytest.fixture
    def optimizer(self, mock_connector):
        return QueryOptimizer(mock_connector)
    
    @pytest.fixture
    def explain_analysis(self):
        return ExplainAnalysis(
            query="SELECT * FROM users",
            plan={},
            total_cost=1000.0,
            execution_time=None,
            rows_examined=10000,
            rows_returned=10000,
            index_usage=[],
            sequential_scans=['users'],
            warnings=[]
        )
    
    def test_suggest_rewrite_select_star(self, optimizer, explain_analysis):
        """Test rewrite suggestion for SELECT *"""
        query = "SELECT * FROM users WHERE age > 25"
        
        rewrites = optimizer.suggest_rewrites(query, explain_analysis)
        
        select_star_rewrite = next((r for r in rewrites if 'SELECT *' in r.reason), None)
        assert select_star_rewrite is not None
        assert select_star_rewrite.priority == OptimizationLevel.INFO
        assert select_star_rewrite.confidence > 0
    
    def test_suggest_rewrite_order_by_without_limit(self, optimizer):
        """Test rewrite suggestion for ORDER BY without LIMIT"""
        explain_analysis = ExplainAnalysis(
            query="SELECT * FROM users ORDER BY created_at DESC",
            plan={},
            total_cost=1500.0,
            execution_time=None,
            rows_examined=10000,
            rows_returned=None,
            index_usage=[],
            sequential_scans=['users'],
            warnings=[]
        )
        
        query = "SELECT * FROM users ORDER BY created_at DESC"
        rewrites = optimizer.suggest_rewrites(query, explain_analysis)
        
        limit_rewrite = next((r for r in rewrites if 'LIMIT' in r.suggested_query), None)
        assert limit_rewrite is not None
        assert 'LIMIT' in limit_rewrite.suggested_query
        assert limit_rewrite.confidence >= 0.8
    
    def test_suggest_rewrite_subquery(self, optimizer, explain_analysis):
        """Test rewrite suggestion for subquery to JOIN"""
        query = "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)"
        
        rewrites = optimizer.suggest_rewrites(query, explain_analysis)
        
        subquery_rewrite = next((r for r in rewrites if 'subquery' in r.reason.lower() or 'JOIN' in r.reason), None)
        assert subquery_rewrite is not None
    
    def test_query_rewrite_to_dict(self):
        """Test query rewrite serialization"""
        rewrite = QueryRewrite(
            original_query="SELECT * FROM users",
            suggested_query="SELECT id, name FROM users",
            reason="SELECT * retrieves unnecessary columns",
            estimated_improvement="10-30% faster",
            priority=OptimizationLevel.INFO,
            confidence=0.7
        )
        
        data = rewrite.to_dict()
        assert data['original_query'] == "SELECT * FROM users"
        assert data['confidence'] == 0.7


class TestOptimizationReport:
    """Test optimization report generation"""
    
    @pytest.fixture
    def mock_connector(self):
        connector = Mock(spec=DatabaseConnector)
        connector.is_connected = False
        return connector
    
    @pytest.fixture
    def optimizer(self, mock_connector):
        return QueryOptimizer(mock_connector)
    
    def test_optimize_query_full_report(self, optimizer, mock_connector):
        """Test generating full optimization report"""
        # Mock EXPLAIN result
        explain_result = [
            ([json.dumps([{
                'Plan': {
                    'Node Type': 'Seq Scan',
                    'Relation Name': 'users',
                    'Total Cost': 1250.5,
                    'Plan Rows': 10000,
                    'Actual Rows': 150
                }
            }])],)
        ]
        
        mock_connector.execute_query.return_value = explain_result
        mock_connector.is_connected = False
        
        query = "SELECT * FROM users WHERE age > 25"
        report = optimizer.optimize_query(query, track_metrics=False)
        
        assert report.query == query
        assert report.explain_analysis is not None
        assert isinstance(report.index_recommendations, list)
        assert isinstance(report.query_rewrites, list)
        assert report.generated_at is not None
    
    def test_optimize_query_with_metrics(self, optimizer, mock_connector):
        """Test optimization report with metrics tracking"""
        # Mock EXPLAIN and query execution
        explain_result = [
            ([json.dumps([{
                'Plan': {
                    'Node Type': 'Seq Scan',
                    'Relation Name': 'users',
                    'Total Cost': 1250.5
                }
            }])],)
        ]
        
        query_result = [('result1',), ('result2',)]
        
        def execute_side_effect(query, *args, **kwargs):
            if 'EXPLAIN' in query:
                return explain_result
            else:
                return query_result
        
        mock_connector.execute_query.side_effect = execute_side_effect
        mock_connector.is_connected = False
        
        query = "SELECT * FROM users WHERE age > 25"
        report = optimizer.optimize_query(query, track_metrics=True)
        
        assert report.before_metrics is not None
        assert 'execution_time' in report.before_metrics
        assert 'rows_returned' in report.before_metrics
    
    def test_optimization_report_to_dict(self, optimizer, mock_connector):
        """Test optimization report serialization"""
        explain_result = [
            ([json.dumps([{
                'Plan': {
                    'Node Type': 'Seq Scan',
                    'Relation Name': 'users',
                    'Total Cost': 1250.5
                }
            }])],)
        ]
        
        mock_connector.execute_query.return_value = explain_result
        mock_connector.is_connected = False
        
        report = optimizer.optimize_query("SELECT * FROM users")
        report_dict = report.to_dict()
        
        assert 'query' in report_dict
        assert 'explain_analysis' in report_dict
        assert 'index_recommendations' in report_dict
        assert 'query_rewrites' in report_dict
        assert 'generated_at' in report_dict


class TestOptimizationStorage:
    """Test optimization metrics storage"""
    
    def test_record_before_metrics(self):
        """Test recording before metrics"""
        storage = OptimizationStorage()
        
        query_id = storage.record_before_metrics(
            query_id="query-1",
            query="SELECT * FROM users",
            agent_id="agent-1",
            execution_time=45.2,
            rows_examined=10000
        )
        
        assert query_id == "query-1"
        metric = storage.get_metric("query-1")
        assert metric.before_execution_time == 45.2
        assert metric.before_rows_examined == 10000
    
    def test_update_after_metrics(self):
        """Test updating after metrics"""
        storage = OptimizationStorage()
        
        storage.record_before_metrics(
            query_id="query-1",
            query="SELECT * FROM users",
            agent_id="agent-1",
            execution_time=45.2
        )
        
        storage.update_after_metrics(
            query_id="query-1",
            execution_time=12.5,
            indexes_applied=["idx_users_age"]
        )
        
        metric = storage.get_metric("query-1")
        assert metric.after_execution_time == 12.5
        assert metric.indexes_applied == ["idx_users_age"]
        assert metric.improvement_percentage is not None
        assert metric.improvement_percentage > 0
    
    def test_calculate_improvement_percentage(self):
        """Test improvement percentage calculation"""
        storage = OptimizationStorage()
        
        storage.record_before_metrics(
            query_id="query-1",
            query="SELECT * FROM users",
            agent_id="agent-1",
            execution_time=100.0
        )
        
        storage.update_after_metrics(
            query_id="query-1",
            execution_time=50.0
        )
        
        metric = storage.get_metric("query-1")
        assert metric.improvement_percentage == 50.0
    
    def test_list_metrics(self):
        """Test listing metrics"""
        storage = OptimizationStorage()
        
        storage.record_before_metrics("query-1", "SELECT 1", "agent-1", 10.0)
        storage.record_before_metrics("query-2", "SELECT 2", "agent-1", 20.0)
        storage.record_before_metrics("query-3", "SELECT 3", "agent-2", 30.0)
        
        # List all
        all_metrics = storage.list_metrics()
        assert len(all_metrics) == 3
        
        # Filter by agent
        agent_metrics = storage.list_metrics(agent_id="agent-1")
        assert len(agent_metrics) == 2
    
    def test_save_and_get_recommendations(self):
        """Test saving and retrieving recommendations"""
        storage = OptimizationStorage()
        
        recommendations = [
            {
                'type': 'index',
                'recommendation': {'table': 'users', 'columns': ['age']}
            },
            {
                'type': 'rewrite',
                'recommendation': {'original': 'SELECT *', 'suggested': 'SELECT id'}
            }
        ]
        
        storage.save_recommendations("agent-1", recommendations)
        retrieved = storage.get_recommendations("agent-1")
        
        assert len(retrieved) == 2
        assert retrieved[0]['type'] == 'index'
    
    def test_metric_to_dict(self):
        """Test metric serialization"""
        storage = OptimizationStorage()
        
        storage.record_before_metrics(
            query_id="query-1",
            query="SELECT * FROM users",
            agent_id="agent-1",
            execution_time=45.2
        )
        
        metric = storage.get_metric("query-1")
        data = metric.to_dict()
        
        assert data['query_id'] == "query-1"
        assert data['before_execution_time'] == 45.2
        assert 'recorded_at' in data


class TestOptimizationRoutes:
    """Test optimization API routes"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        from main import create_app
        app = create_app('testing')
        app.config['TESTING'] = True
        return app.test_client()
    
    @pytest.fixture
    def mock_agent(self):
        """Mock agent for authentication"""
        from ai_agent_connector.app.api.routes import agent_registry
        agent = {
            'agent_id': 'test-agent',
            'api_key': 'test-api-key',
            'name': 'Test Agent',
            'database': {
                'host': 'localhost',
                'database': 'test_db'
            }
        }
        agent_registry._agents['test-agent'] = agent
        return agent
    
    @patch('ai_agent_connector.app.api.routes.agent_registry.get_database_connector')
    def test_optimize_query_endpoint(self, mock_get_connector, client, mock_agent):
        """Test optimize query endpoint"""
        # Mock connector
        mock_connector = Mock()
        mock_connector.is_connected = False
        mock_connector.execute_query.return_value = [
            (['[{"Plan":{"Node Type":"Seq Scan","Total Cost":1250.5}}]'],)
        ]
        mock_get_connector.return_value = mock_connector
        
        response = client.post(
            '/api/agents/test-agent/query/optimize',
            headers={'X-API-Key': 'test-api-key'},
            json={
                'query': 'SELECT * FROM users WHERE age > 25',
                'track_metrics': False
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'explain_analysis' in data
        assert 'index_recommendations' in data
        assert 'query_rewrites' in data
    
    def test_optimize_query_requires_auth(self, client):
        """Test that optimize endpoint requires authentication"""
        response = client.post(
            '/api/agents/test-agent/query/optimize',
            json={'query': 'SELECT 1'}
        )
        
        assert response.status_code == 401
    
    def test_optimize_query_missing_query(self, client, mock_agent):
        """Test optimize endpoint with missing query"""
        response = client.post(
            '/api/agents/test-agent/query/optimize',
            headers={'X-API-Key': 'test-api-key'},
            json={}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('ai_agent_connector.app.api.routes.optimization_storage')
    def test_get_optimization_metrics(self, mock_storage, client, mock_agent):
        """Test get optimization metrics endpoint"""
        from ai_agent_connector.app.utils.optimization_storage import OptimizationMetric
        
        mock_metric = OptimizationMetric(
            query_id="query-1",
            query="SELECT * FROM users",
            agent_id="test-agent",
            before_execution_time=45.2,
            after_execution_time=12.5,
            before_rows_examined=10000,
            after_rows_examined=10000,
            indexes_applied=["idx_users_age"],
            rewrites_applied=[],
            improvement_percentage=72.3,
            recorded_at=datetime.utcnow().isoformat()
        )
        
        mock_storage.list_metrics.return_value = [mock_metric]
        
        response = client.get(
            '/api/agents/test-agent/query/optimize/metrics',
            headers={'X-API-Key': 'test-api-key'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'metrics' in data
        assert len(data['metrics']) == 1
    
    @patch('ai_agent_connector.app.api.routes.optimization_storage')
    def test_get_optimization_recommendations(self, mock_storage, client, mock_agent):
        """Test get optimization recommendations endpoint"""
        recommendations = [
            {
                'type': 'index',
                'recommendation': {'table': 'users', 'columns': ['age']}
            }
        ]
        
        mock_storage.get_recommendations.return_value = recommendations
        
        response = client.get(
            '/api/agents/test-agent/query/optimize/recommendations',
            headers={'X-API-Key': 'test-api-key'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'recommendations' in data
        assert len(data['recommendations']) == 1


class TestOptimizationIntegration:
    """Test optimization integration"""
    
    def test_full_optimization_workflow(self):
        """Test complete optimization workflow"""
        storage = OptimizationStorage()
        
        # Record before metrics
        query_id = storage.record_before_metrics(
            query_id="query-1",
            query="SELECT * FROM users WHERE age > 25",
            agent_id="agent-1",
            execution_time=45.2,
            rows_examined=10000
        )
        
        # Simulate applying optimizations
        storage.update_after_metrics(
            query_id=query_id,
            execution_time=12.5,
            indexes_applied=["idx_users_age"],
            rows_examined=150
        )
        
        # Verify metrics
        metric = storage.get_metric(query_id)
        assert metric.improvement_percentage is not None
        assert metric.improvement_percentage > 0
        assert len(metric.indexes_applied) > 0
    
    @patch('ai_agent_connector.app.utils.query_optimizer.DatabaseConnector')
    def test_optimizer_with_real_connector_pattern(self, mock_db_class):
        """Test optimizer works with connector pattern"""
        mock_connector = Mock()
        mock_connector.is_connected = False
        mock_connector.execute_query.return_value = [
            (['[{"Plan":{"Node Type":"Seq Scan"}}]'],)
        ]
        mock_db_class.return_value = mock_connector
        
        optimizer = QueryOptimizer(mock_connector)
        report = optimizer.optimize_query("SELECT * FROM users", track_metrics=False)
        
        assert report is not None
        assert report.explain_analysis is not None

