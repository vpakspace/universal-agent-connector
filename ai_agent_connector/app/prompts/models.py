"""
Prompt models and storage
"""

import json
import secrets
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class PromptStatus(Enum):
    """Prompt status"""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    TESTING = "testing"


@dataclass
class PromptVariable:
    """Prompt variable definition"""
    name: str
    description: str
    default_value: str
    required: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptVariable':
        return cls(**data)


@dataclass
class PromptTemplate:
    """Prompt template"""
    id: str
    name: str
    description: str
    system_prompt: str
    user_prompt_template: str
    variables: List[PromptVariable]
    agent_id: Optional[str] = None
    status: str = PromptStatus.DRAFT.value
    created_at: str = None
    updated_at: str = None
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow().isoformat()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['variables'] = [v.to_dict() for v in self.variables]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptTemplate':
        variables = [PromptVariable.from_dict(v) for v in data.get('variables', [])]
        data['variables'] = variables
        return cls(**data)
    
    def render(self, context: Dict[str, Any]) -> tuple[str, str]:
        """
        Render prompt with variables
        
        Args:
            context: Variable values
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Render system prompt
        system = self.system_prompt
        for var in self.variables:
            value = context.get(var.name, var.default_value)
            system = system.replace(f"{{{{{var.name}}}}}", str(value))
        
        # Render user prompt
        user = self.user_prompt_template
        for var in self.variables:
            value = context.get(var.name, var.default_value)
            user = user.replace(f"{{{{{var.name}}}}}", str(value))
        
        return system, user


@dataclass
class ABTest:
    """A/B test configuration"""
    id: str
    name: str
    description: str
    prompt_a_id: str
    prompt_b_id: str
    agent_id: str
    split_ratio: float = 0.5  # 0.5 = 50/50 split
    status: str = "active"
    created_at: str = None
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.metrics is None:
            self.metrics = {
                'prompt_a': {'queries': 0, 'success': 0, 'errors': 0, 'avg_tokens': 0},
                'prompt_b': {'queries': 0, 'success': 0, 'errors': 0, 'avg_tokens': 0}
            }
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ABTest':
        return cls(**data)
    
    def select_prompt(self, user_id: Optional[str] = None) -> str:
        """
        Select prompt for A/B test based on split ratio
        
        Args:
            user_id: Optional user ID for consistent assignment
            
        Returns:
            Prompt ID (prompt_a_id or prompt_b_id)
        """
        # Simple hash-based assignment for consistency
        if user_id:
            import hashlib
            hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            return self.prompt_a_id if (hash_val % 100) < (self.split_ratio * 100) else self.prompt_b_id
        else:
            import random
            return self.prompt_a_id if random.random() < self.split_ratio else self.prompt_b_id


class PromptStore:
    """In-memory prompt storage (use database in production)"""
    
    def __init__(self):
        self._prompts: Dict[str, PromptTemplate] = {}
        self._ab_tests: Dict[str, ABTest] = {}
        self._templates: Dict[str, PromptTemplate] = {}
        self._initialize_default_templates()
    
    def _initialize_default_templates(self):
        """Initialize default template library"""
        # Default PostgreSQL template
        default_postgres = PromptTemplate(
            id="template-postgres-default",
            name="PostgreSQL Default",
            description="Default prompt for PostgreSQL databases",
            system_prompt="""You are a SQL expert specializing in {{database_type}} databases.
Your task is to convert natural language questions into accurate SQL queries.

Rules:
1. Generate ONLY valid {{database_type}} SQL
2. Use proper table and column names from the schema
3. For PostgreSQL, use proper schema.table notation when needed
4. Return ONLY the SQL query, no explanations or markdown
5. Use parameterized queries with %s for values when appropriate
6. Ensure the query is safe and follows best practices

Schema Information:
{{schema_info}}""",
            user_prompt_template="{{natural_language_query}}",
            variables=[
                PromptVariable("database_type", "Database type", "PostgreSQL", True),
                PromptVariable("schema_info", "Schema information", "No schema information available", False),
                PromptVariable("natural_language_query", "Natural language query", "", True)
            ],
            status=PromptStatus.ACTIVE.value,
            metadata={"category": "postgresql", "default": True}
        )
        
        # Optimized for analytics
        analytics_template = PromptTemplate(
            id="template-analytics",
            name="Analytics Optimized",
            description="Optimized for analytical queries with aggregations",
            system_prompt="""You are a SQL expert specializing in analytical queries for {{database_type}} databases.
Focus on generating efficient queries for reporting and analytics.

Rules:
1. Prefer aggregations (SUM, COUNT, AVG) when appropriate
2. Use GROUP BY for grouping data
3. Include ORDER BY for sorted results
4. Optimize for read performance
5. Return ONLY the SQL query, no explanations

