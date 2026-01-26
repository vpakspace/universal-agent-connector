"""
Query Optimization Module
Provides automatic query optimization suggestions including EXPLAIN analysis,
index recommendations, and query rewrites.
"""

import re
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from ..db import DatabaseConnector


class OptimizationLevel(Enum):
    """Optimization severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class IndexRecommendation:
    """Index recommendation"""
    table: str
    columns: List[str]
    index_type: str  # btree, hash, gin, etc.
    reason: str
    estimated_improvement: str  # e.g., "50% faster"
    priority: OptimizationLevel
    sql: str  # CREATE INDEX statement
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QueryRewrite:
    """Query rewrite suggestion"""
    original_query: str
    suggested_query: str
    reason: str
    estimated_improvement: str
    priority: OptimizationLevel
    confidence: float  # 0.0 to 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExplainAnalysis:
    """EXPLAIN analysis results"""
    query: str
    plan: Dict[str, Any]
    total_cost: Optional[float]
    execution_time: Optional[float]
    rows_examined: Optional[int]
    rows_returned: Optional[int]
    index_usage: List[str]
    sequential_scans: List[str]
    warnings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OptimizationReport:
    """Complete optimization report"""
    query: str
    explain_analysis: ExplainAnalysis
    index_recommendations: List[IndexRecommendation]
    query_rewrites: List[QueryRewrite]
    before_metrics: Optional[Dict[str, Any]]
    after_metrics: Optional[Dict[str, Any]]
    estimated_improvement: str
    generated_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'query': self.query,
            'explain_analysis': self.explain_analysis.to_dict(),
            'index_recommendations': [r.to_dict() for r in self.index_recommendations],
            'query_rewrites': [r.to_dict() for r in self.query_rewrites],
            'before_metrics': self.before_metrics,
            'after_metrics': self.after_metrics,
            'estimated_improvement': self.estimated_improvement,
            'generated_at': self.generated_at
        }


class QueryOptimizer:
    """Query optimizer with EXPLAIN analysis and recommendations"""
    
    def __init__(self, connector: DatabaseConnector):
        """
        Initialize query optimizer
        
        Args:
            connector: Database connector instance
        """
        self.connector = connector
    
    def analyze_query(self, query: str) -> ExplainAnalysis:
        """
        Analyze query using EXPLAIN
        
        Args:
            query: SQL query to analyze
            
        Returns:
            ExplainAnalysis object
        """
        was_connected = self.connector.is_connected
        try:
            if not was_connected:
                self.connector.connect()
            
            # Use EXPLAIN (ANALYZE, BUFFERS, VERBOSE) for PostgreSQL
            explain_query = f"EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT JSON) {query}"
            
            try:
                result = self.connector.execute_query(explain_query, fetch=True)
                
                # Parse EXPLAIN output
                if result and len(result) > 0:
                    explain_data = result[0][0] if isinstance(result[0][0], str) else result[0]
                    if isinstance(explain_data, str):
                        explain_data = json.loads(explain_data)
                    
                    plan = explain_data[0] if isinstance(explain_data, list) else explain_data
                    plan_data = plan.get('Plan', plan)
                    
                    return self._parse_explain_output(query, plan_data)
                else:
                    # Fallback: simple EXPLAIN
                    return self._simple_explain(query)
                    
            except Exception as e:
                # Fallback to simple EXPLAIN if ANALYZE fails
                return self._simple_explain(query)
                
        except Exception as e:
            # Return minimal analysis on error
            return ExplainAnalysis(
                query=query,
                plan={},
                total_cost=None,
                execution_time=None,
                rows_examined=None,
                rows_returned=None,
                index_usage=[],
                sequential_scans=[],
                warnings=[f"Error analyzing query: {str(e)}"]
            )
        finally:
            try:
                if not was_connected:
                    self.connector.disconnect()
            except Exception:
                pass
    
    def _simple_explain(self, query: str) -> ExplainAnalysis:
        """Simple EXPLAIN without ANALYZE"""
        try:
            explain_query = f"EXPLAIN (FORMAT JSON) {query}"
            result = self.connector.execute_query(explain_query, fetch=True)
            
            if result and len(result) > 0:
                plan_data = json.loads(result[0][0])[0].get('Plan', {})
                return self._parse_explain_output(query, plan_data)
        except Exception:
            pass
        
        return ExplainAnalysis(
            query=query,
            plan={},
            total_cost=None,
            execution_time=None,
            rows_examined=None,
            rows_returned=None,
            index_usage=[],
            sequential_scans=[],
            warnings=["Could not get detailed EXPLAIN analysis"]
        )
    
    def _parse_explain_output(self, query: str, plan_data: Dict[str, Any]) -> ExplainAnalysis:
        """Parse EXPLAIN output"""
        total_cost = plan_data.get('Total Cost')
        execution_time = plan_data.get('Actual Total Time')
        rows_examined = plan_data.get('Plan Rows') or plan_data.get('Actual Rows')
        rows_returned = plan_data.get('Actual Rows')
        
        index_usage = []
        sequential_scans = []
        warnings = []
        
        # Recursively analyze plan
        self._analyze_plan_node(plan_data, index_usage, sequential_scans, warnings)
        
        return ExplainAnalysis(
            query=query,
            plan=plan_data,
            total_cost=total_cost,
            execution_time=execution_time,
            rows_examined=rows_examined,
            rows_returned=rows_returned,
            index_usage=index_usage,
            sequential_scans=sequential_scans,
            warnings=warnings
        )
    
    def _analyze_plan_node(self, node: Dict[str, Any], index_usage: List[str], 
                          sequential_scans: List[str], warnings: List[str]):
        """Recursively analyze plan nodes"""
        node_type = node.get('Node Type', '')
        
        # Check for sequential scans
        if 'Seq Scan' in node_type:
            table_name = node.get('Relation Name', 'unknown')
            sequential_scans.append(table_name)
            if node.get('Filter'):
                warnings.append(f"Sequential scan on {table_name} with filter")
        
        # Check for index usage
        if 'Index' in node_type:
            index_name = node.get('Index Name', 'unknown')
            index_usage.append(index_name)
        
        # Check for other issues
        if node.get('Filter') and 'Seq Scan' in node_type:
            warnings.append(f"Filter applied after scan on {node.get('Relation Name', 'unknown')}")
        
        # Recurse into child plans
        if 'Plans' in node:
            for child in node['Plans']:
                self._analyze_plan_node(child, index_usage, sequential_scans, warnings)
    
    def recommend_indexes(self, query: str, explain_analysis: ExplainAnalysis) -> List[IndexRecommendation]:
        """
        Recommend indexes based on query and EXPLAIN analysis
        
        Args:
            query: SQL query
            explain_analysis: EXPLAIN analysis results
            
        Returns:
            List of index recommendations
        """
        recommendations = []
        
        # Analyze WHERE clauses for index opportunities
        where_pattern = re.compile(r'WHERE\s+(.+?)(?:\s+ORDER\s+BY|\s+GROUP\s+BY|\s+LIMIT|$)', re.IGNORECASE)
        where_match = where_pattern.search(query)
        
        if where_match:
            where_clause = where_match.group(1)
            
            # Find table.column patterns in WHERE clause
            column_pattern = re.compile(r'(\w+)\.(\w+)|(\w+)\s*[=<>!]')
            columns = column_pattern.findall(where_clause)
            
            for seq_scan_table in explain_analysis.sequential_scans:
                # Recommend index on filtered columns
                for col_tuple in columns:
                    if col_tuple[0]:  # table.column format
                        table, column = col_tuple[0], col_tuple[1]
                        if table == seq_scan_table or column:
                            recommendations.append(IndexRecommendation(
                                table=seq_scan_table,
                                columns=[column or col_tuple[2]],
                                index_type="btree",
                                reason=f"WHERE clause filters on {column or col_tuple[2]}",
                                estimated_improvement="50-90% faster",
                                priority=OptimizationLevel.CRITICAL if seq_scan_table in explain_analysis.sequential_scans else OptimizationLevel.WARNING,
                                sql=f"CREATE INDEX idx_{seq_scan_table}_{column or col_tuple[2]} ON {seq_scan_table} ({column or col_tuple[2]});"
                            ))
        
        # Analyze JOIN conditions
        join_pattern = re.compile(r'JOIN\s+(\w+)\s+ON\s+(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)', re.IGNORECASE)
        joins = join_pattern.findall(query)
        
        for join in joins:
            table2, table1, col1, table2_ref, col2 = join
            recommendations.append(IndexRecommendation(
                table=table1,
                columns=[col1],
                index_type="btree",
                reason=f"JOIN condition on {col1}",
                estimated_improvement="30-70% faster",
                priority=OptimizationLevel.WARNING,
                sql=f"CREATE INDEX idx_{table1}_{col1} ON {table1} ({col1});"
            ))
        
        # Analyze ORDER BY
        order_pattern = re.compile(r'ORDER\s+BY\s+(\w+)(?:\.(\w+))?', re.IGNORECASE)
        order_match = order_pattern.search(query)
        
        if order_match and explain_analysis.sequential_scans:
            table = order_match.group(1) if order_match.group(2) else None
            column = order_match.group(2) or order_match.group(1)
            
            if table in explain_analysis.sequential_scans or not table:
                recommendations.append(IndexRecommendation(
                    table=table or explain_analysis.sequential_scans[0],
                    columns=[column],
                    index_type="btree",
                    reason=f"ORDER BY on {column}",
                    estimated_improvement="20-50% faster",
                    priority=OptimizationLevel.INFO,
                    sql=f"CREATE INDEX idx_{table or 'table'}_{column} ON {table or 'table'} ({column});"
                ))
        
        # Remove duplicates
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            key = (rec.table, tuple(rec.columns))
            if key not in seen:
                seen.add(key)
                unique_recommendations.append(rec)
        
        return unique_recommendations
    
    def suggest_rewrites(self, query: str, explain_analysis: ExplainAnalysis) -> List[QueryRewrite]:
        """
        Suggest query rewrites for optimization
        
        Args:
            query: Original SQL query
            explain_analysis: EXPLAIN analysis results
            
        Returns:
            List of query rewrite suggestions
        """
        suggestions = []
        
        # Check for SELECT *
        if re.search(r'SELECT\s+\*\s+FROM', query, re.IGNORECASE):
            # Suggest specific columns (simplified - would need schema info)
            suggested = re.sub(r'SELECT\s+\*', 'SELECT /* specific columns */', query, flags=re.IGNORECASE)
            suggestions.append(QueryRewrite(
                original_query=query,
                suggested_query=suggested,
                reason="SELECT * retrieves unnecessary columns",
                estimated_improvement="10-30% faster, less data transfer",
                priority=OptimizationLevel.INFO,
                confidence=0.7
            ))
        
        # Check for missing WHERE clause on large tables
        if explain_analysis.sequential_scans and not re.search(r'WHERE', query, re.IGNORECASE):
            suggestions.append(QueryRewrite(
                original_query=query,
                suggested_query=query,  # Would need user input for WHERE clause
                reason="No WHERE clause - consider adding filters",
                estimated_improvement="Varies based on filter selectivity",
                priority=OptimizationLevel.WARNING,
                confidence=0.5
            ))
        
        # Check for inefficient subqueries
        if re.search(r'SELECT.*\(SELECT', query, re.IGNORECASE):
            # Suggest JOIN instead
            suggestions.append(QueryRewrite(
                original_query=query,
                suggested_query=query,  # Simplified - would need actual rewrite logic
                reason="Consider using JOIN instead of subquery",
                estimated_improvement="20-50% faster",
                priority=OptimizationLevel.WARNING,
                confidence=0.6
            ))
        
        # Check for ORDER BY without LIMIT on large result sets
        if re.search(r'ORDER\s+BY', query, re.IGNORECASE) and not re.search(r'LIMIT', query, re.IGNORECASE):
            if explain_analysis.rows_examined and explain_analysis.rows_examined > 1000:
                suggested = query.rstrip(';') + ' LIMIT 100;'
                suggestions.append(QueryRewrite(
                    original_query=query,
                    suggested_query=suggested,
                    reason="ORDER BY without LIMIT on large result set",
                    estimated_improvement="50-90% faster with LIMIT",
                    priority=OptimizationLevel.WARNING,
                    confidence=0.8
                ))
        
        return suggestions
    
    def optimize_query(self, query: str, track_metrics: bool = False) -> OptimizationReport:
        """
        Generate complete optimization report
        
        Args:
            query: SQL query to optimize
            track_metrics: Whether to track before/after metrics
            
        Returns:
            OptimizationReport
        """
        # Get before metrics if tracking
        before_metrics = None
        if track_metrics:
            try:
                start_time = datetime.utcnow()
                result = self.connector.execute_query(query, fetch=True)
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                before_metrics = {
                    'execution_time': execution_time,
                    'rows_returned': len(result) if result else 0
                }
            except Exception:
                pass
        
        # Analyze query
        explain_analysis = self.analyze_query(query)
        
        # Get recommendations
        index_recommendations = self.recommend_indexes(query, explain_analysis)
        query_rewrites = self.suggest_rewrites(query, explain_analysis)
        
        # Calculate estimated improvement
        improvements = []
        if index_recommendations:
            improvements.append(f"{len(index_recommendations)} index recommendation(s)")
        if query_rewrites:
            improvements.append(f"{len(query_rewrites)} rewrite suggestion(s)")
        
        estimated_improvement = ", ".join(improvements) if improvements else "No major improvements found"
        
        return OptimizationReport(
            query=query,
            explain_analysis=explain_analysis,
            index_recommendations=index_recommendations,
            query_rewrites=query_rewrites,
            before_metrics=before_metrics,
            after_metrics=None,  # Would be populated after applying optimizations
            estimated_improvement=estimated_improvement,
            generated_at=datetime.utcnow().isoformat()
        )

