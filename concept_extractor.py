"""
Concept Extractor
Extracts business concepts from natural language queries using keyword matching with confidence scoring
"""

import re
from typing import List, Tuple, Dict
from collections import Counter


# Keyword mappings for each concept with weights
CONCEPT_KEYWORDS: Dict[str, Dict[str, float]] = {
    "Revenue": {
        "revenue": 1.0,
        "sales": 1.0,
        "income": 0.9,
        "earnings": 0.9,
        "money": 0.7,
        "profit": 0.8,
        "invoice": 0.8,
        "payment": 0.7,
        "billing": 0.7,
        "revenue data": 1.0,
        "total sales": 1.0,
        "monthly revenue": 1.0,
        "quarterly revenue": 1.0
    },
    "Customer": {
        "customer": 1.0,
        "client": 0.9,
        "user": 0.8,
        "account": 0.7,
        "buyer": 0.8,
        "customer list": 1.0,
        "customer profile": 1.0,
        "customer segment": 1.0,
        "lifetime value": 0.9,
        "customer satisfaction": 0.9,
        "client data": 1.0
    },
    "Inventory": {
        "inventory": 1.0,
        "stock": 1.0,
        "product": 0.9,
        "warehouse": 0.9,
        "supply": 0.8,
        "stock levels": 1.0,
        "low stock": 1.0,
        "inventory value": 1.0,
        "products": 0.9,
        "warehouse inventory": 1.0,
        "stock reorder": 1.0,
        "availability": 0.8
    },
    "Employee": {
        "employee": 1.0,
        "staff": 0.9,
        "worker": 0.8,
        "personnel": 0.9,
        "hr": 0.8,
        "employee list": 1.0,
        "department": 0.8,
        "payroll": 0.9,
        "attendance": 0.8,
        "team": 0.7,
        "staffing": 0.8,
        "salary": 0.8,
        "employee performance": 0.9
    },
    "Transaction": {
        "transaction": 1.0,
        "payment": 0.9,
        "transfer": 0.8,
        "purchase": 0.9,
        "order": 0.9,
        "transaction history": 1.0,
        "payment log": 1.0,
        "financial transaction": 1.0,
        "transaction summary": 1.0,
        "transaction report": 1.0,
        "payment history": 1.0,
        "order history": 0.9,
        "purchase history": 0.9
    }
}


def normalize_text(text: str) -> str:
    """
    Normalize text for keyword matching
    
    Args:
        text: Input text
        
    Returns:
        Normalized text (lowercase, cleaned)
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove punctuation for matching (but keep structure)
    text = text.strip()
    
    return text


def calculate_concept_score(text: str, concept: str, keywords: Dict[str, float]) -> float:
    """
    Calculate confidence score for a concept based on keyword matches
    
    Args:
        text: Normalized input text
        concept: Concept name
        keywords: Dictionary of keywords and their weights for this concept
        
    Returns:
        Confidence score (0.0 to 1.0)
    """
    if not text or not keywords:
        return 0.0
    
    total_score = 0.0
    matches = 0
    
    # Check for keyword matches (exact and partial)
    for keyword, weight in keywords.items():
        # Exact phrase match (higher weight)
        if keyword in text:
            total_score += weight
            matches += 1
        # Word-level match (lower weight)
        elif len(keyword.split()) == 1:  # Single word
            word_pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(word_pattern, text):
                total_score += weight * 0.8  # Slight penalty for word-level match
                matches += 1
    
    # Normalize score (max possible score is sum of all weights)
    max_possible_score = sum(keywords.values())
    
    if max_possible_score == 0:
        return 0.0
    
    # Calculate normalized score (0.0 to 1.0)
    normalized_score = total_score / max_possible_score
    
    # Boost score if multiple keywords matched (indicates stronger match)
    if matches > 1:
        match_boost = min(0.2, matches * 0.05)  # Up to 0.2 boost
        normalized_score = min(1.0, normalized_score + match_boost)
    
    return normalized_score


def extract_concepts(text: str, min_confidence: float = 0.3) -> List[Tuple[str, float]]:
    """
    Extract business concepts from natural language text with confidence scores
    
    Uses keyword matching with weighted scoring to identify relevant business concepts.
    
    Args:
        text: Natural language query/text
        min_confidence: Minimum confidence score threshold (default: 0.3)
        
    Returns:
        List of (concept_name, confidence_score) tuples, sorted by score descending
        
    Example:
        extract_concepts("Show me customer purchase history")
        # Returns: [("Customer", 0.95), ("Transaction", 0.85)]
    """
    if not text or not text.strip():
        return []
    
    # Normalize input text
    normalized_text = normalize_text(text)
    
    # Calculate scores for each concept
    concept_scores: List[Tuple[str, float]] = []
    
    for concept, keywords in CONCEPT_KEYWORDS.items():
        score = calculate_concept_score(normalized_text, concept, keywords)
        
        if score >= min_confidence:
            concept_scores.append((concept, score))
    
    # Sort by score descending
    concept_scores.sort(key=lambda x: x[1], reverse=True)
    
    return concept_scores


def extract_primary_concept(text: str) -> Tuple[str, float]:
    """
    Extract the primary (highest confidence) concept from text
    
    Args:
        text: Natural language query/text
        
    Returns:
        Tuple of (concept_name, confidence_score) or ("Unknown", 0.0) if no match
    """
    concepts = extract_concepts(text, min_confidence=0.1)
    
    if concepts:
        return concepts[0]  # Highest confidence concept
    
    return ("Unknown", 0.0)


def get_concept_keywords(concept: str) -> Dict[str, float]:
    """
    Get keyword dictionary for a specific concept
    
    Args:
        concept: Concept name
        
    Returns:
        Dictionary of keywords and weights, or empty dict if concept not found
    """
    return CONCEPT_KEYWORDS.get(concept, {})


def explain_concept_match(text: str, concept: str) -> str:
    """
    Generate explanation of why a concept was matched
    
    Args:
        text: Original text
        concept: Concept name
        
    Returns:
        Explanation string
    """
    keywords = get_concept_keywords(concept)
    normalized_text = normalize_text(text)
    
    matched_keywords = []
    for keyword in keywords.keys():
        if keyword in normalized_text or re.search(r'\b' + re.escape(keyword.split()[0]) + r'\b', normalized_text):
            matched_keywords.append(keyword)
    
    if matched_keywords:
        return f"Matched '{concept}' based on keywords: {', '.join(matched_keywords[:3])}"
    else:
        return f"No clear keywords matched for '{concept}'"

