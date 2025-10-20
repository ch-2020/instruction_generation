"""
OpenAI API integration module for disassembly instruction generation.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
from abc import ABC, abstractmethod
from datetime import datetime
import asyncio
import aiohttp
import httpx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI import
try:
    import openai
except ImportError:
    openai = None

logger = logging.getLogger(__name__)


class OpenAIProvider:
    """OpenAI GPT provider implementation."""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", **kwargs):
        self.api_key = api_key
        self.model = model
        self.max_tokens = kwargs.get('max_tokens', 4000)
        self.temperature = kwargs.get('temperature', 0.1)
        
        if openai is None:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")
        
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            http_client=httpx.AsyncClient()
        )
    
    async def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate response using OpenAI API."""
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return {
                "success": True,
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": self.model,
                "provider": "openai"
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "provider": "openai"
            }
    
    def get_provider_name(self) -> str:
        return "OpenAI"


class LLMManager:
    """Manager class for handling OpenAI API."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize LLM manager with configuration.
        
        Args:
            config_file: Path to configuration file
        """
        self.provider = None
        self.config = self._load_config(config_file)
        self._initialize_provider()
    
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or environment variables."""
        config = {
            "default_provider": "openai",
            "providers": {
                "openai": {
                    "api_key_env": "OPENAI_API_KEY",
                    "default_model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                    "max_tokens": int(os.getenv("MAX_TOKENS", "4000")),
                    "temperature": float(os.getenv("TEMPERATURE", "0.1"))
                }
            }
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
            except Exception as e:
                logger.warning(f"Could not load config file {config_file}: {str(e)}")
        
        return config
    
    def _initialize_provider(self):
        """Initialize OpenAI provider."""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("No OpenAI API key found")
                return
            
            provider_config = self.config["providers"]["openai"]
            self.provider = OpenAIProvider(
                api_key=api_key,
                model=provider_config["default_model"],
                max_tokens=provider_config["max_tokens"],
                temperature=provider_config["temperature"]
            )
                    
        except Exception as e:
            logger.error(f"Error initializing OpenAI provider: {str(e)}")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        if self.provider:
            return ["openai"]
        return []
    
    def get_provider(self) -> Optional[OpenAIProvider]:
        """Get the OpenAI provider."""
        return self.provider
    
    async def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a response using OpenAI.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            
        Returns:
            Dictionary containing the response and metadata
        """
        if not self.provider:
            return {
                "success": False,
                "error": "No OpenAI provider available. Please check your API key.",
                "provider": "openai"
            }
        
        try:
            start_time = datetime.now()
            response = await self.provider.generate_response(prompt, system_prompt)
            end_time = datetime.now()
            
            response["processing_time_seconds"] = (end_time - start_time).total_seconds()
            response["timestamp"] = end_time.isoformat()
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "provider": "openai",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the OpenAI provider."""
        if not self.provider:
            return {
                "available": False,
                "error": "OpenAI provider not available"
            }
        
        return {
            "available": True,
            "name": self.provider.get_provider_name(),
            "model": self.provider.model,
            "max_tokens": self.provider.max_tokens,
            "temperature": self.provider.temperature
        }


# Convenience functions for easy usage
async def generate_disassembly_instructions(data_content: str, component_type: str = "Auto-detect from document", custom_component: str = None) -> Dict[str, Any]:
    """
    Generate disassembly instructions from extracted data.
    
    Args:
        data_content: Extracted text content from PDFs/websites
        component_type: Type of component to disassemble
        custom_component: Custom component name if component_type is "Other"
        
    Returns:
        Dictionary containing generated instructions
    """
    system_prompt = """You are an expert automotive technician and technical writer. Your task is to analyze automotive documentation and generate detailed, step-by-step disassembly instructions.

Please generate comprehensive disassembly instructions in JSON format that include:
1. Step-by-step procedures with clear descriptions
2. Required tools and equipment
3. Safety warnings and precautions
4. Time estimates for each step
5. Difficulty ratings (beginner, intermediate, advanced, expert)
6. Part identification and handling instructions

Focus on automotive parts and systems. Be thorough, accurate, and safety-conscious."""

    # Add component-specific instructions
    if component_type != "Auto-detect from document":
        if component_type == "Other" and custom_component:
            target_component = custom_component
        else:
            target_component = component_type
        
        system_prompt += f"\n\nIMPORTANT: Focus specifically on disassembling {target_component}. Extract and generate instructions only for this component type. If the document contains information about multiple components, prioritize the {target_component} disassembly procedures."

    user_prompt = f"""Please analyze the following automotive documentation and generate detailed disassembly instructions:

{data_content}

Generate the instructions in a structured JSON format with the following structure:
{{
    "product_info": {{
        "name": "Product name",
        "type": "Product type",
        "model": "Model number if available"
    }},
    "general_safety_requirements": ["list", "of", "safety", "requirements"],
    "general_tools_required": ["list", "of", "required", "tools"],
    "difficulty_overview": "overall difficulty level",
    "estimated_total_time_minutes": estimated_time_in_minutes,
    "steps": [
        {{
            "step_number": 1,
            "title": "Step title",
            "description": "Detailed step description",
            "tools_required": ["tool1", "tool2"],
            "safety_warnings": ["warning1", "warning2"],
            "time_estimate_minutes": estimated_minutes,
            "time_category": "quick|moderate|extensive|complex",
            "difficulty_level": "beginner|intermediate|advanced|expert",
            "part_identification": "Description of parts involved",
            "special_instructions": "Any special notes"
        }}
    ],
    "additional_notes": "Any additional important notes",
    "warnings": ["Important warnings"]
}}"""

    manager = LLMManager()
    return await manager.generate_response(user_prompt, system_prompt)


def test_llm_integration():
    """Test function for LLM integration."""
    async def run_test():
        manager = LLMManager()
        
        print(f"Available providers: {manager.get_available_providers()}")
        
        if manager.get_available_providers():
            test_prompt = "Generate a simple 3-step disassembly instruction for removing a car door panel."
            response = await manager.generate_response(test_prompt)
            
            print(f"Response successful: {response['success']}")
            if response['success']:
                print(f"Content: {response['content'][:200]}...")
                print(f"Provider: {response['provider']}")
                print(f"Processing time: {response['processing_time_seconds']:.2f} seconds")
            else:
                print(f"Error: {response['error']}")
        else:
            print("No LLM providers available. Please check your API keys.")
    
    asyncio.run(run_test())


if __name__ == "__main__":
    test_llm_integration()