Schema Information:
{{schema_info}}""",
            user_prompt_template="{{natural_language_query}}",
            variables=[
                PromptVariable("database_type", "Database type", "PostgreSQL", True),
                PromptVariable("schema_info", "Schema information", "No schema information available", False),
                PromptVariable("natural_language_query", "Natural language query", "", True)
            ],
            status=PromptStatus.ACTIVE.value,
            metadata={"category": "analytics", "optimized_for": "reporting"}
        )
        
        # Strict validation template
        strict_template = PromptTemplate(
            id="template-strict",
            name="Strict Validation",
            description="Strict validation with detailed error checking",
            system_prompt="""You are a SQL expert with strict validation requirements for {{database_type}} databases.

Rules:
1. Validate all table and column names against the schema
2. Use explicit JOIN syntax (no implicit joins)
3. Always specify column names (no SELECT *)
4. Include WHERE clauses for data filtering
5. Validate data types match operations
6. Return ONLY the SQL query, no explanations

Schema Information:
{{schema_info}}""",
            user_prompt_template="{{natural_language_query}}",
            variables=[
                PromptVariable("database_type", "Database type", "PostgreSQL", True),
                PromptVariable("schema_info", "Schema information", "No schema information available", False),
                PromptVariable("natural_language_query", "Natural language query", "", True)
            ],
            status=PromptStatus.ACTIVE.value,
            metadata={"category": "validation", "strict": True}
        )
        
        self._templates = {
            default_postgres.id: default_postgres,
            analytics_template.id: analytics_template,
            strict_template.id: strict_template
        }
    
    def create_prompt(self, prompt: PromptTemplate) -> PromptTemplate:
        """Create a new prompt"""
        if prompt.id in self._prompts:
            raise ValueError(f"Prompt {prompt.id} already exists")
        prompt.updated_at = datetime.utcnow().isoformat()
        self._prompts[prompt.id] = prompt
        return prompt
    
    def get_prompt(self, prompt_id: str) -> Optional[PromptTemplate]:
        """Get prompt by ID"""
        return self._prompts.get(prompt_id)
    
    def update_prompt(self, prompt_id: str, updates: Dict[str, Any]) -> Optional[PromptTemplate]:
        """Update prompt"""
        prompt = self._prompts.get(prompt_id)
        if not prompt:
            return None
        
        for key, value in updates.items():
            if hasattr(prompt, key):
                setattr(prompt, key, value)
        
        prompt.updated_at = datetime.utcnow().isoformat()
        return prompt
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete prompt"""
        if prompt_id in self._prompts:
            del self._prompts[prompt_id]
            return True
        return False
    
    def list_prompts(self, agent_id: Optional[str] = None, status: Optional[str] = None) -> List[PromptTemplate]:
        """List prompts"""
        prompts = list(self._prompts.values())
        
        if agent_id:
            prompts = [p for p in prompts if p.agent_id == agent_id]
        
        if status:
            prompts = [p for p in prompts if p.status == status]
        
        return prompts
    
    def get_templates(self) -> List[PromptTemplate]:
        """Get template library"""
        return list(self._templates.values())
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Get template by ID"""
        return self._templates.get(template_id)
    
    def create_ab_test(self, ab_test: ABTest) -> ABTest:
        """Create A/B test"""
        if ab_test.id in self._ab_tests:
            raise ValueError(f"A/B test {ab_test.id} already exists")
        self._ab_tests[ab_test.id] = ab_test
        return ab_test
    
    def get_ab_test(self, test_id: str) -> Optional[ABTest]:
        """Get A/B test by ID"""
        return self._ab_tests.get(test_id)
    
    def list_ab_tests(self, agent_id: Optional[str] = None) -> List[ABTest]:
        """List A/B tests"""
        tests = list(self._ab_tests.values())
        if agent_id:
            tests = [t for t in tests if t.agent_id == agent_id]
        return tests
    
    def update_ab_test_metrics(self, test_id: str, prompt_id: str, success: bool, tokens: int):
        """Update A/B test metrics"""
        test = self._ab_tests.get(test_id)
        if not test:
            return
        
        if prompt_id == test.prompt_a_id:
            metrics = test.metrics['prompt_a']
        elif prompt_id == test.prompt_b_id:
            metrics = test.metrics['prompt_b']
        else:
            return
        
        metrics['queries'] += 1
        if success:
            metrics['success'] += 1
        else:
            metrics['errors'] += 1
        
        # Update average tokens
        total_tokens = metrics['avg_tokens'] * (metrics['queries'] - 1) + tokens
        metrics['avg_tokens'] = total_tokens / metrics['queries']


# Global prompt store instance
prompt_store = PromptStore()

