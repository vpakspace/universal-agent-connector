"""
Training Data Export System
Exports query + SQL pairs for fine-tuning custom models with privacy-safe anonymization
"""

import uuid
import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import csv


class ExportFormat(Enum):
    """Supported export formats for training data"""
    JSONL = "jsonl"  # JSON Lines (one JSON object per line) - preferred for fine-tuning
    CSV = "csv"  # CSV format
    JSON = "json"  # JSON array format


@dataclass
class QuerySQLPair:
    """A pair of natural language query and generated SQL"""
    pair_id: str
    natural_language_query: str
    sql_query: str
    timestamp: str
    database_type: Optional[str] = None
    database_name: Optional[str] = None
    table_names: List[str] = field(default_factory=list)
    success: bool = True
    execution_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuerySQLPair':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class DatasetStatistics:
    """Statistics about the exported dataset"""
    total_pairs: int = 0
    successful_pairs: int = 0
    failed_pairs: int = 0
    unique_tables: Set[str] = field(default_factory=set)
    database_types: Set[str] = field(default_factory=set)
    avg_query_length: float = 0.0
    avg_sql_length: float = 0.0
    date_range: Dict[str, Optional[str]] = field(default_factory=dict)
    query_type_distribution: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['unique_tables'] = list(self.unique_tables)
        result['database_types'] = list(self.database_types)
        return result


