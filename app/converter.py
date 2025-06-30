"""
Core dashboard conversion logic
Converts Grafana dashboards to Kibana format
"""

import time
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import copy
import logging

from .models import (
    GrafanaDashboard, 
    KibanaDashboard, 
    ConversionResponse, 
    ConversionStatus,
    ConversionOptions
)
from app.llm_service import LLMService


class DashboardConverter:
    """Main converter class for transforming Grafana dashboards to Kibana"""
    
    def __init__(self):
        self.panel_type_mapping = {
            'graph': 'visualization',
            'singlestat': 'visualization',
            'stat': 'visualization',
            'table': 'visualization',
            'timeseries': 'visualization',
            'heatmap': 'visualization',
            'piechart': 'visualization',
            'bargauge': 'visualization',
            'gauge': 'visualization',
            'text': 'text',
            'row': 'container',
            'alertlist': 'visualization',
            'dashlist': 'visualization',
            'logs': 'visualization',
            'nodeGraph': 'visualization',
            'traces': 'visualization'
        }
        
        self.datasource_mapping = {
            'prometheus': 'prometheus',
            'elasticsearch': 'elasticsearch',
            'influxdb': 'influxdb',
            'mysql': 'mysql',
            'postgres': 'postgres',
            'graphite': 'graphite',
            'cloudwatch': 'cloudwatch',
            'azuremonitor': 'azuremonitor',
            'stackdriver': 'stackdriver'
        }

        self.llm_service = LLMService()

    def convert_dashboard(self, grafana_dashboard: GrafanaDashboard, options: Optional[ConversionOptions] = None) -> ConversionResponse:
        """
        Convert a Grafana dashboard to Kibana format
        
        Args:
            grafana_dashboard: The Grafana dashboard to convert
            options: Conversion options
            
        Returns:
            ConversionResponse with the converted dashboard
        """
        start_time = time.time()
        
        if options is None:
            options = ConversionOptions()
            
        progress_callback = getattr(options, 'progress_callback', None)
        
        try:
            # Create conversion response
            response = ConversionResponse(
                status=ConversionStatus.PROCESSING,
                grafana_dashboard=grafana_dashboard
            )
            
            # Convert the dashboard
            kibana_dashboard = self._convert_to_kibana_format(grafana_dashboard, options, progress_callback)
            
            # Update response
            response.status = ConversionStatus.COMPLETED
            response.kibana_dashboard = kibana_dashboard
            response.completed_at = datetime.utcnow()
            response.conversion_time_ms = int((time.time() - start_time) * 1000)
            
            return response
            
        except Exception as e:
            # Handle conversion errors
            response = ConversionResponse(
                status=ConversionStatus.FAILED,
                grafana_dashboard=grafana_dashboard,
                error_message=str(e),
                completed_at=datetime.utcnow(),
                conversion_time_ms=int((time.time() - start_time) * 1000)
            )
            return response

    def _convert_to_kibana_format(self, grafana_dashboard: GrafanaDashboard, options: ConversionOptions, progress_callback=None) -> KibanaDashboard:
        """Convert Grafana dashboard to Kibana format"""
        
        # Generate unique ID for the dashboard
        dashboard_id = str(uuid.uuid4())
        
        # Convert dashboard attributes
        attributes = {
            "title": grafana_dashboard.title,
            "hits": 0,
            "description": "",
            "panelsJSON": self._convert_panels(grafana_dashboard.panels, options, progress_callback),
            "optionsJSON": self._convert_options(grafana_dashboard),
            "version": 1,
            "timeRestore": False,
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": self._convert_search_source(grafana_dashboard)
            }
        }
        
        # Convert references
        references = self._convert_references(grafana_dashboard, options)
        
        # Create Kibana dashboard
        kibana_dashboard = KibanaDashboard(
            id=dashboard_id,
            type="dashboard",
            attributes=attributes,
            references=references,
            migrationVersion={
                "dashboard": "8.0.0"
            },
            coreMigrationVersion="8.0.0",
            updated_at=datetime.utcnow().isoformat(),
            created_at=datetime.utcnow().isoformat(),
            version="1"
        )
        
        return kibana_dashboard

    def _convert_panels(self, panels: List[Dict[str, Any]], options: ConversionOptions, progress_callback=None) -> str:
        """Convert Grafana panels to Kibana format, using AI if enabled"""
        kibana_panels = []
        total_panels = len(panels)
        for idx, panel in enumerate(panels):
            ai_used = False
            kibana_panel = None
            # Use AI for panel type and query translation if enabled
            if self.llm_service.is_available():
                prompt = self.llm_service.build_prompt_for_panel(panel)
                try:
                    ai_response = self.llm_service.query(prompt)
                    # Suggest visualization type
                    kibana_type = self.llm_service.suggest_visualization_type(panel)
                    # Translate queries
                    targets = panel.get('targets', [])
                    ai_queries = []
                    for target in targets:
                        query = target.get('expr') or target.get('query') or ''
                        datasource = target.get('datasource', panel.get('datasource', 'prometheus'))
                        if query:
                            translated = self.llm_service.translate_query(query, datasource, 'elasticsearch')
                            if translated:
                                ai_queries.append(translated)
                                ai_used = True
                            else:
                                ai_queries.append(query)
                        else:
                            ai_queries.append('')
                    # Build panel with AI suggestions
                    kibana_panel = self._convert_single_panel(panel, options)
                    if kibana_panel:
                        if kibana_type:
                            kibana_panel['type'] = kibana_type
                            ai_used = True
                        if ai_queries:
                            if 'embeddableConfig' in kibana_panel and 'searchSource' in kibana_panel['embeddableConfig']:
                                kibana_panel['embeddableConfig']['searchSource']['query'] = ai_queries[0] if len(ai_queries) == 1 else ai_queries
                            ai_used = True
                        kibana_panel['ai_converted'] = ai_used
                except Exception as e:
                    logging.getLogger("converter.ai").error(f"AI conversion failed for panel {panel.get('id')}: {e}")
                    # Fallback to rule-based
                    kibana_panel = self._convert_single_panel(panel, options)
            else:
                kibana_panel = self._convert_single_panel(panel, options)
            if kibana_panel is not None:
                kibana_panel['ai_converted'] = ai_used
                kibana_panels.append(kibana_panel)
            # Call progress_callback after each panel
            if progress_callback:
                progress_callback(idx + 1, total_panels, f"Processed panel {idx + 1} of {total_panels}")
        return json.dumps(kibana_panels)

    def _convert_single_panel(self, panel: Dict[str, Any], options: ConversionOptions) -> Optional[Dict[str, Any]]:
        """Convert a single Grafana panel to Kibana format"""
        
        panel_type = panel.get('type', 'graph')
        kibana_type = self.panel_type_mapping.get(panel_type, 'visualization')
        
        # Skip unsupported panel types
        if kibana_type == 'container':
            return None
            
        # Convert panel structure
        kibana_panel = {
            "type": kibana_type,
            "id": panel.get('id', str(uuid.uuid4())) if options.preserve_panel_ids else str(uuid.uuid4()),
            "panelIndex": panel.get('gridPos', {}).get('h', 8),
            "gridData": {
                "x": panel.get('gridPos', {}).get('x', 0),
                "y": panel.get('gridPos', {}).get('y', 0),
                "w": panel.get('gridPos', {}).get('w', 12),
                "h": panel.get('gridPos', {}).get('h', 8),
                "i": panel.get('id', str(uuid.uuid4()))
            },
            "version": "8.0.0",
            "embeddableConfig": self._convert_embeddable_config(panel),
            "title": panel.get('title', 'Untitled Panel'),
            "savedObjectId": str(uuid.uuid4())
        }
        
        return kibana_panel

    def _convert_embeddable_config(self, panel: Dict[str, Any]) -> Dict[str, Any]:
        """Convert panel configuration for Kibana embeddable"""
        config = {}
        
        # Convert visualization-specific settings
        if panel.get('type') in ['graph', 'timeseries', 'stat']:
            config.update({
                "vis": {
                    "type": self._map_visualization_type(panel.get('type')),
                    "params": self._convert_visualization_params(panel)
                }
            })
        
        # Convert targets/queries
        if 'targets' in panel:
            config["searchSource"] = {
                "query": self._convert_queries(panel.get('targets', []))
            }
        
        return config

    def _map_visualization_type(self, grafana_type: str) -> str:
        """Map Grafana visualization types to Kibana types"""
        mapping = {
            'graph': 'line',
            'timeseries': 'line',
            'stat': 'metric',
            'singlestat': 'metric',
            'table': 'table',
            'heatmap': 'heatmap',
            'piechart': 'pie',
            'bargauge': 'gauge',
            'gauge': 'gauge'
        }
        return mapping.get(grafana_type, 'line')

    def _convert_visualization_params(self, panel: Dict[str, Any]) -> Dict[str, Any]:
        """Convert visualization parameters"""
        params = {}
        
        # Convert common visualization settings
        if 'fieldConfig' in panel:
            field_config = panel['fieldConfig']
            if 'defaults' in field_config:
                defaults = field_config['defaults']
                params.update({
                    "type": "metric",
                    "metric": {
                        "percentageMode": defaults.get('unit') == 'percent',
                        "useRanges": True,
                        "colorSchema": "Green to Red",
                        "metricColorMode": "Labels",
                        "numberFormat": "number",
                        "colorFullBackground": False
                    }
                })
        
        return params

    def _convert_queries(self, targets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert Grafana queries to Kibana format"""
        if not targets:
            return {"query": "", "language": "kuery"}
        
        # For now, return a basic query structure
        # In a full implementation, this would parse and convert specific query languages
        return {
            "query": "",
            "language": "kuery"
        }

    def _convert_options(self, grafana_dashboard: GrafanaDashboard) -> str:
        """Convert dashboard options"""
        options = {
            "hidePanelTitles": grafana_dashboard.hideControls or False,
            "useMargins": True,
            "syncColors": False,
            "syncCursor": True,
            "syncTooltips": False,
            "hideAllLegends": False
        }
        
        return str(options)

    def _convert_search_source(self, grafana_dashboard: GrafanaDashboard) -> str:
        """Convert search source configuration"""
        search_source = {
            "query": {"query": "", "language": "kuery"},
            "filter": [],
            "highlight": {
                "pre_tags": ["@kibana-highlighted-field@"],
                "post_tags": ["@/kibana-highlighted-field@"],
                "fields": {"*": {}},
                "require_field_match": False,
                "fragment_size": 2147483647
            }
        }
        
        return str(search_source)

    def _convert_references(self, grafana_dashboard: GrafanaDashboard, options: ConversionOptions) -> List[Dict[str, Any]]:
        """Convert dashboard references"""
        references = []
        
        # Add index pattern references
        if options.index_pattern_mapping:
            for grafana_ds, kibana_index in options.index_pattern_mapping.items():
                references.append({
                    "name": f"kibanaSavedObjectMeta.searchSourceJSON.index",
                    "type": "index-pattern",
                    "id": kibana_index
                })
        
        return references

    def validate_grafana_dashboard(self, dashboard_data: Dict[str, Any]) -> bool:
        """Validate that the input is a valid Grafana dashboard"""
        required_fields = ['title', 'panels']
        
        for field in required_fields:
            if field not in dashboard_data:
                return False
        
        if not isinstance(dashboard_data.get('panels', []), list):
            return False
        
        return True

    def get_conversion_summary(self, grafana_dashboard: GrafanaDashboard) -> Dict[str, Any]:
        """Get a summary of what will be converted"""
        summary = {
            "total_panels": len(grafana_dashboard.panels),
            "supported_panels": 0,
            "unsupported_panels": 0,
            "panel_types": {},
            "datasources": set(),
            "variables": len(grafana_dashboard.templating.get('list', [])) if grafana_dashboard.templating else 0,
            "annotations": len(grafana_dashboard.annotations.get('list', [])) if grafana_dashboard.annotations else 0
        }
        
        for panel in grafana_dashboard.panels:
            panel_type = panel.get('type', 'unknown')
            summary["panel_types"][panel_type] = summary["panel_types"].get(panel_type, 0) + 1
            
            if panel_type in self.panel_type_mapping:
                summary["supported_panels"] += 1
            else:
                summary["unsupported_panels"] += 1
            
            # Extract datasource information
            if 'targets' in panel:
                for target in panel['targets']:
                    if 'datasource' in target:
                        ds = target['datasource']
                        if isinstance(ds, dict):
                            summary["datasources"].add(ds.get('name', str(ds)))
                        else:
                            summary["datasources"].add(str(ds))
        
        summary["datasources"] = list(summary["datasources"])
        
        return summary 

    def export_to_ndjson(self, kibana_dashboard: KibanaDashboard) -> str:
        """
        Export a KibanaDashboard as newline-delimited JSON (ndjson) for Elastic/Kibana Serverless import.
        Returns a string where each line is a JSON object.
        """
        obj = copy.deepcopy(kibana_dashboard.dict(exclude_none=True))
        # Always re-serialize these fields as valid JSON strings
        if "attributes" in obj:
            for key in ["panelsJSON", "optionsJSON"]:
                if key in obj["attributes"]:
                    val = obj["attributes"][key]
                    # If it's a string but not valid JSON, try to eval and re-dump
                    if isinstance(val, str):
                        try:
                            # Try to parse as JSON
                            val_json = json.loads(val)
                        except Exception:
                            # Try to eval Python repr
                            import ast
                            val_json = ast.literal_eval(val)
                        obj["attributes"][key] = json.dumps(val_json)
                    else:
                        obj["attributes"][key] = json.dumps(val)
            # kibanaSavedObjectMeta.searchSourceJSON
            if "kibanaSavedObjectMeta" in obj["attributes"]:
                meta = obj["attributes"]["kibanaSavedObjectMeta"]
                if isinstance(meta, dict) and "searchSourceJSON" in meta:
                    val = meta["searchSourceJSON"]
                    if isinstance(val, str):
                        try:
                            val_json = json.loads(val)
                        except Exception:
                            import ast
                            val_json = ast.literal_eval(val)
                        meta["searchSourceJSON"] = json.dumps(val_json)
                    else:
                        meta["searchSourceJSON"] = json.dumps(val)
        if obj.get("id") is None:
            obj.pop("id")
        return json.dumps(obj, separators=(",", ":")) + "\n" 