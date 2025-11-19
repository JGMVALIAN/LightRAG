"""
Legal Reasoning Engine for Spanish Law
Implements juridical principles: lex superior, lex posterior, lex specialis
"""
from datetime import date, datetime
from typing import List, Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from .legal_corpus import LegalHierarchy, get_law_by_id


class ConflictType(Enum):
    """Types of normative conflicts"""
    HIERARCHY = "hierarchy"  # Different hierarchy levels
    TEMPORAL = "temporal"  # Same hierarchy, different dates
    SPECIALTY = "specialty"  # General vs specific law
    TERRITORIAL = "territorial"  # Different territorial scope
    NO_CONFLICT = "no_conflict"


@dataclass
class NormativeConflict:
    """Represents a conflict between legal norms"""
    conflict_type: ConflictType
    norms: List[Dict]
    resolution: Dict
    applicable_principle: str
    reasoning: str


class SpanishLegalReasoningEngine:
    """
    Applies Spanish juridical principles to resolve normative conflicts

    Principles applied:
    1. Lex superior derogat legi inferiori (hierarchy)
    2. Lex posterior derogat legi priori (temporal)
    3. Lex specialis derogat legi generali (specialty)
    4. Lex favorabilis (most favorable interpretation)
    """

    def __init__(self):
        """Initialize the legal reasoning engine"""
        self.hierarchy_order = {
            LegalHierarchy.CONSTITUCION: 1,
            LegalHierarchy.LEY_ORGANICA: 2,
            LegalHierarchy.LEY_ORDINARIA: 3,
            LegalHierarchy.REAL_DECRETO_LEGISLATIVO: 4,
            LegalHierarchy.REAL_DECRETO_LEY: 5,
            LegalHierarchy.REAL_DECRETO: 6,
            LegalHierarchy.ORDEN_MINISTERIAL: 7,
            LegalHierarchy.RESOLUCION: 8,
            LegalHierarchy.CIRCULAR: 9,
        }

    def resolve_conflict(self, norms: List[Dict]) -> NormativeConflict:
        """
        Resolve conflict between multiple norms

        Args:
            norms: List of norm dictionaries with metadata
                   Each must contain: id, hierarchy, publication_date

        Returns:
            NormativeConflict with resolution and reasoning
        """
        if len(norms) < 2:
            return NormativeConflict(
                conflict_type=ConflictType.NO_CONFLICT,
                norms=norms,
                resolution=norms[0] if norms else {},
                applicable_principle="N/A",
                reasoning="Solo hay una norma aplicable"
            )

        # Step 1: Apply Lex Superior (hierarchy)
        conflict = self._apply_lex_superior(norms)
        if len(conflict['remaining_norms']) == 1:
            return NormativeConflict(
                conflict_type=ConflictType.HIERARCHY,
                norms=norms,
                resolution=conflict['remaining_norms'][0],
                applicable_principle="Lex superior derogat legi inferiori",
                reasoning=conflict['reasoning']
            )

        # Step 2: Apply Lex Specialis (specialty)
        conflict = self._apply_lex_specialis(conflict['remaining_norms'])
        if len(conflict['remaining_norms']) == 1:
            return NormativeConflict(
                conflict_type=ConflictType.SPECIALTY,
                norms=norms,
                resolution=conflict['remaining_norms'][0],
                applicable_principle="Lex specialis derogat legi generali",
                reasoning=conflict['reasoning']
            )

        # Step 3: Apply Lex Posterior (temporal)
        conflict = self._apply_lex_posterior(conflict['remaining_norms'])
        return NormativeConflict(
            conflict_type=ConflictType.TEMPORAL,
            norms=norms,
            resolution=conflict['remaining_norms'][0],
            applicable_principle="Lex posterior derogat legi priori",
            reasoning=conflict['reasoning']
        )

    def _apply_lex_superior(self, norms: List[Dict]) -> Dict:
        """
        Apply principle of hierarchy (lex superior)

        Returns norms of highest hierarchy level
        """
        # Get hierarchy levels
        hierarchy_levels = []
        for norm in norms:
            hierarchy = norm.get('hierarchy')
            if isinstance(hierarchy, LegalHierarchy):
                level = self.hierarchy_order[hierarchy]
            else:
                level = 999  # Unknown hierarchy
            hierarchy_levels.append(level)

        # Find highest hierarchy (lowest number)
        highest_level = min(hierarchy_levels)

        # Filter norms of highest hierarchy
        superior_norms = [
            norm for norm, level in zip(norms, hierarchy_levels)
            if level == highest_level
        ]

        reasoning = (
            f"Aplicando lex superior: {len(superior_norms)} norma(s) "
            f"de jerarquía superior (nivel {highest_level}) prevalecen sobre "
            f"{len(norms) - len(superior_norms)} de menor jerarquía"
        )

        return {
            'remaining_norms': superior_norms,
            'reasoning': reasoning
        }

    def _apply_lex_specialis(self, norms: List[Dict]) -> Dict:
        """
        Apply principle of specialty (lex specialis)

        Checks for:
        - Specific subject matter vs general
        - Specific territorial scope
        - Specific temporal scope
        """
        # Check if any norm is marked as special law
        special_norms = [
            norm for norm in norms
            if norm.get('is_special_law', False)
        ]

        if special_norms:
            reasoning = (
                f"Aplicando lex specialis: {len(special_norms)} norma(s) "
                f"especial(es) prevalecen sobre {len(norms) - len(special_norms)} "
                f"norma(s) general(es)"
            )
            return {
                'remaining_norms': special_norms,
                'reasoning': reasoning
            }

        # Check for specific sector laws (defensa, seguridad)
        # Ley 24/2011 (defensa) is lex specialis over LCSP for defense contracts
        defense_specific = [
            norm for norm in norms
            if 'defensa' in norm.get('keywords', []) or
               'seguridad' in norm.get('keywords', [])
        ]

        if defense_specific and len(defense_specific) < len(norms):
            reasoning = (
                f"Aplicando lex specialis: Norma(s) específica(s) del sector "
                f"(defensa/seguridad) prevalecen sobre normas generales"
            )
            return {
                'remaining_norms': defense_specific,
                'reasoning': reasoning
            }

        # No specialty found, return all
        return {
            'remaining_norms': norms,
            'reasoning': "No se identifican normas especiales"
        }

    def _apply_lex_posterior(self, norms: List[Dict]) -> Dict:
        """
        Apply principle of temporal precedence (lex posterior)

        Returns most recent norm
        """
        # Sort by publication date (most recent first)
        sorted_norms = sorted(
            norms,
            key=lambda n: n.get('publication_date', date.min),
            reverse=True
        )

        most_recent = sorted_norms[0]
        pub_date = most_recent.get('publication_date')

        reasoning = (
            f"Aplicando lex posterior: La norma más reciente "
            f"({pub_date.strftime('%d/%m/%Y') if pub_date else 'fecha desconocida'}) "
            f"prevalece sobre normas anteriores"
        )

        return {
            'remaining_norms': [most_recent],
            'reasoning': reasoning
        }

    def check_temporal_validity(self, norm: Dict,
                               reference_date: Optional[date] = None) -> bool:
        """
        Check if a norm is valid on a given date

        Args:
            norm: Norm dictionary with publication_date, entry_force_date, repeal_date
            reference_date: Date to check (default: today)

        Returns:
            True if norm is valid on reference_date
        """
        if reference_date is None:
            reference_date = date.today()

        # Check entry into force
        entry_date = norm.get('entry_force_date') or norm.get('publication_date')
        if entry_date and reference_date < entry_date:
            return False

        # Check if repealed
        repeal_date = norm.get('repeal_date')
        if repeal_date and reference_date >= repeal_date:
            return False

        # Check active flag
        if 'active' in norm and not norm['active']:
            return False

        return True

    def find_applicable_article(self, law_id: str, subject: str) -> Optional[Dict]:
        """
        Find the most applicable article for a subject within a law

        Args:
            law_id: Law identifier
            subject: Subject matter (e.g., "procedimiento abierto")

        Returns:
            Article metadata if found
        """
        law = get_law_by_id(law_id)
        if not law:
            return None

        key_articles = law.get('key_articles', {})

        # Simple keyword matching (could be enhanced with embeddings)
        subject_lower = subject.lower()
        best_match = None
        best_score = 0

        for art_id, art_title in key_articles.items():
            art_title_lower = art_title.lower()

            # Count matching words
            subject_words = set(subject_lower.split())
            article_words = set(art_title_lower.split())
            matches = len(subject_words & article_words)

            if matches > best_score:
                best_score = matches
                best_match = {
                    'article_id': art_id,
                    'article_title': art_title,
                    'law_id': law_id,
                    'law_title': law.get('title'),
                    'match_score': matches
                }

        return best_match

    def analyze_jurisprudential_hierarchy(self,
                                         supreme_court: Optional[str] = None,
                                         constitutional_court: Optional[str] = None) -> str:
        """
        Analyze hierarchy between jurisprudence and legislation

        Args:
            supreme_court: Citation to Supreme Court ruling
            constitutional_court: Citation to Constitutional Court ruling

        Returns:
            Analysis text
        """
        analysis = []

        if constitutional_court:
            analysis.append(
                "La jurisprudencia del Tribunal Constitucional tiene carácter vinculante "
                "y puede declarar la inconstitucionalidad de normas con rango de ley."
            )

        if supreme_court:
            analysis.append(
                "La doctrina del Tribunal Supremo complementa el ordenamiento jurídico "
                "y es vinculante para juzgados y tribunales inferiores (art. 1.6 CC)."
            )

        if not analysis:
            analysis.append(
                "La jurisprudencia complementa el ordenamiento jurídico español, "
                "estableciendo interpretación uniforme de normas."
            )

        return " ".join(analysis)

    def explain_principle_application(self, principle: str) -> str:
        """
        Get detailed explanation of a juridical principle

        Args:
            principle: Principle name

        Returns:
            Explanation text
        """
        explanations = {
            "lex_superior": (
                "Lex superior derogat legi inferiori: En caso de conflicto entre normas "
                "de diferente jerarquía, prevalece la de rango superior. "
                "Jerarquía española: Constitución > Ley Orgánica > Ley Ordinaria > "
                "Real Decreto Legislativo > Real Decreto-Ley > Real Decreto > "
                "Orden Ministerial > Resolución."
            ),
            "lex_posterior": (
                "Lex posterior derogat legi priori: Entre normas de igual jerarquía, "
                "la norma posterior deroga a la anterior. La derogación puede ser "
                "expresa (cuando la norma posterior lo indica) o tácita "
                "(por incompatibilidad material)."
            ),
            "lex_specialis": (
                "Lex specialis derogat legi generali: La norma especial prevalece "
                "sobre la general, incluso si esta es posterior. Ejemplo: "
                "Ley 24/2011 (contratos defensa) prevalece sobre LCSP en materia "
                "de contratos de defensa y seguridad."
            ),
            "lex_favorabilis": (
                "Lex favorabilis: En Derecho sancionador, se aplica la norma más "
                "favorable al administrado, incluso si es anterior (retroactividad "
                "de la norma más favorable - art. 128 LPAC)."
            )
        }

        return explanations.get(
            principle.lower().replace(" ", "_"),
            "Principio jurídico no reconocido"
        )


# Example usage
if __name__ == "__main__":
    from .legal_corpus import SPANISH_PROCUREMENT_LAWS, SPANISH_DEFENSE_LAWS

    engine = SpanishLegalReasoningEngine()

    # Simulate conflict: LCSP vs Ley Contratos Defensa
    norms = [
        SPANISH_PROCUREMENT_LAWS['lcsp_2017'],
        SPANISH_DEFENSE_LAWS['ley_concesiones_2003']
    ]

    # Mark defense law as special
    norms[1]['is_special_law'] = True

    conflict = engine.resolve_conflict(norms)

    print("=" * 60)
    print("ANÁLISIS DE CONFLICTO NORMATIVO")
    print("=" * 60)
    print(f"\nTipo de conflicto: {conflict.conflict_type.value}")
    print(f"Principio aplicable: {conflict.applicable_principle}")
    print(f"\nRazonamiento: {conflict.reasoning}")
    print(f"\nNorma aplicable: {conflict.resolution.get('title')}")
    print("\n" + engine.explain_principle_application("lex_specialis"))
