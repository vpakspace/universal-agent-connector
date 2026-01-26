"""
Entity Disambiguation & Semantic Merging (JAG-001)
Prevents conflating entities like "Jaguar (cat)" and "Jaguar (car company)"
"""

from .type_checker import type_compatibility_check, TypeCompatibilityError, TypeChecker
from .jaguar_resolver import DisambiguationService, DisambiguationResult
from .graph_storage_interface import GraphStorageInterface, MockGraphStorage

__all__ = [
    'type_compatibility_check',
    'TypeCompatibilityError',
    'TypeChecker',
    'DisambiguationService',
    'DisambiguationResult',
    'GraphStorageInterface',
    'MockGraphStorage'
]

