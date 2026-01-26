"""
Natural language explanations of query results
Explains query results in plain language
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json


@dataclass
class ExplanationConfig:
    """Configuration for explanation"""
    language: str = "en"
    detail_level: str = "medium"  # brief, medium, detailed
    include_statistics: bool = True
    include_trends: bool = True
    include_comparisons: bool = True


class ResultExplainer:
    """
    Generates natural language explanations of query results.
    """
    
    def __init__(self):
        """Initialize result explainer"""
        pass
    
    def explain_results(
        self,
        data: List[Dict[str, Any]],
        query: Optional[str] = None,
        config: Optional[ExplanationConfig] = None
    ) -> Dict[str, Any]:
        """
        Generate natural language explanation of results.
        
        Args:
            data: Query result data
            query: Optional original query
            config: Explanation configuration
            
        Returns:
            Dict with explanation and insights
        """
        if not config:
            config = ExplanationConfig()
        
        if not data:
            return {
                'explanation': 'The query returned no results.',
                'summary': 'No data found',
                'insights': []
            }
        
        # Generate explanation
        explanation = self._generate_explanation(data, query, config)
        
        # Generate insights
        insights = self._generate_insights(data, config)
        
        # Generate summary
        summary = self._generate_summary(data, config)
        
        return {
            'explanation': explanation,
            'summary': summary,
            'insights': insights,
            'statistics': self._calculate_statistics(data) if config.include_statistics else None,
            'row_count': len(data)
        }
    
    def _generate_explanation(
        self,
        data: List[Dict[str, Any]],
        query: Optional[str],
        config: ExplanationConfig
    ) -> str:
        """Generate natural language explanation"""
        row_count = len(data)
        
        # Start with basic explanation
        if row_count == 1:
            explanation = f"The query returned 1 result."
        else:
            explanation = f"The query returned {row_count} results."
        
        # Add statistics if enabled
        if config.include_statistics:
            stats = self._calculate_statistics(data)
            if stats:
                numeric_cols = [col for col, val in stats.items() if isinstance(val, dict) and 'sum' in val]
                if numeric_cols:
                    col = numeric_cols[0]
                    col_stats = stats[col]
                    explanation += f" The total {col} is {col_stats.get('sum', 0):,.0f}."
                    if col_stats.get('avg'):
                        explanation += f" The average is {col_stats.get('avg', 0):,.2f}."
        
        # Add trends if enabled
        if config.include_trends and len(data) > 1:
            trends = self._detect_trends(data)
            if trends:
                explanation += f" {trends}"
        
        # Add comparisons if enabled
        if config.include_comparisons and len(data) > 1:
            comparisons = self._generate_comparisons(data)
            if comparisons:
                explanation += f" {comparisons}"
        
        return explanation
    
    def _generate_summary(self, data: List[Dict[str, Any]], config: ExplanationConfig) -> str:
        """Generate summary"""
        row_count = len(data)
        
        if row_count == 0:
            return "No results found"
        elif row_count == 1:
            return "1 result returned"
        else:
            return f"{row_count} results returned"
    
    def _generate_insights(
        self,
        data: List[Dict[str, Any]],
        config: ExplanationConfig
    ) -> List[str]:
        """Generate insights"""
        insights = []
        
        if not data:
            return insights
        
        # Detect patterns
        patterns = self._detect_patterns(data)
        insights.extend(patterns)
        
        # Detect outliers
        outliers = self._detect_outliers(data)
        insights.extend(outliers)
        
        # Detect trends
        if config.include_trends:
            trends = self._detect_trends(data)
            if trends:
                insights.append(trends)
        
        return insights
    
    def _calculate_statistics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics for numeric columns"""
        if not data:
            return {}
        
        stats = {}
        numeric_cols = self._get_numeric_columns(data)
        
        for col in numeric_cols:
            values = [row.get(col, 0) for row in data if isinstance(row.get(col), (int, float))]
            if values:
                stats[col] = {
                    'sum': sum(values),
                    'avg': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'count': len(values)
                }
        
        return stats
    
    def _detect_trends(self, data: List[Dict[str, Any]]) -> Optional[str]:
        """Detect trends in data"""
        if len(data) < 2:
            return None
        
        numeric_cols = self._get_numeric_columns(data)
        if not numeric_cols:
            return None
        
        col = numeric_cols[0]
        values = [row.get(col, 0) for row in data if isinstance(row.get(col), (int, float))]
        
        if len(values) < 2:
            return None
        
        # Simple trend detection
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = sum(first_half) / len(first_half) if first_half else 0
        second_avg = sum(second_half) / len(second_half) if second_half else 0
        
        if second_avg > first_avg * 1.1:
            change_pct = ((second_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0
            return f"{col} increased by {change_pct:.1f}% over time."
        elif second_avg < first_avg * 0.9:
            change_pct = ((first_avg - second_avg) / first_avg * 100) if first_avg > 0 else 0
            return f"{col} decreased by {change_pct:.1f}% over time."
        
        return None
    
    def _detect_patterns(self, data: List[Dict[str, Any]]) -> List[str]:
        """Detect patterns in data"""
        patterns = []
        
        # Check for common patterns
        if len(data) > 10:
            patterns.append(f"Large dataset with {len(data)} records")
        
        # Check for null values
        null_counts = {}
        for row in data:
            for key, value in row.items():
                if value is None:
                    null_counts[key] = null_counts.get(key, 0) + 1
        
        if null_counts:
            for col, count in null_counts.items():
                if count > len(data) * 0.1:  # More than 10% null
                    patterns.append(f"{col} has {count} missing values ({count/len(data)*100:.1f}%)")
        
        return patterns
    
    def _detect_outliers(self, data: List[Dict[str, Any]]) -> List[str]:
        """Detect outliers in data"""
        outliers = []
        
        numeric_cols = self._get_numeric_columns(data)
        for col in numeric_cols:
            values = [row.get(col, 0) for row in data if isinstance(row.get(col), (int, float))]
            if len(values) < 3:
                continue
            
            avg = sum(values) / len(values)
            std = (sum((x - avg) ** 2 for x in values) / len(values)) ** 0.5
            
            for i, value in enumerate(values):
                if std > 0 and abs(value - avg) > 2 * std:
                    outliers.append(f"Row {i+1} has an outlier value in {col}: {value} (average: {avg:.2f})")
                    break  # Only report first outlier per column
        
        return outliers
    
    def _generate_comparisons(self, data: List[Dict[str, Any]]) -> Optional[str]:
        """Generate comparisons"""
        if len(data) < 2:
            return None
        
        numeric_cols = self._get_numeric_columns(data)
        if not numeric_cols:
            return None
        
        col = numeric_cols[0]
        values = [row.get(col, 0) for row in data if isinstance(row.get(col), (int, float))]
        
        if len(values) < 2:
            return None
        
        min_val = min(values)
        max_val = max(values)
        
        if max_val > min_val * 1.5:
            return f"{col} ranges from {min_val:,.0f} to {max_val:,.0f}, showing significant variation."
        
        return None
    
    def _get_numeric_columns(self, data: List[Dict[str, Any]]) -> List[str]:
        """Get numeric columns from data"""
        if not data:
            return []
        
        numeric_cols = []
        for key, value in data[0].items():
            if isinstance(value, (int, float)):
                numeric_cols.append(key)
        
        return numeric_cols

