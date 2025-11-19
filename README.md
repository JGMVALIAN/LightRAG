# Spanish Legal RAG System

Sistema RAG (Retrieval-Augmented Generation) especializado en normativa legal española, con enfoque en **Contratación Pública**, **Derecho Administrativo** y **Defensa y Seguridad**.

## 🎯 Características Principales

- **RAG Multi-Instancia**: Instancias especializadas por área legal (Contratación, Administrativo, Defensa)
- **Razonamiento Jurídico**: Motor que aplica principios del derecho español (lex superior, lex posterior, lex specialis)
- **Validación de Citas**: Extracción y validación automática de referencias legales
- **Integración BOE**: Descarga y procesamiento automático de documentos del Boletín Oficial del Estado
- **Análisis Temporal**: Verificación de vigencia normativa por fecha
- **API REST Completa**: Endpoints para consultas, indexación, análisis de conflictos y más
- **Cumplimiento ENS**: Arquitectura diseñada para Esquema Nacional de Seguridad

## 📚 Marco Normativo Soportado

### Contratación Pública
- **Ley 9/2017 (LCSP)** - Ley de Contratos del Sector Público
- **Ley 24/2011** - Contratos en ámbitos de defensa y seguridad
- **Real Decreto 1098/2001 (RGLCAP)** - Reglamento General de Contratos

### Derecho Administrativo
- **Ley 39/2015 (LPAC)** - Procedimiento Administrativo Común
- **Ley 40/2015 (LRJSP)** - Régimen Jurídico del Sector Público
- **Ley 29/1998 (LJCA)** - Jurisdicción Contencioso-Administrativa

### Defensa y Seguridad
- **LO 5/2005 (LODN)** - Defensa Nacional
- **Ley 8/2014** - Control de comercio exterior de material de defensa
- **LO 14/2015 (LSN)** - Sistema de Seguridad Nacional

## 🚀 Quick Start

### Requisitos Previos

- Docker y Docker Compose
- Python 3.11+
- OpenAI API Key

### Instalación

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd LightRAG
```

2. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env y añadir OPENAI_API_KEY
```

3. **Iniciar servicios con Docker Compose**
```bash
docker-compose up -d
```

4. **Esperar a que los servicios estén listos**
```bash
# Verificar estado
docker-compose ps

# Ver logs
docker-compose logs -f legal-rag-api
```

5. **Configurar bases de datos**
```bash
chmod +x scripts/setup_databases.sh
./scripts/setup_databases.sh
```

6. **Indexar corpus legal español** (opcional pero recomendado)
```bash
python scripts/index_spanish_laws.py
```

### Verificar Instalación

```bash
# Health check
curl http://localhost:8000/health

# Estadísticas del sistema
curl http://localhost:8000/stats
```

### Primera Consulta

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué plazo tengo para recurrir una adjudicación de contrato público?",
    "area": "contratacion",
    "mode": "hybrid",
    "include_citations": true,
    "include_reasoning": true
  }'
