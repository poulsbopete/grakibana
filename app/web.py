"""
Web interface endpoints for Grafana to Kibana converter
"""

import json
import os
import uuid
from typing import Dict, Any
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import aiofiles
import traceback
import threading

from .models import ConversionRequest, ConversionResponse, ConversionOptions
from .converter import DashboardConverter

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Global converter instance
converter = DashboardConverter()

# File storage (in production, use proper file storage)
UPLOAD_DIR = "uploads"
DOWNLOAD_DIR = "downloads"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# In-memory progress tracking
conversion_progress = {}
progress_lock = threading.Lock()

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main web interface"""
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/upload")
async def upload_dashboard(
    file: UploadFile = File(...),
    preserve_panel_ids: bool = Form(True),
    convert_queries: bool = Form(True),
    convert_visualizations: bool = Form(True),
    convert_variables: bool = Form(True),
    convert_annotations: bool = Form(True),
    target_kibana_version: str = Form("8.11.0")
):
    """
    Upload and convert a Grafana dashboard file
    """
    try:
        # Validate file type
        if not (file.filename.endswith('.json') or file.filename.endswith('.ndjson')):
            raise HTTPException(status_code=400, detail="Only JSON or NDJSON files are supported")
        
        # Read file content
        content = await file.read()
        dashboard_data = json.loads(content.decode('utf-8'))
        
        # Validate dashboard
        if not converter.validate_grafana_dashboard(dashboard_data):
            raise HTTPException(status_code=400, detail="Invalid Grafana dashboard format")
        
        # Create conversion options
        is_serverless = (target_kibana_version == "serverless")
        options = ConversionOptions(
            preserve_panel_ids=preserve_panel_ids,
            convert_queries=convert_queries,
            convert_visualizations=convert_visualizations,
            convert_variables=convert_variables,
            convert_annotations=convert_annotations,
            target_kibana_version=target_kibana_version
        )
        
        # Convert dashboard
        from .models import GrafanaDashboard
        grafana_dashboard = GrafanaDashboard(**dashboard_data)

        # Generate a job_id for this conversion
        job_id = str(uuid.uuid4())
        conversion_progress[job_id] = {"progress": 0, "status": "Starting conversion..."}

        # Patch the converter to update progress after each panel
        def progress_callback(current, total, status):
            with progress_lock:
                conversion_progress[job_id] = {"progress": int(current / total * 100), "status": status}

        # Pass progress_callback to the converter
        response = converter.convert_dashboard(
            grafana_dashboard,
            ConversionOptions(
                preserve_panel_ids=preserve_panel_ids,
                convert_queries=convert_queries,
                convert_visualizations=convert_visualizations,
                convert_variables=convert_variables,
                convert_annotations=convert_annotations,
                target_kibana_version=target_kibana_version,
                progress_callback=progress_callback
            )
        )
        
        # Save converted dashboard to file (both .json and .ndjson)
        if response.status.value == "completed" and response.kibana_dashboard:
            file_id = str(uuid.uuid4())
            output_file_json = os.path.join(DOWNLOAD_DIR, f"{file_id}.json")
            output_file_ndjson = os.path.join(DOWNLOAD_DIR, f"{file_id}.ndjson")
            
            async with aiofiles.open(output_file_json, 'w') as f:
                await f.write(json.dumps(response.kibana_dashboard.dict(), indent=2))
            async with aiofiles.open(output_file_ndjson, 'w') as f:
                await f.write(converter.export_to_ndjson(response.kibana_dashboard))
            
            # Mark progress as 100%
            with progress_lock:
                conversion_progress[job_id] = {"progress": 100, "status": "Conversion completed!"}
            return {
                "success": True,
                "file_id": file_id,
                "conversion_id": response.id,
                "job_id": job_id,
                "status": response.status.value,
                "conversion_time_ms": response.conversion_time_ms,
                "summary": converter.get_conversion_summary(grafana_dashboard)
            }
        else:
            with progress_lock:
                conversion_progress[job_id] = {"progress": 100, "status": "Failed: " + (response.error_message or "Unknown error")}
            return {
                "success": False,
                "error": response.error_message,
                "conversion_id": response.id,
                "job_id": job_id
            }
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        print("\n--- Exception in /upload endpoint ---")
        traceback.print_exc()
        print("--- End Exception ---\n")
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@router.get("/download/{file_id}")
async def download_converted_dashboard(file_id: str, format: str = "json"):
    """
    Download a converted dashboard file
    """
    if format == "ndjson":
        file_path = os.path.join(DOWNLOAD_DIR, f"{file_id}.ndjson")
        media_type = "application/x-ndjson"
        filename = f"kibana_dashboard_{file_id}.ndjson"
    else:
        file_path = os.path.join(DOWNLOAD_DIR, f"{file_id}.json")
        media_type = "application/json"
        filename = f"kibana_dashboard_{file_id}.json"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=filename
    )


@router.post("/validate")
async def validate_dashboard_web(file: UploadFile = File(...)):
    """
    Validate a dashboard file without converting it
    """
    try:
        content = await file.read()
        dashboard_data = json.loads(content.decode('utf-8'))
        
        # Validate dashboard structure
        is_valid = converter.validate_grafana_dashboard(dashboard_data)
        
        if not is_valid:
            return {
                "valid": False,
                "errors": ["Invalid dashboard structure"]
            }
        
        # Get conversion summary
        from .models import GrafanaDashboard
        grafana_dashboard = GrafanaDashboard(**dashboard_data)
        summary = converter.get_conversion_summary(grafana_dashboard)
        
        return {
            "valid": True,
            "summary": summary,
            "warnings": _generate_warnings(summary)
        }
        
    except json.JSONDecodeError:
        return {
            "valid": False,
            "errors": ["Invalid JSON file"]
        }
    except Exception as e:
        return {
            "valid": False,
            "errors": [str(e)]
        }


@router.get("/preview/{conversion_id}")
async def preview_conversion(conversion_id: str):
    """
    Get a preview of a conversion result
    """
    # This would typically fetch from a database
    # For now, return a placeholder
    return {
        "conversion_id": conversion_id,
        "preview": "Preview functionality would be implemented here"
    }


@router.get("/api/status")
async def api_status():
    """
    Get API status for the web interface
    """
    return {
        "status": "healthy",
        "service": "grafana-to-kibana-converter",
        "version": "1.0.0"
    }


@router.get("/progress/{job_id}")
async def get_progress(job_id: str):
    with progress_lock:
        progress = conversion_progress.get(job_id)
    if not progress:
        return {"progress": 0, "status": "Not started"}
    return progress


def _generate_warnings(summary: Dict[str, Any]) -> list:
    """Generate warnings based on conversion summary"""
    warnings = []
    
    if summary["unsupported_panels"] > 0:
        warnings.append(f"{summary['unsupported_panels']} unsupported panel types will be skipped")
    
    if summary["total_panels"] > 50:
        warnings.append("Large number of panels may affect conversion performance")
    
    if not summary["datasources"]:
        warnings.append("No datasources detected - queries may need manual configuration")
    
    return warnings 