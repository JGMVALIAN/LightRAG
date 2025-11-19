"""
Spanish Legal Citation Resolver
Extracts and validates Spanish legal citations from text
"""
import re
from typing import List, Dict, Optional, Tuple
from datetime import date
from dataclasses import dataclass

from .legal_corpus import get_law_by_id, get_all_laws


@dataclass
class Citation:
    """Represents a legal citation"""
    citation_type: str  # 'ley', 'real_decreto', 'lo', 'articulo', 'directiva_ue'
    identifier: str  # e.g., "9/2017", "39/2015"
    article: Optional[str] = None  # e.g., "99", "121.3"
    section: Optional[str] = None  # e.g., "a)", "2.b"
    raw_text: str = ""  # Original citation text
    start_pos: int = 0  # Position in source text
    end_pos: int = 0
    validated: bool = False
    law_metadata: Optional[Dict] = None


class SpanishCitationResolver:
    """
    Resolver for Spanish legal citations.
    Supports formats like:
    - Ley 9/2017 (LCSP)
    - Ley 39/2015 (LPAC)
    - Real Decreto 1098/2001
    - Ley Orgánica 5/2005
    - Artículo 99 LCSP
    - Art. 121.3 LPAC
    - Directiva 2014/24/UE
    """

    # Citation patterns for Spanish legal formats
    CITATION_PATTERNS = {
        'ley_ordinaria': re.compile(
            r'Ley\s+(?:N[°º]?\s*)?(\d+/\d{4})',
            re.IGNORECASE
        ),
        'ley_organica': re.compile(
            r'(?:L\.?O\.?|Ley\s+Orgánica)\s+(?:N[°º]?\s*)?(\d+/\d{4})',
            re.IGNORECASE
        ),
        'real_decreto': re.compile(
            r'Real\s+Decreto(?:\s+Legislativo)?\s+(?:N[°º]?\s*)?(\d+/\d{4})',
            re.IGNORECASE
        ),
        'real_decreto_ley': re.compile(
            r'Real\s+Decreto[‐-]Ley\s+(?:N[°º]?\s*)?(\d+/\d{4})',
            re.IGNORECASE
        ),
        'orden_ministerial': re.compile(
            r'Orden\s+(?:Ministerial\s+)?(?:N[°º]?\s*)?([A-Z]{3}/\d+/\d{4})',
            re.IGNORECASE
        ),
        'directiva_ue': re.compile(
            r'Directiva\s+(\d{4}/\d+/UE)',
            re.IGNORECASE
        ),
        'articulo': re.compile(
            r'Art(?:ículo|[.\s])\s*(\d+)(?:\.(\d+))?(?:\s+([a-z])\))?',
            re.IGNORECASE
        ),
        'boe': re.compile(
            r'BOE[‐-]A[‐-](\d{4}[‐-]\d+)',
            re.IGNORECASE
        ),
    }

    # Common abbreviations
    ABBREVIATIONS = {
        'LCSP': 'ley-9-2017',
        'LPAC': 'ley-39-2015',
        'LRJSP': 'ley-40-2015',
        'LJCA': 'ley-29-1998',
        'LODN': 'lo-5-2005',
        'LSN': 'lo-14-2015',
    }

    def __init__(self):
        """Initialize the citation resolver"""
        self.laws_db = get_all_laws()

    def extract_citations(self, text: str) -> List[Citation]:
        """
        Extract all legal citations from text

        Args:
            text: Input text to analyze

        Returns:
            List of Citation objects found in text
        """
        citations = []

        # Extract each type of citation
        for citation_type, pattern in self.CITATION_PATTERNS.items():
            for match in pattern.finditer(text):
                citation = Citation(
                    citation_type=citation_type,
                    identifier=match.group(1),
                    raw_text=match.group(0),
                    start_pos=match.start(),
                    end_pos=match.end()
                )

                # Extract article number if present
                if citation_type == 'articulo' and len(match.groups()) > 0:
                    citation.article = match.group(1)
                    if match.group(2):  # Subarticle (e.g., 121.3)
                        citation.article += f".{match.group(2)}"
                    if match.group(3):  # Section (e.g., a)
                        citation.section = match.group(3)

                citations.append(citation)

        # Sort by position in text
        citations.sort(key=lambda c: c.start_pos)

        return citations

    def validate_citation(self, citation: Citation) -> bool:
        """
        Validate if citation corresponds to a known law

        Args:
            citation: Citation object to validate

        Returns:
            True if citation is valid and found in database
        """
        # Try to find law by identifier
        law_id = self._normalize_identifier(citation.identifier, citation.citation_type)
        law = get_law_by_id(law_id)

        if law:
            citation.validated = True
            citation.law_metadata = law
            return True

        # Try BOE identifier
        if citation.citation_type == 'boe':
            boe_id = f"BOE-A-{citation.identifier}"
            law = get_law_by_id(boe_id)
            if law:
                citation.validated = True
                citation.law_metadata = law
                return True

        return False

    def _normalize_identifier(self, identifier: str, citation_type: str) -> str:
        """
        Normalize law identifier for database lookup

        Args:
            identifier: Raw identifier (e.g., "9/2017")
            citation_type: Type of citation

        Returns:
            Normalized identifier (e.g., "ley-9-2017")
        """
        if citation_type == 'ley_ordinaria':
            return f"ley-{identifier.replace('/', '-')}"
        elif citation_type == 'ley_organica':
            return f"lo-{identifier.replace('/', '-')}"
        elif citation_type == 'real_decreto':
            return f"rd-{identifier.replace('/', '-')}"
        elif citation_type == 'real_decreto_ley':
            return f"rdl-{identifier.replace('/', '-')}"
        elif citation_type == 'boe':
            return f"BOE-A-{identifier}"
        else:
            return identifier

    def resolve_abbreviation(self, abbr: str) -> Optional[Dict]:
        """
        Resolve legal abbreviation to full law

        Args:
            abbr: Abbreviation (e.g., "LCSP", "LPAC")

        Returns:
            Law metadata if found, None otherwise
        """
        law_id = self.ABBREVIATIONS.get(abbr.upper())
        if law_id:
            return get_law_by_id(law_id)
        return None

    def extract_article_context(self, text: str, citation: Citation,
                               context_chars: int = 200) -> str:
        """
        Extract context around a citation

        Args:
            text: Source text
            citation: Citation object
            context_chars: Characters to include before/after

        Returns:
            Context string
        """
        start = max(0, citation.start_pos - context_chars)
        end = min(len(text), citation.end_pos + context_chars)

        context = text[start:end]

        # Mark the citation
        citation_start = citation.start_pos - start
        citation_end = citation.end_pos - start

        return (
            context[:citation_start] +
            f"**{context[citation_start:citation_end]}**" +
            context[citation_end:]
        )

    def find_related_citations(self, citation: Citation,
                              all_citations: List[Citation]) -> List[Citation]:
        """
        Find citations related to a given citation
        (same law, nearby articles, etc.)

        Args:
            citation: Reference citation
            all_citations: List of all citations to search

        Returns:
            List of related citations
        """
        related = []

        for other in all_citations:
            if other == citation:
                continue

            # Same law
            if (citation.law_metadata and other.law_metadata and
                citation.law_metadata.get('id') == other.law_metadata.get('id')):
                related.append(other)

            # Adjacent articles (within 5 articles)
            if (citation.article and other.article and
                citation.law_metadata and other.law_metadata and
                citation.law_metadata.get('id') == other.law_metadata.get('id')):
                try:
                    art1 = int(citation.article.split('.')[0])
                    art2 = int(other.article.split('.')[0])
                    if abs(art1 - art2) <= 5:
                        related.append(other)
                except ValueError:
                    pass

        return related

    def format_citation(self, citation: Citation, style: str = 'full') -> str:
        """
        Format citation according to style

        Args:
            citation: Citation to format
            style: 'full', 'short', or 'boe'

        Returns:
            Formatted citation string
        """
        if not citation.law_metadata:
            return citation.raw_text

        law = citation.law_metadata

        if style == 'full':
            result = law.get('title', citation.raw_text)
            if citation.article:
                result += f", artículo {citation.article}"
            return result

        elif style == 'short':
            result = law.get('short_title', citation.raw_text)
            if citation.article:
                result += f" art. {citation.article}"
            return result

        elif style == 'boe':
            return f"{law.get('boe', 'N/A')}"

        return citation.raw_text

    def validate_all_citations(self, citations: List[Citation]) -> Tuple[int, int]:
        """
        Validate all citations in a list

        Args:
            citations: List of citations to validate

        Returns:
            Tuple of (validated_count, total_count)
        """
        validated = 0
        for citation in citations:
            if self.validate_citation(citation):
                validated += 1

        return validated, len(citations)


# Example usage and testing
if __name__ == "__main__":
    resolver = SpanishCitationResolver()

    # Test text with Spanish legal citations
    test_text = """
    Según la Ley 9/2017, de Contratos del Sector Público (LCSP),
    el procedimiento abierto se regula en el artículo 99.
    Por otra parte, la Ley 39/2015 (LPAC) establece en su art. 21
    los plazos del procedimiento administrativo. Ver también
    Real Decreto 1098/2001 y la Directiva 2014/24/UE.
    """

    citations = resolver.extract_citations(test_text)
    print(f"Found {len(citations)} citations:")

    for cit in citations:
        resolver.validate_citation(cit)
        print(f"- {cit.raw_text} ({cit.citation_type})")
        if cit.validated:
            print(f"  ✓ Validated: {cit.law_metadata.get('title')}")
        else:
            print(f"  ✗ Not validated")
