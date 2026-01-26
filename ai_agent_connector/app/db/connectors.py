"""
Database connectors for multiple database types
Supports PostgreSQL, MySQL, MongoDB, BigQuery, and Snowflake
"""

import os
import signal
from typing import Optional, Dict, Any, List, Tuple, Union
from contextlib import contextmanager

from .base_connector import BaseDatabaseConnector
from .pooling import (
    extract_pooling_config,
    extract_timeout_config,
    PoolingConfig,
    TimeoutConfig
)


class PostgreSQLConnector(BaseDatabaseConnector):
    """PostgreSQL database connector with pooling and timeout support"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        try:
            import psycopg2  # type: ignore
            from psycopg2 import pool  # type: ignore
            from psycopg2.extras import RealDictCursor  # type: ignore
            self.psycopg2 = psycopg2
            self.pool_module = pool
            self.RealDictCursor = RealDictCursor
        except ImportError:
            raise ImportError("psycopg2-binary is required for PostgreSQL connections")
        
        self.conn: Optional[Any] = None
        self.pool: Optional[Any] = None
        
        # Extract pooling and timeout configurations
        self.pooling_config = extract_pooling_config(config)
        self.timeout_config = extract_timeout_config(config)
        
        # Parse connection string or individual parameters
        if config.get('connection_string'):
            self.connection_string = config['connection_string']
            self.host = self.port = self.user = self.password = self.database = None
        else:
            self.connection_string = None
            self.host = config.get('host') or os.getenv('DB_HOST')
            self.port = config.get('port') or int(os.getenv('DB_PORT', 5432))
            self.user = config.get('user') or os.getenv('DB_USER')
            self.password = config.get('password') or os.getenv('DB_PASSWORD')
            self.database = config.get('database') or os.getenv('DB_NAME')
        
        # Build connection parameters with timeouts
        self._build_connection_params()
    
    def _build_connection_params(self) -> Dict[str, Any]:
        """Build connection parameters with timeout settings"""
        params = {}
        
        if self.connection_string:
            # For connection strings, timeouts are typically set via query parameters
            # We'll handle this in connect() method
            return params
        
        if not all([self.host, self.user, self.database]):
            return params
        
        params = {
            'host': self.host,
            'port': self.port,
            'user': self.user,
            'password': self.password,
            'dbname': self.database,
            'connect_timeout': self.timeout_config.connect_timeout
        }
        
        return params
    
    def connect(self) -> bool:
        """Establish connection to PostgreSQL database"""
        if self._is_connected and self.conn and not self.conn.closed:
            return True
        
        try:
            # Use connection pool if enabled
            if self.pooling_config.enabled:
                if self.pool is None:
                    self._create_pool()
                self.conn = self.pool.getconn(timeout=self.pooling_config.pool_timeout)
            else:
                # Direct connection
                if self.connection_string:
                    # Add timeout to connection string if not present
                    conn_str = self.connection_string
                    if 'connect_timeout' not in conn_str:
                        separator = '&' if '?' in conn_str else '?'
                        conn_str = f"{conn_str}{separator}connect_timeout={self.timeout_config.connect_timeout}"
                    self.conn = self.psycopg2.connect(conn_str)
                else:
                    params = self._build_connection_params()
                    if not params:
                        raise ValueError(
                            "Missing required connection parameters. "
                            "Provide host, user, and database, or use connection_string."
                        )
                    self.conn = self.psycopg2.connect(**params)
            
            self._is_connected = True
            return True
            
        except Exception as e:
            self._is_connected = False
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}") from e
    
    def _create_pool(self) -> None:
        """Create connection pool"""
        if self.pool is not None:
            return
        
        try:
            if self.connection_string:
                # For connection strings, create pool with connection string
                self.pool = self.pool_module.ThreadedConnectionPool(
                    minconn=self.pooling_config.min_size,
                    maxconn=self.pooling_config.max_size + self.pooling_config.max_overflow,
                    dsn=self.connection_string
                )
            else:
                params = self._build_connection_params()
                if not params:
                    raise ValueError("Cannot create pool: missing connection parameters")
                
                self.pool = self.pool_module.ThreadedConnectionPool(
                    minconn=self.pooling_config.min_size,
                    maxconn=self.pooling_config.max_size + self.pooling_config.max_overflow,
                    host=params['host'],
                    port=params['port'],
                    user=params['user'],
                    password=params['password'],
                    dbname=params['dbname'],
                    connect_timeout=params.get('connect_timeout', 10)
                )
        except Exception as e:
            raise ConnectionError(f"Failed to create connection pool: {e}") from e
    
    def disconnect(self) -> None:
        """Close the database connection"""
        if self.conn:
            if self.pooling_config.enabled and self.pool:
                # Return connection to pool
                try:
                    self.pool.putconn(self.conn)
                except Exception:
                    # If pool is closed or connection is invalid, just close it
                    try:
                        self.conn.close()
                    except Exception:
                        pass
            else:
                # Direct connection - close it
                if not self.conn.closed:
                    self.conn.close()
            self.conn = None
            self._is_connected = False
    
    def close_pool(self) -> None:
        """Close the connection pool"""
        if self.pool:
            try:
                self.pool.closeall()
            except Exception:
                pass
            self.pool = None
    
    def execute_query(
        self,
        query: str,
        params: Optional[Union[Dict[str, Any], Tuple, List]] = None,
        fetch: bool = True,
        as_dict: bool = False
    ) -> Optional[Union[List[Tuple], List[Dict[str, Any]]]]:
        """Execute a SQL query with timeout support"""
        if not self._is_connected or not self.conn or self.conn.closed:
            raise ConnectionError("Database not connected. Call connect() first.")
        
        cursor_factory = self.RealDictCursor if as_dict else None
        
        # Set query timeout if supported
        timeout = self.timeout_config.query_timeout
        
        try:
            with self.conn.cursor(cursor_factory=cursor_factory) as cur:
                # Set statement timeout (PostgreSQL specific)
                if timeout > 0:
                    try:
                        cur.execute(f"SET statement_timeout = {timeout * 1000}")  # Convert to milliseconds
                    except Exception:
                        pass  # If setting timeout fails, continue without it
                
                cur.execute(query, params)
                
                if fetch:
                    return cur.fetchall()
                else:
                    self.conn.commit()
                    return None
                    
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise Exception(f"Query execution failed: {e}") from e
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected and self.conn is not None and not self.conn.closed
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get PostgreSQL database information"""
        if not self.is_connected:
            return {'error': 'Not connected'}
        
        try:
            result = self.execute_query("SELECT version()", fetch=True, as_dict=True)
            version = result[0]['version'] if result else 'Unknown'
            return {
                'type': 'postgresql',
                'version': version,
                'database': self.database or 'unknown'
            }
        except Exception:
            return {'type': 'postgresql', 'database': self.database or 'unknown'}


