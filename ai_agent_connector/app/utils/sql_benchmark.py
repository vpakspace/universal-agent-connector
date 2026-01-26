"""
SQL Generation Benchmark Suite
Tests and measures AI performance for natural language to SQL conversion
"""

import json
import os
import sqlparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class BenchmarkQuery:
    """Represents a benchmark query with NL and expected SQL"""
    id: str
    category: str
    difficulty: str  # easy, medium, hard
    natural_language: str
    expected_sql: str
    description: str = ""
    schema_context: Optional[Dict[str, Any]] = None


@dataclass
class BenchmarkResult:
    """Result of a single benchmark query execution"""
    query_id: str
    timestamp: str
    model: str
    generated_sql: str
    expected_sql: str
    accuracy_score: float
    is_exact_match: bool
    execution_time_ms: float
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class BenchmarkRun:
    """Complete benchmark run with all results"""
    run_id: str
    timestamp: str
    model: str
    total_queries: int
    passed: int
    failed: int
    accuracy_score: float
    execution_time_ms: float
    results: List[BenchmarkResult]
    metadata: Optional[Dict[str, Any]] = None


class SQLAccuracyScorer:
    """Scores SQL accuracy by comparing generated SQL with expected SQL"""
    
    @staticmethod
    def normalize_sql(sql: str) -> str:
        """Normalize SQL for comparison"""
        if not sql:
            return ""
        
        # Parse and format SQL
        try:
            parsed = sqlparse.parse(sql)
            if parsed:
                # Format SQL consistently
                formatted = sqlparse.format(
                    sql,
                    reindent=True,
                    keyword_case='upper',
                    strip_comments=True
                )
                # Remove extra whitespace
                lines = [line.strip() for line in formatted.split('\n') if line.strip()]
                return ' '.join(lines).strip()
        except Exception:
            pass
        
        # Fallback: basic normalization
        return ' '.join(sql.split()).strip().upper()
    
    @staticmethod
    def extract_keywords(sql: str) -> set:
        """Extract SQL keywords and identifiers"""
        try:
            parsed = sqlparse.parse(sql)
            keywords = set()
            identifiers = set()
            
            for statement in parsed:
                for token in statement.flatten():
                    if token.ttype in sqlparse.sql.Keyword:
                        keywords.add(token.value.upper())
                    elif token.ttype is None and token.value.strip():
                        # Potential identifier
                        value = token.value.strip().strip('"').strip("'").strip('`')
                        if value and not value.isdigit():
                            identifiers.add(value.upper())
            
            return keywords | identifiers
        except Exception:
            # Fallback: simple keyword extraction
            sql_upper = sql.upper()
            keywords = {'SELECT', 'FROM', 'WHERE', 'JOIN', 'GROUP', 'ORDER', 'HAVING', 'LIMIT', 'INSERT', 'UPDATE', 'DELETE'}
            found = {kw for kw in keywords if kw in sql_upper}
            return found
    
    @staticmethod
    def calculate_accuracy(generated: str, expected: str) -> Tuple[float, bool]:
        """
        Calculate accuracy score between generated and expected SQL
        
        Returns:
            Tuple of (accuracy_score, is_exact_match)
        """
        if not generated or not expected:
            return (0.0, False)
        
        # Normalize both SQLs
        gen_norm = SQLAccuracyScorer.normalize_sql(generated)
        exp_norm = SQLAccuracyScorer.normalize_sql(expected)
        
        # Exact match
        if gen_norm == exp_norm:
            return (1.0, True)
        
        # Extract keywords and identifiers
        gen_keywords = SQLAccuracyScorer.extract_keywords(generated)
        exp_keywords = SQLAccuracyScorer.extract_keywords(expected)
        
        if not exp_keywords:
            return (0.0, False)
        
        # Calculate keyword overlap
        keyword_overlap = len(gen_keywords & exp_keywords) / len(exp_keywords)
        
        # Calculate structural similarity (simplified)
        # Check if main components match
        components = {
            'SELECT': 'SELECT' in gen_norm and 'SELECT' in exp_norm,
            'FROM': 'FROM' in gen_norm and 'FROM' in exp_norm,
            'WHERE': ('WHERE' in gen_norm) == ('WHERE' in exp_norm),
            'JOIN': ('JOIN' in gen_norm) == ('JOIN' in exp_norm),
            'GROUP BY': ('GROUP BY' in gen_norm) == ('GROUP BY' in exp_norm),
            'ORDER BY': ('ORDER BY' in gen_norm) == ('ORDER BY' in exp_norm),
        }
        
        component_score = sum(components.values()) / len(components)
        
        # Combined score (weighted)
        accuracy = (keyword_overlap * 0.6) + (component_score * 0.4)
        
        return (min(accuracy, 1.0), False)


