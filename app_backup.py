"""
Streamlit web interface for the Disassembly Instruction Generator.
"""

import streamlit as st
import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import tempfile
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import our modules
from src.instruction_generator import DisassemblyInstructionGenerator
from src.llm_manager import LLMManager
from src.models import DisassemblyInstructions, DisassemblyStep

# Page configuration
st.set_page_config(
    page_title="Disassembly Instruction Generator",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .step-card {
        border: 1px solid #dee2e6;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'generator' not in st.session_state:
    st.session_state.generator = None
if 'generated_instructions' not in st.session_state:
    st.session_state.generated_instructions = None
if 'processing_status' not in st.session_state:
    st.session_state.processing_status = None

def initialize_generator():
    """Initialize the instruction generator."""
    try:
        if st.session_state.generator is None:
            st.session_state.generator = DisassemblyInstructionGenerator()
        return True
    except Exception as e:
        st.error(f"Error initializing generator: {str(e)}")
        return False

def display_step_card(step: Dict[str, Any], step_num: int):
    """Display a disassembly step in a card format."""
    with st.container():
        st.markdown(f"""
        <div class="step-card">
            <h4>Step {step_num}: {step.get('title', 'Untitled Step')}</h4>
            <p><strong>Description:</strong> {step.get('description', 'No description available')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if step.get('tools_required'):
                st.write("**Tools Required:**")
                for tool in step['tools_required']:
                    st.write(f"• {tool}")
        
        with col2:
            if step.get('safety_warnings'):
                st.write("**Safety Warnings:**")
                for warning in step['safety_warnings']:
                    st.write(f"⚠️ {warning}")
        
        with col3:
            if step.get('time_estimate_minutes'):
                st.write(f"**Time Estimate:** {step['time_estimate_minutes']} minutes")
            if step.get('difficulty_level'):
                st.write(f"**Difficulty:** {step['difficulty_level'].title()}")

def main():
    """Main application function."""
    
    # Header
    st.markdown('<h1 class="main-header">🔧 Disassembly Instruction Generator</h1>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
        <strong>Welcome!</strong> This application uses LLM technology to extract data from automotive manuals, 
        specifications, and websites to generate detailed disassembly instructions for technicians and production planners.
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Initialize generator
        if initialize_generator():
            generator = st.session_state.generator
            available_providers = generator.get_available_providers()
            
            if available_providers:
                st.success(f"✅ OpenAI available")
            else:
                st.error("❌ OpenAI not available. Please check your API key.")
                st.stop()
        else:
            st.stop()
        
        st.markdown("---")
        
        # Processing options
        st.subheader("📋 Processing Options")
        include_safety = st.checkbox("Include Safety Warnings", value=True)
        include_tools = st.checkbox("Include Tool Requirements", value=True)
        include_time = st.checkbox("Include Time Estimates", value=True)
        include_difficulty = st.checkbox("Include Difficulty Ratings", value=True)
        
        max_steps = st.slider("Maximum Steps", min_value=10, max_value=100, value=50)
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📄 PDF Processing", "🌐 Website Processing", "📊 Results", "📋 Instructions"])
    
    with tab1:
        st.markdown('<h2 class="section-header">PDF Document Processing</h2>', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Upload PDF Manual or Documentation",
            type=['pdf'],
            help="Upload automotive manuals, specifications, or technical documents"
        )
        
        if uploaded_file is not None:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.info(f"📄 **File:** {uploaded_file.name} ({uploaded_file.size:,} bytes)")
            
            with col2:
                if st.button("🚀 Generate PDF Instructions", type="primary"):
                    with st.spinner("Processing PDF and generating instructions..."):
                        try:
                            # Process PDF
                            result = asyncio.run(
                                generator.generate_instructions_from_pdf(tmp_path)
                            )
                            
                            if result['success']:
                                st.session_state.generated_instructions = result['instructions']
                                st.session_state.processing_status = "success"
                                st.success("✅ Instructions generated successfully!")
                                
                                # Display extraction stats
                                stats = result.get('extraction_stats', {})
                                st.info(f"""
                                **Extraction Statistics:**
                                - Text Length: {stats.get('text_length', 0):,} characters
                                - Images Extracted: {stats.get('images_extracted', 0)}
                                - Tables Extracted: {stats.get('tables_extracted', 0)}
                                """)
                            else:
                                st.session_state.processing_status = "error"
                                st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
                                
                        except Exception as e:
                            st.session_state.processing_status = "error"
                            st.error(f"❌ Processing error: {str(e)}")
                        finally:
                            # Clean up temporary file
                            os.unlink(tmp_path)
    
    with tab2:
        st.markdown('<h2 class="section-header">Website Processing</h2>', unsafe_allow_html=True)
        
        website_url = st.text_input(
            "Enter Website URL",
            placeholder="https://example.com/automotive-manual",
            help="Enter URL of automotive parts website or technical documentation"
        )
        
        follow_links = st.checkbox("Follow Related Links", value=True, help="Extract content from related pages")
        
        if website_url:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.info(f"🌐 **URL:** {website_url}")
            
            with col2:
                if st.button("🚀 Generate Website Instructions", type="primary"):
                    with st.spinner("Processing website and generating instructions..."):
                        try:
                            # Process website
                            result = asyncio.run(
                                generator.generate_instructions_from_website(
                                    website_url,
                                    follow_links=follow_links
                                )
                            )
                            
                            if result['success']:
                                st.session_state.generated_instructions = result['instructions']
                                st.session_state.processing_status = "success"
                                st.success("✅ Instructions generated successfully!")
                                
                                # Display extraction stats
                                stats = result.get('extraction_stats', {})
                                st.info(f"""
                                **Extraction Statistics:**
                                - Text Length: {stats.get('text_length', 0):,} characters
                                - Images Extracted: {stats.get('images_extracted', 0)}
                                - Links Found: {stats.get('links_found', 0)}
                                - Pages Extracted: {stats.get('pages_extracted', 0)}
                                """)
                            else:
                                st.session_state.processing_status = "error"
                                st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
                                
                        except Exception as e:
                            st.session_state.processing_status = "error"
                            st.error(f"❌ Processing error: {str(e)}")
    
    with tab3:
        st.markdown('<h2 class="section-header">Processing Results</h2>', unsafe_allow_html=True)
        
        if st.session_state.processing_status == "success" and st.session_state.generated_instructions:
            instructions = st.session_state.generated_instructions
            
            # Product information
            st.subheader("📋 Product Information")
            product_info = instructions.get('product_info', {})
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Product Name", product_info.get('name', 'Unknown'))
            with col2:
                st.metric("Product Type", product_info.get('type', 'Unknown'))
            with col3:
                st.metric("Model", product_info.get('model', 'Unknown'))
            
            # Overview metrics
            st.subheader("📊 Overview")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Steps", instructions.get('total_steps', len(instructions.get('steps', []))))
            with col2:
                st.metric("Estimated Time", f"{instructions.get('estimated_total_time_minutes', 0)} min")
            with col3:
                st.metric("Difficulty", instructions.get('difficulty_overview', 'Unknown').title())
            with col4:
                st.metric("Safety Requirements", len(instructions.get('general_safety_requirements', [])))
            
            # Safety requirements
            if instructions.get('general_safety_requirements'):
                st.subheader("⚠️ General Safety Requirements")
                for req in instructions['general_safety_requirements']:
                    st.write(f"• {req}")
            
            # Required tools
            if instructions.get('general_tools_required'):
                st.subheader("🔧 Required Tools")
                for tool in instructions['general_tools_required']:
                    st.write(f"• {tool}")
            
            # Additional notes and warnings
            if instructions.get('additional_notes'):
                st.subheader("📝 Additional Notes")
                st.write(instructions['additional_notes'])
            
            if instructions.get('warnings'):
                st.subheader("⚠️ Important Warnings")
                for warning in instructions['warnings']:
                    st.write(f"⚠️ {warning}")
            
            # Download options
            st.subheader("💾 Download Instructions")
            col1, col2 = st.columns(2)
            
            with col1:
                json_data = json.dumps(instructions, indent=2, ensure_ascii=False)
                st.download_button(
                    label="📄 Download JSON",
                    data=json_data,
                    file_name=f"disassembly_instructions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            with col2:
                # Create a simple text version
                text_content = f"""
DISASSEMBLY INSTRUCTIONS
========================

Product: {product_info.get('name', 'Unknown')}
Type: {product_info.get('type', 'Unknown')}
Model: {product_info.get('model', 'Unknown')}
Difficulty: {instructions.get('difficulty_overview', 'Unknown').title()}
Estimated Time: {instructions.get('estimated_total_time_minutes', 0)} minutes

SAFETY REQUIREMENTS:
{chr(10).join(f"• {req}" for req in instructions.get('general_safety_requirements', []))}

REQUIRED TOOLS:
{chr(10).join(f"• {tool}" for tool in instructions.get('general_tools_required', []))}

STEPS:
{chr(10).join(f"{i+1}. {step.get('title', 'Untitled')}: {step.get('description', 'No description')}" for i, step in enumerate(instructions.get('steps', [])))}
"""
                
                st.download_button(
                    label="📝 Download Text",
                    data=text_content,
                    file_name=f"disassembly_instructions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
        
        elif st.session_state.processing_status == "error":
            st.error("❌ Processing failed. Please check the error messages in the previous tabs.")
        
        else:
            st.info("ℹ️ No instructions generated yet. Please process a PDF or website first.")
    
    with tab4:
        st.markdown('<h2 class="section-header">Step-by-Step Instructions</h2>', unsafe_allow_html=True)
        
        if st.session_state.generated_instructions:
            instructions = st.session_state.generated_instructions
            steps = instructions.get('steps', [])
            
            if steps:
                st.write(f"**Total Steps:** {len(steps)}")
                
                # Step navigation
                if len(steps) > 1:
                    step_num = st.selectbox(
                        "Select Step to View",
                        range(1, len(steps) + 1),
                        format_func=lambda x: f"Step {x}: {steps[x-1].get('title', 'Untitled')}"
                    )
                    display_step_card(steps[step_num - 1], step_num)
                else:
                    display_step_card(steps[0], 1)
                
                # Show all steps in expandable sections
                st.subheader("📋 All Steps")
                for i, step in enumerate(steps):
                    with st.expander(f"Step {i+1}: {step.get('title', 'Untitled Step')}"):
                        display_step_card(step, i+1)
            else:
                st.warning("No steps found in the generated instructions.")
        else:
            st.info("ℹ️ No instructions available. Please generate instructions first.")

if __name__ == "__main__":
    main()
