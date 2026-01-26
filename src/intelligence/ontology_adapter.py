"""
Universal Ontology Adapter (JAG Universal)

Base class and format-specific parsers for loading enterprise ontologies.
Supports multiple formats: Turtle (.ttl), OWL (.owl), JSON-LD (.jsonld), YAML (.yaml)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
import os

# Optional imports
try:
    import rdflib  # type: ignore
    from rdflib import Graph, Namespace, URIRef, Literal  # type: ignore
    from rdflib.namespace import RDF, RDFS, OWL  # type: ignore
    HAS_RDFLIB = True
except ImportError:
    HAS_RDFLIB = False
    rdflib = None  # type: ignore
    Graph = None  # type: ignore
    Namespace = None  # type: ignore
    URIRef = None  # type: ignore
    Literal = None  # type: ignore
    RDF = None  # type: ignore
    RDFS = None  # type: ignore
    OWL = None  # type: ignore

try:
    import yaml  # type: ignore
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None  # type: ignore

try:
    import json
    HAS_JSON = True
except ImportError:
    HAS_JSON = False
    json = None  # type: ignore


@dataclass
class OntologyClass:
    """Represents an ontology class"""
    uri: str
    label: str
    comment: Optional[str] = None
    parent_classes: List[str] = None  # type: ignore
    properties: List[str] = None  # type: ignore
    restrictions: Dict[str, Any] = None  # type: ignore
    
    def __post_init__(self):
        if self.parent_classes is None:
            self.parent_classes = []
        if self.properties is None:
            self.properties = []
        if self.restrictions is None:
            self.restrictions = {}


@dataclass
class OntologyProperty:
    """Represents an ontology property"""
    uri: str
    label: str
    comment: Optional[str] = None
    domain: Optional[str] = None  # Class that uses this property
    range: Optional[str] = None  # Type of values
    cardinality: Optional[Dict[str, int]] = None  # min, max, exactly
    inverse_property: Optional[str] = None


@dataclass
class OntologyAxiom:
    """Represents an ontology axiom/restriction"""
    type: str  # e.g., "minAge", "cardinality", "typeRestriction"
    subject: str  # Class or property URI
    predicate: str  # Restriction type
    object: Any  # Restriction value
    source: str  # Source format (OWL, SHACL, YAML)


class OntologyAdapter(ABC):
    """
    Abstract base class for ontology parsers.
    
    Each format-specific parser implements this interface.
    """
    
    @abstractmethod
    def parse_ontology(self, file_path: str) -> Dict[str, Any]:
        """
        Parse ontology file and return structured representation.
        
        Args:
            file_path: Path to ontology file
            
        Returns:
            Dictionary with parsed ontology data
        """
        pass
    
    @abstractmethod
    def extract_classes(self, ontology_data: Dict[str, Any]) -> List[OntologyClass]:
        """
        Extract all classes from ontology.
        
        Args:
            ontology_data: Parsed ontology data
            
        Returns:
            List of OntologyClass objects
        """
        pass
    
    @abstractmethod
    def extract_properties(self, ontology_data: Dict[str, Any]) -> List[OntologyProperty]:
        """
        Extract all properties from ontology.
        
        Args:
            ontology_data: Parsed ontology data
            
        Returns:
            List of OntologyProperty objects
        """
        pass
    
    @abstractmethod
    def extract_axioms(self, ontology_data: Dict[str, Any]) -> List[OntologyAxiom]:
        """
        Extract all axioms/restrictions from ontology.
        
        Args:
            ontology_data: Parsed ontology data
            
        Returns:
            List of OntologyAxiom objects
        """
        pass


class TurtleParser(OntologyAdapter):
    """
    Parser for Turtle/OWL format (.ttl, .owl files).
    
    Uses rdflib to parse RDF/Turtle ontologies.
    """
    
    def __init__(self):
        """Initialize Turtle parser"""
        if not HAS_RDFLIB:
            raise ImportError(
                "rdflib is required for Turtle/OWL parsing. "
                "Install with: pip install rdflib"
            )
    
    def parse_ontology(self, file_path: str) -> Dict[str, Any]:
        """Parse Turtle/OWL file using rdflib"""
        graph = Graph()
        
        # Detect format from extension
        if file_path.endswith('.ttl'):
            graph.parse(file_path, format='turtle')
        elif file_path.endswith('.owl'):
            graph.parse(file_path, format='xml')
        else:
            # Try turtle first, fallback to xml
            try:
                graph.parse(file_path, format='turtle')
            except:
                graph.parse(file_path, format='xml')
        
        return {
            'graph': graph,
            'format': 'turtle',
            'file_path': file_path
        }
    
    def extract_classes(self, ontology_data: Dict[str, Any]) -> List[OntologyClass]:
        """Extract classes from RDF graph"""
        graph = ontology_data['graph']
        classes = []
        
        # Find all OWL classes
        for class_uri in graph.subjects(RDF.type, OWL.Class):
            # Get label
            label = None
            for label_obj in graph.objects(class_uri, RDFS.label):
                if isinstance(label_obj, Literal):
                    label = str(label_obj)
                    break
            
            if not label:
                # Use URI fragment as label
                label = str(class_uri).split('#')[-1].split('/')[-1]
            
            # Get comment
            comment = None
            for comment_obj in graph.objects(class_uri, RDFS.comment):
                if isinstance(comment_obj, Literal):
                    comment = str(comment_obj)
                    break
            
            # Get parent classes (subClassOf)
            parent_classes = []
            for parent in graph.objects(class_uri, RDFS.subClassOf):
                if isinstance(parent, URIRef):
                    parent_classes.append(str(parent))
            
            # Get properties (properties where this class is domain)
            properties = []
            for prop_uri in graph.subjects(RDFS.domain, class_uri):
                properties.append(str(prop_uri))
            
            classes.append(OntologyClass(
                uri=str(class_uri),
                label=label,
                comment=comment,
                parent_classes=parent_classes,
                properties=properties
            ))
        
        return classes
    
    def extract_properties(self, ontology_data: Dict[str, Any]) -> List[OntologyProperty]:
        """Extract properties from RDF graph"""
        graph = ontology_data['graph']
        properties = []
        
        # Find all OWL ObjectProperties and DatatypeProperties
        for prop_uri in graph.subjects(RDF.type, OWL.ObjectProperty):
            prop = self._extract_property(graph, prop_uri)
            if prop:
                properties.append(prop)
        
        for prop_uri in graph.subjects(RDF.type, OWL.DatatypeProperty):
            prop = self._extract_property(graph, prop_uri)
            if prop:
                properties.append(prop)
        
        return properties
    
    def _extract_property(self, graph: Any, prop_uri: Any) -> Optional[OntologyProperty]:
        """Extract single property details"""
        # Get label
        label = None
        for label_obj in graph.objects(prop_uri, RDFS.label):
            if isinstance(label_obj, Literal):
                label = str(label_obj)
                break
        
        if not label:
            label = str(prop_uri).split('#')[-1].split('/')[-1]
        
        # Get comment
        comment = None
        for comment_obj in graph.objects(prop_uri, RDFS.comment):
            if isinstance(comment_obj, Literal):
                comment = str(comment_obj)
                break
        
        # Get domain
        domain = None
        for domain_obj in graph.objects(prop_uri, RDFS.domain):
            if isinstance(domain_obj, URIRef):
                domain = str(domain_obj)
                break
        
        # Get range
        range_uri = None
        for range_obj in graph.objects(prop_uri, RDFS.range):
            if isinstance(range_obj, URIRef):
                range_uri = str(range_obj)
                break
        
        # Get inverse property
        inverse = None
        for inverse_obj in graph.objects(prop_uri, OWL.inverseOf):
            if isinstance(inverse_obj, URIRef):
                inverse = str(inverse_obj)
                break
        
        return OntologyProperty(
            uri=str(prop_uri),
            label=label,
            comment=comment,
            domain=domain,
            range=range_uri,
            inverse_property=inverse
        )
    
    def extract_axioms(self, ontology_data: Dict[str, Any]) -> List[OntologyAxiom]:
        """Extract axioms/restrictions from RDF graph"""
        graph = ontology_data['graph']
        axioms = []
        
        # Extract OWL restrictions (simplified)
        # This is a basic implementation - can be extended for complex restrictions
        for subj, pred, obj in graph:
            if isinstance(obj, URIRef) and str(obj).endswith('Restriction'):
                # OWL restriction found
                axioms.append(OntologyAxiom(
                    type='owl_restriction',
                    subject=str(subj),
                    predicate=str(pred),
                    object=str(obj),
                    source='owl'
                ))
        
        return axioms


class YAMLParser(OntologyAdapter):
    """
    Parser for simplified YAML ontology manifests.
    
    Supports simplified YAML format for quick ontology definition.
    """
    
    def __init__(self):
        """Initialize YAML parser"""
        if not HAS_YAML:
            raise ImportError(
                "pyyaml is required for YAML parsing. "
                "Install with: pip install pyyaml"
            )
    
    def parse_ontology(self, file_path: str) -> Dict[str, Any]:
        """Parse YAML ontology file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return {
            'data': data,
            'format': 'yaml',
            'file_path': file_path
        }
    
    def extract_classes(self, ontology_data: Dict[str, Any]) -> List[OntologyClass]:
        """Extract classes from YAML data"""
        data = ontology_data['data']
        classes = []
        
        if 'classes' in data:
            for class_def in data['classes']:
                classes.append(OntologyClass(
                    uri=class_def.get('uri', ''),
                    label=class_def.get('label', ''),
                    comment=class_def.get('comment'),
                    parent_classes=class_def.get('extends', []),
                    properties=class_def.get('properties', []),
                    restrictions=class_def.get('restrictions', {})
                ))
        
        return classes
    
    def extract_properties(self, ontology_data: Dict[str, Any]) -> List[OntologyProperty]:
        """Extract properties from YAML data"""
        data = ontology_data['data']
        properties = []
        
        if 'properties' in data:
            for prop_def in data['properties']:
                properties.append(OntologyProperty(
                    uri=prop_def.get('uri', ''),
                    label=prop_def.get('label', ''),
                    comment=prop_def.get('comment'),
                    domain=prop_def.get('domain'),
                    range=prop_def.get('range'),
                    cardinality=prop_def.get('cardinality'),
                    inverse_property=prop_def.get('inverse')
                ))
        
        return properties
    
    def extract_axioms(self, ontology_data: Dict[str, Any]) -> List[OntologyAxiom]:
        """Extract axioms from YAML data"""
        data = ontology_data['data']
        axioms = []
        
        if 'axioms' in data:
            for axiom_def in data['axioms']:
                axioms.append(OntologyAxiom(
                    type=axiom_def.get('type', 'custom'),
                    subject=axiom_def.get('subject', ''),
                    predicate=axiom_def.get('predicate', ''),
                    object=axiom_def.get('object'),
                    source='yaml'
                ))
        
        return axioms


