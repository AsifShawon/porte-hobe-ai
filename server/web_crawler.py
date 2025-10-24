# Advanced web crawler using Crawlee for clean data extraction
# pip install ddgs crawlee

import asyncio
import time
import json
import re
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path

from ddgs import DDGS
from crawlee.crawlers import PlaywrightCrawler

# --- Configuration ---
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

def search_duckduckgo(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search DuckDuckGo and return results."""
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
    except Exception as e:
        print(f"[ERROR] Search failed: {e}")
    return results

class WebCrawler:
    """Enhanced web crawler using Crawlee for clean data extraction."""
    
    def __init__(self):
        self.crawled_data = []
        
    async def crawl_handler(self, context):
        """Handler for each crawled page - extracts clean data."""
        request = context.request
        page = context.page
        
        try:
            # Wait for page to load completely
            await page.wait_for_load_state('domcontentloaded', timeout=15000)
            
            # Additional wait for dynamic content
            await page.wait_for_timeout(2000)
            
            # Extract title
            title = await page.title()
            
            # Get page content using multiple extraction strategies
            content_strategies = []
            
            # Strategy 1: Try main content selectors
            try:
                main_content_1 = await page.evaluate("""() => {
                    const mainSelectors = [
                        'main', 'article', '[role="main"]', 
                        '.content', '#content', '.main-content', '#main-content',
                        '.post-content', '.entry-content', '.article-content', 
                        '.story-body', '.article-body', '.post-body'
                    ];
                    
                    for (const selector of mainSelectors) {
                        const element = document.querySelector(selector);
                        if (element && element.innerText && element.innerText.length > 100) {
                            return element.innerText.trim();
                        }
                    }
                    return '';
                }""")
                content_strategies.append(("main_content", main_content_1))
            except Exception as e:
                print(f"Strategy 1 failed: {e}")
            
            # Strategy 2: Get all paragraphs
            try:
                paragraph_content = await page.evaluate("""() => {
                    const paragraphs = Array.from(document.querySelectorAll('p'));
                    const text = paragraphs
                        .map(p => p.innerText ? p.innerText.trim() : '')
                        .filter(text => text.length > 20)
                        .join('\\n\\n');
                    return text;
                }""")
                content_strategies.append(("paragraphs", paragraph_content))
            except Exception as e:
                print(f"Strategy 2 failed: {e}")
            
            # Strategy 3: Body content with noise removal
            try:
                body_content = await page.evaluate("""() => {
                    // Clone body to avoid modifying original
                    const bodyClone = document.body.cloneNode(true);
                    
                    // Remove noise elements
                    const noiseSelectors = [
                        'nav', 'header', 'footer', 'aside', 'form',
                        '.sidebar', '.navigation', '.menu', '.nav',
                        '.ad', '.advertisement', '.ads', '[class*="ad-"]',
                        '.social', '.share', '.comment', '.popup', '.modal',
                        'script', 'style', 'noscript', 'svg',
                        '.cookie', '.newsletter', '.subscription'
                    ];
                    
                    noiseSelectors.forEach(selector => {
                        const elements = bodyClone.querySelectorAll(selector);
                        elements.forEach(el => el.remove());
                    });
                    
                    return bodyClone.innerText ? bodyClone.innerText.trim() : '';
                }""")
                content_strategies.append(("body_filtered", body_content))
            except Exception as e:
                print(f"Strategy 3 failed: {e}")
            
            # Strategy 4: Simple fallback - just get all text
            try:
                simple_content = await page.evaluate("""() => {
                    return document.body.innerText || document.body.textContent || '';
                }""")
                content_strategies.append(("simple_text", simple_content))
            except Exception as e:
                print(f"Strategy 4 failed: {e}")
            
            # Choose the best content (longest meaningful text)
            main_content = ""
            best_strategy = "none"
            for strategy_name, content in content_strategies:
                if content and len(content) > len(main_content):
                    main_content = content
                    best_strategy = strategy_name
            
            # Clean up the selected content
            if main_content:
                # Remove excessive whitespace
                main_content = re.sub(r'\s+', ' ', main_content)
                main_content = re.sub(r'\n\s*\n', '\n\n', main_content)
                main_content = main_content.strip()
            
            # Extract metadata
            try:
                meta_description = await page.evaluate("""() => {
                    const desc = document.querySelector('meta[name="description"]') || 
                               document.querySelector('meta[property="og:description"]');
                    return desc ? desc.content : '';
                }""")
            except Exception:
                meta_description = ""
            
            # Extract headings structure (more robust)
            try:
                headings = await page.evaluate("""() => {
                    const headings = [];
                    const headingElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
                    headingElements.forEach(h => {
                        const text = h.innerText ? h.innerText.trim() : '';
                        if (text && text.length > 2 && text.length < 200) {
                            headings.push({
                                level: h.tagName.toLowerCase(),
                                text: text
                            });
                        }
                    });
                    return headings.slice(0, 10); // Limit to first 10 headings
                }""")
            except Exception:
                headings = []
            
            # Extract meaningful links
            try:
                links = await page.evaluate("""() => {
                    const links = [];
                    const linkElements = document.querySelectorAll('a[href]');
                    linkElements.forEach(a => {
                        const href = a.href;
                        const text = a.innerText ? a.innerText.trim() : '';
                        if (text && text.length > 3 && text.length < 100 && 
                            href && href.startsWith('http') && !href.includes('#')) {
                            links.push({ text, url: href });
                        }
                    });
                    // Remove duplicates and limit
                    const uniqueLinks = links.filter((link, index, self) => 
                        self.findIndex(l => l.url === link.url) === index
                    );
                    return uniqueLinks.slice(0, 8);
                }""")
            except Exception:
                links = []
            
            # Convert to Markdown format
            markdown_content = self.convert_to_markdown(
                title, main_content, headings, links, meta_description
            )
            
            # Store extracted data
            page_data = {
                "title": title or "",
                "url": request.url,
                "meta_description": meta_description,
                "content": main_content,  # Keep original for compatibility
                "markdown": markdown_content,  # New markdown version
                "headings": headings,
                "links": links,
                "word_count": len(main_content.split()) if main_content else 0,
                "extraction_strategy": best_strategy,
                "content_length": len(main_content),
                "extracted_at": datetime.now().isoformat()
            }
            
            self.crawled_data.append(page_data)
            print(f"✓ Extracted {len(main_content)} chars using '{best_strategy}' from: {title[:60]}...")
            
        except Exception as e:
            print(f"[ERROR] Failed to extract from {request.url}: {e}")
            # Store minimal data for failed extractions
            self.crawled_data.append({
                "title": await page.title() if page else "",
                "url": request.url,
                "meta_description": "",
                "content": "",
                "headings": [],
                "links": [],
                "word_count": 0,
                "content_length": 0,
                "extraction_strategy": "failed",
                "extracted_at": datetime.now().isoformat(),
                "error": str(e)
            })

    def convert_to_markdown(self, title: str, content: str, headings: list, links: list, meta_description: str) -> str:
        """Convert extracted content to well-formatted Markdown."""
        markdown_lines = []
        
        # Add title
        if title:
            markdown_lines.append(f"# {title}")
            markdown_lines.append("")
        
        # Add meta description as quote
        if meta_description:
            markdown_lines.append(f"> {meta_description}")
            markdown_lines.append("")
        
        # Process content with headings
        if content and headings:
            # Split content into sections based on headings
            content_sections = self.split_content_by_headings(content, headings)
            for section in content_sections:
                markdown_lines.extend(section)
                markdown_lines.append("")
        else:
            # If no headings, just add content as paragraphs
            if content:
                paragraphs = content.split('\n\n')
                for para in paragraphs:
                    para = para.strip()
                    if para and len(para) > 20:  # Filter out very short lines
                        markdown_lines.append(para)
                        markdown_lines.append("")
        
        # Add links section if any meaningful links exist
        meaningful_links = [link for link in links if link.get('text') and len(link.get('text', '')) > 5]
        if meaningful_links:
            markdown_lines.append("## Related Links")
            markdown_lines.append("")
            for link in meaningful_links[:8]:  # Limit to 8 links
                link_text = link.get('text', '').strip()
                link_url = link.get('url', '').strip()
                if link_text and link_url:
                    markdown_lines.append(f"- [{link_text}]({link_url})")
            markdown_lines.append("")
        
        return '\n'.join(markdown_lines).strip()
    
    def split_content_by_headings(self, content: str, headings: list) -> list:
        """Split content into sections based on headings."""
        sections = []
        content_lower = content.lower()
        
        # Sort headings by their position in content
        heading_positions = []
        for heading in headings:
            heading_text = heading.get('text', '').strip()
            if heading_text:
                pos = content_lower.find(heading_text.lower())
                if pos != -1:
                    heading_positions.append({
                        'pos': pos,
                        'text': heading_text,
                        'level': heading.get('level', 'h2')
                    })
        
        heading_positions.sort(key=lambda x: x['pos'])
        
        # Extract content sections
        for i, heading in enumerate(heading_positions):
            section_lines = []
            
            # Add heading with proper markdown level
            level_num = int(heading['level'][1]) if heading['level'][1].isdigit() else 2
            markdown_heading = '#' * min(level_num + 1, 6)  # Offset by 1 since title is h1
            section_lines.append(f"{markdown_heading} {heading['text']}")
            section_lines.append("")
            
            # Find content between this heading and the next
            start_pos = heading['pos'] + len(heading['text'])
            end_pos = heading_positions[i + 1]['pos'] if i + 1 < len(heading_positions) else len(content)
            
            section_content = content[start_pos:end_pos].strip()
            
            # Clean and format the section content
            if section_content:
                # Remove the heading text if it appears at the start
                if section_content.lower().startswith(heading['text'].lower()):
                    section_content = section_content[len(heading['text']):].strip()
                
                # Split into paragraphs and clean
                paragraphs = section_content.split('\n\n')
                for para in paragraphs:
                    para = para.strip()
                    if para and len(para) > 20:  # Filter short lines
                        # Handle code blocks (simple detection)
                        if ('def ' in para or 'import ' in para or 
                            para.count('\n') > 2 and any(keyword in para.lower() for keyword in ['python', 'print(', 'return ', 'if '])):
                            section_lines.append("```python")
                            section_lines.append(para)
                            section_lines.append("```")
                        else:
                            section_lines.append(para)
                        section_lines.append("")
            
            sections.append(section_lines)
        
        return sections

    async def crawl_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Crawl multiple URLs using Crawlee."""
        self.crawled_data = []  # Reset data
        
        # Create crawler with optimized settings
        crawler = PlaywrightCrawler(
            max_requests_per_crawl=len(urls),
            request_handler=self.crawl_handler,
            headless=True,
            browser_type='chromium',
        )
        
        # Add URLs to crawl
        await crawler.add_requests(urls)
        
        # Run the crawler
        await crawler.run()
        
        return self.crawled_data

def save_to_json(data: List[Dict], filename: Optional[str] = None) -> str:
    """Save data to JSON file."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crawl_results_{timestamp}.json"
    
    filepath = Path(filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return str(filepath)

def save_to_markdown(data: List[Dict], filename: Optional[str] = None) -> str:
    """Save crawled data as a combined Markdown file."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crawl_results_{timestamp}.md"
    
    filepath = Path(filename)
    markdown_content = []
    
    # Add header
    markdown_content.append("# Web Crawl Results")
    markdown_content.append(f"\n*Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*")
    markdown_content.append("\n---\n")
    
    for i, result in enumerate(data, 1):
        if result.get('markdown'):
            markdown_content.append(f"\n## Result {i}")
            markdown_content.append(f"\n**URL:** {result.get('url', 'N/A')}")
            markdown_content.append(f"**Word Count:** {result.get('word_count', 0)}")
            markdown_content.append(f"**Extraction Strategy:** {result.get('extraction_strategy', 'unknown')}")
            markdown_content.append("\n" + "="*80 + "\n")
            markdown_content.append(result['markdown'])
            markdown_content.append("\n" + "="*80 + "\n")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(markdown_content))
    
    return str(filepath)