class MySQLConnector(BaseDatabaseConnector):
    """MySQL database connector with pooling and timeout support"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        try:
            import pymysql  # type: ignore
            self.pymysql = pymysql
        except ImportError:
            raise ImportError("pymysql is required for MySQL connections")
        
        self.conn: Optional[Any] = None
        self.pool: Optional[Any] = None
        
        # Extract pooling and timeout configurations
        self.pooling_config = extract_pooling_config(config)
        self.timeout_config = extract_timeout_config(config)
        
        if config.get('connection_string'):
            # Parse MySQL connection string: mysql://user:pass@host:port/db
            import urllib.parse
            parsed = urllib.parse.urlparse(config['connection_string'])
            self.host = parsed.hostname or 'localhost'
            self.port = parsed.port or 3306
            self.user = parsed.username
            self.password = parsed.password
            self.database = parsed.path.lstrip('/') if parsed.path else None
        else:
            self.host = config.get('host', 'localhost')
            self.port = config.get('port', 3306)
            self.user = config.get('user')
            self.password = config.get('password')
            self.database = config.get('database')
    
    def connect(self) -> bool:
        """Establish connection to MySQL database"""
        if self._is_connected and self.conn:
            return True
        
        try:
            if not all([self.host, self.user, self.database]):
                raise ValueError("Missing required connection parameters: host, user, database")
            
            # Use connection pool if enabled
            if self.pooling_config.enabled:
                if self.pool is None:
                    self._create_pool()
                self.conn = self.pool.connection()
            else:
                # Direct connection with timeout settings
                self.conn = self.pymysql.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    cursorclass=self.pymysql.cursors.DictCursor,
                    connect_timeout=self.timeout_config.connect_timeout,
                    read_timeout=self.timeout_config.read_timeout,
                    write_timeout=self.timeout_config.write_timeout
                )
            
            self._is_connected = True
            return True
            
        except Exception as e:
            self._is_connected = False
            raise ConnectionError(f"Failed to connect to MySQL: {e}") from e
    
    def _create_pool(self) -> None:
        """Create MySQL connection pool"""
        if self.pool is not None:
            return
        
        try:
            from pymysql import pools  # type: ignore
            
            # Create pool configuration
            pool_config = {
                'host': self.host,
                'port': self.port,
                'user': self.user,
                'password': self.password,
                'database': self.database,
                'cursorclass': self.pymysql.cursors.DictCursor,
                'connect_timeout': self.timeout_config.connect_timeout,
                'read_timeout': self.timeout_config.read_timeout,
                'write_timeout': self.timeout_config.write_timeout
            }
            
            # Create pool (pymysql uses a different pooling mechanism)
            # For simplicity, we'll use a custom pool manager
            self.pool = self._create_custom_pool(pool_config)
        except Exception as e:
            raise ConnectionError(f"Failed to create connection pool: {e}") from e
    
    def _create_custom_pool(self, pool_config: Dict[str, Any]) -> Any:
        """Create a simple connection pool for MySQL"""
        # Since pymysql doesn't have built-in pooling like psycopg2,
        # we'll create a simple pool using a queue
        from queue import Queue
        import threading
        
        class SimpleConnectionPool:
            def __init__(self, config: Dict[str, Any], min_size: int, max_size: int):
                self.config = config
                self.min_size = min_size
                self.max_size = max_size
                self.pool = Queue(maxsize=max_size)
                self.lock = threading.Lock()
                self.created = 0
                
                # Pre-populate pool
                for _ in range(min_size):
                    conn = self.pymysql.connect(**config)
                    self.pool.put(conn)
                    self.created += 1
            
            def connection(self):
                try:
                    # Try to get connection from pool (non-blocking)
                    conn = self.pool.get_nowait()
                    return conn
                except:
                    # Pool empty, create new connection if under max
                    with self.lock:
                        if self.created < self.max_size:
                            conn = self.pymysql.connect(**self.config)
                            self.created += 1
                            return conn
                        else:
                            # Wait for connection from pool
                            return self.pool.get(timeout=self.pooling_config.pool_timeout)
            
            def put_connection(self, conn):
                try:
                    self.pool.put_nowait(conn)
                except:
                    # Pool full, close connection
                    conn.close()
            
            def closeall(self):
                while not self.pool.empty():
                    try:
                        conn = self.pool.get_nowait()
                        conn.close()
                    except:
                        break
        
        return SimpleConnectionPool(pool_config, self.pooling_config.min_size, 
                                   self.pooling_config.max_size + self.pooling_config.max_overflow)
    
    def disconnect(self) -> None:
        """Close the database connection"""
        if self.conn:
            if self.pooling_config.enabled and self.pool:
                # Return connection to pool
                try:
                    self.pool.put_connection(self.conn)
                except Exception:
                    # If pool is closed or connection is invalid, just close it
                    try:
                        self.conn.close()
                    except Exception:
                        pass
            else:
                # Direct connection - close it
                self.conn.close()
            self.conn = None
            self._is_connected = False
    
    def close_pool(self) -> None:
        """Close the connection pool"""
        if self.pool:
            try:
                self.pool.closeall()
            except Exception:
                pass
            self.pool = None
    
    def execute_query(
        self,
        query: str,
        params: Optional[Union[Dict[str, Any], Tuple, List]] = None,
        fetch: bool = True,
        as_dict: bool = False
    ) -> Optional[Union[List[Tuple], List[Dict[str, Any]]]]:
        """Execute a SQL query with timeout support"""
        if not self._is_connected or not self.conn:
            raise ConnectionError("Database not connected. Call connect() first.")
        
        # MySQL timeouts are set at connection level, but we can set query timeout
        timeout = self.timeout_config.query_timeout
        
        try:
            with self.conn.cursor() as cur:
                # Set query timeout if supported (MySQL 5.7.8+)
                if timeout > 0:
                    try:
                        cur.execute(f"SET SESSION max_execution_time = {timeout * 1000}")  # Convert to milliseconds
                    except Exception:
                        pass  # If setting timeout fails, continue without it
                
                cur.execute(query, params)
                
                if fetch:
                    results = cur.fetchall()
                    if as_dict:
                        return results
                    else:
                        # Convert dict cursor results to tuples
                        return [tuple(row.values()) for row in results]
                else:
                    self.conn.commit()
                    return None
                    
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise Exception(f"Query execution failed: {e}") from e
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected and self.conn is not None
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get MySQL database information"""
        if not self.is_connected:
            return {'error': 'Not connected'}
        
        try:
            result = self.execute_query("SELECT VERSION() as version", fetch=True, as_dict=True)
            version = result[0]['version'] if result else 'Unknown'
            return {
                'type': 'mysql',
                'version': version,
                'database': self.database or 'unknown'
            }
        except Exception:
            return {'type': 'mysql', 'database': self.database or 'unknown'}


