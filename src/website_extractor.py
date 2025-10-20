"""
Website extraction module for automotive parts websites and technical documentation.
"""

import requests
from bs4 import BeautifulSoup
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import logging
from urllib.parse import urljoin, urlparse
import time
from datetime import datetime
import json
import re

logger = logging.getLogger(__name__)


class WebsiteExtractor:
    """Extracts data from automotive websites and technical documentation."""
    
    def __init__(self, timeout: int = 30, max_depth: int = 3, user_agent: str = "DisassemblyInstructionGenerator/1.0"):
        """
        Initialize website extractor.
        
        Args:
            timeout: Request timeout in seconds
            max_depth: Maximum depth for following links
            user_agent: User agent string for requests
        """
        self.timeout = timeout
        self.max_depth = max_depth
        self.user_agent = user_agent
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
    def extract_from_url(self, url: str, follow_links: bool = True) -> Dict[str, Any]:
        """
        Extract data from a website URL.
        
        Args:
            url: URL to extract data from
            follow_links: Whether to follow relevant links
            
        Returns:
            Dictionary containing extracted text, images, links, and metadata
        """
        try:
            logger.info(f"Extracting data from URL: {url}")
            
            # Validate URL
            if not self._is_valid_url(url):
                raise ValueError(f"Invalid URL: {url}")
            
            # Extract main page content
            main_content = self._extract_page_content(url)
            
            # Follow relevant links if enabled
            related_content = []
            if follow_links and main_content['success']:
                related_content = self._extract_related_pages(url, main_content.get('links', []))
            
            # Combine all content
            all_text = main_content.get('text_content', '')
            all_images = main_content.get('images', [])
            all_links = main_content.get('links', [])
            
            for content in related_content:
                all_text += '\n\n' + content.get('text_content', '')
                all_images.extend(content.get('images', []))
                all_links.extend(content.get('links', []))
            
            return {
                "text_content": all_text,
                "images": all_images,
                "links": all_links,
                "main_url": url,
                "extracted_urls": [url] + [c.get('url', '') for c in related_content],
                "metadata": main_content.get('metadata', {}),
                "extraction_timestamp": datetime.now().isoformat(),
                "success": main_content['success']
            }
            
        except Exception as e:
            logger.error(f"Error extracting from URL {url}: {str(e)}")
            return {
                "text_content": "",
                "images": [],
                "links": [],
                "main_url": url,
                "extracted_urls": [],
                "metadata": {},
                "extraction_timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e)
            }
    
    def _extract_page_content(self, url: str) -> Dict[str, Any]:
        """Extract content from a single page."""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract text content
            text_content = self._extract_text_content(soup)
            
            # Extract images
            images = self._extract_images(soup, url)
            
            # Extract links
            links = self._extract_links(soup, url)
            
            # Extract metadata
            metadata = self._extract_metadata(soup, response)
            
            return {
                "text_content": text_content,
                "images": images,
                "links": links,
                "metadata": metadata,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error extracting page content from {url}: {str(e)}")
            return {
                "text_content": "",
                "images": [],
                "links": [],
                "metadata": {},
                "success": False,
                "error": str(e)
            }
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract relevant text content from HTML."""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Focus on main content areas
        main_content_selectors = [
            'main', 'article', '.content', '.main-content', 
            '.post-content', '.entry-content', '#content',
            '.product-description', '.specifications', '.manual-content'
        ]
        
        main_content = ""
        for selector in main_content_selectors:
            elements = soup.select(selector)
            for element in elements:
                main_content += element.get_text(separator='\n', strip=True) + '\n\n'
        
        # If no main content found, extract from body
        if not main_content.strip():
            body = soup.find('body')
            if body:
                main_content = body.get_text(separator='\n', strip=True)
        
        # Clean up text
        main_content = self._clean_text(main_content)
        
        return main_content
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """Extract images from the page."""
        images = []
        
        img_tags = soup.find_all('img')
        for img in img_tags:
            try:
                src = img.get('src')
                if src:
                    # Convert relative URLs to absolute
                    img_url = urljoin(base_url, src)
                    
                    # Get image metadata
                    alt_text = img.get('alt', '')
                    title = img.get('title', '')
                    
                    images.append({
                        "url": img_url,
                        "alt_text": alt_text,
                        "title": title,
                        "width": img.get('width'),
                        "height": img.get('height')
                    })
                    
            except Exception as e:
                logger.warning(f"Error extracting image: {str(e)}")
                
        return images
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """Extract relevant links from the page."""
        links = []
        
        # Look for links that might contain relevant content
        relevant_keywords = [
            'manual', 'instruction', 'guide', 'specification', 'technical',
            'disassembly', 'assembly', 'repair', 'service', 'parts',
            'documentation', 'download', 'pdf', 'diagram', 'schematic'
        ]
        
        link_tags = soup.find_all('a', href=True)
        for link in link_tags:
            try:
                href = link.get('href')
                if href:
                    # Convert relative URLs to absolute
                    link_url = urljoin(base_url, href)
                    
                    # Check if link text or URL contains relevant keywords
                    link_text = link.get_text(strip=True).lower()
                    url_lower = link_url.lower()
                    
                    is_relevant = any(keyword in link_text or keyword in url_lower 
                                    for keyword in relevant_keywords)
                    
                    if is_relevant:
                        links.append({
                            "url": link_url,
                            "text": link.get_text(strip=True),
                            "title": link.get('title', ''),
                            "is_relevant": True
                        })
                    else:
                        links.append({
                            "url": link_url,
                            "text": link.get_text(strip=True),
                            "title": link.get('title', ''),
                            "is_relevant": False
                        })
                        
            except Exception as e:
                logger.warning(f"Error extracting link: {str(e)}")
                
        return links
    
    def _extract_metadata(self, soup: BeautifulSoup, response: requests.Response) -> Dict[str, Any]:
        """Extract metadata from the page."""
        metadata = {
            "url": response.url,
            "status_code": response.status_code,
            "content_type": response.headers.get('content-type', ''),
            "content_length": len(response.content),
            "title": "",
            "description": "",
            "keywords": "",
            "author": "",
            "last_modified": response.headers.get('last-modified', ''),
            "extraction_timestamp": datetime.now().isoformat()
        }
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            metadata["title"] = title_tag.get_text(strip=True)
        
        # Extract meta tags
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name', '').lower()
            content = meta.get('content', '')
            
            if name == 'description':
                metadata["description"] = content
            elif name == 'keywords':
                metadata["keywords"] = content
            elif name == 'author':
                metadata["author"] = content
            elif name == 'robots':
                metadata["robots"] = content
        
        return metadata
    
    def _extract_related_pages(self, base_url: str, links: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract content from related pages."""
        related_content = []
        
        # Filter for relevant links from the same domain
        base_domain = urlparse(base_url).netloc
        relevant_links = [
            link for link in links 
            if link.get('is_relevant', False) and urlparse(link['url']).netloc == base_domain
        ]
        
        # Limit to first few relevant links to avoid too much content
        relevant_links = relevant_links[:5]
        
        for link in relevant_links:
            try:
                logger.info(f"Extracting related page: {link['url']}")
                content = self._extract_page_content(link['url'])
                if content['success']:
                    content['url'] = link['url']
                    related_content.append(content)
                    
                # Add small delay to be respectful
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Error extracting related page {link['url']}: {str(e)}")
                
        return related_content
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common web artifacts
        text = re.sub(r'(Cookie|Privacy|Terms|Copyright).*?\.', '', text, flags=re.IGNORECASE)
        
        # Remove email addresses and phone numbers (optional)
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '', text)
        
        return text.strip()
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def extract_specific_sections(self, text_content: str, keywords: List[str]) -> Dict[str, str]:
        """
        Extract specific sections from text based on keywords.
        Useful for finding relevant sections in automotive documentation.
        
        Args:
            text_content: Full text content from website
            keywords: List of keywords to search for sections
            
        Returns:
            Dictionary mapping keywords to extracted sections
        """
        sections = {}
        paragraphs = text_content.split('\n\n')
        
        for keyword in keywords:
            sections[keyword] = []
            
            for paragraph in paragraphs:
                paragraph_lower = paragraph.lower()
                
                # Check if paragraph contains the keyword
                if keyword.lower() in paragraph_lower:
                    # Check if it's a section header or relevant content
                    if any(word in paragraph_lower for word in ['section', 'chapter', 'part', 'procedure', 'step', 'instruction']):
                        sections[keyword].append(paragraph)
                    elif len(paragraph) > 100:  # Substantial content
                        sections[keyword].append(paragraph)
                        
        return sections


def test_website_extraction():
    """Test function for website extraction."""
    extractor = WebsiteExtractor()
    
    # Test with a sample automotive website
    test_url = "https://example-automotive-parts.com/manual"
    
    try:
        result = extractor.extract_from_url(test_url)
        print(f"Extraction successful: {result['success']}")
        print(f"Text length: {len(result['text_content'])} characters")
        print(f"Images found: {len(result['images'])}")
        print(f"Links found: {len(result['links'])}")
        print(f"Extracted URLs: {len(result['extracted_urls'])}")
        print(f"Metadata: {result['metadata']}")
    except Exception as e:
        print(f"Test failed: {str(e)}")
        print("Please provide a valid automotive website URL for testing.")


if __name__ == "__main__":
    test_website_extraction()
