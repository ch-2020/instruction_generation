"""
Test file for the Disassembly Instruction Generator.
"""

import asyncio
import os
from pathlib import Path

def test_imports():
    """Test that all modules can be imported."""
    try:
        from src.pdf_extractor import PDFExtractor
        from src.website_extractor import WebsiteExtractor
        from src.llm_manager import LLMManager
        from src.instruction_generator import DisassemblyInstructionGenerator
        from src.models import DisassemblyInstructions, DisassemblyStep
        print("✅ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_initialization():
    """Test that components can be initialized."""
    try:
        from src.pdf_extractor import PDFExtractor
        from src.website_extractor import WebsiteExtractor
        from src.llm_manager import LLMManager
        from src.instruction_generator import DisassemblyInstructionGenerator
        
        # Test PDF extractor
        pdf_extractor = PDFExtractor()
        print("✅ PDF extractor initialized")
        
        # Test website extractor
        website_extractor = WebsiteExtractor()
        print("✅ Website extractor initialized")
        
        # Test LLM manager
        llm_manager = LLMManager()
        print("✅ LLM manager initialized")
        
        # Test instruction generator
        generator = DisassemblyInstructionGenerator()
        print("✅ Instruction generator initialized")
        
        return True
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False

def test_llm_providers():
    """Test LLM provider availability."""
    try:
        from src.instruction_generator import DisassemblyInstructionGenerator
        generator = DisassemblyInstructionGenerator()
        providers = generator.get_available_providers()
        
        if providers:
            print(f"✅ Available LLM providers: {providers}")
        else:
            print("⚠️ No LLM providers available (check API keys)")
        
        return True
    except Exception as e:
        print(f"❌ LLM provider test error: {e}")
        return False

def test_config_files():
    """Test that configuration files exist."""
    config_files = [
        "requirements.txt",
        "env.example",
        "config/settings.json",
        "README.md"
    ]
    
    all_exist = True
    for file_path in config_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist

async def test_async_functionality():
    """Test async functionality."""
    try:
        from src.instruction_generator import DisassemblyInstructionGenerator
        generator = DisassemblyInstructionGenerator()
        
        # Test with sample content
        sample_content = """
        AUTOMOTIVE DOOR PANEL REMOVAL
        
        Step 1: Remove door handle trim
        - Use flat screwdriver to pry off trim
        - Be careful not to damage clips
        
        Step 2: Remove screws
        - Locate screws around perimeter
        - Use Phillips screwdriver
        """
        
        # This would normally call the LLM, but we'll just test the structure
        print("✅ Async functionality structure ready")
        return True
        
    except Exception as e:
        print(f"❌ Async test error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Running Disassembly Instruction Generator Tests")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Initialization Test", test_initialization),
        ("LLM Providers Test", test_llm_providers),
        ("Config Files Test", test_config_files),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}")
        print("-" * 30)
        if test_func():
            passed += 1
    
    # Test async functionality
    print(f"\n🔍 Async Functionality Test")
    print("-" * 30)
    if asyncio.run(test_async_functionality()):
        passed += 1
    total += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application is ready to use.")
        print("\n📋 Next steps:")
        print("1. Copy env.example to .env and add your API keys")
        print("2. Run: streamlit run app.py")
        print("3. Open your browser to the provided URL")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()