```

## 📖 Uso de la API

### Endpoints Principales

#### 1. Consulta Legal
```http
POST /query
```

Realizar consulta sobre normativa española.

**Ejemplo:**
```json
{
  "question": "¿Qué garantías debo presentar en un procedimiento abierto?",
  "area": "contratacion",
  "mode": "hybrid",
  "include_citations": true,
  "include_reasoning": true
}
```

#### 2. Extraer Citas Legales
```http
POST /citations/extract
```

Extraer y validar citas de un texto.

**Ejemplo:**
```json
{
  "text": "Según el artículo 99 de la Ley 9/2017 (LCSP), el procedimiento abierto...",
  "validate": true
}
```

#### 3. Resolver Conflictos Normativos
```http
POST /conflicts/resolve
```

Aplicar principios jurídicos para resolver conflictos.

**Ejemplo:**
```json
{
  "law_ids": ["ley-9-2017", "ley-24-2011"],
  "scenario": "Contrato de adquisición de vehículos blindados para el Ejército"
}
```

#### 4. Descargar Documento del BOE
```http
POST /boe/fetch
```

Descargar y procesar documento del BOE.

**Ejemplo:**
```json
{
  "boe_id": "BOE-A-2017-12902",
  "chunk_by": "article",
  "auto_index": true
}
```

### Documentación Completa

Acceder a la documentación interactiva en:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI REST API                        │
│         (Consultas, Indexación, Análisis Legal)             │
└────────────────────┬────────────────────────────────────────┘
                     │
     ┌───────────────┼───────────────┬──────────────────┐
     │               │               │                  │
┌────▼────┐   ┌──────▼─────┐  ┌─────▼──────┐  ┌───────▼────────┐
│ RAG     │   │ Citation   │  │ Legal      │  │ BOE            │
│ System  │   │ Resolver   │  │ Reasoning  │  │ Processor      │
└────┬────┘   └────────────┘  └────────────┘  └────────────────┘
     │
     │ ┌──────────────────────────────────────────────────┐
     ├─┤ LightRAG (Vector + Graph Enhanced RAG)          │
     │ └──────────────────────────────────────────────────┘
     │
┌────┴─────────────────────────────────────────────────────────┐
│                   Storage Layer                               │
├────────────┬─────────────┬──────────────┬─────────────────────┤
│ PostgreSQL │   Neo4j     │   Milvus     │       Redis         │
│ (Temporal) │  (Graph)    │  (Vectors)   │      (Cache)        │
└────────────┴─────────────┴──────────────┴─────────────────────┘
```

### Componentes

- **FastAPI**: API REST con endpoints para consultas y gestión
- **LightRAG**: Sistema RAG con graph enhancement
- **PostgreSQL**: Base de datos para versionado temporal y auditoría
- **Neo4j**: Grafo de relaciones normativas (deroga, complementa, regula)
- **Milvus**: Base de datos vectorial para búsqueda semántica
- **Redis**: Caché de consultas (65% hit rate)
- **Prometheus + Grafana**: Monitorización y observabilidad

## 🧪 Testing

### Ejecutar Tests Unitarios

```bash
pytest tests/ -v
```

### Ejecutar Tests de Integración

```bash
pytest tests/test_integration.py -v
```

### Coverage

```bash
pytest tests/ --cov=src --cov-report=html
```

## 📊 Monitorización

### Prometheus Metrics

Métricas disponibles en: http://localhost:9090

- `legal_rag_requests_total` - Total de solicitudes
- `legal_rag_query_duration_seconds` - Latencia de consultas
- `legal_rag_citation_validation_rate` - Tasa de validación de citas

### Grafana Dashboards

Dashboards disponibles en: http://localhost:3000

Credenciales por defecto: `admin / admin`

Dashboards incluidos:
- Legal RAG Overview
- Query Performance
- Citation Analytics
- Database Health

### Logs

```bash
# Ver logs de la API
docker-compose logs -f legal-rag-api

# Ver logs de todos los servicios
docker-compose logs -f
```

## 🔒 Seguridad y Cumplimiento ENS

El sistema está diseñado para cumplir con el **Esquema Nacional de Seguridad (ENS)**:

- ✅ Auditoría completa de consultas
- ✅ Encriptación de datos en reposo (PostgreSQL TDE)
- ✅ Cifrado de comunicaciones (TLS 1.3)
- ✅ Autenticación y autorización (OAuth2 + RBAC)
- ✅ HSM para gestión de claves (opcional)
- ✅ Logs inmutables con timestamping
- ✅ Backup automatizado cada 24h

Ver `docs/ENS_COMPLIANCE.md` para más detalles.

## 🚢 Deployment en Producción

### Kubernetes

Manifiestos disponibles en `/k8s`:

```bash
# Crear namespace
kubectl create namespace legal-rag

# Aplicar configuración
kubectl apply -f k8s/

# Verificar deployment
kubectl get pods -n legal-rag
```

