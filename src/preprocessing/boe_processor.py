"""
BOE (Boletín Oficial del Estado) Document Processor
Fetches and processes Spanish legal documents from BOE
"""
import re
import httpx
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
from datetime import date, datetime
from dataclasses import dataclass
import asyncio


@dataclass
class BOEDocument:
    """Represents a BOE document"""
    boe_id: str  # e.g., "BOE-A-2017-12902"
    title: str
    publication_date: date
    department: str
    document_type: str  # LEY, REAL_DECRETO, etc.
    summary: str
    full_text: str
    url: str
    articles: List[Dict]
    metadata: Dict


class BOEProcessor:
    """
    Processor for BOE (Official State Gazette) documents

    Features:
    - Fetch documents from BOE website
    - Parse HTML/XML structure
    - Extract articles, sections, and dispositions
    - Structure for RAG indexing
    """

    BOE_BASE_URL = "https://www.boe.es"
    BOE_SEARCH_URL = f"{BOE_BASE_URL}/buscar/act.php"
    BOE_PDF_URL = f"{BOE_BASE_URL}/boe/dias"

    # Document type patterns
    DOC_TYPES = {
        'LEY': re.compile(r'^Ley\s+(?:Orgánica\s+)?(\d+/\d{4})', re.IGNORECASE),
        'REAL_DECRETO': re.compile(r'^Real\s+Decreto(?:\s+Legislativo)?\s+(\d+/\d{4})', re.IGNORECASE),
        'ORDEN': re.compile(r'^Orden\s+([A-Z]{3}/\d+/\d{4})', re.IGNORECASE),
    }

    def __init__(self, cache_dir: str = "./data/boe_cache"):
        """
        Initialize BOE processor

        Args:
            cache_dir: Directory to cache downloaded documents
        """
        self.cache_dir = cache_dir
        self.client = httpx.AsyncClient(timeout=30.0)

    async def fetch_document(self, boe_id: str) -> Optional[BOEDocument]:
        """
        Fetch a document from BOE by its identifier

        Args:
            boe_id: BOE identifier (e.g., "BOE-A-2017-12902")

        Returns:
            BOEDocument if found, None otherwise
        """
        url = f"{self.BOE_BASE_URL}/buscar/doc.php?id={boe_id}"

        try:
            response = await self.client.get(url)
            response.raise_for_status()

            html_content = response.text
            return self._parse_boe_html(html_content, boe_id, url)

        except httpx.HTTPError as e:
            print(f"Error fetching BOE document {boe_id}: {e}")
            return None

    def _parse_boe_html(self, html: str, boe_id: str, url: str) -> BOEDocument:
        """
        Parse BOE HTML document

        Args:
            html: HTML content
            boe_id: BOE identifier
            url: Source URL

        Returns:
            Structured BOEDocument
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Extract metadata
        title = self._extract_title(soup)
        publication_date = self._extract_publication_date(soup)
        department = self._extract_department(soup)
        document_type = self._classify_document_type(title)
        summary = self._extract_summary(soup)

        # Extract full text
        full_text = self._extract_full_text(soup)

        # Parse articles
        articles = self._extract_articles(full_text)

        # Build metadata
        metadata = {
            'boe_id': boe_id,
            'url': url,
            'processed_date': datetime.now().isoformat(),
            'article_count': len(articles),
            'word_count': len(full_text.split()),
        }

        return BOEDocument(
            boe_id=boe_id,
            title=title,
            publication_date=publication_date,
            department=department,
            document_type=document_type,
            summary=summary,
            full_text=full_text,
            url=url,
            articles=articles,
            metadata=metadata
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract document title from BOE HTML"""
        title_elem = soup.find('h1', class_='titulo') or soup.find('h1')
        if title_elem:
            return title_elem.get_text(strip=True)
        return "Título no encontrado"

    def _extract_publication_date(self, soup: BeautifulSoup) -> date:
        """Extract publication date"""
        date_elem = soup.find('span', class_='fecha')
        if date_elem:
            date_text = date_elem.get_text(strip=True)
            # Parse Spanish date format: "08/11/2017"
            try:
                return datetime.strptime(date_text, "%d/%m/%Y").date()
            except ValueError:
                pass

        return date.today()

    def _extract_department(self, soup: BeautifulSoup) -> str:
        """Extract department/ministry"""
        dept_elem = soup.find('span', class_='departamento')
        if dept_elem:
            return dept_elem.get_text(strip=True)
        return "Departamento no especificado"

    def _classify_document_type(self, title: str) -> str:
        """Classify document type from title"""
        for doc_type, pattern in self.DOC_TYPES.items():
            if pattern.match(title):
                return doc_type
        return "OTRO"

    def _extract_summary(self, soup: BeautifulSoup) -> str:
        """Extract document summary"""
        summary_elem = soup.find('div', class_='resumen') or soup.find('p', class_='resumen')
        if summary_elem:
            return summary_elem.get_text(strip=True)
        return ""

    def _extract_full_text(self, soup: BeautifulSoup) -> str:
        """Extract full document text"""
        # Look for main content div
        content_div = (
            soup.find('div', class_='documento') or
            soup.find('div', class_='texto') or
            soup.find('div', id='texto')
        )

        if content_div:
            # Remove script and style elements
            for element in content_div(['script', 'style', 'nav', 'header', 'footer']):
                element.decompose()

            return content_div.get_text(separator='\n', strip=True)

        return soup.get_text(separator='\n', strip=True)

    def _extract_articles(self, text: str) -> List[Dict]:
        """
        Extract articles from full text

        Spanish legal structure:
        - Artículo N°.- Title
        - 1. Paragraph
        - a) Sub-point
        """
        articles = []

        # Pattern to match articles
        # Matches: "Artículo 99.-" or "Artículo 121.-"
        article_pattern = re.compile(
            r'Artículo\s+(\d+(?:\.\d+)?)[°º]?\.?[-–]\s*(.*?)(?=Artículo\s+\d+|Disposición|Anexo|$)',
            re.DOTALL | re.IGNORECASE
        )

        for match in article_pattern.finditer(text):
            article_num = match.group(1)
            article_content = match.group(2).strip()

            # Extract article title (first line usually)
            lines = article_content.split('\n')
            article_title = lines[0].strip() if lines else ""

            # Extract numbered paragraphs
            paragraphs = self._extract_paragraphs(article_content)

            articles.append({
                'number': article_num,
                'title': article_title,
                'content': article_content,
                'paragraphs': paragraphs,
                'word_count': len(article_content.split())
            })

        return articles

    def _extract_paragraphs(self, article_content: str) -> List[Dict]:
        """Extract numbered paragraphs from article"""
        paragraphs = []

        # Pattern for numbered paragraphs: "1.", "2.", etc.
        para_pattern = re.compile(r'^(\d+)\.\s+(.*?)(?=^\d+\.|$)', re.MULTILINE | re.DOTALL)

        for match in para_pattern.finditer(article_content):
            para_num = match.group(1)
            para_text = match.group(2).strip()

            # Extract lettered sub-points: a), b), c)
            sub_points = self._extract_subpoints(para_text)

            paragraphs.append({
                'number': para_num,
                'text': para_text,
                'sub_points': sub_points
            })

        return paragraphs

    def _extract_subpoints(self, paragraph_text: str) -> List[Dict]:
        """Extract lettered sub-points (a), b), etc.)"""
        sub_points = []

        # Pattern for lettered points: a), b), etc.
        subpoint_pattern = re.compile(r'([a-z])\)\s+(.*?)(?=[a-z]\)|$)', re.IGNORECASE | re.DOTALL)

        for match in subpoint_pattern.finditer(paragraph_text):
            letter = match.group(1)
            text = match.group(2).strip()

            sub_points.append({
                'letter': letter,
                'text': text
            })

        return sub_points

    def structure_for_rag(self, doc: BOEDocument, chunk_by: str = 'article') -> List[Dict]:
        """
        Structure document for RAG indexing

        Args:
            doc: BOEDocument to structure
            chunk_by: 'article', 'paragraph', or 'full'

        Returns:
            List of chunks with metadata for RAG indexing
        """
        chunks = []

        if chunk_by == 'full':
            # Index entire document as one chunk
            chunks.append({
                'text': doc.full_text,
                'metadata': {
                    'boe_id': doc.boe_id,
                    'title': doc.title,
                    'type': 'full_document',
                    'url': doc.url,
                    'publication_date': doc.publication_date.isoformat()
                }
            })

        elif chunk_by == 'article':
            # Index each article separately
            for article in doc.articles:
                chunk_text = f"""
{doc.title}

Artículo {article['number']}: {article['title']}

{article['content']}
                """.strip()

                chunks.append({
                    'text': chunk_text,
                    'metadata': {
                        'boe_id': doc.boe_id,
                        'title': doc.title,
                        'type': 'article',
                        'article_number': article['number'],
                        'article_title': article['title'],
                        'url': f"{doc.url}#art{article['number']}",
                        'publication_date': doc.publication_date.isoformat()
                    }
                })

        elif chunk_by == 'paragraph':
            # Index each paragraph separately
            for article in doc.articles:
                for para in article.get('paragraphs', []):
                    chunk_text = f"""
{doc.title} - Artículo {article['number']}: {article['title']}

Apartado {para['number']}: {para['text']}
                    """.strip()

                    chunks.append({
                        'text': chunk_text,
                        'metadata': {
                            'boe_id': doc.boe_id,
                            'title': doc.title,
                            'type': 'paragraph',
                            'article_number': article['number'],
                            'paragraph_number': para['number'],
                            'url': f"{doc.url}#art{article['number']}",
                            'publication_date': doc.publication_date.isoformat()
                        }
                    })

        return chunks

    async def fetch_and_index_law(self, boe_id: str, chunk_by: str = 'article') -> List[Dict]:
        """
        Fetch a law from BOE and structure it for indexing

        Args:
            boe_id: BOE identifier
            chunk_by: Chunking strategy

        Returns:
            List of chunks ready for RAG indexing
        """
        doc = await self.fetch_document(boe_id)
        if not doc:
            return []

        return self.structure_for_rag(doc, chunk_by=chunk_by)

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Example usage
async def main():
    """Example usage of BOE processor"""
    processor = BOEProcessor()

    # Fetch LCSP (Ley 9/2017)
    print("Fetching LCSP from BOE...")
    chunks = await processor.fetch_and_index_law(
        boe_id="BOE-A-2017-12902",
        chunk_by='article'
    )

    print(f"\nProcessed {len(chunks)} chunks")
    if chunks:
        print(f"\nFirst chunk preview:")
        print(chunks[0]['text'][:500])
        print(f"\nMetadata: {chunks[0]['metadata']}")

    await processor.close()


if __name__ == "__main__":
    asyncio.run(main())
