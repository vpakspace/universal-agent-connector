"""
Air-gapped mode utilities
Prevents external API calls when air-gapped mode is enabled
"""

import os
from typing import Optional
from enum import Enum


class AirGappedModeError(Exception):
    """Raised when external API call is attempted in air-gapped mode"""
    pass


class ExternalProvider(Enum):
    """External AI providers that are blocked in air-gapped mode"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM_EXTERNAL = "custom_external"  # Custom provider with external API base


def is_air_gapped_mode() -> bool:
    """
    Check if air-gapped mode is enabled
    
    Returns:
        bool: True if air-gapped mode is enabled
    """
    return os.getenv('AIR_GAPPED_MODE', 'false').lower() in ('true', '1', 'yes')


def validate_provider_allowed(provider: str, api_base: Optional[str] = None) -> None:
    """
    Validate that a provider is allowed in air-gapped mode
    
    Args:
        provider: Provider name (openai, anthropic, custom, local)
        api_base: API base URL (for custom providers)
        
    Raises:
        AirGappedModeError: If external provider is used in air-gapped mode
    """
    if not is_air_gapped_mode():
        return  # Air-gapped mode not enabled, allow all providers
    
    # Local provider is always allowed
    if provider.lower() == 'local':
        return
    
    # Block external providers
    if provider.lower() in ('openai', 'anthropic'):
        raise AirGappedModeError(
            f"External provider '{provider}' is not allowed in air-gapped mode. "
            "Use 'local' provider with a local AI model (Ollama, LocalAI, etc.)"
        )
    
    # For custom providers, check if API base is external
    if provider.lower() == 'custom' and api_base:
        if is_external_url(api_base):
            raise AirGappedModeError(
                f"Custom provider with external API base '{api_base}' is not allowed in air-gapped mode. "
                "Use 'local' provider or ensure API base points to a local service."
            )


def is_external_url(url: str) -> bool:
    """
    Check if a URL is external (not localhost or local network)
    
    Args:
        url: URL to check
        
    Returns:
        bool: True if URL is external
    """
    if not url:
        return False
    
    url_lower = url.lower().strip()
    
    # Local URLs are allowed
    local_patterns = [
        'localhost',
        '127.0.0.1',
        '0.0.0.0',
        '::1',  # IPv6 localhost
        'local',  # .local domain
    ]
    
    # Check if URL contains local patterns
    for pattern in local_patterns:
        if pattern in url_lower:
            return False
    
    # Private network ranges (RFC 1918)
    # Note: This is a simple check, may need more sophisticated IP parsing
    private_ranges = [
        '10.',
        '172.16.',
        '172.17.',
        '172.18.',
        '172.19.',
        '172.20.',
        '172.21.',
        '172.22.',
        '172.23.',
        '172.24.',
        '172.25.',
        '172.26.',
        '172.27.',
        '172.28.',
        '172.29.',
        '172.30.',
        '172.31.',
        '192.168.',
    ]
    
    for private_range in private_ranges:
        if url_lower.startswith(f'http://{private_range}') or url_lower.startswith(f'https://{private_range}'):
            return False
    
    # If not local or private, assume external
    return True


def get_local_ai_config() -> dict:
    """
    Get local AI configuration for air-gapped mode
    
    Returns:
        dict: Configuration with base_url and default model
    """
    return {
        'base_url': os.getenv('LOCAL_AI_BASE_URL', 'http://localhost:11434'),
        'model': os.getenv('LOCAL_AI_MODEL', 'llama2'),
        'api_key': os.getenv('LOCAL_AI_API_KEY')  # Optional, most local models don't need it
    }

