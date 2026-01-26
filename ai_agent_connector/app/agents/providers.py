"""
AI Agent Provider System
Supports OpenAI, Anthropic, and custom model providers
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import os
from ..utils.air_gapped import validate_provider_allowed, AirGappedModeError

# Global cost tracker instance (will be initialized in routes.py)
_cost_tracker = None

def set_cost_tracker(tracker):
    """Set the global cost tracker instance"""
    global _cost_tracker
    _cost_tracker = tracker

def get_cost_tracker():
    """Get the global cost tracker instance"""
    return _cost_tracker


class AgentProvider(Enum):
    """Supported AI agent providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"
    LOCAL = "local"  # Local AI models (Ollama, LocalAI, etc.)


@dataclass
class AgentConfiguration:
    """Configuration for an AI agent"""
    provider: AgentProvider
    model: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None  # For custom providers
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 30
    max_retries: int = 3
    custom_headers: Dict[str, str] = field(default_factory=dict)
    custom_params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'provider': self.provider.value,
            'model': self.model,
            'api_key': '***' if self.api_key else None,
            'api_base': self.api_base,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'custom_headers': self.custom_headers,
            'custom_params': self.custom_params
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfiguration':
        """Create from dictionary"""
        provider = AgentProvider(data.get('provider', 'openai'))
        return cls(
            provider=provider,
            model=data.get('model', ''),
            api_key=data.get('api_key'),
            api_base=data.get('api_base'),
            temperature=data.get('temperature', 0.7),
            max_tokens=data.get('max_tokens'),
            timeout=data.get('timeout', 30),
            max_retries=data.get('max_retries', 3),
            custom_headers=data.get('custom_headers', {}),
            custom_params=data.get('custom_params', {})
        )


class BaseAgentProvider(ABC):
    """Base class for AI agent providers"""
    
    @abstractmethod
    def execute_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a query using the AI agent.
        
        Args:
            query: Query or prompt to send to the agent
            context: Optional context information
            
        Returns:
            Dict containing response and metadata
        """
        pass
    
    @abstractmethod
    def validate_configuration(self) -> bool:
        """
        Validate the agent configuration.
        
        Returns:
            bool: True if configuration is valid
        """
        pass


class OpenAIProvider(BaseAgentProvider):
    """OpenAI agent provider"""
    
    def __init__(self, config: AgentConfiguration):
        # Validate provider is allowed in air-gapped mode
        validate_provider_allowed('openai')
        self.config = config
        self._client = None
    
    def _get_client(self):
        """Get OpenAI client (lazy initialization)"""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.config.api_key,
                    timeout=self.config.timeout,
                    max_retries=self.config.max_retries
                )
            except ImportError:
                raise ImportError("openai package is required for OpenAI provider")
        return self._client
    
    def execute_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute query using OpenAI"""
        client = self._get_client()
        
        messages = []
        if context:
            messages.append({"role": "system", "content": context.get('system_prompt', '')})
        messages.append({"role": "user", "content": query})
        
        response = client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            **self.config.custom_params
        )
        
        usage_data = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }
        
        # Track cost
        if _cost_tracker:
            try:
                agent_id = context.get('agent_id') if context else None
                _cost_tracker.track_call(
                    provider='openai',
                    model=response.model,
                    usage=usage_data,
                    agent_id=agent_id,
                    operation_type='query',
                    metadata={'query_length': len(query)}
                )
            except Exception:
                pass  # Don't fail if cost tracking fails
        
        return {
            'response': response.choices[0].message.content,
            'model': response.model,
            'usage': usage_data,
            'provider': 'openai'
        }
    
    def validate_configuration(self) -> bool:
        """Validate OpenAI configuration"""
        if not self.config.api_key:
            return False
        if not self.config.model:
            return False
        return True