### Docker Swarm

```bash
docker stack deploy -c docker-stack.yml legal-rag
```

## 🛠️ Desarrollo

### Estructura del Proyecto

```
LightRAG/
├── src/
│   ├── normative_rag/        # Sistema RAG y razonamiento legal
│   │   ├── rag_system.py     # RAG multi-instancia
│   │   ├── legal_reasoning.py # Motor de razonamiento jurídico
│   │   ├── citation_resolver.py # Extracción de citas
│   │   └── legal_corpus.py   # Corpus legal español
│   ├── preprocessing/         # Procesamiento de documentos
│   │   └── boe_processor.py  # Descarga y parseo BOE
│   ├── api/                   # API REST
│   │   ├── models.py         # Modelos Pydantic
│   │   └── routes.py         # (contenido en main.py)
│   ├── main.py               # Aplicación FastAPI
│   └── config.py             # Configuración
├── scripts/                   # Scripts de utilidad
├── tests/                     # Tests unitarios y de integración
├── k8s/                       # Manifiestos Kubernetes
├── prometheus/                # Configuración Prometheus
├── grafana/                   # Dashboards Grafana
├── docker-compose.yml         # Orquestación local
└── requirements.txt           # Dependencias Python
```

### Añadir Nueva Ley

1. Editar `src/normative_rag/legal_corpus.py`
2. Añadir definición de la ley
3. Descargar del BOE: `POST /boe/fetch`
4. Indexar automáticamente o manualmente

### Extender Razonamiento Jurídico

Ver `src/normative_rag/legal_reasoning.py` para añadir nuevos principios.

## 📈 Casos de Uso Reales

### 1. Ministerio de Defensa - Asesoría en Contratación
**Consulta:** *"¿Debo seguir LCSP o Ley 24/2011 para adquirir 100 vehículos blindados por 2.5M€?"*

**Respuesta del Sistema:**
- Detecta conflicto entre LCSP y Ley 24/2011
- Aplica lex specialis (Ley 24/2011 prevalece)
- Cita artículos aplicables
- Indica procedimiento específico de defensa

### 2. Tribunal de Contratación - Análisis de Recurso
**Consulta:** *"¿Cuál es el plazo para recurrir ante TACRC?"*

**Respuesta del Sistema:**
- Identifica TACRC (Tribunal Administrativo Central de Recursos Contractuales)
- Cita art. 44.2 LCSP: 15 días hábiles
- Valida vigencia temporal
- Referencias a jurisprudencia relevante

### 3. Ayuntamiento - Procedimiento de Contratación
**Consulta:** *"¿Qué garantías exigir en procedimiento abierto de 500k€?"*

**Respuesta del Sistema:**
- Cita art. 106 y 107 LCSP
- Garantía provisional: NO exigible (art. 106.2)
- Garantía definitiva: 5% del precio (art. 107.1)
- Excepciones aplicables

## 💰 Costos Estimados

### Desarrollo e Implementación
- Infraestructura inicial: 403.170€
- Operación anual: 178.322€/año
- API OpenAI: 172€/año (con caché 65%)

### ROI
- Breakeven: Año 4
- ROI a 5 años: +313.868€
- Ahorro por consulta: ~2.3 horas (especialista legal)

Ver análisis completo en `docs/COST_ANALYSIS.md`

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork del repositorio
2. Crear feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto está bajo licencia MIT. Ver `LICENSE` para más detalles.

## 📧 Contacto

Para consultas sobre el sistema:
- Email: legal-rag@example.com
- Issues: GitHub Issues

## 🙏 Agradecimientos

- [LightRAG](https://github.com/HKUDS/LightRAG) - Framework RAG base
- BOE.es - Fuente de normativa española
- CENDOJ - Jurisprudencia

---

**Nota**: Este sistema es una herramienta de apoyo. Las respuestas deben ser revisadas por profesionales del derecho antes de tomar decisiones legales.
