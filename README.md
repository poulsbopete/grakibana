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