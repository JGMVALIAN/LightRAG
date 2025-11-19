"""
Spanish Legal RAG System - FastAPI Application
API REST para consultas legales sobre normativa española
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import logging
from typing import Dict

from .config import settings
from .api.models import (
    QueryRequest, QueryResponse,
    IndexRequest, IndexResponse,
    BOEFetchRequest, BOEFetchResponse,
    CitationExtractRequest, CitationExtractResponse,
    ConflictResolveRequest, ConflictResolveResponse,
    HealthResponse, StatsResponse
)
from .normative_rag import (
    SpanishLegalRAGSystem,
    LegalArea,
    SpanishCitationResolver,
    SpanishLegalReasoningEngine,
    get_law_by_id
)
from .preprocessing import BOEProcessor

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'legal_rag_requests_total',
    'Total de solicitudes al Legal RAG',
    ['endpoint', 'method', 'status']
)

QUERY_DURATION = Histogram(
    'legal_rag_query_duration_seconds',
    'Duración de consultas legales',
    ['area', 'mode']
)

CITATION_VALIDATION_RATE = Histogram(
    'legal_rag_citation_validation_rate',
    'Tasa de validación de citas legales'
)

# Global instances
rag_system: SpanishLegalRAGSystem = None
citation_resolver: SpanishCitationResolver = None
reasoning_engine: SpanishLegalReasoningEngine = None
boe_processor: BOEProcessor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for FastAPI app"""
    global rag_system, citation_resolver, reasoning_engine, boe_processor

    # Startup
    logger.info("Initializing Spanish Legal RAG System...")

    rag_system = SpanishLegalRAGSystem(
        working_dir=settings.lightrag_working_dir,
        enable_reasoning=settings.enable_legal_reasoning,
        enable_citation_validation=settings.enable_citation_validation,
        enable_cache=settings.enable_cache
    )

    citation_resolver = SpanishCitationResolver()
    reasoning_engine = SpanishLegalReasoningEngine()
    boe_processor = BOEProcessor()

    logger.info("System initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down...")
    if boe_processor:
        await boe_processor.close()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Spanish Legal RAG API",
    description="Sistema RAG para consultas legales sobre normativa española (Contratación, Administrativo, Defensa)",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get RAG system
def get_rag_system() -> SpanishLegalRAGSystem:
    """Dependency injection for RAG system"""
    if rag_system is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG system not initialized"
        )
    return rag_system


def get_citation_resolver() -> SpanishCitationResolver:
    """Dependency injection for citation resolver"""
    if citation_resolver is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Citation resolver not initialized"
        )
    return citation_resolver


def get_reasoning_engine() -> SpanishLegalReasoningEngine:
    """Dependency injection for reasoning engine"""
    if reasoning_engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reasoning engine not initialized"
        )
    return reasoning_engine


def get_boe_processor() -> BOEProcessor:
    """Dependency injection for BOE processor"""
    if boe_processor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="BOE processor not initialized"
        )
    return boe_processor


# Routes
@app.get("/", tags=["General"])
async def root():
    """Root endpoint"""
    return {
        "service": "Spanish Legal RAG API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check(rag: SpanishLegalRAGSystem = Depends(get_rag_system)):
    """Health check endpoint"""
    stats = rag.get_statistics()

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        rag_instances=stats['rag_instances'],
        features=stats['features']
    )


@app.get("/stats", response_model=StatsResponse, tags=["General"])
async def get_statistics(rag: SpanishLegalRAGSystem = Depends(get_rag_system)):
    """Get system statistics"""
    stats = rag.get_statistics()
    return StatsResponse(**stats)


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/query", response_model=QueryResponse, tags=["Legal Queries"])
async def query_legal(
    request: QueryRequest,
    rag: SpanishLegalRAGSystem = Depends(get_rag_system)
):
    """
    Realizar consulta legal sobre normativa española

    Áreas disponibles:
    - **contratacion**: Ley 9/2017 LCSP y normativa de contratación pública
    - **administrativo**: Ley 39/2015 LPAC, Ley 40/2015 LRJSP
    - **defensa**: LO 5/2005 LODN, Ley 24/2011 Contratos Defensa

    Modos de búsqueda:
    - **naive**: Búsqueda simple
    - **local**: Búsqueda local en grafos
    - **global**: Búsqueda global en grafos
    - **hybrid**: Combinación de local y global (recomendado)
    """
    try:
        # Convert area string to LegalArea enum
        area_enum = None
        if request.area:
            area_enum = LegalArea(request.area)

        # Perform query with timing
        with QUERY_DURATION.labels(
            area=request.area or 'general',
            mode=request.mode
        ).time():
            result = await rag.query(
                question=request.question,
                area=area_enum,
                mode=request.mode,
                include_citations=request.include_citations,
                include_reasoning=request.include_reasoning,
                reference_date=request.reference_date
            )

        # Record metrics
        REQUEST_COUNT.labels(
            endpoint='/query',
            method='POST',
            status='success'
        ).inc()

        if result.get('citations_summary'):
            CITATION_VALIDATION_RATE.observe(
                result['citations_summary']['validation_rate']
            )

        return QueryResponse(**result)

    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        REQUEST_COUNT.labels(
            endpoint='/query',
            method='POST',
            status='error'
        ).inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando consulta: {str(e)}"
        )


