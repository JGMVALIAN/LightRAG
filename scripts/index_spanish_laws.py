#!/usr/bin/env python3
"""
Script to index Spanish legal corpus into RAG system
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.normative_rag import SpanishLegalRAGSystem, LegalArea, get_all_laws
from src.preprocessing import BOEProcessor


async def index_all_spanish_laws():
    """Index all Spanish laws from corpus"""
    print("=" * 60)
    print("Spanish Legal RAG - Corpus Indexing")
    print("=" * 60)

    # Initialize systems
    rag = SpanishLegalRAGSystem(
        working_dir="./data/lightrag",
        enable_reasoning=True,
        enable_citation_validation=True
    )

    processor = BOEProcessor()

    # Get all laws
    laws = get_all_laws()
    print(f"\nFound {len(laws)} laws to index")

    # Index each law
    for law_key, law_data in laws.items():
        print(f"\n{'='*60}")
        print(f"Processing: {law_data.get('title')}")
        print(f"BOE: {law_data.get('boe')}")
        print(f"{'='*60}")

        try:
            # Fetch and structure document
            boe_id = law_data.get('boe')
            if not boe_id:
                print(f"⚠ No BOE ID found, skipping...")
                continue

            chunks = await processor.fetch_and_index_law(
                boe_id=boe_id,
                chunk_by='article'
            )

            if not chunks:
                print(f"⚠ No chunks created, skipping...")
                continue

            print(f"✓ Created {len(chunks)} chunks")

            # Index into appropriate area
            area = law_data.get('area', LegalArea.GENERAL)
            indexed_count = 0

            for chunk in chunks:
                await rag.index_document(
                    document=chunk['text'],
                    area=area,
                    metadata=chunk['metadata']
                )
                indexed_count += 1

                if indexed_count % 10 == 0:
                    print(f"  Indexed {indexed_count}/{len(chunks)} chunks...")

            print(f"✓ Successfully indexed {indexed_count} chunks into {area.value}")

        except Exception as e:
            print(f"✗ Error processing {law_key}: {e}")
            continue

    # Cleanup
    await processor.close()

    # Print statistics
    print("\n" + "=" * 60)
    print("INDEXING COMPLETE")
    print("=" * 60)
    stats = rag.get_statistics()
    print(f"\nRAG Instances: {stats['rag_instances']}")
    print(f"Areas: {', '.join(stats['areas'])}")
    print(f"Total Laws: {stats['total_laws']}")
    print("\n✓ Spanish legal corpus indexed successfully!")


if __name__ == "__main__":
    asyncio.run(index_all_spanish_laws())
