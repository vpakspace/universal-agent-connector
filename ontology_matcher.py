"""
Ontology Matcher for Self-Healing Query System
Finds semantically similar column names when queries fail
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict


def load_ontology() -> Dict[str, List[str]]:
    """
    Load column ontology from JSON file
    
    Returns:
        Dictionary mapping concepts to column name lists
    """
    ontology_path = Path(__file__).parent / "column_ontology.json"
    
    try:
        with open(ontology_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Ontology file not found: {ontology_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in ontology file: {e}")


def load_learned_mappings() -> Dict[str, Dict[str, str]]:
    """
    Load learned column mappings from previous healing sessions
    
    Returns:
        Dictionary mapping table -> failed_column -> suggested_column
    """
    mappings_path = Path(__file__).parent / "learned_mappings.json"
    
    if not mappings_path.exists():
        return {}
    
    try:
        with open(mappings_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}  # Return empty dict if file is malformed


def save_learned_mapping(table: str, failed_column: str, suggested_column: str) -> None:
    """
    Save a learned mapping for future use
    
    Args:
        table: Table name
        failed_column: Column name that failed
        suggested_column: Column name that worked
    """
    mappings_path = Path(__file__).parent / "learned_mappings.json"
    
    # Load existing mappings
    mappings = load_learned_mappings()
    
    # Add new mapping
    if table not in mappings:
        mappings[table] = {}
    
    mappings[table][failed_column] = suggested_column
    
    # Save to file
    with open(mappings_path, 'w', encoding='utf-8') as f:
        json.dump(mappings, f, indent=2, ensure_ascii=False)


def find_semantic_alternatives(failed_column: str, table: str) -> List[str]:
    """
    Find semantically similar column names for a failed column
    
    This function:
    1. Checks learned mappings first (table-specific)
    2. Searches ontology for concepts containing the column
    3. Returns all alternatives from matching concepts
    
    Args:
        failed_column: Column name that failed
        table: Table name (for learned mappings)
    
    Returns:
        List of alternative column names (excluding the failed one)
    """
    alternatives = []
    
    # First, check learned mappings (highest priority)
    learned_mappings = load_learned_mappings()
    if table in learned_mappings and failed_column in learned_mappings[table]:
        suggested = learned_mappings[table][failed_column]
        if suggested != failed_column:
            alternatives.append(suggested)
    
    # Load ontology
    ontology = load_ontology()
    
    # Normalize column name for matching (lowercase, underscores)
    normalized_failed = failed_column.lower().replace('-', '_').replace(' ', '_')
    
    # Search ontology for concepts that contain this column
    for concept, column_list in ontology.items():
        # Check if failed column is in this concept's column list
        normalized_list = [col.lower().replace('-', '_').replace(' ', '_') for col in column_list]
        
        if normalized_failed in normalized_list:
            # Add all other columns from this concept as alternatives
            for col in column_list:
                normalized_col = col.lower().replace('-', '_').replace(' ', '_')
                if normalized_col != normalized_failed and col not in alternatives:
                    alternatives.append(col)
    
    # If no alternatives found, try fuzzy matching on column name
    if not alternatives:
        # Extract base words from column name
        words = normalized_failed.split('_')
        
        # Search for concepts with similar words
        for concept, column_list in ontology.items():
            concept_words = concept.split('_')
            
            # If any word matches, add columns from this concept
            if any(word in concept_words for word in words if len(word) > 2):
                for col in column_list:
                    if col not in alternatives:
                        alternatives.append(col)
    
    # Remove the failed column from alternatives (if it somehow got in)
    alternatives = [alt for alt in alternatives if alt.lower() != failed_column.lower()]
    
    return alternatives[:10]  # Limit to top 10 alternatives


def find_table_alternatives(failed_table: str) -> List[str]:
    """
    Find alternative table names (basic implementation)
    
    Args:
        failed_table: Table name that failed
    
    Returns:
        List of alternative table names
    """
    # For now, return empty list (can be enhanced with table ontology)
    # In production, you might have a table ontology mapping
    return []


class ColumnNotFoundError(Exception):
    """Exception raised when a column is not found"""
    pass


class TableNotFoundError(Exception):
    """Exception raised when a table is not found"""
    pass


class TypeMismatchError(Exception):
    """Exception raised when there's a type mismatch"""
    pass

