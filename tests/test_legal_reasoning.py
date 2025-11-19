"""
Tests for Spanish Legal Reasoning Engine
"""
import pytest
from datetime import date
from src.normative_rag import (
    SpanishLegalReasoningEngine,
    ConflictType,
    get_laws_by_area,
    LegalArea,
    LegalHierarchy
)


@pytest.fixture
def engine():
    """Fixture for legal reasoning engine"""
    return SpanishLegalReasoningEngine()


@pytest.fixture
def sample_laws():
    """Fixture for sample laws"""
    laws = get_laws_by_area(LegalArea.CONTRATACION)
    return list(laws.values())[:2]  # Get first 2 laws


def test_hierarchy_resolution(engine):
    """Test lex superior principle"""
    # Create mock norms with different hierarchies
    norms = [
        {
            'id': 'test-rd',
            'hierarchy': LegalHierarchy.REAL_DECRETO,
            'publication_date': date(2020, 1, 1),
            'title': 'Real Decreto Test'
        },
        {
            'id': 'test-ley',
            'hierarchy': LegalHierarchy.LEY_ORDINARIA,
            'publication_date': date(2020, 1, 1),
            'title': 'Ley Test'
        }
    ]

    conflict = engine.resolve_conflict(norms)

    assert conflict.conflict_type == ConflictType.HIERARCHY
    assert conflict.applicable_principle == 'Lex superior derogat legi inferiori'
    assert conflict.resolution['id'] == 'test-ley'  # Ley prevails over Real Decreto


def test_temporal_resolution(engine):
    """Test lex posterior principle"""
    norms = [
        {
            'id': 'test-old',
            'hierarchy': LegalHierarchy.LEY_ORDINARIA,
            'publication_date': date(2015, 1, 1),
            'title': 'Ley Antigua'
        },
        {
            'id': 'test-new',
            'hierarchy': LegalHierarchy.LEY_ORDINARIA,
            'publication_date': date(2020, 1, 1),
            'title': 'Ley Nueva'
        }
    ]

    conflict = engine.resolve_conflict(norms)

    assert conflict.conflict_type == ConflictType.TEMPORAL
    assert conflict.applicable_principle == 'Lex posterior derogat legi priori'
    assert conflict.resolution['id'] == 'test-new'  # Newer law prevails


def test_specialty_resolution(engine):
    """Test lex specialis principle"""
    norms = [
        {
            'id': 'test-general',
            'hierarchy': LegalHierarchy.LEY_ORDINARIA,
            'publication_date': date(2020, 1, 1),
            'title': 'Ley General',
            'is_special_law': False
        },
        {
            'id': 'test-special',
            'hierarchy': LegalHierarchy.LEY_ORDINARIA,
            'publication_date': date(2019, 1, 1),  # Older but special
            'title': 'Ley Especial',
            'is_special_law': True
        }
    ]

    conflict = engine.resolve_conflict(norms)

    assert conflict.conflict_type == ConflictType.SPECIALTY
    assert conflict.applicable_principle == 'Lex specialis derogat legi generali'
    assert conflict.resolution['id'] == 'test-special'  # Special law prevails


def test_single_norm_no_conflict(engine):
    """Test no conflict with single norm"""
    norms = [
        {
            'id': 'test-single',
            'hierarchy': LegalHierarchy.LEY_ORDINARIA,
            'publication_date': date(2020, 1, 1),
            'title': 'Única Ley'
        }
    ]

    conflict = engine.resolve_conflict(norms)

    assert conflict.conflict_type == ConflictType.NO_CONFLICT
    assert conflict.resolution['id'] == 'test-single'


def test_temporal_validity_active(engine):
    """Test temporal validity for active norm"""
    norm = {
        'id': 'test',
        'publication_date': date(2020, 1, 1),
        'entry_force_date': date(2020, 3, 1),
        'active': True
    }

    # Check validity after entry into force
    is_valid = engine.check_temporal_validity(norm, reference_date=date(2021, 1, 1))
    assert is_valid is True


def test_temporal_validity_before_entry(engine):
    """Test temporal validity before entry into force"""
    norm = {
        'id': 'test',
        'publication_date': date(2020, 1, 1),
        'entry_force_date': date(2020, 3, 1),
        'active': True
    }

    # Check validity before entry into force
    is_valid = engine.check_temporal_validity(norm, reference_date=date(2020, 2, 1))
    assert is_valid is False


def test_temporal_validity_repealed(engine):
    """Test temporal validity for repealed norm"""
    norm = {
        'id': 'test',
        'publication_date': date(2010, 1, 1),
        'entry_force_date': date(2010, 3, 1),
        'repeal_date': date(2020, 1, 1),
        'active': False
    }

    # Check validity after repeal
    is_valid = engine.check_temporal_validity(norm, reference_date=date(2021, 1, 1))
    assert is_valid is False


def test_explain_lex_superior(engine):
    """Test explanation of lex superior principle"""
    explanation = engine.explain_principle_application('lex_superior')

    assert 'Lex superior derogat legi inferiori' in explanation
    assert 'Constitución' in explanation
    assert 'jerarquía' in explanation or 'jerarquia' in explanation


def test_explain_lex_posterior(engine):
    """Test explanation of lex posterior principle"""
    explanation = engine.explain_principle_application('lex_posterior')

    assert 'Lex posterior derogat legi priori' in explanation
    assert 'posterior' in explanation


def test_explain_lex_specialis(engine):
    """Test explanation of lex specialis principle"""
    explanation = engine.explain_principle_application('lex_specialis')

    assert 'Lex specialis derogat legi generali' in explanation
    assert 'especial' in explanation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
