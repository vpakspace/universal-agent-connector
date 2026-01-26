"""
Visualization generation from query results
Generates charts and tables from query results
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json


class ChartType(Enum):
    """Chart types"""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"
    TABLE = "table"
    HEATMAP = "heatmap"


@dataclass
class VisualizationConfig:
    """Configuration for visualization"""
    chart_type: ChartType
    title: Optional[str] = None
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    color_scheme: Optional[str] = None
    width: int = 800
    height: int = 600
    show_legend: bool = True
    show_grid: bool = True
    aggregation: Optional[str] = None  # sum, avg, count, etc.
    group_by: Optional[str] = None


class VisualizationGenerator:
    """
    Generates visualizations from query results.
    """
    
    def __init__(self):
        """Initialize visualization generator"""
        pass
    
    def generate_visualization(
        self,
        data: List[Dict[str, Any]],
        config: VisualizationConfig
    ) -> Dict[str, Any]:
        """
        Generate a visualization from data.
        
        Args:
            data: Query result data
            config: Visualization configuration
            
        Returns:
            Dict with visualization data and metadata
        """
        if not data:
            return {
                'type': config.chart_type.value,
                'data': [],
                'message': 'No data available for visualization'
            }
        
        # Process data based on chart type
        processed_data = self._process_data(data, config)
        
        # Generate visualization spec
        visualization = {
            'type': config.chart_type.value,
            'title': config.title or f'{config.chart_type.value.title()} Chart',
            'data': processed_data,
            'config': {
                'width': config.width,
                'height': config.height,
                'show_legend': config.show_legend,
                'show_grid': config.show_grid,
                'color_scheme': config.color_scheme or 'default'
            }
        }
        
        # Add chart-specific configuration
        if config.chart_type != ChartType.TABLE:
            visualization['axes'] = {
                'x': config.x_axis or self._detect_x_axis(data),
                'y': config.y_axis or self._detect_y_axis(data)
            }
        
        return visualization
    
    def _process_data(self, data: List[Dict[str, Any]], config: VisualizationConfig) -> List[Dict[str, Any]]:
        """Process data for visualization"""
        if config.chart_type == ChartType.TABLE:
            return data
        
        # Group data if needed
        if config.group_by:
            grouped = self._group_data(data, config.group_by, config.aggregation)
            return grouped
        
        # Aggregate if needed
        if config.aggregation and not config.group_by:
            aggregated = self._aggregate_data(data, config.aggregation)
            return aggregated
        
        return data
    
    def _group_data(
        self,
        data: List[Dict[str, Any]],
        group_by: str,
        aggregation: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Group and aggregate data"""
        groups = {}
        
        for row in data:
            key = row.get(group_by, 'Unknown')
            if key not in groups:
                groups[key] = []
            groups[key].append(row)
        
        result = []
        for key, group_data in groups.items():
            if aggregation:
                aggregated_value = self._apply_aggregation(group_data, aggregation)
                result.append({group_by: key, 'value': aggregated_value})
            else:
                result.append({group_by: key, 'count': len(group_data)})
        
        return result
    
    def _aggregate_data(
        self,
        data: List[Dict[str, Any]],
        aggregation: str
    ) -> Dict[str, Any]:
        """Aggregate data"""
        numeric_columns = self._get_numeric_columns(data)
        
        result = {}
        for col in numeric_columns:
            values = [row.get(col, 0) for row in data if isinstance(row.get(col), (int, float))]
            if values:
                if aggregation == 'sum':
                    result[col] = sum(values)
                elif aggregation == 'avg':
                    result[col] = sum(values) / len(values)
                elif aggregation == 'count':
                    result[col] = len(values)
                elif aggregation == 'min':
                    result[col] = min(values)
                elif aggregation == 'max':
                    result[col] = max(values)
        
        return result
    
    def _apply_aggregation(
        self,
        data: List[Dict[str, Any]],
        aggregation: str
    ) -> float:
        """Apply aggregation to data"""
        numeric_columns = self._get_numeric_columns(data)
        if not numeric_columns:
            return 0
        
        col = numeric_columns[0]
        values = [row.get(col, 0) for row in data if isinstance(row.get(col), (int, float))]
        
        if not values:
            return 0
        
        if aggregation == 'sum':
            return sum(values)
        elif aggregation == 'avg':
            return sum(values) / len(values)
        elif aggregation == 'count':
            return len(values)
        elif aggregation == 'min':
            return min(values)
        elif aggregation == 'max':
            return max(values)
        
        return 0
    
    def _get_numeric_columns(self, data: List[Dict[str, Any]]) -> List[str]:
        """Get numeric columns from data"""
        if not data:
            return []
        
        numeric_cols = []
        for key, value in data[0].items():
            if isinstance(value, (int, float)):
                numeric_cols.append(key)
        
        return numeric_cols
    
    def _detect_x_axis(self, data: List[Dict[str, Any]]) -> Optional[str]:
        """Detect X axis column"""
        if not data:
            return None
        
        # Prefer string/date columns
        for key, value in data[0].items():
            if isinstance(value, str) and not isinstance(value, (int, float)):
                return key
        
        # Fallback to first column
        return list(data[0].keys())[0] if data[0] else None
    
    def _detect_y_axis(self, data: List[Dict[str, Any]]) -> Optional[str]:
        """Detect Y axis column"""
        numeric_cols = self._get_numeric_columns(data)
        return numeric_cols[0] if numeric_cols else None
    
    def generate_table(self, data: List[Dict[str, Any]], title: Optional[str] = None) -> Dict[str, Any]:
        """Generate a table visualization"""
        config = VisualizationConfig(
            chart_type=ChartType.TABLE,
            title=title
        )
        return self.generate_visualization(data, config)
    
    def generate_chart(
        self,
        data: List[Dict[str, Any]],
        chart_type: ChartType,
        title: Optional[str] = None,
        x_axis: Optional[str] = None,
        y_axis: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a chart visualization"""
        config = VisualizationConfig(
            chart_type=chart_type,
            title=title,
            x_axis=x_axis,
            y_axis=y_axis
        )
        return self.generate_visualization(data, config)