class JSONLDParser(OntologyAdapter):
    """
    Parser for JSON-LD format (.jsonld files).
    
    Uses JSON-LD context to parse linked data ontologies.
    """
    
    def __init__(self):
        """Initialize JSON-LD parser"""
        if not HAS_JSON:
            raise ImportError("json module required (built-in)")
    
    def parse_ontology(self, file_path: str) -> Dict[str, Any]:
        """Parse JSON-LD ontology file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            'data': data,
            'format': 'jsonld',
            'file_path': file_path
        }
    
    def extract_classes(self, ontology_data: Dict[str, Any]) -> List[OntologyClass]:
        """Extract classes from JSON-LD data"""
        data = ontology_data['data']
        classes = []
        
        # JSON-LD can be a list or object
        if isinstance(data, list):
            items = data
        elif '@graph' in data:
            items = data['@graph']
        else:
            items = [data]
        
        for item in items:
            if '@type' in item and ('Class' in str(item['@type']) or 'owl:Class' in str(item['@type'])):
                classes.append(OntologyClass(
                    uri=item.get('@id', ''),
                    label=item.get('rdfs:label', item.get('label', '')),
                    comment=item.get('rdfs:comment', item.get('comment')),
                    parent_classes=item.get('rdfs:subClassOf', [])
                ))
        
        return classes
    
    def extract_properties(self, ontology_data: Dict[str, Any]) -> List[OntologyProperty]:
        """Extract properties from JSON-LD data"""
        data = ontology_data['data']
        properties = []
        
        if isinstance(data, list):
            items = data
        elif '@graph' in data:
            items = data['@graph']
        else:
            items = [data]
        
        for item in items:
            if '@type' in item and ('Property' in str(item['@type']) or 'owl:Property' in str(item['@type'])):
                properties.append(OntologyProperty(
                    uri=item.get('@id', ''),
                    label=item.get('rdfs:label', item.get('label', '')),
                    comment=item.get('rdfs:comment', item.get('comment')),
                    domain=item.get('rdfs:domain'),
                    range=item.get('rdfs:range'),
                    inverse_property=item.get('owl:inverseOf')
                ))
        
        return properties
    
    def extract_axioms(self, ontology_data: Dict[str, Any]) -> List[OntologyAxiom]:
        """Extract axioms from JSON-LD data"""
        # JSON-LD axioms would be in the data structure
        # This is a simplified implementation
        return []


def get_ontology_adapter(file_path: str) -> OntologyAdapter:
    """
    Factory function to get appropriate ontology adapter based on file extension.
    
    Args:
        file_path: Path to ontology file
        
    Returns:
        Appropriate OntologyAdapter instance
        
    Raises:
        ValueError: If file format not supported
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in ['.ttl', '.owl']:
        return TurtleParser()
    elif ext in ['.yaml', '.yml']:
        return YAMLParser()
    elif ext in ['.jsonld', '.json-ld']:
        return JSONLDParser()
    else:
        raise ValueError(f"Unsupported ontology format: {ext}. Supported: .ttl, .owl, .yaml, .jsonld")