class AnthropicProvider(BaseAgentProvider):
    """Anthropic (Claude) agent provider"""
    
    def __init__(self, config: AgentConfiguration):
        # Validate provider is allowed in air-gapped mode
        validate_provider_allowed('anthropic')
        self.config = config
        self._client = None
    
    def _get_client(self):
        """Get Anthropic client (lazy initialization)"""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(
                    api_key=self.config.api_key,
                    timeout=self.config.timeout
                )
            except ImportError:
                raise ImportError("anthropic package is required for Anthropic provider")
        return self._client
    
    def execute_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute query using Anthropic"""
        client = self._get_client()
        
        system_prompt = context.get('system_prompt', '') if context else ''
        
        response = client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens or 1024,
            temperature=self.config.temperature,
            system=system_prompt if system_prompt else None,
            messages=[{"role": "user", "content": query}],
            **self.config.custom_params
        )
        
        usage_data = {
            'input_tokens': response.usage.input_tokens,
            'output_tokens': response.usage.output_tokens
        }
        
        # Track cost
        if _cost_tracker:
            try:
                agent_id = context.get('agent_id') if context else None
                _cost_tracker.track_call(
                    provider='anthropic',
                    model=response.model,
                    usage=usage_data,
                    agent_id=agent_id,
                    operation_type='query',
                    metadata={'query_length': len(query)}
                )
            except Exception:
                pass  # Don't fail if cost tracking fails
        
        return {
            'response': response.content[0].text,
            'model': response.model,
            'usage': usage_data,
            'provider': 'anthropic'
        }
    
    def validate_configuration(self) -> bool:
        """Validate Anthropic configuration"""
        if not self.config.api_key:
            return False
        if not self.config.model:
            return False
        return True


class CustomProvider(BaseAgentProvider):
    """Custom agent provider for custom models"""
    
    def __init__(self, config: AgentConfiguration):
        # Validate provider is allowed in air-gapped mode
        validate_provider_allowed('custom', config.api_base)
        self.config = config
        self._session = None
    
    def _get_session(self):
        """Get HTTP session for custom provider"""
        if self._session is None:
            import requests
            self._session = requests.Session()
            if self.config.custom_headers:
                self._session.headers.update(self.config.custom_headers)
        return self._session
    
    def execute_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute query using custom provider"""
        if not self.config.api_base:
            raise ValueError("api_base is required for custom provider")
        
        session = self._get_session()
        
        payload = {
            'query': query,
            'model': self.config.model,
            'temperature': self.config.temperature,
            **self.config.custom_params
        }
        
        if context:
            payload['context'] = context
        
        response = session.post(
            self.config.api_base,
            json=payload,
            timeout=self.config.timeout,
            headers={'Authorization': f'Bearer {self.config.api_key}'} if self.config.api_key else {}
        )
        response.raise_for_status()
        
        response_data = response.json()
        usage_data = response_data.get('usage', {})
        
        # Track cost (if usage data available)
        if _cost_tracker and usage_data:
            try:
                agent_id = context.get('agent_id') if context else None
                _cost_tracker.track_call(
                    provider='custom',
                    model=self.config.model,
                    usage=usage_data,
                    agent_id=agent_id,
                    operation_type='query',
                    metadata={'query_length': len(query), 'api_base': self.config.api_base}
                )
            except Exception:
                pass  # Don't fail if cost tracking fails
        
        return {
            'response': response_data.get('response', ''),
            'model': self.config.model,
            'provider': 'custom',
            'usage': usage_data,
            'raw_response': response_data
        }
    
    def validate_configuration(self) -> bool:
        """Validate custom provider configuration"""
        if not self.config.api_base:
            return False
        if not self.config.model:
            return False
        return True


class LocalProvider(BaseAgentProvider):
    """Local AI model provider (Ollama, LocalAI, etc.)"""
    
    def __init__(self, config: AgentConfiguration):
        self.config = config
        self._client = None
    
    def _get_client(self):
        """Get local AI client (lazy initialization)"""
        if self._client is None:
            # Default to Ollama if api_base not specified
            api_base = self.config.api_base or os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
            
            try:
                # Try to use OpenAI-compatible client for local models
                from openai import OpenAI
                self._client = OpenAI(
                    base_url=api_base,
                    api_key=self.config.api_key or 'not-needed',  # Local models may not need API key
                    timeout=self.config.timeout,
                    max_retries=self.config.max_retries
                )
            except ImportError:
                raise ImportError("openai package is required for local provider (for OpenAI-compatible API)")
        return self._client
    
    def execute_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute query using local AI model"""
        client = self._get_client()
        
        messages = []
        if context:
            messages.append({"role": "system", "content": context.get('system_prompt', '')})
        messages.append({"role": "user", "content": query})
        
        try:
            response = client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                **self.config.custom_params
            )
            
            usage_data = {
                'prompt_tokens': getattr(response.usage, 'prompt_tokens', 0) if hasattr(response, 'usage') else 0,
                'completion_tokens': getattr(response.usage, 'completion_tokens', 0) if hasattr(response, 'usage') else 0,
                'total_tokens': getattr(response.usage, 'total_tokens', 0) if hasattr(response, 'usage') else 0
            }
            
            return {
                'response': response.choices[0].message.content,
                'model': response.model,
                'usage': usage_data,
                'provider': 'local'
            }
        except Exception as e:
            raise RuntimeError(f"Local AI model error: {str(e)}")
    
    def validate_configuration(self) -> bool:
        """Validate local provider configuration"""
        if not self.config.model:
            return False
        # api_base is optional (defaults to Ollama)
        # api_key is optional for local models
        return True


def create_agent_provider(config: AgentConfiguration) -> BaseAgentProvider:
    """
    Create an agent provider instance based on configuration.
    
    Args:
        config: Agent configuration
        
    Returns:
        BaseAgentProvider: Provider instance
        
    Raises:
        ValueError: If provider type is unsupported
    """
    if config.provider == AgentProvider.OPENAI:
        return OpenAIProvider(config)
    elif config.provider == AgentProvider.ANTHROPIC:
        return AnthropicProvider(config)
    elif config.provider == AgentProvider.CUSTOM:
        return CustomProvider(config)
    elif config.provider == AgentProvider.LOCAL:
        return LocalProvider(config)
    else:
        raise ValueError(f"Unsupported provider: {config.provider}")

