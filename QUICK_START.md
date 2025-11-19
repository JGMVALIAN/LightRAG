# Guía de Inicio Rápido - Sistema Legal RAG Español

## 🎯 ¿Qué es este sistema?

Un sistema RAG (Retrieval-Augmented Generation) especializado en normativa legal española que permite:

- **Consultar** legislación española de forma natural
- **Validar** citas legales automáticamente
- **Resolver** conflictos normativos aplicando principios jurídicos
- **Analizar** vigencia temporal de normas
- **Procesar** documentos del BOE automáticamente

## 🚀 Instalación en 5 Pasos

### 1. Clonar y Configurar

```bash
git clone https://github.com/JGMVALIAN/LightRAG.git
cd LightRAG
cp .env.example .env
```

### 2. Añadir API Key de OpenAI

Editar `.env` y añadir:
```bash
OPENAI_API_KEY=sk-tu-clave-aqui
```

### 3. Iniciar Servicios

```bash
# Opción 1: Usando Make (recomendado)
make docker-up

# Opción 2: Docker Compose directo
docker-compose up -d
```

### 4. Configurar Bases de Datos

```bash
# Esperar 15 segundos a que los servicios arranquen
sleep 15

# Ejecutar setup
make setup
```

### 5. Verificar Instalación

```bash
# Health check
make health

# Estadísticas
make stats
```

## 📝 Ejemplos de Uso

### Ejemplo 1: Consulta sobre Contratación Pública

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué procedimiento debo usar para contratar servicios de limpieza por 200.000€?",
    "area": "contratacion",
    "mode": "hybrid",
    "include_citations": true,
    "include_reasoning": true
  }'
```

**Respuesta esperada:**
- Identificación del procedimiento aplicable (abierto simplificado según LCSP)
- Citas a artículos específicos (art. 131 LCSP)
- Plazos y requisitos
- Garantías exigibles

### Ejemplo 2: Plazos Administrativos

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿En cuánto tiempo debo responder a un recurso de alzada?",
    "area": "administrativo",
    "mode": "hybrid"
  }'
```

**Respuesta esperada:**
- Plazo de 3 meses (art. 122 LPAC)
- Efectos del silencio administrativo
- Referencias legales validadas

### Ejemplo 3: Extracción de Citas

```bash
curl -X POST http://localhost:8000/citations/extract \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Según el artículo 99 de la Ley 9/2017 y el Real Decreto 1098/2001, el procedimiento abierto...",
    "validate": true
  }'
```

**Respuesta:**
```json
{
  "total_citations": 3,
  "validated_citations": 3,
  "validation_rate": 1.0,
  "citations": [
    {
      "text": "artículo 99",
      "type": "articulo",
      "validated": true,
      "law": "Ley 9/2017, de Contratos del Sector Público"
    },
    {
      "text": "Ley 9/2017",
      "type": "ley_ordinaria",
      "validated": true,
      "law": "Ley 9/2017, de Contratos del Sector Público"
    },
    {
      "text": "Real Decreto 1098/2001",
      "type": "real_decreto",
      "validated": true,
      "law": "Real Decreto 1098/2001, Reglamento General de la Ley de Contratos"
    }
  ]
}
```

### Ejemplo 4: Resolver Conflicto Normativo

```bash
curl -X POST http://localhost:8000/conflicts/resolve \
  -H "Content-Type: application/json" \
  -d '{
    "law_ids": ["ley-9-2017", "ley-24-2011"],
    "scenario": "Adquisición de vehículos blindados para el Ejército"
  }'
```

**Respuesta esperada:**
- Aplicación de lex specialis
- Ley 24/2011 prevalece sobre LCSP para contratos de defensa
- Explicación del principio jurídico aplicado

### Ejemplo 5: Descargar e Indexar del BOE

```bash
curl -X POST http://localhost:8000/boe/fetch \
  -H "Content-Type: application/json" \
  -d '{
    "boe_id": "BOE-A-2017-12902",
    "chunk_by": "article",
    "auto_index": true
  }'
```

## 📊 Acceder a Interfaces Web

Una vez iniciado el sistema, acceder a:

- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc
- **Grafana (Monitorización)**: http://localhost:3000 (admin/admin)
- **Prometheus (Métricas)**: http://localhost:9090
- **Neo4j Browser**: http://localhost:7474

## 🔧 Comandos Make Útiles