class SQLBenchmarkSuite:
    """Benchmark suite for SQL generation accuracy"""
    
    def __init__(self, benchmark_file: Optional[str] = None):
        """
        Initialize benchmark suite
        
        Args:
            benchmark_file: Path to JSON file with benchmark queries
        """
        self.benchmark_file = benchmark_file or self._get_default_benchmark_file()
        self.queries: List[BenchmarkQuery] = []
        self.results_dir = Path("benchmark_results")
        self.results_dir.mkdir(exist_ok=True)
        self._load_queries()
    
    def _get_default_benchmark_file(self) -> str:
        """Get path to default benchmark queries file"""
        base_dir = Path(__file__).parent.parent.parent.parent
        return str(base_dir / "benchmark_queries.json")
    
    def _load_queries(self):
        """Load benchmark queries from file"""
        if os.path.exists(self.benchmark_file):
            with open(self.benchmark_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.queries = [
                    BenchmarkQuery(**item) for item in data.get('queries', [])
                ]
        else:
            # Use default queries if file doesn't exist
            self.queries = self._get_default_queries()
            self._save_queries()
    
    def _save_queries(self):
        """Save queries to file"""
        data = {
            'version': '1.0',
            'total_queries': len(self.queries),
            'queries': [asdict(q) for q in self.queries]
        }
        with open(self.benchmark_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _get_default_queries(self) -> List[BenchmarkQuery]:
        """Generate default benchmark queries (100+)"""
        queries = []
        
        # Basic SELECT queries (Easy)
        basic_queries = [
            ("Show me all users", "SELECT * FROM users", "basic_select_all"),
            ("Get all products", "SELECT * FROM products", "basic_select_table"),
            ("List all customers", "SELECT * FROM customers", "basic_select_list"),
            ("Show all orders", "SELECT * FROM orders", "basic_select_orders"),
            ("Get all employees", "SELECT * FROM employees", "basic_select_employees"),
            ("List all products with prices", "SELECT * FROM products WHERE price IS NOT NULL", "basic_with_condition"),
            ("Show users created today", "SELECT * FROM users WHERE DATE(created_at) = CURRENT_DATE", "basic_date_filter"),
            ("Get active users", "SELECT * FROM users WHERE status = 'active'", "basic_status_filter"),
            ("List products in stock", "SELECT * FROM products WHERE stock > 0", "basic_numeric_filter"),
            ("Show recent orders", "SELECT * FROM orders ORDER BY created_at DESC LIMIT 10", "basic_order_limit"),
        ]
        
        for i, (nl, sql, desc) in enumerate(basic_queries):
            queries.append(BenchmarkQuery(
                id=f"basic_{i+1}",
                category="basic_select",
                difficulty="easy",
                natural_language=nl,
                expected_sql=sql,
                description=desc
            ))
        
        # SELECT with WHERE (Medium)
        where_queries = [
            ("Find users with email containing 'gmail'", "SELECT * FROM users WHERE email LIKE '%gmail%'", "where_like"),
            ("Get orders from last 7 days", "SELECT * FROM orders WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'", "where_date_range"),
            ("Show products priced between 10 and 100", "SELECT * FROM products WHERE price BETWEEN 10 AND 100", "where_between"),
            ("Find customers in New York or Los Angeles", "SELECT * FROM customers WHERE city IN ('New York', 'Los Angeles')", "where_in"),
            ("Get users who registered this month", "SELECT * FROM users WHERE EXTRACT(MONTH FROM created_at) = EXTRACT(MONTH FROM CURRENT_DATE)", "where_date_extract"),
            ("Show orders with total greater than 1000", "SELECT * FROM orders WHERE total > 1000", "where_comparison"),
            ("Find products not in stock", "SELECT * FROM products WHERE stock = 0 OR stock IS NULL", "where_null_check"),
            ("Get users with verified email", "SELECT * FROM users WHERE email_verified = TRUE", "where_boolean"),
            ("Show orders placed on weekends", "SELECT * FROM orders WHERE EXTRACT(DOW FROM created_at) IN (0, 6)", "where_weekend"),
            ("Find products with discount", "SELECT * FROM products WHERE discount IS NOT NULL AND discount > 0", "where_multiple_conditions"),
        ]
        
        for i, (nl, sql, desc) in enumerate(where_queries):
            queries.append(BenchmarkQuery(
                id=f"where_{i+1}",
                category="where_clause",
                difficulty="medium",
                natural_language=nl,
                expected_sql=sql,
                description=desc
            ))
        
        # JOIN queries (Medium)
        join_queries = [
            ("Show users with their orders", "SELECT u.*, o.* FROM users u JOIN orders o ON u.id = o.user_id", "join_basic"),
            ("Get products with their categories", "SELECT p.*, c.name as category_name FROM products p JOIN categories c ON p.category_id = c.id", "join_with_alias"),
            ("List orders with customer names", "SELECT o.*, c.name as customer_name FROM orders o JOIN customers c ON o.customer_id = c.id", "join_customer"),
            ("Show employees and their departments", "SELECT e.*, d.name as department_name FROM employees e JOIN departments d ON e.department_id = d.id", "join_department"),
            ("Get products with supplier information", "SELECT p.*, s.name as supplier_name FROM products p JOIN suppliers s ON p.supplier_id = s.id", "join_supplier"),
            ("Find orders with shipping details", "SELECT o.*, s.address, s.city FROM orders o JOIN shipping s ON o.id = s.order_id", "join_shipping"),
            ("Show users with their profiles", "SELECT u.*, p.bio, p.avatar FROM users u LEFT JOIN profiles p ON u.id = p.user_id", "join_left"),
            ("Get products with reviews", "SELECT p.*, r.rating, r.comment FROM products p LEFT JOIN reviews r ON p.id = r.product_id", "join_left_reviews"),
            ("List customers with order counts", "SELECT c.*, COUNT(o.id) as order_count FROM customers c LEFT JOIN orders o ON c.id = o.customer_id GROUP BY c.id", "join_with_aggregate"),
            ("Show employees with manager names", "SELECT e.*, m.name as manager_name FROM employees e LEFT JOIN employees m ON e.manager_id = m.id", "join_self"),
        ]
        
        for i, (nl, sql, desc) in enumerate(join_queries):
            queries.append(BenchmarkQuery(
                id=f"join_{i+1}",
                category="joins",
                difficulty="medium",
                natural_language=nl,
                expected_sql=sql,
                description=desc
            ))
        
        # Aggregate queries (Medium)
        aggregate_queries = [
            ("Count total users", "SELECT COUNT(*) as total_users FROM users", "aggregate_count"),
            ("Get average order value", "SELECT AVG(total) as avg_order_value FROM orders", "aggregate_avg"),
            ("Show total revenue", "SELECT SUM(total) as total_revenue FROM orders", "aggregate_sum"),
            ("Find maximum product price", "SELECT MAX(price) as max_price FROM products", "aggregate_max"),
            ("Get minimum stock level", "SELECT MIN(stock) as min_stock FROM products", "aggregate_min"),
            ("Count orders by status", "SELECT status, COUNT(*) as count FROM orders GROUP BY status", "aggregate_group_by"),
            ("Show total sales by month", "SELECT EXTRACT(MONTH FROM created_at) as month, SUM(total) as total_sales FROM orders GROUP BY EXTRACT(MONTH FROM created_at)", "aggregate_date_group"),
            ("Get average rating by product", "SELECT product_id, AVG(rating) as avg_rating FROM reviews GROUP BY product_id", "aggregate_avg_group"),
            ("Find top 10 customers by order count", "SELECT customer_id, COUNT(*) as order_count FROM orders GROUP BY customer_id ORDER BY order_count DESC LIMIT 10", "aggregate_top_n"),
            ("Show revenue by category", "SELECT c.name, SUM(p.price * o.quantity) as revenue FROM orders o JOIN products p ON o.product_id = p.id JOIN categories c ON p.category_id = c.id GROUP BY c.name", "aggregate_join_group"),
        ]
        
        for i, (nl, sql, desc) in enumerate(aggregate_queries):
            queries.append(BenchmarkQuery(
                id=f"aggregate_{i+1}",
                category="aggregates",
                difficulty="medium",
                natural_language=nl,
                expected_sql=sql,
                description=desc
            ))
        
        # Complex queries (Hard)
        complex_queries = [
            ("Find users who ordered more than 5 times", "SELECT u.* FROM users u WHERE (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) > 5", "complex_subquery_count"),
            ("Show products never ordered", "SELECT p.* FROM products p WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.product_id = p.id)", "complex_not_exists"),
            ("Get customers who spent more than average", "SELECT c.* FROM customers c WHERE (SELECT SUM(o.total) FROM orders o WHERE o.customer_id = c.id) > (SELECT AVG(total) FROM orders)", "complex_subquery_avg"),
            ("Find users with orders in last 30 days", "SELECT DISTINCT u.* FROM users u JOIN orders o ON u.id = o.user_id WHERE o.created_at >= CURRENT_DATE - INTERVAL '30 days'", "complex_date_join"),
            ("Show products with highest rating", "SELECT p.* FROM products p WHERE p.id IN (SELECT product_id FROM reviews GROUP BY product_id HAVING AVG(rating) >= 4.5)", "complex_subquery_having"),
            ("Get monthly sales trend", "SELECT EXTRACT(YEAR FROM created_at) as year, EXTRACT(MONTH FROM created_at) as month, SUM(total) as sales FROM orders GROUP BY EXTRACT(YEAR FROM created_at), EXTRACT(MONTH FROM created_at) ORDER BY year, month", "complex_date_aggregate"),
            ("Find customers who bought all products in a category", "SELECT c.* FROM customers c WHERE NOT EXISTS (SELECT p.id FROM products p WHERE p.category_id = 1 AND NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id AND o.product_id = p.id))", "complex_double_not_exists"),
            ("Show users with increasing order values", "SELECT u.* FROM users u WHERE EXISTS (SELECT 1 FROM orders o1 JOIN orders o2 ON o1.user_id = o2.user_id WHERE o1.user_id = u.id AND o2.created_at > o1.created_at AND o2.total > o1.total)", "complex_correlated"),
            ("Get top 3 products by revenue per category", "SELECT * FROM (SELECT p.*, ROW_NUMBER() OVER (PARTITION BY p.category_id ORDER BY (SELECT SUM(o.total) FROM orders o WHERE o.product_id = p.id) DESC) as rn FROM products p) ranked WHERE rn <= 3", "complex_window_function"),
            ("Find customers with orders in all months this year", "SELECT c.* FROM customers c WHERE (SELECT COUNT(DISTINCT EXTRACT(MONTH FROM o.created_at)) FROM orders o WHERE o.customer_id = c.id AND EXTRACT(YEAR FROM o.created_at) = EXTRACT(YEAR FROM CURRENT_DATE)) = 12", "complex_count_distinct"),
        ]
        
        for i, (nl, sql, desc) in enumerate(complex_queries):
            queries.append(BenchmarkQuery(
                id=f"complex_{i+1}",
                category="complex",
                difficulty="hard",
                natural_language=nl,
                expected_sql=sql,
                description=desc
            ))
        
        # Additional queries to reach 100+
        additional_queries = [
            # Date/Time queries
            ("Show orders from today", "SELECT * FROM orders WHERE DATE(created_at) = CURRENT_DATE", "date_today"),
            ("Get users registered this week", "SELECT * FROM users WHERE created_at >= DATE_TRUNC('week', CURRENT_DATE)", "date_week"),
            ("Find orders from last month", "SELECT * FROM orders WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') AND created_at < DATE_TRUNC('month', CURRENT_DATE)", "date_last_month"),
            ("Show products added in last year", "SELECT * FROM products WHERE created_at >= CURRENT_DATE - INTERVAL '1 year'", "date_year"),
            
            # Text search
            ("Search users by name containing 'John'", "SELECT * FROM users WHERE name LIKE '%John%'", "text_like"),
            ("Find products with description matching 'organic'", "SELECT * FROM products WHERE description ILIKE '%organic%'", "text_ilike"),
            ("Get orders with notes containing 'urgent'", "SELECT * FROM orders WHERE notes LIKE '%urgent%'", "text_search"),
            
            # Sorting
            ("Show users sorted by name", "SELECT * FROM users ORDER BY name ASC", "sort_asc"),
            ("Get products sorted by price descending", "SELECT * FROM products ORDER BY price DESC", "sort_desc"),
            ("List orders by date newest first", "SELECT * FROM orders ORDER BY created_at DESC", "sort_date"),
            
            # Limits
            ("Get first 5 users", "SELECT * FROM users LIMIT 5", "limit_basic"),
            ("Show top 10 products", "SELECT * FROM products ORDER BY price DESC LIMIT 10", "limit_top"),
            ("Get 20 most recent orders", "SELECT * FROM orders ORDER BY created_at DESC LIMIT 20", "limit_recent"),
            
            # Multiple conditions
            ("Find active users in New York", "SELECT * FROM users WHERE status = 'active' AND city = 'New York'", "multi_and"),
            ("Get products in stock or on sale", "SELECT * FROM products WHERE stock > 0 OR on_sale = TRUE", "multi_or"),
            ("Show orders with total between 50 and 500", "SELECT * FROM orders WHERE total >= 50 AND total <= 500", "multi_range"),
            
            # NULL handling
            ("Find users without email", "SELECT * FROM users WHERE email IS NULL", "null_check"),
            ("Get products with prices", "SELECT * FROM products WHERE price IS NOT NULL", "null_not"),
            ("Show orders without notes", "SELECT * FROM orders WHERE notes IS NULL OR notes = ''", "null_empty"),
        ]
        
        for i, (nl, sql, desc) in enumerate(additional_queries):
            queries.append(BenchmarkQuery(
                id=f"additional_{i+1}",
                category="additional",
                difficulty="easy" if i < 15 else "medium",
                natural_language=nl,
                expected_sql=sql,
                description=desc
            ))
        
        return queries
    
    def run_benchmark(
        self,
        converter,
        model: str = "gpt-4o-mini",
        query_ids: Optional[List[str]] = None
    ) -> BenchmarkRun:
        """
        Run benchmark suite
        
        Args:
            converter: NLToSQLConverter instance
            model: Model name
            query_ids: Optional list of query IDs to run (default: all)
            
        Returns:
            BenchmarkRun with results
        """
        import time
        
        queries_to_run = self.queries
        if query_ids:
            queries_to_run = [q for q in self.queries if q.id in query_ids]
        
        results = []
        start_time = time.time()
        
        scorer = SQLAccuracyScorer()
        
        for query in queries_to_run:
            try:
                query_start = time.time()
                
                # Convert NL to SQL
                result = converter.convert_to_sql(
                    query.natural_language,
                    schema_info=query.schema_context
                )
                
                query_time = (time.time() - query_start) * 1000
                
                generated_sql = result.get('sql', '')
                error = result.get('error')
                
                # Calculate accuracy
                accuracy, is_exact = scorer.calculate_accuracy(
                    generated_sql,
                    query.expected_sql
                )
                
                benchmark_result = BenchmarkResult(
                    query_id=query.id,
                    timestamp=datetime.utcnow().isoformat(),
                    model=model,
                    generated_sql=generated_sql,
                    expected_sql=query.expected_sql,
                    accuracy_score=accuracy,
                    is_exact_match=is_exact,
                    execution_time_ms=query_time,
                    error=error,
                    metadata={
                        'category': query.category,
                        'difficulty': query.difficulty,
                        'description': query.description
                    }
                )
                
                results.append(benchmark_result)
                
            except Exception as e:
                benchmark_result = BenchmarkResult(
                    query_id=query.id,
                    timestamp=datetime.utcnow().isoformat(),
                    model=model,
                    generated_sql="",
                    expected_sql=query.expected_sql,
                    accuracy_score=0.0,
                    is_exact_match=False,
                    execution_time_ms=0.0,
                    error=str(e)
                )
                results.append(benchmark_result)
        
        total_time = (time.time() - start_time) * 1000
        
        # Calculate summary
        passed = sum(1 for r in results if r.is_exact_match)
        failed = len(results) - passed
        avg_accuracy = sum(r.accuracy_score for r in results) / len(results) if results else 0.0
        
        run = BenchmarkRun(
            run_id=f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.utcnow().isoformat(),
            model=model,
            total_queries=len(results),
            passed=passed,
            failed=failed,
            accuracy_score=avg_accuracy,
            execution_time_ms=total_time,
            results=results,
            metadata={
                'total_queries': len(queries_to_run),
                'categories': list(set(q.category for q in queries_to_run))
            }
        )
        
        # Save results
        self._save_run(run)
        
        return run
    
    def _save_run(self, run: BenchmarkRun):
        """Save benchmark run to file"""
        filename = f"{run.run_id}.json"
        filepath = self.results_dir / filename
        
        data = asdict(run)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_runs(self, limit: int = 50) -> List[BenchmarkRun]:
        """Get recent benchmark runs"""
        runs = []
        for filepath in sorted(self.results_dir.glob("run_*.json"), reverse=True)[:limit]:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    runs.append(BenchmarkRun(**data))
            except Exception:
                continue
        return runs
    
    def get_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get accuracy trends over time"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        runs = self.get_runs(limit=1000)
        
        # Filter by date
        recent_runs = [
            r for r in runs
            if datetime.fromisoformat(r.timestamp.replace('Z', '+00:00')) >= cutoff_date
        ]
        
        # Group by date and model
        trends = {}
        for run in recent_runs:
            date = run.timestamp[:10]  # YYYY-MM-DD
            model = run.model
            
            key = f"{date}_{model}"
            if key not in trends:
                trends[key] = {
                    'date': date,
                    'model': model,
                    'accuracy_scores': [],
                    'passed_counts': [],
                    'total_queries': []
                }
            
            trends[key]['accuracy_scores'].append(run.accuracy_score)
            trends[key]['passed_counts'].append(run.passed)
            trends[key]['total_queries'].append(run.total_queries)
        
        # Calculate averages
        trend_data = []
        for key, data in trends.items():
            trend_data.append({
                'date': data['date'],
                'model': data['model'],
                'avg_accuracy': sum(data['accuracy_scores']) / len(data['accuracy_scores']),
                'total_passed': sum(data['passed_counts']),
                'total_queries': sum(data['total_queries']),
                'runs': len(data['accuracy_scores'])
            })
        
        # Sort by date
        trend_data.sort(key=lambda x: x['date'])
        
        return {
            'period_days': days,
            'total_runs': len(recent_runs),
            'trends': trend_data
        }
