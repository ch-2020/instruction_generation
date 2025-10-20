# Disassembly Instruction Generator

An LLM-powered application that extracts data from automotive manuals, specifications, and BOMs to generate detailed disassembly instructions for technicians and production planners using OpenAI's GPT models.

## Features

- **Multi-source Data Extraction**: PDF manuals, websites, and documents
- **OpenAI Integration**: Uses OpenAI GPT models for instruction generation
- **Component Selection**: Choose specific automotive components to disassemble
- **Structured Output**: JSON-formatted step-by-step disassembly instructions
- **Comprehensive Details**: Safety warnings, tool requirements, time estimates, difficulty levels
- **Web Interface**: Streamlit-based UI for technicians and production planners
- **Batch Processing**: Handle multiple documents efficiently

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `env.example` to `.env` and configure your OpenAI API key
4. Run the application: `streamlit run app.py`

## Configuration

Edit `config/settings.json` to configure:
- OpenAI model settings
- Output formats
- Safety requirements
- Tool specifications

## Usage

1. Upload PDF manuals or enter website URLs
2. Select the component type you want to disassemble
3. Configure disassembly parameters
4. Generate structured disassembly instructions
5. Export results in JSON format

## Supported Data Sources

- PDF instruction manuals
- Technical specifications
- Bill of Materials (BOM)
- Automotive part websites
- Technical documentation

## Output Format

The application generates detailed JSON instructions including:
- Step-by-step procedures
- Required tools and equipment
- Safety warnings and precautions
- Time estimates and difficulty ratings
- Part identification and handling instructions

## API Key Setup

### OpenAI
1. Get API key from https://platform.openai.com/api-keys
2. Add to `.env`: `OPENAI_API_KEY=your_key_here`

## Project Structure

```
disassembly_instruction_generator/
├── src/
│   ├── pdf_extractor.py          # PDF data extraction
│   ├── website_extractor.py      # Website data extraction
│   ├── llm_manager.py           # OpenAI API management
│   ├── instruction_generator.py # Core instruction generation
│   └── models.py                # Data models
├── config/
│   └── settings.json            # Configuration settings
├── app.py                       # Streamlit web interface
├── requirements.txt             # Python dependencies
├── env.example                  # Environment variables template
└── README.md                    # This file
```

## Examples

### Processing a PDF Manual
1. Upload a PDF file through the web interface
2. Click "Generate Instructions"
3. Download the JSON output

### Processing a Website
1. Enter the website URL
2. Choose whether to follow related links
3. Generate instructions
4. Review and download results

## Troubleshooting

### Common Issues
- **OpenAI not available**: Check your API key in `.env`
- **PDF extraction fails**: Ensure PDF is not password-protected
- **Website extraction fails**: Check URL accessibility and network connection

### Logs
Check the console output for detailed error messages and processing information.
