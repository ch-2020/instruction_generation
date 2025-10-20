"""
Data models for the Disassembly Instruction Generator application.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class DifficultyLevel(str, Enum):
    """Difficulty levels for disassembly steps."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class TimeCategory(str, Enum):
    """Time categories for disassembly steps."""
    QUICK = "quick"  # < 5 minutes
    MODERATE = "moderate"  # 5-30 minutes
    EXTENSIVE = "extensive"  # 30-120 minutes
    COMPLEX = "complex"  # > 120 minutes


class ToolType(str, Enum):
    """Common automotive tools."""
    SOCKET_WRENCH = "socket_wrench"
    TORX_DRIVER = "torx_driver"
    PHILLIPS_SCREWDRIVER = "phillips_screwdriver"
    FLAT_SCREWDRIVER = "flat_screwdriver"
    PLIERS = "pliers"
    WIRE_CUTTERS = "wire_cutters"
    HAMMER = "hammer"
    MALLET = "mallet"
    PRY_BAR = "pry_bar"
    SPECIALTY_TOOL = "specialty_tool"


class SafetyRequirement(str, Enum):
    """Safety requirements for disassembly."""
    EYE_PROTECTION = "eye_protection"
    GLOVES = "gloves"
    PROPER_LIGHTING = "proper_lighting"
    VENTILATION = "ventilation"
    FIRE_EXTINGUISHER = "fire_extinguisher"
    FIRST_AID_KIT = "first_aid_kit"


class DataSource(BaseModel):
    """Represents a data source for extraction."""
    source_type: str  # "pdf", "website", "document"
    source_path: str
    extraction_timestamp: datetime
    file_size: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtractedData(BaseModel):
    """Represents extracted data from a source."""
    source: DataSource
    text_content: str
    images: List[str] = Field(default_factory=list)  # Base64 encoded images
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DisassemblyStep(BaseModel):
    """Individual step in the disassembly process."""
    step_number: int
    title: str
    description: str
    tools_required: List[str] = Field(default_factory=list)
    safety_warnings: List[str] = Field(default_factory=list)
    time_estimate_minutes: Optional[int] = None
    time_category: Optional[str] = None
    difficulty_level: str = "intermediate"
    part_identification: Optional[str] = None
    special_instructions: Optional[str] = None
    images: List[str] = Field(default_factory=list)  # Reference to step images


class DisassemblyInstructions(BaseModel):
    """Complete disassembly instructions for a product."""
    product_info: Dict[str, Any] = Field(default_factory=dict)
    extraction_sources: List[DataSource] = Field(default_factory=list)
    generation_timestamp: datetime
    total_steps: int
    estimated_total_time_minutes: Optional[int] = None
    difficulty_overview: str = "intermediate"
    general_safety_requirements: List[str] = Field(default_factory=list)
    general_tools_required: List[str] = Field(default_factory=list)
    steps: List[DisassemblyStep] = Field(default_factory=list)
    additional_notes: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GenerationRequest(BaseModel):
    """Request for generating disassembly instructions."""
    extracted_data: List[ExtractedData]
    llm_provider: str
    model: str
    include_safety_warnings: bool = True
    include_tool_requirements: bool = True
    include_time_estimates: bool = True
    include_difficulty_ratings: bool = True
    detail_level: str = "comprehensive"
    max_steps: int = 50


class GenerationResponse(BaseModel):
    """Response from instruction generation."""
    success: bool
    instructions: Optional[DisassemblyInstructions] = None
    error_message: Optional[str] = None
    processing_time_seconds: Optional[float] = None
    tokens_used: Optional[int] = None
