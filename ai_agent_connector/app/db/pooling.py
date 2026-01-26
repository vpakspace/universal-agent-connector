"""
Connection pooling and timeout configuration
Provides standardized pooling and timeout settings for all database types
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class PoolingConfig:
    """Configuration for connection pooling"""
    enabled: bool = False
    min_size: int = 1
    max_size: int = 10
    max_overflow: int = 5
    pool_timeout: int = 30  # seconds to wait for connection from pool
    pool_recycle: int = 3600  # seconds before recycling connection
    pool_pre_ping: bool = True  # verify connections before using
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'PoolingConfig':
        """Create PoolingConfig from dictionary"""
        return cls(
            enabled=config.get('enabled', False),
            min_size=config.get('min_size', 1),
            max_size=config.get('max_size', 10),
            max_overflow=config.get('max_overflow', 5),
            pool_timeout=config.get('pool_timeout', 30),
            pool_recycle=config.get('pool_recycle', 3600),
            pool_pre_ping=config.get('pool_pre_ping', True)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'enabled': self.enabled,
            'min_size': self.min_size,
            'max_size': self.max_size,
            'max_overflow': self.max_overflow,
            'pool_timeout': self.pool_timeout,
            'pool_recycle': self.pool_recycle,
            'pool_pre_ping': self.pool_pre_ping
        }


@dataclass
class TimeoutConfig:
    """Configuration for connection and query timeouts"""
    connect_timeout: int = 10  # seconds to wait for initial connection
    query_timeout: int = 30  # seconds to wait for query execution
    read_timeout: int = 30  # seconds to wait for read operations
    write_timeout: int = 30  # seconds to wait for write operations
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'TimeoutConfig':
        """Create TimeoutConfig from dictionary"""
        return cls(
            connect_timeout=config.get('connect_timeout', 10),
            query_timeout=config.get('query_timeout', 30),
            read_timeout=config.get('read_timeout', 30),
            write_timeout=config.get('write_timeout', 30)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'connect_timeout': self.connect_timeout,
            'query_timeout': self.query_timeout,
            'read_timeout': self.read_timeout,
            'write_timeout': self.write_timeout
        }


def extract_pooling_config(config: Dict[str, Any]) -> PoolingConfig:
    """
    Extract pooling configuration from database config.
    
    Args:
        config: Database configuration dictionary
        
    Returns:
        PoolingConfig instance
    """
    pooling_dict = config.get('pooling', {})
    if isinstance(pooling_dict, dict):
        return PoolingConfig.from_dict(pooling_dict)
    return PoolingConfig()


def extract_timeout_config(config: Dict[str, Any]) -> TimeoutConfig:
    """
    Extract timeout configuration from database config.
    
    Args:
        config: Database configuration dictionary
        
    Returns:
        TimeoutConfig instance
    """
    timeout_dict = config.get('timeouts', {})
    if isinstance(timeout_dict, dict):
        return TimeoutConfig.from_dict(timeout_dict)
    return TimeoutConfig()


def validate_pooling_config(pooling: PoolingConfig) -> None:
    """
    Validate pooling configuration.
    
    Args:
        pooling: PoolingConfig to validate
        
    Raises:
        ValueError: If configuration is invalid
    """
    if pooling.min_size < 1:
        raise ValueError("pooling.min_size must be at least 1")
    if pooling.max_size < pooling.min_size:
        raise ValueError("pooling.max_size must be >= pooling.min_size")
    if pooling.max_overflow < 0:
        raise ValueError("pooling.max_overflow must be >= 0")
    if pooling.pool_timeout < 0:
        raise ValueError("pooling.pool_timeout must be >= 0")
    if pooling.pool_recycle < 0:
        raise ValueError("pooling.pool_recycle must be >= 0")


def validate_timeout_config(timeouts: TimeoutConfig) -> None:
    """
    Validate timeout configuration.
    
    Args:
        timeouts: TimeoutConfig to validate
        
    Raises:
        ValueError: If configuration is invalid
    """
    if timeouts.connect_timeout < 1:
        raise ValueError("timeouts.connect_timeout must be at least 1 second")
    if timeouts.query_timeout < 1:
        raise ValueError("timeouts.query_timeout must be at least 1 second")
    if timeouts.read_timeout < 1:
        raise ValueError("timeouts.read_timeout must be at least 1 second")
    if timeouts.write_timeout < 1:
        raise ValueError("timeouts.write_timeout must be at least 1 second")

