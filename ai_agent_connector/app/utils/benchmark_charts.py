"""
Chart generation for SQL benchmark trends
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path


class BenchmarkChartGenerator:
    """Generate charts for benchmark trends"""
    
    def __init__(self, results_dir: Optional[str] = None):
        """
        Initialize chart generator
        
        Args:
            results_dir: Directory containing benchmark results
        """
        if results_dir:
            self.results_dir = Path(results_dir)
        else:
            self.results_dir = Path("benchmark_results")
        self.results_dir.mkdir(exist_ok=True)
    
    def generate_accuracy_trend_chart(
        self,
        trends_data: Dict[str, Any],
        chart_type: str = "line"
    ) -> Dict[str, Any]:
        """
        Generate accuracy trend chart data
        
        Args:
            trends_data: Trends data from benchmark suite
            chart_type: Type of chart (line, bar, area)
            
        Returns:
            Chart configuration for Chart.js or similar
        """
        trends = trends_data.get('trends', [])
        
        if not trends:
            return {
                'type': chart_type,
                'data': {
                    'labels': [],
                    'datasets': []
                },
                'options': {}
            }
        
        # Group by model
        models = {}
        for trend in trends:
            model = trend['model']
            if model not in models:
                models[model] = {
                    'labels': [],
                    'accuracy': [],
                    'passed': [],
                    'total': []
                }
            
            models[model]['labels'].append(trend['date'])
            models[model]['accuracy'].append(trend['avg_accuracy'])
            models[model]['passed'].append(trend['total_passed'])
            models[model]['total'].append(trend['total_queries'])
        
        # Create datasets
        datasets = []
        colors = [
            {'border': 'rgb(75, 192, 192)', 'background': 'rgba(75, 192, 192, 0.2)'},
            {'border': 'rgb(255, 99, 132)', 'background': 'rgba(255, 99, 132, 0.2)'},
            {'border': 'rgb(54, 162, 235)', 'background': 'rgba(54, 162, 235, 0.2)'},
            {'border': 'rgb(255, 206, 86)', 'background': 'rgba(255, 206, 86, 0.2)'},
            {'border': 'rgb(153, 102, 255)', 'background': 'rgba(153, 102, 255, 0.2)'},
        ]
        
        for i, (model, data) in enumerate(models.items()):
            color = colors[i % len(colors)]
            datasets.append({
                'label': f'{model} Accuracy',
                'data': data['accuracy'],
                'borderColor': color['border'],
                'backgroundColor': color['background'],
                'fill': chart_type == 'area',
                'tension': 0.1
            })
        
        # Use labels from first model (all should have same dates)
        labels = list(models.values())[0]['labels'] if models else []
        
        return {
            'type': chart_type,
            'data': {
                'labels': labels,
                'datasets': datasets
            },
            'options': {
                'responsive': True,
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'max': 1.0,
                        'ticks': {
                            'callback': "function(value) { return (value * 100).toFixed(0) + '%'; }"
                        },
                        'title': {
                            'display': True,
                            'text': 'Accuracy Score'
                        }
                    },
                    'x': {
                        'title': {
                            'display': True,
                            'text': 'Date'
                        }
                    }
                },
                'plugins': {
                    'title': {
                        'display': True,
                        'text': 'SQL Generation Accuracy Trends'
                    },
                    'legend': {
                        'display': True,
                        'position': 'top'
                    },
                    'tooltip': {
                        'callbacks': {
                            'label': "function(context) { return context.dataset.label + ': ' + (context.parsed.y * 100).toFixed(2) + '%'; }"
                        }
                    }
                }
            }
        }
    
    def generate_pass_rate_chart(
        self,
        trends_data: Dict[str, Any],
        chart_type: str = "bar"
    ) -> Dict[str, Any]:
        """
        Generate pass rate chart (exact matches)
        
        Args:
            trends_data: Trends data from benchmark suite
            chart_type: Type of chart (bar, line)
            
        Returns:
            Chart configuration
        """
        trends = trends_data.get('trends', [])
        
        if not trends:
            return {
                'type': chart_type,
                'data': {
                    'labels': [],
                    'datasets': []
                }
            }
        
        # Group by model
        models = {}
        for trend in trends:
            model = trend['model']
            if model not in models:
                models[model] = {
                    'labels': [],
                    'pass_rates': []
                }
            
            total = trend['total_queries']
            passed = trend['total_passed']
            pass_rate = (passed / total * 100) if total > 0 else 0
            
            models[model]['labels'].append(trend['date'])
            models[model]['pass_rates'].append(pass_rate)
        
        # Create datasets
        datasets = []
        colors = [
            {'border': 'rgb(75, 192, 192)', 'background': 'rgba(75, 192, 192, 0.5)'},
            {'border': 'rgb(255, 99, 132)', 'background': 'rgba(255, 99, 132, 0.5)'},
            {'border': 'rgb(54, 162, 235)', 'background': 'rgba(54, 162, 235, 0.5)'},
        ]
        
        for i, (model, data) in enumerate(models.items()):
            color = colors[i % len(colors)]
            datasets.append({
                'label': f'{model} Pass Rate',
                'data': data['pass_rates'],
                'borderColor': color['border'],
                'backgroundColor': color['background']
            })
        
        labels = list(models.values())[0]['labels'] if models else []
        
        return {
            'type': chart_type,
            'data': {
                'labels': labels,
                'datasets': datasets
            },
            'options': {
                'responsive': True,
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'max': 100,
                        'ticks': {
                            'callback': "function(value) { return value + '%'; }"
                        },
                        'title': {
                            'display': True,
                            'text': 'Pass Rate (%)'
                        }
                    },
                    'x': {
                        'title': {
                            'display': True,
                            'text': 'Date'
                        }
                    }
                },
                'plugins': {
                    'title': {
                        'display': True,
                        'text': 'SQL Generation Pass Rate (Exact Matches)'
                    },
                    'legend': {
                        'display': True
                    }
                }
            }
        }
    
    def generate_category_accuracy_chart(
        self,
        run_results: List[Dict[str, Any]],
        chart_type: str = "bar"
    ) -> Dict[str, Any]:
        """
        Generate accuracy by category chart
        
        Args:
            run_results: List of benchmark results
            chart_type: Type of chart (bar, pie)
            
        Returns:
            Chart configuration
        """
        # Group by category
        categories = {}
        for result in run_results:
            category = result.get('category', 'unknown')
            if category not in categories:
                categories[category] = {
                    'scores': [],
                    'count': 0
                }
            
            categories[category]['scores'].append(result.get('accuracy_score', 0))
            categories[category]['count'] += 1
        
        # Calculate averages
        category_data = []
        for category, data in categories.items():
            avg_score = sum(data['scores']) / len(data['scores']) if data['scores'] else 0
            category_data.append({
                'category': category,
                'accuracy': avg_score,
                'count': data['count']
            })
        
        # Sort by accuracy
        category_data.sort(key=lambda x: x['accuracy'], reverse=True)
        
        labels = [d['category'] for d in category_data]
        accuracies = [d['accuracy'] * 100 for d in category_data]  # Convert to percentage
        
        colors = [
            'rgba(75, 192, 192, 0.5)',
            'rgba(255, 99, 132, 0.5)',
            'rgba(54, 162, 235, 0.5)',
            'rgba(255, 206, 86, 0.5)',
            'rgba(153, 102, 255, 0.5)',
        ]
        
        return {
            'type': chart_type,
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': 'Accuracy by Category',
                    'data': accuracies,
                    'backgroundColor': colors[:len(labels)],
                    'borderColor': [c.replace('0.5', '1.0') for c in colors[:len(labels)]],
                    'borderWidth': 1
                }]
            },
            'options': {
                'responsive': True,
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'max': 100,
                        'ticks': {
                            'callback': "function(value) { return value + '%'; }"
                        },
                        'title': {
                            'display': True,
                            'text': 'Accuracy (%)'
                        }
                    }
                },
                'plugins': {
                    'title': {
                        'display': True,
                        'text': 'Accuracy by Query Category'
                    },
                    'legend': {
                        'display': False
                    }
                }
            }
        }
    
    def generate_difficulty_chart(
        self,
        run_results: List[Dict[str, Any]],
        chart_type: str = "bar"
    ) -> Dict[str, Any]:
        """
        Generate accuracy by difficulty level chart
        
        Args:
            run_results: List of benchmark results
            chart_type: Type of chart (bar, pie)
            
        Returns:
            Chart configuration
        """
        # Group by difficulty
        difficulties = {}
        for result in run_results:
            difficulty = result.get('difficulty', 'unknown')
            if difficulty not in difficulties:
                difficulties[difficulty] = {
                    'scores': [],
                    'count': 0
                }
            
            difficulties[difficulty]['scores'].append(result.get('accuracy_score', 0))
            difficulties[difficulty]['count'] += 1
        
        # Calculate averages
        difficulty_order = ['easy', 'medium', 'hard']
        difficulty_data = []
        for diff in difficulty_order:
            if diff in difficulties:
                data = difficulties[diff]
                avg_score = sum(data['scores']) / len(data['scores']) if data['scores'] else 0
                difficulty_data.append({
                    'difficulty': diff,
                    'accuracy': avg_score,
                    'count': data['count']
                })
        
        labels = [d['difficulty'].title() for d in difficulty_data]
        accuracies = [d['accuracy'] * 100 for d in difficulty_data]
        
        return {
            'type': chart_type,
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': 'Accuracy by Difficulty',
                    'data': accuracies,
                    'backgroundColor': [
                        'rgba(75, 192, 192, 0.5)',   # Easy - green
                        'rgba(255, 206, 86, 0.5)',   # Medium - yellow
                        'rgba(255, 99, 132, 0.5)'    # Hard - red
                    ][:len(labels)],
                    'borderColor': [
                        'rgb(75, 192, 192)',
                        'rgb(255, 206, 86)',
                        'rgb(255, 99, 132)'
                    ][:len(labels)],
                    'borderWidth': 1
                }]
            },
            'options': {
                'responsive': True,
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'max': 100,
                        'ticks': {
                            'callback': "function(value) { return value + '%'; }"
                        },
                        'title': {
                            'display': True,
                            'text': 'Accuracy (%)'
                        }
                    }
                },
                'plugins': {
                    'title': {
                        'display': True,
                        'text': 'Accuracy by Difficulty Level'
                    },
                    'legend': {
                        'display': False
                    }
                }
            }
        }
    
    def generate_html_dashboard(
        self,
        trends_data: Dict[str, Any],
        latest_run: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate HTML dashboard with all charts
        
        Args:
            trends_data: Trends data
            latest_run: Latest benchmark run data
            
        Returns:
            HTML string with embedded charts
        """
        accuracy_chart = self.generate_accuracy_trend_chart(trends_data)
        pass_rate_chart = self.generate_pass_rate_chart(trends_data)
        
        # Get category and difficulty charts from latest run
        category_chart = None
        difficulty_chart = None
        if latest_run and 'results' in latest_run:
            category_chart = self.generate_category_accuracy_chart(latest_run['results'])
            difficulty_chart = self.generate_difficulty_chart(latest_run['results'])
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>SQL Benchmark Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .chart-container {{
            margin: 30px 0;
            padding: 20px;
            background: #fafafa;
            border-radius: 4px;
        }}
        .chart-title {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #555;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            font-size: 14px;
            opacity: 0.9;
        }}
        .summary-card .value {{
            font-size: 32px;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>SQL Generation Benchmark Dashboard</h1>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Runs</h3>
                <div class="value">{trends_data.get('total_runs', 0)}</div>
            </div>
            <div class="summary-card">
                <h3>Period</h3>
                <div class="value">{trends_data.get('period_days', 30)} days</div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Accuracy Trends Over Time</div>
            <canvas id="accuracyChart"></canvas>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Pass Rate (Exact Matches) Over Time</div>
            <canvas id="passRateChart"></canvas>
        </div>
"""
        
        if category_chart:
            html += f"""
        <div class="chart-container">
            <div class="chart-title">Accuracy by Category</div>
            <canvas id="categoryChart"></canvas>
        </div>
"""
        
        if difficulty_chart:
            html += f"""
        <div class="chart-container">
            <div class="chart-title">Accuracy by Difficulty</div>
            <canvas id="difficultyChart"></canvas>
        </div>
"""
        
        html += f"""
    </div>
    
    <script>
        // Accuracy Trend Chart
        const accuracyCtx = document.getElementById('accuracyChart');
        new Chart(accuracyCtx, {json.dumps(accuracy_chart)});
        
        // Pass Rate Chart
        const passRateCtx = document.getElementById('passRateChart');
        new Chart(passRateCtx, {json.dumps(pass_rate_chart)});
"""
        
        if category_chart:
            html += f"""
        // Category Chart
        const categoryCtx = document.getElementById('categoryChart');
        new Chart(categoryCtx, {json.dumps(category_chart)});
"""
        
        if difficulty_chart:
            html += f"""
        // Difficulty Chart
        const difficultyCtx = document.getElementById('difficultyChart');
        new Chart(difficultyCtx, {json.dumps(difficulty_chart)});
"""
        
        html += """
    </script>
</body>
</html>
"""
        
        return html