class MongoDBConnector(BaseDatabaseConnector):
    """MongoDB database connector"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        try:
            from pymongo import MongoClient  # type: ignore
            self.MongoClient = MongoClient
        except ImportError:
            raise ImportError("pymongo is required for MongoDB connections")
        
        self.client: Optional[Any] = None
        self.db: Optional[Any] = None
        
        if config.get('connection_string'):
            self.connection_string = config['connection_string']
            self.database_name = config.get('database', 'admin')
        else:
            self.connection_string = None
            self.host = config.get('host', 'localhost')
            self.port = config.get('port', 27017)
            self.user = config.get('user')
            self.password = config.get('password')
            self.database_name = config.get('database', 'admin')
    
    def connect(self) -> bool:
        """Establish connection to MongoDB"""
        if self._is_connected and self.client:
            return True
        
        try:
            if self.connection_string:
                self.client = self.MongoClient(self.connection_string)
            else:
                if self.user and self.password:
                    self.client = self.MongoClient(
                        host=self.host,
                        port=self.port,
                        username=self.user,
                        password=self.password,
                        authSource=self.database_name
                    )
                else:
                    self.client = self.MongoClient(
                        host=self.host,
                        port=self.port
                    )
            
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            
            self._is_connected = True
            return True
            
        except Exception as e:
            self._is_connected = False
            raise ConnectionError(f"Failed to connect to MongoDB: {e}") from e
    
    def disconnect(self) -> None:
        """Close the database connection"""
        if self.client:
            self.client.close()
            self._is_connected = False
    
    def execute_query(
        self,
        query: str,
        params: Optional[Union[Dict[str, Any], Tuple, List]] = None,
        fetch: bool = True,
        as_dict: bool = False
    ) -> Optional[Union[List[Tuple], List[Dict[str, Any]]]]:
        """
        Execute a MongoDB query.
        
        Note: For MongoDB, the query should be a JSON string or dict.
        This is a simplified implementation - in production, you'd want
        more sophisticated query parsing.
        """
        if not self._is_connected or not self.db:
            raise ConnectionError("Database not connected. Call connect() first.")
        
        try:
            import json
            # Parse query - expecting format like: {"collection": "users", "filter": {...}, "projection": {...}}
            if isinstance(query, str):
                query_dict = json.loads(query)
            else:
                query_dict = query
            
            collection_name = query_dict.get('collection')
            if not collection_name:
                raise ValueError("Query must specify 'collection'")
            
            collection = self.db[collection_name]
            filter_dict = query_dict.get('filter', {})
            projection = query_dict.get('projection')
            
            if fetch:
                cursor = collection.find(filter_dict, projection)
                results = list(cursor)
                if as_dict:
                    return results
                else:
                    # Convert to list of tuples (simplified)
                    return [tuple(doc.values()) for doc in results]
            else:
                # For write operations
                operation = query_dict.get('operation', 'find')
                if operation == 'insert':
                    data = query_dict.get('data', [])
                    if isinstance(data, list):
                        collection.insert_many(data)
                    else:
                        collection.insert_one(data)
                elif operation == 'update':
                    collection.update_many(
                        filter_dict,
                        query_dict.get('update', {})
                    )
                elif operation == 'delete':
                    collection.delete_many(filter_dict)
                return None
                
        except Exception as e:
            raise Exception(f"Query execution failed: {e}") from e
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected and self.client is not None
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get MongoDB database information"""
        if not self.is_connected:
            return {'error': 'Not connected'}
        
        try:
            server_info = self.client.server_info()
            return {
                'type': 'mongodb',
                'version': server_info.get('version', 'Unknown'),
                'database': self.database_name
            }
        except Exception:
            return {'type': 'mongodb', 'database': self.database_name}