@app.post("/index", response_model=IndexResponse, tags=["Document Management"])
async def index_document(
    request: IndexRequest,
    rag: SpanishLegalRAGSystem = Depends(get_rag_system)
):
    """
    Indexar un documento legal en el sistema RAG

    El documento será indexado en el área específica para mejorar las consultas futuras.
    """
    try:
        area_enum = LegalArea(request.area)

        result = await rag.index_document(
            document=request.document_text,
            area=area_enum,
            metadata=request.metadata
        )

        REQUEST_COUNT.labels(
            endpoint='/index',
            method='POST',
            status='success'
        ).inc()

        return IndexResponse(**result)

    except Exception as e:
        logger.error(f"Error indexing document: {e}", exc_info=True)
        REQUEST_COUNT.labels(
            endpoint='/index',
            method='POST',
            status='error'
        ).inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error indexando documento: {str(e)}"
        )


@app.post("/boe/fetch", response_model=BOEFetchResponse, tags=["BOE Integration"])
async def fetch_boe_document(
    request: BOEFetchRequest,
    processor: BOEProcessor = Depends(get_boe_processor),
    rag: SpanishLegalRAGSystem = Depends(get_rag_system)
):
    """
    Descargar y procesar documento del BOE

    Ejemplos de BOE IDs:
    - BOE-A-2017-12902 (Ley 9/2017 LCSP)
    - BOE-A-2015-10565 (Ley 39/2015 LPAC)
    - BOE-A-2005-18933 (LO 5/2005 LODN)
    """
    try:
        chunks = await processor.fetch_and_index_law(
            boe_id=request.boe_id,
            chunk_by=request.chunk_by
        )

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documento BOE no encontrado: {request.boe_id}"
            )

        # Auto-index if requested
        indexed = False
        if request.auto_index and chunks:
            # Determine area from metadata (simplified)
            area = LegalArea.GENERAL
            for chunk in chunks:
                await rag.index_document(
                    document=chunk['text'],
                    area=area,
                    metadata=chunk['metadata']
                )
            indexed = True

        REQUEST_COUNT.labels(
            endpoint='/boe/fetch',
            method='POST',
            status='success'
        ).inc()

        # Get document metadata from first chunk
        first_meta = chunks[0]['metadata'] if chunks else {}

        return BOEFetchResponse(
            boe_id=request.boe_id,
            title=first_meta.get('title', 'N/A'),
            publication_date=first_meta.get('publication_date', ''),
            chunks_created=len(chunks),
            indexed=indexed,
            url=first_meta.get('url', '')
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching BOE document: {e}", exc_info=True)
        REQUEST_COUNT.labels(
            endpoint='/boe/fetch',
            method='POST',
            status='error'
        ).inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error descargando documento BOE: {str(e)}"
        )


@app.post("/citations/extract", response_model=CitationExtractResponse, tags=["Legal Analysis"])
async def extract_citations(
    request: CitationExtractRequest,
    resolver: SpanishCitationResolver = Depends(get_citation_resolver)
):
    """
    Extraer y validar citas legales de un texto

    Formatos soportados:
    - Ley 9/2017 (LCSP)
    - Ley Orgánica 5/2005
    - Real Decreto 1098/2001
    - Artículo 99 LCSP
    - Directiva 2014/24/UE
    """
    try:
        citations = resolver.extract_citations(request.text)

        if request.validate:
            validated, total = resolver.validate_all_citations(citations)
        else:
            validated, total = 0, len(citations)

        citation_infos = [
            {
                'text': cit.raw_text,
                'type': cit.citation_type,
                'validated': cit.validated,
                'law': cit.law_metadata.get('title') if cit.law_metadata else None
            }
            for cit in citations
        ]

        REQUEST_COUNT.labels(
            endpoint='/citations/extract',
            method='POST',
            status='success'
        ).inc()

        return CitationExtractResponse(
            text=request.text,
            citations=citation_infos,
            total_citations=total,
            validated_citations=validated,
            validation_rate=validated / total if total > 0 else 0.0
        )

    except Exception as e:
        logger.error(f"Error extracting citations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extrayendo citas: {str(e)}"
        )


@app.post("/conflicts/resolve", response_model=ConflictResolveResponse, tags=["Legal Analysis"])
async def resolve_conflict(
    request: ConflictResolveRequest,
    engine: SpanishLegalReasoningEngine = Depends(get_reasoning_engine)
):
    """
    Resolver conflictos normativos aplicando principios jurídicos españoles

    Principios aplicados:
    - **Lex superior**: La norma superior prevalece sobre la inferior
    - **Lex posterior**: La norma posterior prevalece sobre la anterior
    - **Lex specialis**: La norma especial prevalece sobre la general

    Ejemplo: Conflicto entre LCSP y Ley 24/2011 (contratos defensa)
    """
    try:
        # Retrieve laws by ID
        laws = []
        for law_id in request.law_ids:
            law = get_law_by_id(law_id)
            if not law:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Ley no encontrada: {law_id}"
                )
            laws.append(law)

        # Resolve conflict
        conflict = engine.resolve_conflict(laws)

        REQUEST_COUNT.labels(
            endpoint='/conflicts/resolve',
            method='POST',
            status='success'
        ).inc()

        return ConflictResolveResponse(
            conflict_type=conflict.conflict_type.value,
            applicable_principle=conflict.applicable_principle,
            reasoning=conflict.reasoning,
            applicable_norm=conflict.resolution.get('title', 'N/A'),
            explanation=engine.explain_principle_application(
                conflict.applicable_principle.replace(' ', '_').lower()
            ),
            laws_analyzed=[
                {
                    'id': law.get('id'),
                    'title': law.get('title'),
                    'hierarchy': law.get('hierarchy').name if law.get('hierarchy') else 'N/A'
                }
                for law in laws
            ]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving conflict: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resolviendo conflicto: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        log_level=settings.log_level.lower()
    )
