#!/bin/bash
# Setup script for databases and initial configuration

set -e

echo "====================================="
echo "Spanish Legal RAG - Database Setup"
echo "====================================="

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Error: .env file not found"
    exit 1
fi

echo ""
echo "1. Waiting for PostgreSQL..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c '\q' 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done
echo "✓ PostgreSQL is up"

echo ""
echo "2. Creating PostgreSQL schema..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB <<-EOSQL
    -- Create tables for temporal tracking
    CREATE TABLE IF NOT EXISTS normative_versions (
        id SERIAL PRIMARY KEY,
        law_id VARCHAR(100) NOT NULL,
        boe_id VARCHAR(50) NOT NULL,
        title TEXT NOT NULL,
        publication_date DATE NOT NULL,
        entry_force_date DATE,
        repeal_date DATE,
        active BOOLEAN DEFAULT TRUE,
        full_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX idx_law_id ON normative_versions(law_id);
    CREATE INDEX idx_boe_id ON normative_versions(boe_id);
    CREATE INDEX idx_active ON normative_versions(active);

    -- Create table for query audit log (ENS compliance)
    CREATE TABLE IF NOT EXISTS query_audit_log (
        id SERIAL PRIMARY KEY,
        query_text TEXT NOT NULL,
        area VARCHAR(50),
        user_id VARCHAR(100),
        ip_address INET,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        response_time_ms INTEGER,
        cache_hit BOOLEAN
    );

    CREATE INDEX idx_timestamp ON query_audit_log(timestamp);
    CREATE INDEX idx_user_id ON query_audit_log(user_id);

    -- Create table for citation statistics
    CREATE TABLE IF NOT EXISTS citation_stats (
        id SERIAL PRIMARY KEY,
        law_id VARCHAR(100),
        article VARCHAR(50),
        citation_count INTEGER DEFAULT 0,
        last_cited TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX idx_citation_law ON citation_stats(law_id);
EOSQL
echo "✓ PostgreSQL schema created"

echo ""
echo "3. Waiting for Neo4j..."
until curl -s http://${NEO4J_URI#bolt://}/7474 >/dev/null 2>&1; do
  echo "Neo4j is unavailable - sleeping"
  sleep 2
done
echo "✓ Neo4j is up"

echo ""
echo "4. Creating Neo4j constraints..."
cypher-shell -u $NEO4J_USER -p $NEO4J_PASSWORD <<-EOCYPHER
    CREATE CONSTRAINT law_id IF NOT EXISTS FOR (l:Law) REQUIRE l.id IS UNIQUE;
    CREATE CONSTRAINT article_id IF NOT EXISTS FOR (a:Article) REQUIRE a.id IS UNIQUE;
    CREATE INDEX law_hierarchy IF NOT EXISTS FOR (l:Law) ON (l.hierarchy);
    CREATE INDEX law_area IF NOT EXISTS FOR (l:Law) ON (l.area);
EOCYPHER
echo "✓ Neo4j constraints created"

echo ""
echo "5. Waiting for Milvus..."
until curl -s http://$MILVUS_HOST:9091/healthz >/dev/null 2>&1; do
  echo "Milvus is unavailable - sleeping"
  sleep 2
done
echo "✓ Milvus is up"

echo ""
echo "6. Waiting for Redis..."
until redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD ping 2>/dev/null | grep -q PONG; do
  echo "Redis is unavailable - sleeping"
  sleep 2
done
echo "✓ Redis is up"

echo ""
echo "====================================="
echo "✓ All databases are ready!"
echo "====================================="