class BigQueryConnector(BaseDatabaseConnector):
    """Google BigQuery database connector"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        try:
            from google.cloud import bigquery  # type: ignore
            self.bigquery = bigquery
        except ImportError:
            raise ImportError("google-cloud-bigquery is required for BigQuery connections")
        
        self.client: Optional[Any] = None
        self.project_id: Optional[str] = None
        self.dataset_id: Optional[str] = None
        
        # BigQuery uses service account credentials
        credentials_path = config.get('credentials_path')
        credentials_json = config.get('credentials_json')
        self.project_id = config.get('project_id')
        self.dataset_id = config.get('dataset_id')
        
        if credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        elif credentials_json:
            import json
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                json.dump(credentials_json, f)
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f.name
    
    def connect(self) -> bool:
        """Establish connection to BigQuery"""
        if self._is_connected and self.client:
            return True
        
        try:
            self.client = self.bigquery.Client(project=self.project_id)
            # Test connection
            list(self.client.list_datasets(max_results=1))
            
            self._is_connected = True
            return True
            
        except Exception as e:
            self._is_connected = False
            raise ConnectionError(f"Failed to connect to BigQuery: {e}") from e
    
    def disconnect(self) -> None:
        """Close the database connection"""
        # BigQuery doesn't maintain persistent connections
        self.client = None
        self._is_connected = False
    
    def execute_query(
        self,
        query: str,
        params: Optional[Union[Dict[str, Any], Tuple, List]] = None,
        fetch: bool = True,
        as_dict: bool = False
    ) -> Optional[Union[List[Tuple], List[Dict[str, Any]]]]:
        """Execute a SQL query against BigQuery"""
        if not self._is_connected or not self.client:
            raise ConnectionError("Database not connected. Call connect() first.")
        
        try:
            query_job = self.client.query(query)
            query_job.result()  # Wait for job to complete
            
            if fetch:
                results = list(query_job.result())
                if as_dict:
                    return [dict(row) for row in results]
                else:
                    return [tuple(row.values()) for row in results]
            else:
                return None
                
        except Exception as e:
            raise Exception(f"Query execution failed: {e}") from e
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected and self.client is not None
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get BigQuery database information"""
        if not self.is_connected:
            return {'error': 'Not connected'}
        
        return {
            'type': 'bigquery',
            'project_id': self.project_id,
            'dataset_id': self.dataset_id
        }