```bash
# Ver todos los comandos disponibles
make help

# Iniciar servicios
make docker-up

# Ver logs
make docker-logs

# Parar servicios
make docker-down

# Ejecutar tests
make test

# Consulta de ejemplo
make query-example

# Crear backup
make backup

# Ver estado de salud
make health
```

## 📚 Áreas Legales Disponibles

| Área | Código | Leyes Principales |
|------|--------|-------------------|
| **Contratación Pública** | `contratacion` | Ley 9/2017 (LCSP), Ley 24/2011, RD 1098/2001 |
| **Derecho Administrativo** | `administrativo` | Ley 39/2015 (LPAC), Ley 40/2015 (LRJSP), Ley 29/1998 (LJCA) |
| **Defensa y Seguridad** | `defensa` | LO 5/2005 (LODN), Ley 8/2014, LO 14/2015 (LSN) |
| **General** | `general` | Todas las áreas |

## 🎓 Casos de Uso Comunes

### 1. Oficina de Contratación - Asesoría Rápida
**Pregunta**: *"¿Necesito garantía provisional para un contrato de 300k€?"*
- Respuesta automática citando art. 106 LCSP
- Validación de citas
- Tiempo de respuesta: <2 segundos

### 2. Servicio Jurídico - Análisis de Recurso
**Pregunta**: *"¿Procede recurso de alzada contra resolución del órgano de contratación?"*
- Identificación del recurso aplicable (recurso especial TACRC)
- Plazos (15 días hábiles)
- Efectos suspensivos

### 3. Gestor de Expedientes - Verificación de Plazos
**Pregunta**: *"¿Cuándo caduca el expediente si no hay resolución?"*
- Plazos de caducidad según LPAC
- Efectos del silencio administrativo
- Cómputo de plazos

### 4. Tribunal Administrativo - Precedentes
**Pregunta**: *"¿Qué criterios de adjudicación son válidos para contratos de servicios?"*
- Artículos LCSP relevantes
- Jurisprudencia aplicable (si está indexada)
- Best practices

## 🐛 Solución de Problemas

### Error: "RAG system not initialized"
```bash
# Reiniciar servicios
docker-compose restart legal-rag-api

# Verificar logs
docker-compose logs -f legal-rag-api
```

### Error: "PostgreSQL connection failed"
```bash
# Verificar que PostgreSQL está corriendo
docker-compose ps postgres

# Reiniciar PostgreSQL
docker-compose restart postgres

# Ejecutar setup nuevamente
./scripts/setup_databases.sh
```

### Los servicios no arrancan
```bash
# Limpiar y reiniciar desde cero
make docker-clean
make docker-up
make setup
```

## 📈 Mejores Prácticas

### 1. Usar Modo Híbrido
El modo `hybrid` combina búsqueda local y global para mejores resultados:
```json
{
  "mode": "hybrid"  // Recomendado
}
```

### 2. Habilitar Validación de Citas
```json
{
  "include_citations": true,
  "include_reasoning": true
}
```

### 3. Especificar Área Legal
Para mejores resultados, especificar el área:
```json
{
  "area": "contratacion"  // Más específico = mejor resultado
}
```

### 4. Usar Caché
El sistema tiene 65% cache hit rate. Consultas repetidas son instantáneas.

## 📞 Soporte

- **Documentación Completa**: Ver `README.md`
- **API Reference**: http://localhost:8000/docs
- **Issues**: GitHub Issues del proyecto
- **Tests**: `make test`

## ⚖️ Disclaimer Legal

Este sistema es una **herramienta de apoyo** para profesionales del derecho y gestores públicos.

**Las respuestas generadas deben ser revisadas por personal jurídico cualificado antes de tomar decisiones legales.**

El sistema proporciona:
- ✅ Referencias legales validadas
- ✅ Análisis de conflictos normativos
- ✅ Extracción de citas
- ✅ Verificación de vigencia

**NO sustituye**:
- ❌ Asesoramiento jurídico profesional
- ❌ Análisis de jurisprudencia completo
- ❌ Interpretación contextual compleja
- ❌ Decisiones legales vinculantes

## 🎯 Próximos Pasos

1. **Indexar más leyes**: `python scripts/index_spanish_laws.py`
2. **Explorar API**: http://localhost:8000/docs
3. **Monitorizar**: http://localhost:3000
4. **Personalizar**: Editar `src/normative_rag/legal_corpus.py`

---

**¡Listo para usar!** 🚀

Para más información, consultar `README.md` o la documentación de la API.
