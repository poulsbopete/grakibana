"""
Model Context Protocol endpoints for Grafana to Kibana converter
"""

import asyncio
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from .models import (
    ConversionRequest,
    ConversionResponse,
    BatchConversionRequest,
    BatchConversionResponse,
    StatusResponse,
    ConversionOptions,
    ConversionStatus
)
from .converter import DashboardConverter

router = APIRouter()

# Global converter instance
converter = DashboardConverter()

# In-memory storage for conversions (in production, use a proper database)
conversions: Dict[str, ConversionResponse] = {}
batch_conversions: Dict[str, BatchConversionResponse] = {}


@router.post("/convert", response_model=ConversionResponse)
async def convert_dashboard(request: ConversionRequest) -> ConversionResponse:
    """
    Convert a Grafana dashboard to Kibana format
    
    This endpoint accepts a Grafana dashboard and converts it to Kibana format
    using the Model Context Protocol.
    """
    try:
        # Convert options
        options = ConversionOptions(**request.options) if request.options else ConversionOptions()
        
        # Perform conversion
        response = converter.convert_dashboard(request.dashboard, options)
        
        # Store conversion result
        conversions[response.id] = response
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Conversion failed: {str(e)}")


@router.get("/convert/{conversion_id}", response_model=ConversionResponse)
async def get_conversion_status(conversion_id: str) -> ConversionResponse:
    """
    Get the status of a conversion by ID
    """
    if conversion_id not in conversions:
        raise HTTPException(status_code=404, detail="Conversion not found")
    
    return conversions[conversion_id]


@router.post("/batch", response_model=BatchConversionResponse)
async def batch_convert_dashboards(
    request: BatchConversionRequest,
    background_tasks: BackgroundTasks
) -> BatchConversionResponse:
    """
    Convert multiple Grafana dashboards to Kibana format in batch
    
    This endpoint processes multiple dashboards asynchronously and returns
    a batch ID for tracking progress.
    """
    # Create batch response
    batch_response = BatchConversionResponse(
        total_dashboards=len(request.dashboards)
    )
    
    # Store batch
    batch_conversions[batch_response.batch_id] = batch_response
    
    # Start background processing
    background_tasks.add_task(
        process_batch_conversion,
        batch_response.batch_id,
        request.dashboards,
        request.options
    )
    
    return batch_response


@router.get("/batch/{batch_id}", response_model=BatchConversionResponse)
async def get_batch_status(batch_id: str) -> BatchConversionResponse:
    """
    Get the status of a batch conversion by ID
    """
    if batch_id not in batch_conversions:
        raise HTTPException(status_code=404, detail="Batch conversion not found")
    
    return batch_conversions[batch_id]


@router.get("/status", response_model=StatusResponse)
async def get_service_status() -> StatusResponse:
    """
    Get the overall service status and statistics
    """
    active_conversions = sum(
        1 for conv in conversions.values() 
        if conv.status in [ConversionStatus.PENDING, ConversionStatus.PROCESSING]
    )
    
    return StatusResponse(
        active_conversions=active_conversions,
        total_conversions=len(conversions)
    )


@router.post("/validate")
async def validate_dashboard(dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a Grafana dashboard without converting it
    
    Returns validation results and conversion summary.
    """
    try:
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
        
    except Exception as e:
        return {
            "valid": False,
            "errors": [str(e)]
        }


@router.delete("/convert/{conversion_id}")
async def delete_conversion(conversion_id: str) -> Dict[str, str]:
    """
    Delete a conversion result
    """
    if conversion_id not in conversions:
        raise HTTPException(status_code=404, detail="Conversion not found")
    
    del conversions[conversion_id]
    return {"message": "Conversion deleted successfully"}


@router.delete("/batch/{batch_id}")
async def delete_batch(batch_id: str) -> Dict[str, str]:
    """
    Delete a batch conversion result
    """
    if batch_id not in batch_conversions:
        raise HTTPException(status_code=404, detail="Batch conversion not found")
    
    del batch_conversions[batch_id]
    return {"message": "Batch conversion deleted successfully"}


@router.get("/capabilities")
async def get_capabilities() -> Dict[str, Any]:
    """
    Get the capabilities and supported features of the converter
    """
    return {
        "supported_panel_types": list(converter.panel_type_mapping.keys()),
        "supported_datasources": list(converter.datasource_mapping.keys()),
        "features": {
            "batch_processing": True,
            "real_time_conversion": True,
            "validation": True,
            "conversion_summary": True
        },
        "limitations": {
            "max_panels_per_dashboard": 100,
            "max_batch_size": 50,
            "supported_grafana_versions": ["7.0.0", "8.0.0", "9.0.0", "10.0.0"],
            "supported_kibana_versions": ["7.0.0", "8.0.0", "8.11.0"]
        }
    }


async def process_batch_conversion(
    batch_id: str,
    dashboards: List[Any],
    options: Dict[str, Any]
) -> None:
    """
    Background task to process batch conversions
    """
    batch = batch_conversions[batch_id]
    conversion_options = ConversionOptions(**options) if options else ConversionOptions()
    
    for dashboard_data in dashboards:
        try:
            # Convert dashboard
            response = converter.convert_dashboard(dashboard_data, conversion_options)
            batch.conversions.append(response)
            
            if response.status == ConversionStatus.COMPLETED:
                batch.completed += 1
            else:
                batch.failed += 1
                
        except Exception as e:
            # Create failed response
            failed_response = ConversionResponse(
                status=ConversionStatus.FAILED,
                grafana_dashboard=dashboard_data,
                error_message=str(e)
            )
            batch.conversions.append(failed_response)
            batch.failed += 1
    
    # Mark batch as completed
    batch.completed_at = asyncio.get_event_loop().time()


def _generate_warnings(summary: Dict[str, Any]) -> List[str]:
    """Generate warnings based on conversion summary"""
    warnings = []
    
    if summary["unsupported_panels"] > 0:
        warnings.append(f"{summary['unsupported_panels']} unsupported panel types will be skipped")
    
    if summary["total_panels"] > 50:
        warnings.append("Large number of panels may affect conversion performance")
    
    if not summary["datasources"]:
        warnings.append("No datasources detected - queries may need manual configuration")
    
    return warnings 