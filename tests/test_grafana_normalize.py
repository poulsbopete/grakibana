"""Unit tests for Grafana dashboard.grafana.app/v2beta1 normalization."""

import unittest

from app.converter import DashboardConverter
from app.grafana_normalize import is_grafana_app_dashboard_v2, normalize_grafana_dashboard
from app.models import GrafanaDashboard


MIN_V2 = {
    "apiVersion": "dashboard.grafana.app/v2beta1",
    "kind": "Dashboard",
    "metadata": {"uid": "test-uid", "name": "meta-name"},
    "spec": {
        "title": "Prom-Demo",
        "tags": ["k8s"],
        "editable": True,
        "variables": [
            {
                "kind": "DatasourceVariable",
                "spec": {
                    "name": "ELASTICSEARCH_DS",
                    "pluginId": "elasticsearch",
                    "current": {"text": "ES", "value": "ef77"},
                },
            }
        ],
        "annotations": [
            {
                "kind": "AnnotationQuery",
                "spec": {"name": "Annotations & Alerts", "enable": True},
            }
        ],
        "elements": {
            "panel-2": {
                "kind": "Panel",
                "spec": {
                    "id": 2,
                    "title": "Second",
                    "data": {
                        "kind": "QueryGroup",
                        "spec": {
                            "queries": [
                                {
                                    "kind": "PanelQuery",
                                    "spec": {
                                        "refId": "A",
                                        "query": {
                                            "kind": "DataQuery",
                                            "group": "elasticsearch",
                                            "version": "v0",
                                            "datasource": {"name": "ds1"},
                                            "spec": {
                                                "query": "foo:bar",
                                                "timeField": "@timestamp",
                                            },
                                        },
                                    },
                                }
                            ]
                        },
                    },
                    "vizConfig": {
                        "group": "stat",
                        "version": "12",
                        "spec": {
                            "fieldConfig": {
                                "defaults": {"unit": "short"},
                                "overrides": [],
                            }
                        },
                    },
                },
            },
            "panel-1": {
                "kind": "Panel",
                "spec": {
                    "id": 1,
                    "title": "First",
                    "data": {"kind": "QueryGroup", "spec": {"queries": []}},
                    "vizConfig": {"group": "timeseries", "spec": {}},
                },
            },
        },
        "layout": {
            "kind": "GridLayout",
            "spec": {
                "items": [
                    {
                        "kind": "GridLayoutItem",
                        "spec": {
                            "x": 6,
                            "y": 0,
                            "width": 6,
                            "height": 8,
                            "element": {"kind": "ElementReference", "name": "panel-2"},
                        },
                    },
                    {
                        "kind": "GridLayoutItem",
                        "spec": {
                            "x": 0,
                            "y": 0,
                            "width": 6,
                            "height": 8,
                            "element": {"kind": "ElementReference", "name": "panel-1"},
                        },
                    },
                ]
            },
        },
        "timeSettings": {
            "from": "now-1h",
            "to": "now",
            "timezone": "browser",
            "autoRefresh": "30s",
        },
    },
}


class TestGrafanaV2Normalize(unittest.TestCase):
    def test_detect_v2(self):
        self.assertTrue(is_grafana_app_dashboard_v2(MIN_V2))
        self.assertFalse(is_grafana_app_dashboard_v2({"title": "x", "panels": []}))

    def test_normalize_produces_classic_shape(self):
        n = normalize_grafana_dashboard(MIN_V2)
        self.assertEqual(n["title"], "Prom-Demo")
        self.assertEqual(n["uid"], "test-uid")
        self.assertEqual(len(n["panels"]), 2)
        self.assertEqual(n["refresh"], "30s")
        self.assertIn("templating", n)
        self.assertEqual(n["templating"]["list"][0]["name"], "ELASTICSEARCH_DS")
        self.assertEqual(len(n["annotations"]["list"]), 1)

    def test_panel_order_and_grid(self):
        n = normalize_grafana_dashboard(MIN_V2)
        # Sorted by y then x: panel-1 at (0,0) then panel-2 at (6,0)
        self.assertEqual(n["panels"][0]["title"], "First")
        self.assertEqual(n["panels"][0]["gridPos"], {"x": 0, "y": 0, "w": 6, "h": 8})
        self.assertEqual(n["panels"][1]["type"], "stat")
        self.assertEqual(n["panels"][1]["targets"][0]["expr"], "foo:bar")

    def test_validate_and_pydantic(self):
        c = DashboardConverter()
        self.assertTrue(c.validate_grafana_dashboard(MIN_V2))
        g = GrafanaDashboard(**MIN_V2)
        self.assertEqual(g.title, "Prom-Demo")
        self.assertEqual(len(g.panels), 2)

    def test_convert_completes(self):
        c = DashboardConverter()
        g = GrafanaDashboard(**MIN_V2)
        resp = c.convert_dashboard(g)
        self.assertEqual(resp.status.value, "completed")
        self.assertIsNotNone(resp.kibana_dashboard)


if __name__ == "__main__":
    unittest.main()