class SnowflakeConnector(BaseDatabaseConnector):
    """Snowflake database connector"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        try:
            import snowflake.connector  # type: ignore
            self.snowflake = snowflake.connector
        except ImportError:
            raise ImportError("snowflake-connector-python is required for Snowflake connections")
        
        self.conn: Optional[Any] = None
        
        self.account = config.get('account')
        self.user = config.get('user')
        self.password = config.get('password')
        self.warehouse = config.get('warehouse')
        self.database = config.get('database')
        self.schema = config.get('schema', 'PUBLIC')
        self.role = config.get('role')
    
    def connect(self) -> bool:
        """Establish connection to Snowflake"""
        if self._is_connected and self.conn:
            return True
        
        try:
            if not all([self.account, self.user, self.password]):
                raise ValueError("Missing required connection parameters: account, user, password")
            
            self.conn = self.snowflake.connect(
                account=self.account,
                user=self.user,
                password=self.password,
                warehouse=self.warehouse,
                database=self.database,
                schema=self.schema,
                role=self.role
            )
            
            self._is_connected = True
            return True
            
        except Exception as e:
            self._is_connected = False
            raise ConnectionError(f"Failed to connect to Snowflake: {e}") from e
    
    def disconnect(self) -> None:
        """Close the database connection"""
        if self.conn:
            if self.pooling_config.enabled and self.pool:
                # Return connection to pool
                try:
                    self.pool.put_connection(self.conn)
                except Exception:
                    # If pool is closed or connection is invalid, just close it
                    try:
                        self.conn.close()
                    except Exception:
                        pass
            else:
                # Direct connection - close it
                self.conn.close()
            self.conn = None
            self._is_connected = False
    
    def close_pool(self) -> None:
        """Close the connection pool"""
        if self.pool:
            try:
                self.pool.closeall()
            except Exception:
                pass
            self.pool = None
    
    def execute_query(
        self,
        query: str,
        params: Optional[Union[Dict[str, Any], Tuple, List]] = None,
        fetch: bool = True,
        as_dict: bool = False
    ) -> Optional[Union[List[Tuple], List[Dict[str, Any]]]]:
        """Execute a SQL query against Snowflake"""
        if not self._is_connected or not self.conn:
            raise ConnectionError("Database not connected. Call connect() first.")
        
        cursor = None
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            
            if fetch:
                results = cursor.fetchall()
                if as_dict:
                    # Convert to list of dicts
                    columns = [desc[0] for desc in cursor.description]
                    return [dict(zip(columns, row)) for row in results]
                else:
                    return results
            else:
                return None
                
        except Exception as e:
            raise Exception(f"Query execution failed: {e}") from e
        finally:
            if cursor:
                cursor.close()
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected and self.conn is not None
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get Snowflake database information"""
        if not self.is_connected:
            return {'error': 'Not connected'}
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT CURRENT_VERSION()")
            version = cursor.fetchone()[0]
            cursor.close()
            
            return {
                'type': 'snowflake',
                'version': version,
                'account': self.account,
                'database': self.database,
                'warehouse': self.warehouse
            }
        except Exception:
            return {
                'type': 'snowflake',
                'account': self.account,
                'database': self.database
            }

