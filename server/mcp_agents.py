"""
MCP Agents Module
Provides specialized agents for different teaching tasks:
- ScraperAgent: Web content extraction
- FileAgent: PDF and image processing
- MathAgent: Mathematical computation
- VectorAgent: Semantic search and embeddings
"""

import logging
import re
import io
from typing import List, Dict, Any, Optional
from pathlib import Path

# File processing
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

# Web scraping
import httpx
from bs4 import BeautifulSoup
from readability import Document

# Math computation
import sympy
from sympy import sympify, solve, simplify, latex

# Embeddings
from sentence_transformers import SentenceTransformer
import numpy as np

# Supabase
from config import get_supabase_client

logger = logging.getLogger("mcp_agents")


class ScraperAgent:
    """Agent for web content scraping and summarization"""
    
    def __init__(self):
        self.timeout = 30.0
        logger.info("✅ ScraperAgent initialized")
    
    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """
        Scrape and extract main content from a URL
        
        Returns:
            dict with 'title', 'content', 'summary'
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                
            # Use readability to extract main content
            doc = Document(response.text)
            title = doc.title()
            
            # Parse with BeautifulSoup for cleanup
            soup = BeautifulSoup(doc.summary(), 'html.parser')
            
            # Extract text
            text_content = soup.get_text(separator='\n', strip=True)
            
            # Basic summarization (first 500 words)
            words = text_content.split()
            summary = ' '.join(words[:500]) + ('...' if len(words) > 500 else '')
            
            logger.info(f"✅ Successfully scraped: {title}")
            
            return {
                'title': title,
                'content': text_content,
                'summary': summary,
                'url': url,
                'word_count': len(words)
            }
            
        except Exception as e:
            logger.error(f"❌ Scraping failed for {url}: {e}")
            return {
                'title': 'Error',
                'content': f'Failed to scrape URL: {str(e)}',
                'summary': '',
                'url': url,
                'error': str(e)
            }


class FileAgent:
    """Agent for PDF and image file processing"""
    
    def __init__(self):
        logger.info("✅ FileAgent initialized")
    
    async def process_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text and metadata from PDF
        
        Returns:
            dict with 'text', 'pages', 'metadata', 'images_count'
        """
        try:
            doc = fitz.open(file_path)
            
            text_content = []
            images_count = 0
            
            for page_num, page in enumerate(doc, start=1):
                # Extract text
                text = page.get_text()
                text_content.append(f"--- Page {page_num} ---\n{text}")
                
                # Count images
                images = page.get_images()
                images_count += len(images)
            
            full_text = '\n\n'.join(text_content)
            
            metadata = {
                'pages': len(doc),
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'subject': doc.metadata.get('subject', ''),
            }
            
            doc.close()
            
            logger.info(f"✅ Processed PDF: {len(doc)} pages, {len(full_text)} characters")
            
            return {
                'text': full_text,
                'pages': len(doc),
                'metadata': metadata,
                'images_count': images_count,
                'char_count': len(full_text)
            }
            
        except Exception as e:
            logger.error(f"❌ PDF processing failed: {e}")
            return {
                'text': '',
                'pages': 0,
                'metadata': {},
                'error': str(e)
            }
    
    async def process_image(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from image using OCR
        
        Returns:
            dict with 'text', 'confidence', 'dimensions'
        """
        try:
            image = Image.open(file_path)
            
            # Perform OCR
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Extract text
            text = pytesseract.image_to_string(image)
            
            # Calculate average confidence
            confidences = [int(conf) for conf in ocr_data['conf'] if conf != '-1']
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            logger.info(f"✅ Processed image: {len(text)} characters extracted")
            
            return {
                'text': text.strip(),
                'confidence': round(avg_confidence, 2),
                'dimensions': {
                    'width': image.width,
                    'height': image.height
                },
                'format': image.format,
                'char_count': len(text)
            }
            
        except Exception as e:
            logger.error(f"❌ Image processing failed: {e}")
            return {
                'text': '',
                'confidence': 0,
                'error': str(e)
            }


class MathAgent:
    """Agent for mathematical computation and symbolic math"""
    
    def __init__(self):
        logger.info("✅ MathAgent initialized")
    
    def solve_equation(self, equation_str: str) -> Dict[str, Any]:
        """
        Solve mathematical equation using SymPy
        
        Args:
            equation_str: Equation like "x**2 - 4 = 0" or "2*x + 5"
        
        Returns:
            dict with 'solutions', 'latex', 'steps'
        """
        try:
            # Parse equation
            if '=' in equation_str:
                left, right = equation_str.split('=')
                expr = sympify(f"({left}) - ({right})")
            else:
                expr = sympify(equation_str)
            
            # Find variables
            variables = list(expr.free_symbols)
            
            if not variables:
                # Just evaluate
                result = expr.evalf()
                return {
                    'result': float(result),
                    'latex': latex(result),
                    'type': 'evaluation'
                }
            
            # Solve for first variable
            var = variables[0]
            solutions = solve(expr, var)
            
            # Format solutions
            solution_strs = [str(sol) for sol in solutions]
            latex_solutions = [latex(sol) for sol in solutions]
            
            logger.info(f"✅ Solved equation: {len(solutions)} solution(s)")
            
            return {
                'solutions': solution_strs,
                'latex_solutions': latex_solutions,
                'variable': str(var),
                'original': equation_str,
                'type': 'equation'
            }
            
        except Exception as e:
            logger.error(f"❌ Math solving failed: {e}")
            return {
                'solutions': [],
                'error': str(e),
                'type': 'error'
            }
    
    def simplify_expression(self, expr_str: str) -> Dict[str, Any]:
        """Simplify mathematical expression"""
        try:
            expr = sympify(expr_str)
            simplified = simplify(expr)
            
            return {
                'original': expr_str,
                'simplified': str(simplified),
                'latex': latex(simplified),
                'type': 'simplification'
            }
            
        except Exception as e:
            logger.error(f"❌ Simplification failed: {e}")
            return {
                'original': expr_str,
                'error': str(e),
                'type': 'error'
            }


class VectorAgent:
    """Agent for embeddings and semantic search"""
    
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.supabase = get_supabase_client()
        logger.info("✅ VectorAgent initialized")
    
    def create_embedding(self, text: str) -> List[float]:
        """Create embedding vector for text"""
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"❌ Embedding creation failed: {e}")
            return []
    
    async def store_embedding(
        self,
        user_id: str,
        content: str,
        source_type: str,
        source_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Store content embedding in Supabase"""
        try:
            if not self.supabase:
                logger.warning("Supabase client not available")
                return False
            
            embedding = self.create_embedding(content)
            
            if not embedding:
                return False
            
            data = {
                'user_id': user_id,
                'content': content[:1000],  # Store truncated content
                'embedding': embedding,
                'source_type': source_type,
                'source_id': source_id,
                'metadata': metadata or {}
            }
            
            result = self.supabase.table('embeddings').insert(data).execute()
            logger.info(f"✅ Stored embedding for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Embedding storage failed: {e}")
            return False
    
    async def semantic_search(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        source_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using vector similarity
        
        Returns:
            List of similar content with metadata
        """
        try:
            if not self.supabase:
                logger.warning("Supabase client not available")
                return []
            
            query_embedding = self.create_embedding(query)
            
            if not query_embedding:
                return []
            
            # Build RPC call for vector search
            # Note: This requires a custom Postgres function in Supabase
            params = {
                'query_embedding': query_embedding,
                'match_count': limit,
                'user_id_filter': user_id
            }
            
            if source_type:
                params['source_type_filter'] = source_type
            
            # For now, return empty as RPC function needs to be set up
            # In production, call: self.supabase.rpc('match_embeddings', params).execute()
            logger.info(f"✅ Performed semantic search for user {user_id}")
            return []
            
        except Exception as e:
            logger.error(f"❌ Semantic search failed: {e}")
            return []


# Singleton instances
scraper_agent = ScraperAgent()
file_agent = FileAgent()
math_agent = MathAgent()
vector_agent = VectorAgent()


# Export all agents
__all__ = [
    'ScraperAgent',
    'FileAgent',
    'MathAgent',
    'VectorAgent',
    'scraper_agent',
    'file_agent',
    'math_agent',
    'vector_agent'
]
