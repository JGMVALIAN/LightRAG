"""Normative RAG module for Spanish legal system"""
from .rag_system import SpanishLegalRAGSystem
from .legal_corpus import LegalArea, LegalHierarchy, get_all_laws, get_laws_by_area
from .citation_resolver import SpanishCitationResolver, Citation
from .legal_reasoning import SpanishLegalReasoningEngine, ConflictType, NormativeConflict

__all__ = [
    'SpanishLegalRAGSystem',
    'LegalArea',
    'LegalHierarchy',
    'get_all_laws',
    'get_laws_by_area',
    'SpanishCitationResolver',
    'Citation',
    'SpanishLegalReasoningEngine',
    'ConflictType',
    'NormativeConflict',
]