class TrainingDataExporter:
    """Manages training data export with privacy-safe anonymization"""
    
    def __init__(self, anonymize_sensitive_data: bool = True):
        """
        Initialize training data exporter
        
        Args:
            anonymize_sensitive_data: Whether to anonymize sensitive data in queries
        """
        self.anonymize_sensitive_data = anonymize_sensitive_data
        
        # Storage for query-SQL pairs (in-memory, should use database in production)
        self.query_sql_pairs: List[QuerySQLPair] = []
        
        # Patterns for sensitive data detection
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
        self.ssn_pattern = re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b')
        self.credit_card_pattern = re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b')
        self.ip_pattern = re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')
    
    def _hash_sensitive_value(self, value: str) -> str:
        """Hash a sensitive value for anonymization"""
        hash_value = hashlib.sha256(value.encode('utf-8')).hexdigest()
        return hash_value[:8]  # Use first 8 chars for shorter anonymized values
    
    def _anonymize_query(self, query: str) -> str:
        """
        Anonymize sensitive data in a query string
        
        Args:
            query: Original query string
            
        Returns:
            Anonymized query string
        """
        if not self.anonymize_sensitive_data:
            return query
        
        anonymized = query
        
        # Anonymize emails
        anonymized = self.email_pattern.sub(
            lambda m: f"user_{self._hash_sensitive_value(m.group())}@example.com",
            anonymized
        )
        
        # Anonymize phone numbers
        anonymized = self.phone_pattern.sub(
            lambda m: f"XXX-XXX-{self._hash_sensitive_value(m.group())[:4]}",
            anonymized
        )
        
        # Anonymize SSNs
        anonymized = self.ssn_pattern.sub(
            lambda m: f"XXX-XX-{self._hash_sensitive_value(m.group())[:4]}",
            anonymized
        )
        
        # Anonymize credit card numbers
        anonymized = self.credit_card_pattern.sub(
            lambda m: f"XXXX-XXXX-XXXX-{self._hash_sensitive_value(m.group())[:4]}",
            anonymized
        )
        
        # Anonymize IP addresses
        anonymized = self.ip_pattern.sub(
            lambda m: f"XXX.XXX.XXX.{self._hash_sensitive_value(m.group())[:3]}",
            anonymized
        )
        
        return anonymized
    
    def _extract_table_names(self, sql: str) -> List[str]:
        """Extract table names from SQL query"""
        # Simple regex-based extraction (can be enhanced with SQL parser)
        table_pattern = re.compile(
            r'\b(?:FROM|JOIN|UPDATE|INTO)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            re.IGNORECASE
        )
        tables = table_pattern.findall(sql)
        return list(set(tables))  # Remove duplicates
    
    def _detect_query_type(self, sql: str) -> str:
        """Detect SQL query type"""
        sql_upper = sql.strip().upper()
        if sql_upper.startswith('SELECT'):
            return 'SELECT'
        elif sql_upper.startswith('INSERT'):
            return 'INSERT'
        elif sql_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif sql_upper.startswith('DELETE'):
            return 'DELETE'
        elif sql_upper.startswith('CREATE'):
            return 'CREATE'
        elif sql_upper.startswith('ALTER'):
            return 'ALTER'
        elif sql_upper.startswith('DROP'):
            return 'DROP'
        else:
            return 'OTHER'
    
    def add_query_sql_pair(
        self,
        natural_language_query: str,
        sql_query: str,
        database_type: Optional[str] = None,
        database_name: Optional[str] = None,
        success: bool = True,
        execution_time_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QuerySQLPair:
        """
        Add a query-SQL pair to the training data
        
        Args:
            natural_language_query: Natural language query
            sql_query: Generated SQL query
            database_type: Type of database (postgresql, mysql, etc.)
            database_name: Name of the database
            success: Whether the query was successful
            execution_time_ms: Execution time in milliseconds
            metadata: Additional metadata
            
        Returns:
            QuerySQLPair object
        """
        # Anonymize natural language query
        anonymized_nl_query = self._anonymize_query(natural_language_query)
        
        # Extract table names from SQL
        table_names = self._extract_table_names(sql_query)
        
        # Anonymize database name if provided
        anonymized_db_name = None
        if database_name:
            if self.anonymize_sensitive_data:
                anonymized_db_name = f"db_{self._hash_sensitive_value(database_name)}"
            else:
                anonymized_db_name = database_name
        
        pair = QuerySQLPair(
            pair_id=str(uuid.uuid4()),
            natural_language_query=anonymized_nl_query,
            sql_query=sql_query,
            timestamp=datetime.utcnow().isoformat(),
            database_type=database_type,
            database_name=anonymized_db_name,
            table_names=table_names,
            success=success,
            execution_time_ms=execution_time_ms,
            metadata=metadata or {}
        )
        
        self.query_sql_pairs.append(pair)
        return pair
    
    def get_statistics(
        self,
        pairs: Optional[List[QuerySQLPair]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> DatasetStatistics:
        """
        Calculate statistics for query-SQL pairs
        
        Args:
            pairs: Optional list of pairs to analyze (defaults to all pairs)
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)
            
        Returns:
            DatasetStatistics object
        """
        if pairs is None:
            pairs = self.query_sql_pairs
        
        # Apply date filter if provided
        if start_date or end_date:
            filtered_pairs = []
            for pair in pairs:
                pair_date = pair.timestamp[:10]  # Extract date part
                if start_date and pair_date < start_date:
                    continue
                if end_date and pair_date > end_date:
                    continue
                filtered_pairs.append(pair)
            pairs = filtered_pairs
        
        if not pairs:
            return DatasetStatistics()
        
        stats = DatasetStatistics()
        stats.total_pairs = len(pairs)
        
        # Calculate statistics
        query_lengths = []
        sql_lengths = []
        timestamps = []
        
        for pair in pairs:
            if pair.success:
                stats.successful_pairs += 1
            else:
                stats.failed_pairs += 1
            
            stats.unique_tables.update(pair.table_names)
            
            if pair.database_type:
                stats.database_types.add(pair.database_type)
            
            query_lengths.append(len(pair.natural_language_query))
            sql_lengths.append(len(pair.sql_query))
            timestamps.append(pair.timestamp)
            
            # Detect query type
            query_type = self._detect_query_type(pair.sql_query)
            stats.query_type_distribution[query_type] = stats.query_type_distribution.get(query_type, 0) + 1
        
        # Calculate averages
        if query_lengths:
            stats.avg_query_length = sum(query_lengths) / len(query_lengths)
        if sql_lengths:
            stats.avg_sql_length = sum(sql_lengths) / len(sql_lengths)
        
        # Date range
        if timestamps:
            stats.date_range = {
                'start': min(timestamps),
                'end': max(timestamps)
            }
        
        return stats
    
    def export_to_jsonl(
        self,
        file_path: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        filter_successful_only: bool = False
    ) -> Tuple[int, DatasetStatistics]:
        """
        Export query-SQL pairs to JSONL format (one JSON object per line)
        This format is preferred for fine-tuning LLMs
        
        Args:
            file_path: Path to output file
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)
            filter_successful_only: Only export successful pairs
            
        Returns:
            Tuple of (number of exported pairs, statistics)
        """
        pairs = self._filter_pairs(start_date, end_date, filter_successful_only)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            for pair in pairs:
                json.dump(pair.to_dict(), f, ensure_ascii=False)
                f.write('\n')
        
        stats = self.get_statistics(pairs, start_date, end_date)
        return len(pairs), stats
    
    def export_to_json(
        self,
        file_path: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        filter_successful_only: bool = False
    ) -> Tuple[int, DatasetStatistics]:
        """
        Export query-SQL pairs to JSON format (array of objects)
        
        Args:
            file_path: Path to output file
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)
            filter_successful_only: Only export successful pairs
            
        Returns:
            Tuple of (number of exported pairs, statistics)
        """
        pairs = self._filter_pairs(start_date, end_date, filter_successful_only)
        
        data = {
            'exported_at': datetime.utcnow().isoformat(),
            'format_version': '1.0',
            'total_pairs': len(pairs),
            'pairs': [pair.to_dict() for pair in pairs],
            'statistics': self.get_statistics(pairs, start_date, end_date).to_dict()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        stats = self.get_statistics(pairs, start_date, end_date)
        return len(pairs), stats
    
    def export_to_csv(
        self,
        file_path: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        filter_successful_only: bool = False
    ) -> Tuple[int, DatasetStatistics]:
        """
        Export query-SQL pairs to CSV format
        
        Args:
            file_path: Path to output file
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)
            filter_successful_only: Only export successful pairs
            
        Returns:
            Tuple of (number of exported pairs, statistics)
        """
        pairs = self._filter_pairs(start_date, end_date, filter_successful_only)
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    'pair_id',
                    'natural_language_query',
                    'sql_query',
                    'timestamp',
                    'database_type',
                    'database_name',
                    'table_names',
                    'success',
                    'execution_time_ms',
                    'query_type'
                ]
            )
            writer.writeheader()
            
            for pair in pairs:
                row = pair.to_dict()
                row['table_names'] = ','.join(pair.table_names)
                row['query_type'] = self._detect_query_type(pair.sql_query)
                # Remove metadata field for CSV
                row.pop('metadata', None)
                writer.writerow(row)
        
        stats = self.get_statistics(pairs, start_date, end_date)
        return len(pairs), stats
    
    def export(
        self,
        file_path: str,
        format: ExportFormat = ExportFormat.JSONL,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        filter_successful_only: bool = False
    ) -> Tuple[int, DatasetStatistics]:
        """
        Export query-SQL pairs in specified format
        
        Args:
            file_path: Path to output file
            format: Export format (JSONL, JSON, CSV)
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)
            filter_successful_only: Only export successful pairs
            
        Returns:
            Tuple of (number of exported pairs, statistics)
        """
        if format == ExportFormat.JSONL:
            return self.export_to_jsonl(file_path, start_date, end_date, filter_successful_only)
        elif format == ExportFormat.JSON:
            return self.export_to_json(file_path, start_date, end_date, filter_successful_only)
        elif format == ExportFormat.CSV:
            return self.export_to_csv(file_path, start_date, end_date, filter_successful_only)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _filter_pairs(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        filter_successful_only: bool = False
    ) -> List[QuerySQLPair]:
        """Filter query-SQL pairs based on criteria"""
        pairs = self.query_sql_pairs
        
        # Filter by date range
        if start_date or end_date:
            filtered = []
            for pair in pairs:
                pair_date = pair.timestamp[:10]  # Extract date part
                if start_date and pair_date < start_date:
                    continue
                if end_date and pair_date > end_date:
                    continue
                filtered.append(pair)
            pairs = filtered
        
        # Filter by success
        if filter_successful_only:
            pairs = [p for p in pairs if p.success]
        
        return pairs
    
    def list_pairs(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        filter_successful_only: bool = False,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[QuerySQLPair]:
        """
        List query-SQL pairs with filtering and pagination
        
        Args:
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)
            filter_successful_only: Only return successful pairs
            limit: Maximum number of pairs to return
            offset: Number of pairs to skip
            
        Returns:
            List of QuerySQLPair objects
        """
        pairs = self._filter_pairs(start_date, end_date, filter_successful_only)
        
        # Apply pagination
        if offset:
            pairs = pairs[offset:]
        if limit:
            pairs = pairs[:limit]
        
        return pairs
    
    def get_pair(self, pair_id: str) -> Optional[QuerySQLPair]:
        """Get a specific query-SQL pair by ID"""
        for pair in self.query_sql_pairs:
            if pair.pair_id == pair_id:
                return pair
        return None
    
    def delete_pair(self, pair_id: str) -> bool:
        """Delete a query-SQL pair by ID"""
        for i, pair in enumerate(self.query_sql_pairs):
            if pair.pair_id == pair_id:
                del self.query_sql_pairs[i]
                return True
        return False


# Global instance
training_data_exporter = TrainingDataExporter()


