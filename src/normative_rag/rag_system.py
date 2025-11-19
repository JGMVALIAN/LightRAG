"""
Spanish Legal RAG System
Integrates LightRAG with Spanish legal reasoning capabilities
"""
import os
from typing import List, Dict, Optional, Literal
from datetime import date
import asyncio
import hashlib
import json

# Note: lightrag-hku should be installed via pip
# from lightrag import LightRAG, QueryParam
# from lightrag.llm import gpt_4o_mini_complete, gpt_4o_complete
# from lightrag.utils import EmbeddingFunc

from .legal_corpus import LegalArea, get_laws_by_area, get_all_laws
from .citation_resolver import SpanishCitationResolver
from .legal_reasoning import SpanishLegalReasoningEngine, ConflictType

# For now, we'll define placeholder imports since lightrag might not be installed yet
try:
    from lightrag import LightRAG, QueryParam
    LIGHTRAG_AVAILABLE = True
except ImportError:
    LIGHTRAG_AVAILABLE = False
    print("Warning: LightRAG not available. Install with: pip install lightrag-hku")


class SpanishLegalRAGSystem:
    """
    Legal RAG System specialized for Spanish legislation

    Features:
    - Multi-instance RAG (procurement, administrative, defense, general)
    - Citation extraction and validation
    - Legal reasoning and conflict resolution
    - Temporal validity checking
    - Jurisprudential integration
    """

    def __init__(
        self,
        working_dir: str = "./data/lightrag",
        enable_reasoning: bool = True,
        enable_citation_validation: bool = True,
        enable_cache: bool = True
    ):
        """
        Initialize Spanish Legal RAG System

        Args:
            working_dir: Directory for RAG data storage
            enable_reasoning: Enable legal reasoning engine
            enable_citation_validation: Enable citation validation
            enable_cache: Enable query caching
        """
        self.working_dir = working_dir
        self.enable_reasoning = enable_reasoning
        self.enable_citation_validation = enable_citation_validation
        self.enable_cache = enable_cache

        # Create working directory
        os.makedirs(working_dir, exist_ok=True)

        # Initialize legal components
        self.citation_resolver = SpanishCitationResolver()
        self.reasoning_engine = SpanishLegalReasoningEngine()

        # RAG instances by legal area
        self.rag_instances: Dict[str, Optional[object]] = {}

        # Query cache
        self.query_cache: Dict[str, Dict] = {}

        # Initialize specialized RAG instances
        if LIGHTRAG_AVAILABLE:
            self._initialize_rag_instances()
        else:
            print("LightRAG not available - running in mock mode")

    def _initialize_rag_instances(self):
        """Initialize separate RAG instances for each legal area"""

        # Spanish legal prompts for each area
        prompts = {
            LegalArea.CONTRATACION: {
                "entity_extraction": """
                -Objetivo-
                Dado un texto jurídico sobre contratación pública española, extraer entidades relevantes.
                Enfócate en: procedimientos de contratación, órganos de contratación, criterios de adjudicación,
                garantías, plazos, recursos administrativos.

                -Pasos-
                1. Identifica todas las entidades jurídicas mencionadas
                2. Para cada entidad, extrae: tipo, descripción, artículos relacionados
                3. Identifica relaciones entre entidades (regula, deroga, complementa)

                -Resultado-
                {{
                    "entidades": [lista de entidades],
                    "relaciones": [lista de relaciones],
                    "articulos": [lista de artículos relevantes]
                }}
                """,
                "keywords": [
                    "procedimiento abierto", "procedimiento negociado", "diálogo competitivo",
                    "criterios de adjudicación", "garantía provisional", "garantía definitiva",
                    "recurso especial", "TACRC", "LCSP", "pliegos"
                ]
            },
            LegalArea.ADMINISTRATIVO: {
                "entity_extraction": """
                -Objetivo-
                Dado un texto jurídico administrativo español, extraer entidades relevantes.
                Enfócate en: procedimientos administrativos, actos administrativos, recursos,
                plazos, notificaciones, silencio administrativo.

                -Pasos-
                1. Identifica procedimientos y actos administrativos
                2. Extrae plazos legales y su cómputo
                3. Identifica recursos disponibles y sus requisitos

                -Resultado-
                {{
                    "procedimientos": [lista],
                    "plazos": [lista con días/meses],
                    "recursos": [lista de recursos disponibles]
                }}
                """,
                "keywords": [
                    "procedimiento administrativo", "acto administrativo", "recurso de alzada",
                    "recurso potestativo de reposición", "silencio administrativo",
                    "notificación", "plazo", "LPAC", "contencioso-administrativo"
                ]
            },
            LegalArea.DEFENSA: {
                "entity_extraction": """
                -Objetivo-
                Dado un texto jurídico sobre defensa y seguridad española, extraer entidades relevantes.
                Enfócate en: material de defensa, contratos clasificados, exportaciones,
                infraestructuras críticas, seguridad nacional.

                -Pasos-
                1. Identifica material de defensa y categorías
                2. Extrae requisitos de seguridad y clasificación
                3. Identifica procedimientos específicos del ámbito defensa

                -Resultado-
                {{
                    "material_defensa": [lista],
                    "clasificacion_seguridad": [nivel],
                    "procedimientos_especiales": [lista]
                }}
                """,
                "keywords": [
                    "material de defensa", "seguridad nacional", "información clasificada",
                    "infraestructuras críticas", "Fuerzas Armadas", "CNI",
                    "exportación armamento", "LODN"
                ]
            }
        }

        # Create RAG instance for each area
        for area in [LegalArea.CONTRATACION, LegalArea.ADMINISTRATIVO, LegalArea.DEFENSA]:
            instance_dir = os.path.join(self.working_dir, area.value)
            os.makedirs(instance_dir, exist_ok=True)

            # Note: This is a simplified initialization
            # Full implementation would use actual LightRAG configuration
            self.rag_instances[area.value] = {
                'dir': instance_dir,
                'prompts': prompts.get(area, {}),
                'laws': get_laws_by_area(area),
                'initialized': True
            }

        # General instance for cross-area queries
        self.rag_instances['general'] = {
            'dir': os.path.join(self.working_dir, 'general'),
            'prompts': {},
            'laws': get_all_laws(),
            'initialized': True
        }

    async def query(
        self,
        question: str,
        area: Optional[LegalArea] = None,
        mode: Literal["naive", "local", "global", "hybrid"] = "hybrid",
        include_citations: bool = True,
        include_reasoning: bool = True,
        reference_date: Optional[date] = None
    ) -> Dict:
        """
        Query the Spanish Legal RAG system

        Args:
            question: Legal question in Spanish
            area: Legal area (contratacion, administrativo, defensa) or None for general
            mode: RAG query mode (naive, local, global, hybrid)
            include_citations: Extract and validate citations in response
            include_reasoning: Apply legal reasoning to results
            reference_date: Reference date for temporal validity (default: today)

        Returns:
            Dictionary with answer, citations, reasoning, and metadata
        """
        # Check cache
        if self.enable_cache:
            cache_key = self._get_cache_key(question, area, mode)
            if cache_key in self.query_cache:
                cached = self.query_cache[cache_key]
                cached['cache_hit'] = True
                return cached

        # Select appropriate RAG instance
        instance_key = area.value if area else 'general'
        rag_instance = self.rag_instances.get(instance_key)

        if not rag_instance:
            return {
                'error': f'RAG instance not found for area: {instance_key}',
                'question': question
            }

        # Perform RAG query
        # Note: This is a mock implementation
        # Real implementation would call LightRAG
        answer = await self._perform_rag_query(question, rag_instance, mode)

        # Build response
        response = {
            'question': question,
            'answer': answer,
            'area': instance_key,
            'mode': mode,
            'timestamp': date.today().isoformat(),
            'cache_hit': False
        }

        # Extract and validate citations
        if include_citations and self.enable_citation_validation:
            citations = self.citation_resolver.extract_citations(answer)
            validated_count, total_count = self.citation_resolver.validate_all_citations(citations)

            response['citations'] = [
                {
                    'text': cit.raw_text,
                    'type': cit.citation_type,
                    'validated': cit.validated,
                    'law': cit.law_metadata.get('title') if cit.law_metadata else None
                }
                for cit in citations
            ]
            response['citations_summary'] = {
                'total': total_count,
                'validated': validated_count,
                'validation_rate': validated_count / total_count if total_count > 0 else 0
            }

        # Apply legal reasoning if multiple norms detected
        if include_reasoning and self.enable_reasoning:
            reasoning_analysis = await self._apply_legal_reasoning(answer, rag_instance)
            if reasoning_analysis:
                response['legal_reasoning'] = reasoning_analysis

        # Check temporal validity
        if reference_date:
            response['temporal_validity'] = self._check_temporal_validity(
                response.get('citations', []),
                reference_date
            )

        # Cache result
        if self.enable_cache:
            self.query_cache[cache_key] = response

        return response

    async def _perform_rag_query(self, question: str, rag_instance: Dict, mode: str) -> str:
        """
        Perform RAG query (mock implementation)

        In production, this would call:
        result = await rag_instance.aquery(question, param=QueryParam(mode=mode))
        """
        # Mock response for demonstration
        return f"""
        Según la normativa española aplicable, en respuesta a su consulta sobre {question}:

        La Ley 9/2017 (LCSP) establece en su artículo 99 que el procedimiento abierto
        es aquel en el que cualquier empresario interesado podrá presentar una proposición.

        En cuanto a los plazos, la Ley 39/2015 (LPAC) regula en su artículo 21 que
        los plazos se computarán desde el día siguiente a aquel en que tenga lugar
        la notificación.

        Es importante considerar que, en el ámbito de la defensa, la Ley 24/2011
        establece especialidades aplicables a los contratos en este sector.
        """

    async def _apply_legal_reasoning(self, answer: str, rag_instance: Dict) -> Optional[Dict]:
        """Apply legal reasoning to detect and resolve conflicts"""

        # Extract citations from answer
        citations = self.citation_resolver.extract_citations(answer)
        self.citation_resolver.validate_all_citations(citations)

        # Get unique laws mentioned
        laws = []
        for cit in citations:
            if cit.law_metadata and cit.law_metadata not in laws:
                laws.append(cit.law_metadata)

        # Check for conflicts if multiple laws
        if len(laws) > 1:
            conflict = self.reasoning_engine.resolve_conflict(laws)

            return {
                'conflict_detected': conflict.conflict_type != ConflictType.NO_CONFLICT,
                'conflict_type': conflict.conflict_type.value,
                'applicable_principle': conflict.applicable_principle,
                'reasoning': conflict.reasoning,
                'applicable_norm': conflict.resolution.get('title'),
                'explanation': self.reasoning_engine.explain_principle_application(
                    conflict.applicable_principle.replace(' ', '_').lower()
                )
            }

        return None

    def _check_temporal_validity(self, citations: List[Dict], reference_date: date) -> Dict:
        """Check temporal validity of cited norms"""
        valid_citations = []
        invalid_citations = []

        for cit in citations:
            if cit.get('law'):
                law_id = cit.get('law')
                # This would check against database
                # For now, assume all are valid
                valid_citations.append(cit)

        return {
            'reference_date': reference_date.isoformat(),
            'valid_citations': len(valid_citations),
            'invalid_citations': len(invalid_citations),
            'all_valid': len(invalid_citations) == 0
        }

    def _get_cache_key(self, question: str, area: Optional[LegalArea], mode: str) -> str:
        """Generate cache key for query"""
        key_parts = [
            question.lower().strip(),
            area.value if area else 'general',
            mode
        ]
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()

    async def index_document(self, document: str, area: LegalArea, metadata: Optional[Dict] = None):
        """
        Index a legal document into the RAG system

        Args:
            document: Document text
            area: Legal area
            metadata: Document metadata (law_id, boe, publication_date, etc.)
        """
        instance_key = area.value
        rag_instance = self.rag_instances.get(instance_key)

        if not rag_instance:
            raise ValueError(f"RAG instance not found: {instance_key}")

        # In production, this would call:
        # await rag_instance.ainsert(document)

        print(f"Indexed document in {instance_key}: {len(document)} chars")
        if metadata:
            print(f"  Metadata: {metadata.get('law_id', 'N/A')}")

        return {'status': 'indexed', 'area': instance_key, 'document_length': len(document)}

    def get_statistics(self) -> Dict:
        """Get system statistics"""
        return {
            'rag_instances': len(self.rag_instances),
            'areas': list(self.rag_instances.keys()),
            'cache_size': len(self.query_cache),
            'total_laws': len(get_all_laws()),
            'features': {
                'reasoning_enabled': self.enable_reasoning,
                'citation_validation_enabled': self.enable_citation_validation,
                'cache_enabled': self.enable_cache
            }
        }


# Example usage
async def main():
    """Example usage of Spanish Legal RAG System"""
    rag = SpanishLegalRAGSystem(
        working_dir="./data/legal_rag",
        enable_reasoning=True,
        enable_citation_validation=True
    )

    # Example query
    result = await rag.query(
        question="¿Qué plazo tengo para recurrir una adjudicación de contrato público?",
        area=LegalArea.CONTRATACION,
        mode="hybrid",
        include_citations=True,
        include_reasoning=True
    )

    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

    # Print statistics
    stats = rag.get_statistics()
    print("\n" + "="*60)
    print("SYSTEM STATISTICS")
    print("="*60)
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
