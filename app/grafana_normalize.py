"""
Normalize Grafana dashboard JSON variants into the classic shape expected by the converter:
  { "title", "uid", "panels": [...], "time", "tags", ... }

Supports:
  - Classic Grafana dashboards (passed through unchanged if already valid)
  - Grafana Kubernetes app / Grafana Cloud: apiVersion dashboard.grafana.app/v2beta1, kind Dashboard
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


def _panel_key_order(key: str) -> Tuple[int, str]:
    m = re.match(r"panel-(\d+)$", key or "")
    if m:
        return (int(m.group(1)), key)
    return (10**9, key)


def _viz_group_to_panel_type(group: str) -> str:
    g = (group or "timeseries").lower()
    mapping = {
        "timeseries": "timeseries",
        "stat": "stat",
        "table": "table",
        "piechart": "piechart",
        "barchart": "graph",
        "bargauge": "bargauge",
        "gauge": "gauge",
        "heatmap": "heatmap",
    }
    return mapping.get(g, "timeseries")


def _extract_targets_from_data(data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not data or data.get("kind") != "QueryGroup":
        return [{"refId": "A", "expr": "*"}]
    spec = data.get("spec") or {}
    queries = spec.get("queries") or []
    targets: List[Dict[str, Any]] = []
    for q in queries:
        if q.get("kind") != "PanelQuery":
            continue
        qspec = q.get("spec") or {}
        pq = qspec.get("query") or {}
        inner = pq.get("spec") or {}
        lucene = inner.get("query", "") or "*"
        ref_id = qspec.get("refId", "A")
        ds = pq.get("datasource") or {}
        ds_name = ds.get("name", "elasticsearch") if isinstance(ds, dict) else str(ds)
        targets.append(
            {
                "refId": ref_id,
                "expr": lucene,
                "datasource": {"type": "elasticsearch", "name": ds_name},
            }
        )
    return targets if targets else [{"refId": "A", "expr": "*"}]


def _variables_to_templating(variables: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    lst: List[Dict[str, Any]] = []
    for v in variables:
        kind = v.get("kind")
        spec = v.get("spec") or {}
        if kind == "DatasourceVariable":
            cur = spec.get("current") or {}
            lst.append(
                {
                    "name": spec.get("name", "DS"),
                    "type": "datasource",
                    "query": spec.get("pluginId", "elasticsearch"),
                    "current": {
                        "text": cur.get("text", ""),
                        "value": cur.get("value", ""),
                    },
                }
            )
    return {"list": lst} if lst else None


def is_grafana_app_dashboard_v2(d: Dict[str, Any]) -> bool:
    av = str(d.get("apiVersion") or "")
    return "dashboard.grafana.app" in av and d.get("kind") == "Dashboard" and isinstance(d.get("spec"), dict)


def normalize_grafana_dashboard(dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    If input is dashboard.grafana.app/v2beta1 (spec.elements + spec.layout), convert to classic Grafana JSON.
    Otherwise return the same dict (shallow copy of top-level keys we replace is not needed if we build new dict for v2 only).
    """
    if not is_grafana_app_dashboard_v2(dashboard_data):
        return dashboard_data

    spec = dashboard_data["spec"]
    meta = dashboard_data.get("metadata") or {}
    elements = spec.get("elements") or {}

    layout_items = ((spec.get("layout") or {}).get("spec") or {}).get("items") or []
    layout_by_element: Dict[str, Dict[str, int]] = {}
    for item in layout_items:
        isp = item.get("spec") or {}
        el = (isp.get("element") or {}).get("name")
        if el:
            layout_by_element[el] = {
                "x": int(isp.get("x", 0)),
                "y": int(isp.get("y", 0)),
                "w": int(isp.get("width", 12)),
                "h": int(isp.get("height", 8)),
            }

    panels: List[Dict[str, Any]] = []
    for el_key, el_val in sorted(elements.items(), key=lambda kv: _panel_key_order(kv[0])):
        if not isinstance(el_val, dict) or el_val.get("kind") != "Panel":
            continue
        pspec = el_val.get("spec") or {}
        pid = pspec.get("id")
        title = pspec.get("title") or "Untitled"
        viz = pspec.get("vizConfig") or {}
        grafana_type = _viz_group_to_panel_type(viz.get("group", "timeseries"))
        grid_pos = layout_by_element.get(
            el_key, {"x": 0, "y": 0, "w": 12, "h": 8}
        )
        targets = _extract_targets_from_data(pspec.get("data"))
        inner_viz_spec = viz.get("spec") or {}
        field_config = inner_viz_spec.get("fieldConfig")

        panel: Dict[str, Any] = {
            "id": pid,
            "type": grafana_type,
            "title": title,
            "gridPos": grid_pos,
            "targets": targets,
        }
        if field_config:
            panel["fieldConfig"] = field_config
        panels.append(panel)

    panels.sort(
        key=lambda p: (
            p.get("gridPos", {}).get("y", 0),
            p.get("gridPos", {}).get("x", 0),
            p.get("id") or 0,
        )
    )

    time_settings = spec.get("timeSettings") or {}
    time_obj = {
        "from": time_settings.get("from", "now-6h"),
        "to": time_settings.get("to", "now"),
    }

    out: Dict[str, Any] = {
        "title": spec.get("title") or meta.get("name") or "Imported dashboard",
        "uid": meta.get("uid"),
        "version": 1,
        "time": time_obj,
        "timezone": time_settings.get("timezone", "browser"),
        "schemaVersion": 39,
        "panels": panels,
        "tags": list(spec.get("tags") or []),
        "editable": spec.get("editable", True),
        "graphTooltip": 0,
        "hideControls": False,
    }
    if time_settings.get("autoRefresh"):
        out["refresh"] = time_settings["autoRefresh"]

    tmpl = _variables_to_templating(spec.get("variables") or [])
    if tmpl:
        out["templating"] = tmpl

    ann = spec.get("annotations") or []
    if ann:
        ann_list: List[Dict[str, Any]] = []
        for a in ann:
            if not isinstance(a, dict):
                continue
            aspec = a.get("spec") or {}
            ann_list.append(
                {
                    "name": aspec.get("name", "annotation"),
                    "type": "dashboard",
                    "enable": aspec.get("enable", True),
                }
            )
        if ann_list:
            out["annotations"] = {"list": ann_list}

    return out
