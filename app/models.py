"""
Pydantic models for the Grafana to Kibana converter
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import uuid
from datetime import datetime


class ConversionStatus(str, Enum):
    """Conversion status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class GrafanaDashboard(BaseModel):
    """Grafana dashboard model"""
    title: str
    uid: Optional[str] = None
    version: Optional[int] = 1
    time: Optional[Dict[str, Any]] = None
    timezone: Optional[str] = "browser"
    refresh: Optional[str] = "5s"
    schemaVersion: Optional[int] = 30
    style: Optional[str] = "dark"
    tags: Optional[List[str]] = []
    templating: Optional[Dict[str, Any]] = None
    annotations: Optional[Dict[str, Any]] = None
    panels: List[Dict[str, Any]] = Field(default_factory=list)
    links: Optional[List[Dict[str, Any]]] = None
    editable: Optional[bool] = True
    graphTooltip: Optional[int] = 0
    hideControls: Optional[bool] = False
    timepicker: Optional[Dict[str, Any]] = None
    fiscalYearStartMonth: Optional[int] = 0
    liveNow: Optional[bool] = False


class KibanaDashboard(BaseModel):
    """Kibana dashboard model"""
    id: Optional[str] = None
    type: str = "dashboard"
    attributes: Dict[str, Any] = Field(default_factory=dict)
    references: List[Dict[str, Any]] = Field(default_factory=list)
    migrationVersion: Optional[Dict[str, Any]] = None
    coreMigrationVersion: Optional[str] = None
    updated_at: Optional[str] = None
    created_at: Optional[str] = None
    version: Optional[str] = None
    namespaces: Optional[List[str]] = None
    originId: Optional[str] = None


class ConversionRequest(BaseModel):
    """Request model for dashboard conversion"""
    dashboard: GrafanaDashboard
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)
    target_version: Optional[str] = "8.11.0"


class ConversionResponse(BaseModel):
    """Response model for dashboard conversion"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: ConversionStatus
    grafana_dashboard: GrafanaDashboard
    kibana_dashboard: Optional[KibanaDashboard] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    conversion_time_ms: Optional[int] = None


class BatchConversionRequest(BaseModel):
    """Request model for batch dashboard conversion"""
    dashboards: List[GrafanaDashboard]
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)
    target_version: Optional[str] = "8.11.0"


class BatchConversionResponse(BaseModel):
    """Response model for batch dashboard conversion"""
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    total_dashboards: int
    completed: int = 0
    failed: int = 0
    conversions: List[ConversionResponse] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class ConversionOptions(BaseModel):
    """Options for dashboard conversion"""
    preserve_panel_ids: bool = True
    convert_queries: bool = True
    convert_visualizations: bool = True
    convert_variables: bool = True
    convert_annotations: bool = True
    target_kibana_version: str = "8.11.0"
    index_pattern_mapping: Optional[Dict[str, str]] = None


class StatusResponse(BaseModel):
    """Status response model"""
    service: str = "grafana-to-kibana-converter"
    version: str = "1.0.0"
    status: str = "healthy"
    uptime: Optional[float] = None
    active_conversions: int = 0
    total_conversions: int = 0 