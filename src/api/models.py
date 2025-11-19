"""
Pydantic models for API requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal
from datetime import date


class QueryRequest(BaseModel):
    """Legal query request"""
    question: str = Field(..., description="Pregunta legal en español", min_length=10)
    area: Optional[Literal["contratacion", "administrativo", "defensa"]] = Field(
        None,
        description="Área legal específica (opcional)"
    )
    mode: Literal["naive", "local", "global", "hybrid"] = Field(
        default="hybrid",
        description="Modo de búsqueda RAG"
    )
    include_citations: bool = Field(
        default=True,
        description="Incluir extracción y validación de citas legales"
    )
    include_reasoning: bool = Field(
        default=True,
        description="Aplicar razonamiento jurídico"
    )
    reference_date: Optional[date] = Field(
        None,
        description="Fecha de referencia para validez temporal"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "question": "¿Qué plazo tengo para recurrir una adjudicación?",
                "area": "contratacion",
                "mode": "hybrid",
                "include_citations": True,
                "include_reasoning": True
            }
        }


class CitationInfo(BaseModel):
    """Information about a legal citation"""
    text: str = Field(..., description="Texto de la cita")
    type: str = Field(..., description="Tipo de cita")
    validated: bool = Field(..., description="Si la cita fue validada")
    law: Optional[str] = Field(None, description="Ley completa referenciada")


class CitationsSummary(BaseModel):
    """Summary of citations in response"""
    total: int = Field(..., description="Total de citas encontradas")
    validated: int = Field(..., description="Citas validadas")
    validation_rate: float = Field(..., description="Tasa de validación")


class LegalReasoningInfo(BaseModel):
    """Legal reasoning analysis"""
    conflict_detected: bool
    conflict_type: str
    applicable_principle: str
    reasoning: str
    applicable_norm: str
    explanation: str


class QueryResponse(BaseModel):
    """Legal query response"""
    question: str
    answer: str
    area: str
    mode: str
    timestamp: str
    cache_hit: bool
    citations: Optional[List[CitationInfo]] = None
    citations_summary: Optional[CitationsSummary] = None
    legal_reasoning: Optional[LegalReasoningInfo] = None
    temporal_validity: Optional[Dict] = None


class IndexRequest(BaseModel):
    """Document indexing request"""
    document_text: str = Field(..., description="Texto del documento", min_length=100)
    area: Literal["contratacion", "administrativo", "defensa", "general"] = Field(
        ...,
        description="Área legal del documento"
    )
    metadata: Optional[Dict] = Field(
        None,
        description="Metadatos del documento (law_id, boe, fecha_publicacion, etc.)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "document_text": "Artículo 99. Procedimiento abierto...",
                "area": "contratacion",
                "metadata": {
                    "law_id": "ley-9-2017",
                    "boe": "BOE-A-2017-12902",
                    "article": "99"
                }
            }
        }


class IndexResponse(BaseModel):
    """Document indexing response"""
    status: str
    area: str
    document_length: int
    metadata: Optional[Dict] = None


class BOEFetchRequest(BaseModel):
    """BOE document fetch request"""
    boe_id: str = Field(..., description="Identificador BOE (ej: BOE-A-2017-12902)")
    chunk_by: Literal["article", "paragraph", "full"] = Field(
        default="article",
        description="Estrategia de fragmentación"
    )
    auto_index: bool = Field(
        default=True,
        description="Indexar automáticamente tras descarga"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "boe_id": "BOE-A-2017-12902",
                "chunk_by": "article",
                "auto_index": True
            }
        }


class BOEFetchResponse(BaseModel):
    """BOE document fetch response"""
    boe_id: str
    title: str
    publication_date: str
    chunks_created: int
    indexed: bool
    url: str


class CitationExtractRequest(BaseModel):
    """Citation extraction request"""
    text: str = Field(..., description="Texto a analizar", min_length=10)
    validate: bool = Field(default=True, description="Validar citas extraídas")
    include_context: bool = Field(
        default=False,
        description="Incluir contexto alrededor de las citas"
    )


class CitationExtractResponse(BaseModel):
    """Citation extraction response"""
    text: str
    citations: List[CitationInfo]
    total_citations: int
    validated_citations: int
    validation_rate: float


class ConflictResolveRequest(BaseModel):
    """Normative conflict resolution request"""
    law_ids: List[str] = Field(..., description="IDs de leyes en conflicto", min_items=2)
    scenario: Optional[str] = Field(
        None,
        description="Descripción del escenario de conflicto"
    )


class ConflictResolveResponse(BaseModel):
    """Normative conflict resolution response"""
    conflict_type: str
    applicable_principle: str
    reasoning: str
    applicable_norm: str
    explanation: str
    laws_analyzed: List[Dict]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    rag_instances: int
    features: Dict


class StatsResponse(BaseModel):
    """System statistics response"""
    rag_instances: int
    areas: List[str]
    cache_size: int
    total_laws: int
    features: Dict
