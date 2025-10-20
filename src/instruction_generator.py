"""
Core instruction generation logic for automotive disassembly.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import re
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .llm_manager import LLMManager, generate_disassembly_instructions
from .pdf_extractor import PDFExtractor
from .website_extractor import WebsiteExtractor

logger = logging.getLogger(__name__)


class DisassemblyInstructionGenerator:
    """Main class for generating disassembly instructions from various data sources."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the instruction generator.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.llm_manager = LLMManager(config_file)
        self.pdf_extractor = PDFExtractor()
        self.website_extractor = WebsiteExtractor()
        
        # Load configuration
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration settings."""
        default_config = {
            "include_safety_warnings": True,
            "include_tool_requirements": True,
            "include_time_estimates": True,
            "include_difficulty_ratings": True,
            "include_part_identification": True,
            "max_steps": 50,
            "detail_level": "comprehensive",
            "automotive_keywords": [
                "disassembly", "removal", "detach", "unscrew", "unbolt",
                "disconnect", "separate", "extract", "remove", "take apart"
            ]
        }
        
        if self.config_file and Path(self.config_file).exists():
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    default_config.update(file_config)
            except Exception as e:
                logger.warning(f"Could not load config file: {str(e)}")
        
        return default_config
    
    async def generate_instructions_from_pdf(self, pdf_path: str, 
                                           extract_images: bool = True,
                                           extract_tables: bool = True,
                                           component_type: str = "Auto-detect from document",
                                           custom_component: str = None) -> Dict[str, Any]:
        """
        Generate disassembly instructions from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            extract_images: Whether to extract images from PDF
            extract_tables: Whether to extract tables from PDF
            component_type: Type of component to disassemble
            custom_component: Custom component name if component_type is "Other"
            
        Returns:
            Dictionary containing generated instructions and metadata
        """
        try:
            logger.info(f"Generating instructions from PDF: {pdf_path}")
            
            # Extract data from PDF
            pdf_data = self.pdf_extractor.extract_from_file(pdf_path)
            
            if not pdf_data['success']:
                return {
                    "success": False,
                    "error": f"Failed to extract PDF data: {pdf_data.get('error', 'Unknown error')}",
                    "source": "pdf",
                    "source_path": pdf_path
                }
            
            # Prepare content for LLM
            content = self._prepare_content_for_llm(pdf_data)
            
            # Generate instructions using LLM
            llm_response = await generate_disassembly_instructions(content, component_type, custom_component)
            
            if not llm_response['success']:
                return {
                    "success": False,
                    "error": f"LLM generation failed: {llm_response.get('error', 'Unknown error')}",
                    "source": "pdf",
                    "source_path": pdf_path
                }
            
            # Parse and validate the generated instructions
            instructions = self._parse_llm_response(llm_response['content'])
            
            # Add metadata
            instructions['metadata'] = {
                "source_type": "pdf",
                "source_path": pdf_path,
                "extraction_metadata": pdf_data['metadata'],
                "llm_provider": llm_response.get('provider', 'unknown'),
                "llm_model": llm_response.get('model', 'unknown'),
                "generation_timestamp": datetime.now().isoformat(),
                "processing_time_seconds": llm_response.get('processing_time_seconds', 0),
                "tokens_used": llm_response.get('usage', {}).get('total_tokens', 0)
            }
            
            return {
                "success": True,
                "instructions": instructions,
                "source": "pdf",
                "source_path": pdf_path,
                "extraction_stats": {
                    "text_length": len(pdf_data['text_content']),
                    "images_extracted": len(pdf_data['images']),
                    "tables_extracted": len(pdf_data['tables'])
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating instructions from PDF {pdf_path}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "source": "pdf",
                "source_path": pdf_path
            }
    
    async def generate_instructions_from_website(self, url: str,
                                                follow_links: bool = True,
                                                component_type: str = "Auto-detect from document",
                                                custom_component: str = None) -> Dict[str, Any]:
        """
        Generate disassembly instructions from a website.
        
        Args:
            url: Website URL to extract from
            follow_links: Whether to follow relevant links
            component_type: Type of component to disassemble
            custom_component: Custom component name if component_type is "Other"
            
        Returns:
            Dictionary containing generated instructions and metadata
        """
        try:
            logger.info(f"Generating instructions from website: {url}")
            
            # Extract data from website
            website_data = self.website_extractor.extract_from_url(url, follow_links)
            
            if not website_data['success']:
                return {
                    "success": False,
                    "error": f"Failed to extract website data: {website_data.get('error', 'Unknown error')}",
                    "source": "website",
                    "source_url": url
                }
            
            # Prepare content for LLM
            content = self._prepare_content_for_llm(website_data)
            
            # Generate instructions using LLM
            llm_response = await generate_disassembly_instructions(content, component_type, custom_component)
            
            if not llm_response['success']:
                return {
                    "success": False,
                    "error": f"LLM generation failed: {llm_response.get('error', 'Unknown error')}",
                    "source": "website",
                    "source_url": url
                }
            
            # Parse and validate the generated instructions
            instructions = self._parse_llm_response(llm_response['content'])
            
            # Add metadata
            instructions['metadata'] = {
                "source_type": "website",
                "source_url": url,
                "extraction_metadata": website_data['metadata'],
                "extracted_urls": website_data['extracted_urls'],
                "llm_provider": llm_response.get('provider', 'unknown'),
                "llm_model": llm_response.get('model', 'unknown'),
                "generation_timestamp": datetime.now().isoformat(),
                "processing_time_seconds": llm_response.get('processing_time_seconds', 0),
                "tokens_used": llm_response.get('usage', {}).get('total_tokens', 0)
            }
            
            return {
                "success": True,
                "instructions": instructions,
                "source": "website",
                "source_url": url,
                "extraction_stats": {
                    "text_length": len(website_data['text_content']),
                    "images_extracted": len(website_data['images']),
                    "links_found": len(website_data['links']),
                    "pages_extracted": len(website_data['extracted_urls'])
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating instructions from website {url}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "source": "website",
                "source_url": url
            }
    
    async def generate_instructions_from_multiple_sources(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate instructions from multiple data sources.
        
        Args:
            sources: List of source dictionaries with 'type' and 'path'/'url' keys
            
        Returns:
            Dictionary containing combined instructions
        """
        try:
            logger.info(f"Generating instructions from {len(sources)} sources")
            
            all_content = []
            extraction_stats = []
            
            # Extract data from all sources
            for source in sources:
                source_type = source.get('type', '').lower()
                source_path = source.get('path') or source.get('url')
                
                if source_type == 'pdf':
                    pdf_data = self.pdf_extractor.extract_from_file(source_path)
                    if pdf_data['success']:
                        all_content.append(f"--- PDF: {source_path} ---\n{pdf_data['text_content']}")
                        extraction_stats.append({
                            "type": "pdf",
                            "path": source_path,
                            "text_length": len(pdf_data['text_content']),
                            "images": len(pdf_data['images']),
                            "tables": len(pdf_data['tables'])
                        })
                
                elif source_type == 'website':
                    website_data = self.website_extractor.extract_from_url(source_path)
                    if website_data['success']:
                        all_content.append(f"--- Website: {source_path} ---\n{website_data['text_content']}")
                        extraction_stats.append({
                            "type": "website",
                            "url": source_path,
                            "text_length": len(website_data['text_content']),
                            "images": len(website_data['images']),
                            "links": len(website_data['links'])
                        })
            
            if not all_content:
                return {
                    "success": False,
                    "error": "No valid content extracted from any source",
                    "sources": sources
                }
            
            # Combine all content
            combined_content = "\n\n".join(all_content)
            
            # Generate instructions using LLM
            llm_response = await generate_disassembly_instructions(combined_content, llm_provider)
            
            if not llm_response['success']:
                return {
                    "success": False,
                    "error": f"LLM generation failed: {llm_response.get('error', 'Unknown error')}",
                    "sources": sources
                }
            
            # Parse and validate the generated instructions
            instructions = self._parse_llm_response(llm_response['content'])
            
            # Add metadata
            instructions['metadata'] = {
                "source_type": "multiple",
                "sources": sources,
                "extraction_stats": extraction_stats,
                "llm_provider": llm_response.get('provider', 'unknown'),
                "llm_model": llm_response.get('model', 'unknown'),
                "generation_timestamp": datetime.now().isoformat(),
                "processing_time_seconds": llm_response.get('processing_time_seconds', 0),
                "tokens_used": llm_response.get('usage', {}).get('total_tokens', 0)
            }
            
            return {
                "success": True,
                "instructions": instructions,
                "sources": sources,
                "extraction_stats": extraction_stats
            }
            
        except Exception as e:
            logger.error(f"Error generating instructions from multiple sources: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "sources": sources
            }
    
    def _prepare_content_for_llm(self, extracted_data: Dict[str, Any]) -> str:
        """Prepare extracted data for LLM processing."""
        content_parts = []
        
        # Add main text content
        if extracted_data.get('text_content'):
            content_parts.append(f"Main Content:\n{extracted_data['text_content']}")
        
        # Add table information
        if extracted_data.get('tables'):
            content_parts.append(f"\nTables Found ({len(extracted_data['tables'])}):")
            for i, table in enumerate(extracted_data['tables'][:5]):  # Limit to first 5 tables
                content_parts.append(f"\nTable {i+1} (Page {table.get('page_number', 'Unknown')}):")
                if table.get('data'):
                    # Convert table data to readable format
                    table_text = "\n".join(["\t".join(str(cell) for cell in row) for row in table['data'][:10]])  # Limit rows
                    content_parts.append(table_text)
        
        # Add image information
        if extracted_data.get('images'):
            content_parts.append(f"\nImages Found ({len(extracted_data['images'])}):")
            for i, img in enumerate(extracted_data['images'][:5]):  # Limit to first 5 images
                content_parts.append(f"Image {i+1}: {img.get('alt_text', 'No description')}")
        
        return "\n".join(content_parts)
    
    def _parse_llm_response(self, llm_content: str) -> Dict[str, Any]:
        """Parse and validate LLM response."""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', llm_content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                instructions = json.loads(json_str)
                
                # Validate and enhance the instructions
                instructions = self._validate_and_enhance_instructions(instructions)
                return instructions
            else:
                # If no JSON found, create a structured response
                return self._create_fallback_instructions(llm_content)
                
        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse JSON from LLM response: {str(e)}")
            return self._create_fallback_instructions(llm_content)
    
    def _validate_and_enhance_instructions(self, instructions: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the generated instructions."""
        # Ensure required fields exist
        if 'product_info' not in instructions:
            instructions['product_info'] = {"name": "Unknown Product", "type": "Automotive Part"}
        
        if 'steps' not in instructions:
            instructions['steps'] = []
        
        # Validate and enhance steps
        for i, step in enumerate(instructions['steps']):
            if 'step_number' not in step:
                step['step_number'] = i + 1
            
            if 'difficulty_level' not in step:
                step['difficulty_level'] = 'intermediate'
            
            if 'tools_required' not in step:
                step['tools_required'] = []
            
            if 'safety_warnings' not in step:
                step['safety_warnings'] = []
        
        # Add general fields if missing
        if 'general_safety_requirements' not in instructions:
            instructions['general_safety_requirements'] = [
                "eye_protection", "gloves", "proper_lighting", "ventilation"
            ]
        
        if 'general_tools_required' not in instructions:
            instructions['general_tools_required'] = [
                "socket_wrench", "screwdriver", "pliers"
            ]
        
        if 'difficulty_overview' not in instructions:
            instructions['difficulty_overview'] = 'intermediate'
        
        return instructions
    
    def _create_fallback_instructions(self, content: str) -> Dict[str, Any]:
        """Create fallback instructions when JSON parsing fails."""
        return {
            "product_info": {
                "name": "Unknown Product",
                "type": "Automotive Part",
                "model": "Unknown"
            },
            "general_safety_requirements": [
                "eye_protection", "gloves", "proper_lighting", "ventilation"
            ],
            "general_tools_required": [
                "socket_wrench", "screwdriver", "pliers"
            ],
            "difficulty_overview": "intermediate",
            "estimated_total_time_minutes": 60,
            "steps": [
                {
                    "step_number": 1,
                    "title": "Review Documentation",
                    "description": "Please review the extracted content and generate proper disassembly instructions.",
                    "tools_required": [],
                    "safety_warnings": ["Review all safety requirements before starting"],
                    "time_estimate_minutes": 10,
                    "time_category": "quick",
                    "difficulty_level": "beginner",
                    "part_identification": "Documentation review",
                    "special_instructions": content[:500] + "..." if len(content) > 500 else content
                }
            ],
            "additional_notes": "This is a fallback response. Please review the extracted content manually.",
            "warnings": ["Manual review required - JSON parsing failed"]
        }
    
    def save_instructions(self, instructions: Dict[str, Any], output_path: str) -> bool:
        """Save generated instructions to a JSON file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(instructions, f, indent=2, ensure_ascii=False)
            logger.info(f"Instructions saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving instructions to {output_path}: {str(e)}")
            return False
    
    def get_available_providers(self) -> List[str]:
        """Get list of available LLM providers."""
        return self.llm_manager.get_available_providers()


def test_instruction_generator():
    """Test function for the instruction generator."""
    import asyncio
    
    async def run_test():
        generator = DisassemblyInstructionGenerator()
        
        print(f"Available LLM providers: {generator.get_available_providers()}")
        
        # Test with sample content
        sample_content = """
        AUTOMOTIVE DOOR PANEL REMOVAL PROCEDURE
        
        Step 1: Remove the door handle trim
        - Use a flat screwdriver to pry off the trim
        - Be careful not to damage the plastic clips
        
        Step 2: Remove the door panel screws
        - Locate the screws around the perimeter
        - Use a Phillips screwdriver to remove them
        
        Step 3: Disconnect electrical connectors
        - Carefully disconnect any wiring harnesses
        - Note the connector positions for reassembly
        """
        
        # This would normally be called with actual file paths
        print("Instruction generator initialized successfully!")
        print("Ready to process PDF files and websites.")
    
    asyncio.run(run_test())


if __name__ == "__main__":
    test_instruction_generator()
