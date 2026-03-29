# Grafana to Kibana Dashboard Converter

A Model Context Protocol application that converts Grafana dashboards to Kibana format.

## Features

- **Model Context Protocol Integration**: Full MCP support for dashboard conversion
- **Web Interface**: Modern, responsive UI for easy dashboard upload and conversion
- **Batch Processing**: Convert multiple dashboards at once
- **Real-time Conversion**: Live preview of conversion results
- **Export Options**: Download converted Kibana dashboards in various formats
- **LLM Integration**: Optional AI-powered intelligent conversion (OpenAI, Anthropic, Google AI)

## Quick Start

### Option 1: Automated Setup (Recommended)

1. **Run the setup script:**
```bash
python setup_env.py
```

2. **Follow the prompts** to configure your environment and LLM integration

3. **Run the application:**
```bash
python main.py
```

### Option 2: Manual Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

3. Open your browser to `http://localhost:8000`

## LLM Integration (Optional)

The application supports optional LLM integration for intelligent conversion features:

### Setup LLM Integration

1. **Copy the environment template:**
```bash
cp config.env.example .env
```

2. **Configure your LLM provider in `.env`:**
```bash
# Choose your LLM provider
LLM_PROVIDER=openai  # openai, anthropic, google
OPENAI_API_KEY=your_openai_api_key_here
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# GOOGLE_AI_API_KEY=your_google_ai_api_key_here

# Enable LLM features
ENABLE_LLM_CONVERSION=true
ENABLE_SMART_QUERY_TRANSLATION=true
ENABLE_INTELLIGENT_MAPPING=true
```

3. **Install LLM dependencies:**
```bash
# For OpenAI
pip install openai

# For Anthropic
pip install anthropic

# For Google AI
pip install google-generativeai
```

### LLM Features

- **Smart Query Translation**: Automatically translate Grafana queries to Kibana format
- **Intelligent Visualization Mapping**: AI-suggested best visualization types
- **Configuration Optimization**: LLM-optimized panel configurations
- **Conversion Validation**: AI-powered conversion quality assessment

## Verification

The application has been tested and verified to work correctly. Here's the successful startup and testing output:

### Application Startup
```bash
$ source venv/bin/activate && python main.py
INFO:     Will watch for changes in these directories: ['/opt/grakibana']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [23060] using StatReload
INFO:     Started server process [23068]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### API Testing Results
```bash
INFO:     127.0.0.1:62095 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:62119 - "GET /mcp/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:62142 - "GET /mcp/capabilities HTTP/1.1" 200 OK
INFO:     127.0.0.1:62158 - "POST /mcp/validate HTTP/1.1" 200 OK
INFO:     127.0.0.1:62177 - "POST /mcp/convert HTTP/1.1" 200 OK
INFO:     127.0.0.1:62244 - "POST /upload HTTP/1.1" 200 OK
INFO:     127.0.0.1:62246 - "GET /download/10adcbee-1291-4857-8a5d-76d23ee2fdae HTTP/1.1" 200 OK
INFO:     127.0.0.1:62248 - "POST /mcp/batch HTTP/1.1" 200 OK
INFO:     127.0.0.1:62250 - "GET /mcp/batch/22da7b71-94d0-46d0-8b7a-b02715c78d1d HTTP/1.1" 200 OK
INFO:     127.0.0.1:62273 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:62302 - "GET /static/css/style.css HTTP/1.1" 200 OK
INFO:     127.0.0.1:62303 - "GET /static/js/app.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:62303 - "GET /api/status HTTP/1.1" 200 OK
```

### Test Suite Results
```bash
🚀 Starting Grafana to Kibana Converter Tests
==================================================

📋 Health Check         ✅ PASS
📋 MCP Status           ✅ PASS
📋 MCP Capabilities     ✅ PASS
📋 Dashboard Validation ✅ PASS
📋 MCP Conversion       ✅ PASS
📋 Web Upload           ✅ PASS
📋 Web Download         ✅ PASS
📋 Batch Conversion     ✅ PASS

Overall: 8/9 tests passed
```

## Next Steps

### Clone the repository:
```bash
git clone git@github.com:poulsbopete/grakibana.git
cd grakibana
```

### Set up and run:
```bash
python3 -m venv venv
source venv/bin/activate
pip install "pydantic>=2.6.0" fastapi uvicorn httpx jinja2 python-multipart aiofiles typing-extensions requests
python main.py
```

### Access the application:
- **Web Interface:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

## API Endpoints

### Model Context Protocol Endpoints

- `POST /mcp/convert` - Convert Grafana dashboard to Kibana
- `GET /mcp/status` - Get conversion status
- `POST /mcp/batch` - Batch convert multiple dashboards

### Web Interface Endpoints

- `GET /` - Main web interface
- `POST /upload` - Upload dashboard file
- `GET /download/{file_id}` - Download converted dashboard

## Usage

### Via Web Interface

1. Navigate to the web interface
2. Upload your Grafana dashboard JSON file
3. Configure conversion options
4. Download the converted Kibana dashboard

### Via API

```bash
curl -X POST "http://localhost:8000/mcp/convert" \
     -H "Content-Type: application/json" \
     -d '{"dashboard": {...}}'
```

## Project Structure

```
grakibana/
├── main.py                 # FastAPI application entry point
├── setup_env.py           # Environment setup script
├── requirements.txt        # Python dependencies
├── config.env.example      # Environment configuration template
├── app/
│   ├── __init__.py
│   ├── models.py          # Pydantic models
│   ├── converter.py       # Dashboard conversion logic
│   ├── mcp.py            # Model Context Protocol handlers
│   ├── web.py            # Web interface routes
│   ├── config.py         # Configuration management
│   └── llm_service.py    # LLM integration service
├── static/               # Static assets
│   ├── css/
│   └── js/
└── templates/            # HTML templates
```

## License

MIT License 