# Grafana to Kibana Converter - Deployment Guide

## Quick Start

### Prerequisites
- Python 3.11+ (tested with Python 3.13)
- pip (Python package manager)

### Local Development Setup

1. **Clone and navigate to the project:**
```bash
cd /opt/grakibana
```

2. **Create a virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install "pydantic>=2.6.0" fastapi uvicorn httpx jinja2 python-multipart aiofiles typing-extensions requests
```

4. **Run the application:**
```bash
python main.py
```

5. **Access the application:**
- Web Interface: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Docker Deployment

1. **Build and run with Docker Compose:**
```bash
docker-compose up --build
```

2. **Or build and run manually:**
```bash
docker build -t grafana-to-kibana-converter .
docker run -p 8000:8000 grafana-to-kibana-converter
```

## Usage

### Web Interface

1. Open http://localhost:8000 in your browser
2. Drag and drop a Grafana dashboard JSON file or click "Browse Files"
3. Configure conversion options:
   - Preserve Panel IDs
   - Convert Queries
   - Convert Visualizations
   - Convert Variables
   - Convert Annotations
   - Target Kibana Version
4. Click "Convert Dashboard"
5. Download the converted Kibana dashboard

### Model Context Protocol (MCP) API

#### Convert Dashboard
```bash
curl -X POST "http://localhost:8000/mcp/convert" \
     -H "Content-Type: application/json" \
     -d '{
       "dashboard": {...},
       "options": {
         "preserve_panel_ids": true,
         "convert_queries": true,
         "convert_visualizations": true,
         "convert_variables": true,
         "convert_annotations": true,
         "target_kibana_version": "8.11.0"
       }
     }'
```

#### Check Status
```bash
curl "http://localhost:8000/mcp/status"
```

#### Get Capabilities
```bash
curl "http://localhost:8000/mcp/capabilities"
```

#### Validate Dashboard
```bash
curl -X POST "http://localhost:8000/mcp/validate" \
     -H "Content-Type: application/json" \
     -d @dashboard.json
```

#### Batch Conversion
```bash
curl -X POST "http://localhost:8000/mcp/batch" \
     -H "Content-Type: application/json" \
     -d '{
       "dashboards": [...],
       "options": {...}
     }'
```

### Web API

#### Upload and Convert
```bash
curl -X POST "http://localhost:8000/upload" \
     -F "file=@dashboard.json" \
     -F "preserve_panel_ids=true" \
     -F "convert_queries=true" \
     -F "convert_visualizations=true" \
     -F "convert_variables=true" \
     -F "convert_annotations=true" \
     -F "target_kibana_version=8.11.0"
```

#### Download Converted Dashboard
```bash
curl "http://localhost:8000/download/{file_id}" \
     -o kibana_dashboard.json
```

## Testing

Run the comprehensive test suite:
```bash
python test_converter.py
```

This will test:
- Health check
- MCP status and capabilities
- Dashboard validation
- MCP conversion
- Web upload and download
- Batch conversion

## Configuration

### Environment Variables
- `PYTHONUNBUFFERED=1` - Enable unbuffered Python output
- `ENVIRONMENT=production` - Set environment mode

### Supported Features

#### Panel Types
- graph → line visualization
- singlestat → metric visualization
- stat → metric visualization
- table → table visualization
- timeseries → line visualization
- heatmap → heatmap visualization
- piechart → pie visualization
- bargauge → gauge visualization
- gauge → gauge visualization
- text → text panel
- And more...

#### Data Sources
- Prometheus
- Elasticsearch
- InfluxDB
- MySQL
- PostgreSQL
- Graphite
- CloudWatch
- Azure Monitor
- Stackdriver

#### Conversion Options
- Preserve panel IDs
- Convert queries and expressions
- Convert visualization settings
- Convert template variables
- Convert annotations
- Target Kibana version selection

## Architecture

### Project Structure
```
grakibana/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
├── test_converter.py      # Comprehensive test suite
├── sample_dashboard.json  # Sample Grafana dashboard for testing
├── app/
│   ├── __init__.py
│   ├── models.py          # Pydantic models
│   ├── converter.py       # Dashboard conversion logic
│   ├── mcp.py            # Model Context Protocol handlers
│   └── web.py            # Web interface routes
├── static/               # Static assets
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/
│       └── app.js        # Frontend JavaScript
├── templates/            # HTML templates
│   └── index.html        # Main web interface
├── uploads/              # Uploaded files (created automatically)
└── downloads/            # Converted files (created automatically)
```

### Key Components

1. **DashboardConverter** (`app/converter.py`)
   - Core conversion logic
   - Panel type mapping
   - Visualization conversion
   - Query transformation

2. **MCP Router** (`app/mcp.py`)
   - Model Context Protocol endpoints
   - Batch processing
   - Status tracking
   - Validation

3. **Web Router** (`app/web.py`)
   - File upload handling
   - Web interface endpoints
   - Download functionality

4. **Models** (`app/models.py`)
   - Pydantic data models
   - Request/response schemas
   - Validation rules

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Change port in main.py or use different port
   uvicorn main:app --port 8001
   ```

2. **Permission errors:**
   ```bash
   # Ensure write permissions for uploads/downloads directories
   chmod 755 uploads downloads
   ```

3. **Dependency issues:**
   ```bash
   # Recreate virtual environment
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Logs
- Application logs are printed to stdout
- Check for error messages in the terminal
- Use `docker logs <container_id>` for Docker deployments

## Performance

- **Conversion Speed:** Typically < 100ms for standard dashboards
- **Memory Usage:** ~50MB for the application
- **Concurrent Users:** Supports multiple simultaneous conversions
- **File Size Limits:** No hard limits, but large dashboards may take longer

## Security Considerations

- File uploads are validated for JSON format
- No persistent storage of sensitive data
- Input sanitization and validation
- CORS headers for web interface
- Rate limiting recommended for production

## Production Deployment

For production deployment, consider:

1. **Reverse Proxy:** Use nginx or Apache
2. **SSL/TLS:** Enable HTTPS
3. **Database:** Add persistent storage for conversion history
4. **Monitoring:** Add logging and metrics
5. **Authentication:** Implement user authentication
6. **Rate Limiting:** Add request rate limiting
7. **Backup:** Regular backups of configuration and data

## Support

For issues and questions:
1. Check the test results: `python test_converter.py`
2. Review application logs
3. Verify dashboard JSON format
4. Test with the sample dashboard provided 