async def search_and_crawl(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
    """Search DuckDuckGo and crawl results with clean extraction."""
    print(f"🔍 Searching for: {query}")
    search_results = search_duckduckgo(query, max_results)
    
    if not search_results:
        print("❌ No search results found")
        return []
    
    print(f"📄 Found {len(search_results)} results")
    
    # Extract URLs
    urls = [result["url"] for result in search_results if result["url"]]
    
    if not urls:
        print("❌ No valid URLs to crawl")
        return []
    
    # Crawl with Crawlee
    crawler = WebCrawler()
    crawled_data = await crawler.crawl_urls(urls)
    
    # Merge search snippets with crawled data
    for i, result in enumerate(search_results):
        if i < len(crawled_data):
            crawled_data[i]["search_snippet"] = result["snippet"]
            crawled_data[i]["search_title"] = result["title"]
    
    return crawled_data

# --- Main execution ---
async def main():
    try:
        query = input("Enter your search query: ").strip()
        if not query:
            print("No query provided")
            return
        
        results = await search_and_crawl(query, max_results=3)
        
        if results:
            # Save to JSON
            json_file = save_to_json(results)
            print(f"\n💾 Results saved to: {json_file}")
            
            # Save to Markdown
            markdown_file = save_to_markdown(results)
            print(f"📝 Markdown saved to: {markdown_file}")
            
            # Show enhanced preview
            print("\n" + "="*70)
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title']}")
                print(f"   🔗 URL: {result['url']}")
                print(f"   📊 Words: {result['word_count']}")
                print(f"   📝 Description: {result['meta_description'][:100]}...")
                
                if result['headings']:
                    print(f"   📋 Headings: {', '.join([h['text'][:30] for h in result['headings'][:3]])}...")
                
                # Show markdown preview instead of raw content
                if result.get('markdown'):
                    markdown_preview = result['markdown'][:400] + "..." if len(result['markdown']) > 400 else result['markdown']
                    print(f"   📄 Markdown Preview:\n{markdown_preview}")
                print()
        else:
            print("❌ No results to save")
            
    except KeyboardInterrupt:
        print("\n🛑 Cancelled by user")

if __name__ == "__main__":
    asyncio.run(main())
