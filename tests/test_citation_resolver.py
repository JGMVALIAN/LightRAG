"""
Tests for Spanish Citation Resolver
"""
import pytest
from src.normative_rag import SpanishCitationResolver, Citation


@pytest.fixture
def resolver():
    """Fixture for citation resolver"""
    return SpanishCitationResolver()


def test_extract_ley_ordinaria(resolver):
    """Test extraction of ordinary law citations"""
    text = "La Ley 9/2017 establece el marco de la contratación pública."
    citations = resolver.extract_citations(text)

    assert len(citations) == 1
    assert citations[0].citation_type == 'ley_ordinaria'
    assert citations[0].identifier == '9/2017'


def test_extract_ley_organica(resolver):
    """Test extraction of organic law citations"""
    text = "Según la Ley Orgánica 5/2005 de Defensa Nacional..."
    citations = resolver.extract_citations(text)

    assert len(citations) == 1
    assert citations[0].citation_type == 'ley_organica'
    assert citations[0].identifier == '5/2005'


def test_extract_article(resolver):
    """Test extraction of article references"""
    text = "El artículo 99 de la LCSP regula el procedimiento abierto."
    citations = resolver.extract_citations(text)

    assert len(citations) >= 1
    article_citations = [c for c in citations if c.citation_type == 'articulo']
    assert len(article_citations) >= 1
    assert article_citations[0].article == '99'


def test_validate_known_law(resolver):
    """Test validation of known law"""
    text = "La Ley 9/2017 (LCSP)"
    citations = resolver.extract_citations(text)

    assert len(citations) == 1
    validated = resolver.validate_citation(citations[0])

    assert validated is True
    assert citations[0].law_metadata is not None
    assert 'LCSP' in citations[0].law_metadata['title']


def test_validate_unknown_law(resolver):
    """Test validation of unknown law"""
    text = "La Ley 999/2099 no existe"
    citations = resolver.extract_citations(text)

    assert len(citations) == 1
    validated = resolver.validate_citation(citations[0])

    assert validated is False
    assert citations[0].law_metadata is None


def test_resolve_abbreviation(resolver):
    """Test abbreviation resolution"""
    law = resolver.resolve_abbreviation("LCSP")

    assert law is not None
    assert law['id'] == 'ley-9-2017'
    assert 'Contratos del Sector Público' in law['title']


def test_multiple_citations(resolver):
    """Test extraction of multiple citations"""
    text = """
    La Ley 9/2017 (LCSP) y la Ley 39/2015 (LPAC) regulan
    el procedimiento. Ver artículo 99 y artículo 121.
    """
    citations = resolver.extract_citations(text)

    assert len(citations) >= 3  # At least 2 laws + 1 article


def test_format_citation_full(resolver):
    """Test full citation formatting"""
    text = "Ley 9/2017"
    citations = resolver.extract_citations(text)
    resolver.validate_citation(citations[0])

    formatted = resolver.format_citation(citations[0], style='full')

    assert 'Ley 9/2017' in formatted or 'Contratos del Sector Público' in formatted


def test_format_citation_short(resolver):
    """Test short citation formatting"""
    text = "Ley 9/2017"
    citations = resolver.extract_citations(text)
    resolver.validate_citation(citations[0])

    formatted = resolver.format_citation(citations[0], style='short')

    assert 'LCSP' in formatted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
