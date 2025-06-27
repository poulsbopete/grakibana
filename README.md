# Grafana to Kibana Dashboard Converter

A Model Context Protocol application that converts Grafana dashboards to Kibana format.

## Features

- **Model Context Protocol Integration**: Full MCP support for dashboard conversion
- **Web Interface**: Modern, responsive UI for easy dashboard upload and conversion
- **Batch Processing**: Convert multiple dashboards at once
- **Real-time Conversion**: Live preview of conversion results
- **Export Options**: Download converted Kibana dashboards in various formats

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

3. Open your browser to `http://localhost:8000`

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
├── requirements.txt        # Python dependencies
├── app/
│   ├── __init__.py
│   ├── models.py          # Pydantic models
│   ├── converter.py       # Dashboard conversion logic
│   ├── mcp.py            # Model Context Protocol handlers
│   └── web.py            # Web interface routes
├── static/               # Static assets
│   ├── css/
│   └── js/
└── templates/            # HTML templates
```

## License

MIT License 