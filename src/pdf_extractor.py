"""
PDF extraction module for automotive manuals and technical documents.
"""

import PyPDF2
import pdfplumber
from typing import List, Dict, Any, Optional, Tuple
import base64
import io
from PIL import Image
import logging
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extracts text, images, and tables from PDF documents."""
    
    def __init__(self, max_pages: int = 100, extract_images: bool = True, extract_tables: bool = True):
        """
        Initialize PDF extractor.
        
        Args:
            max_pages: Maximum number of pages to process
            extract_images: Whether to extract images from PDF
            extract_tables: Whether to extract tables from PDF
        """
        self.max_pages = max_pages
        self.extract_images = extract_images
        self.extract_tables = extract_tables
        
    def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Extract data from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing extracted text, images, tables, and metadata
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"PDF file not found: {file_path}")
                
            logger.info(f"Extracting data from PDF: {file_path}")
            
            # Extract text using pdfplumber (better for complex layouts)
            text_content = self._extract_text_pdfplumber(file_path)
            
            # Extract images if enabled
            images = []
            if self.extract_images:
                images = self._extract_images_pdfplumber(file_path)
                
            # Extract tables if enabled
            tables = []
            if self.extract_tables:
                tables = self._extract_tables_pdfplumber(file_path)
            
            # Get file metadata
            metadata = self._get_file_metadata(file_path)
            
            return {
                "text_content": text_content,
                "images": images,
                "tables": tables,
                "metadata": metadata,
                "extraction_timestamp": datetime.now().isoformat(),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error extracting PDF {file_path}: {str(e)}")
            return {
                "text_content": "",
                "images": [],
                "tables": [],
                "metadata": {},
                "extraction_timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e)
            }
    
    def _extract_text_pdfplumber(self, file_path: Path) -> str:
        """Extract text using pdfplumber (better for complex layouts)."""
        text_content = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                total_pages = min(len(pdf.pages), self.max_pages)
                
                for page_num in range(total_pages):
                    page = pdf.pages[page_num]
                    page_text = page.extract_text()
                    
                    if page_text:
                        text_content.append(f"--- Page {page_num + 1} ---\n{page_text}\n")
                        
        except Exception as e:
            logger.warning(f"Error extracting text with pdfplumber: {str(e)}")
            # Fallback to PyPDF2
            text_content = self._extract_text_pypdf2(file_path)
            
        return "\n".join(text_content)
    
    def _extract_text_pypdf2(self, file_path: Path) -> str:
        """Fallback text extraction using PyPDF2."""
        text_content = []
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = min(len(pdf_reader.pages), self.max_pages)
                
                for page_num in range(total_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    
                    if page_text:
                        text_content.append(f"--- Page {page_num + 1} ---\n{page_text}\n")
                        
        except Exception as e:
            logger.error(f"Error extracting text with PyPDF2: {str(e)}")
            
        return "\n".join(text_content)
    
    def _extract_images_pdfplumber(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract images from PDF using pdfplumber."""
        images = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                total_pages = min(len(pdf.pages), self.max_pages)
                
                for page_num in range(total_pages):
                    page = pdf.pages[page_num]
                    
                    # Extract images from the page
                    page_images = page.images
                    
                    for img_idx, img in enumerate(page_images):
                        try:
                            # Get image data
                            img_data = page.within_bbox(img).to_image()
                            
                            # Convert to base64
                            img_buffer = io.BytesIO()
                            img_data.original.save(img_buffer, format='PNG')
                            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
                            
                            images.append({
                                "page_number": page_num + 1,
                                "image_index": img_idx,
                                "bbox": img,
                                "base64_data": img_base64,
                                "format": "PNG"
                            })
                            
                        except Exception as e:
                            logger.warning(f"Error extracting image {img_idx} from page {page_num + 1}: {str(e)}")
                            
        except Exception as e:
            logger.error(f"Error extracting images: {str(e)}")
            
        return images
    
    def _extract_tables_pdfplumber(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract tables from PDF using pdfplumber."""
        tables = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                total_pages = min(len(pdf.pages), self.max_pages)
                
                for page_num in range(total_pages):
                    page = pdf.pages[page_num]
                    
                    # Extract tables from the page
                    page_tables = page.extract_tables()
                    
                    for table_idx, table in enumerate(page_tables):
                        if table:  # Check if table is not empty
                            tables.append({
                                "page_number": page_num + 1,
                                "table_index": table_idx,
                                "data": table,
                                "rows": len(table),
                                "columns": len(table[0]) if table else 0
                            })
                            
        except Exception as e:
            logger.error(f"Error extracting tables: {str(e)}")
            
        return tables
    
    def _get_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Get metadata about the PDF file."""
        try:
            metadata = {
                "file_name": file_path.name,
                "file_size_bytes": file_path.stat().st_size,
                "file_size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
                "file_extension": file_path.suffix,
                "creation_time": datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                "modification_time": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            }
            
            # Try to get PDF metadata
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    if pdf_reader.metadata:
                        metadata.update({
                            "pdf_title": pdf_reader.metadata.get('/Title', ''),
                            "pdf_author": pdf_reader.metadata.get('/Author', ''),
                            "pdf_subject": pdf_reader.metadata.get('/Subject', ''),
                            "pdf_creator": pdf_reader.metadata.get('/Creator', ''),
                            "pdf_producer": pdf_reader.metadata.get('/Producer', ''),
                            "pdf_creation_date": str(pdf_reader.metadata.get('/CreationDate', '')),
                            "pdf_modification_date": str(pdf_reader.metadata.get('/ModDate', ''))
                        })
                    metadata["total_pages"] = len(pdf_reader.pages)
                    
            except Exception as e:
                logger.warning(f"Could not extract PDF metadata: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error getting file metadata: {str(e)}")
            metadata = {}
            
        return metadata
    
    def extract_specific_sections(self, text_content: str, keywords: List[str]) -> Dict[str, str]:
        """
        Extract specific sections from text based on keywords.
        Useful for finding relevant sections in automotive manuals.
        
        Args:
            text_content: Full text content from PDF
            keywords: List of keywords to search for sections
            
        Returns:
            Dictionary mapping keywords to extracted sections
        """
        sections = {}
        lines = text_content.split('\n')
        
        for keyword in keywords:
            sections[keyword] = []
            current_section = []
            in_section = False
            
            for line in lines:
                line_lower = line.lower()
                
                # Check if this line starts a section with our keyword
                if keyword.lower() in line_lower and any(
                    line_lower.startswith(word) for word in ['section', 'chapter', 'part', 'procedure']
                ):
                    if current_section:
                        sections[keyword].append('\n'.join(current_section))
                    current_section = [line]
                    in_section = True
                    
                elif in_section:
                    # Check if we've reached the next section
                    if any(word in line_lower for word in ['section', 'chapter', 'part', 'procedure']) and keyword.lower() not in line_lower:
                        sections[keyword].append('\n'.join(current_section))
                        current_section = []
                        in_section = False
                    else:
                        current_section.append(line)
                        
            # Add the last section if we were in one
            if current_section:
                sections[keyword].append('\n'.join(current_section))
                
        return sections


def test_pdf_extraction():
    """Test function for PDF extraction."""
    extractor = PDFExtractor()
    
    # Test with a sample PDF (you would replace this with an actual PDF path)
    test_file = "sample_manual.pdf"
    
    if Path(test_file).exists():
        result = extractor.extract_from_file(test_file)
        print(f"Extraction successful: {result['success']}")
        print(f"Text length: {len(result['text_content'])} characters")
        print(f"Images found: {len(result['images'])}")
        print(f"Tables found: {len(result['tables'])}")
        print(f"Metadata: {result['metadata']}")
    else:
        print(f"Test file {test_file} not found. Please provide a valid PDF file path.")


if __name__ == "__main__":
    test_pdf_extraction()
