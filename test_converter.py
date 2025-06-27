#!/usr/bin/env python3
"""
Test script for Grafana to Kibana converter
"""

import json
import requests
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
SAMPLE_DASHBOARD_PATH = "sample_dashboard.json"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_mcp_status():
    """Test the MCP status endpoint"""
    print("Testing MCP status...")
    try:
        response = requests.get(f"{BASE_URL}/mcp/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ MCP status: {data}")
            return True
        else:
            print(f"❌ MCP status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ MCP status error: {e}")
        return False

def test_mcp_capabilities():
    """Test the MCP capabilities endpoint"""
    print("Testing MCP capabilities...")
    try:
        response = requests.get(f"{BASE_URL}/mcp/capabilities")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ MCP capabilities: {len(data.get('supported_panel_types', []))} panel types supported")
            return True
        else:
            print(f"❌ MCP capabilities failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ MCP capabilities error: {e}")
        return False

def test_dashboard_validation():
    """Test dashboard validation"""
    print("Testing dashboard validation...")
    try:
        with open(SAMPLE_DASHBOARD_PATH, 'r') as f:
            dashboard_data = json.load(f)
        
        response = requests.post(f"{BASE_URL}/mcp/validate", json=dashboard_data)
        if response.status_code == 200:
            data = response.json()
            if data.get('valid'):
                print("✅ Dashboard validation passed")
                summary = data.get('summary', {})
                print(f"   - Total panels: {summary.get('total_panels', 0)}")
                print(f"   - Supported panels: {summary.get('supported_panels', 0)}")
                print(f"   - Unsupported panels: {summary.get('unsupported_panels', 0)}")
                return True
            else:
                print(f"❌ Dashboard validation failed: {data.get('errors', [])}")
                return False
        else:
            print(f"❌ Dashboard validation request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Dashboard validation error: {e}")
        return False

def test_dashboard_conversion():
    """Test dashboard conversion via MCP"""
    print("Testing dashboard conversion via MCP...")
    try:
        with open(SAMPLE_DASHBOARD_PATH, 'r') as f:
            dashboard_data = json.load(f)
        
        conversion_request = {
            "dashboard": dashboard_data,
            "options": {
                "preserve_panel_ids": True,
                "convert_queries": True,
                "convert_visualizations": True,
                "convert_variables": True,
                "convert_annotations": True,
                "target_kibana_version": "8.11.0"
            }
        }
        
        response = requests.post(f"{BASE_URL}/mcp/convert", json=conversion_request)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'completed':
                print("✅ Dashboard conversion via MCP passed")
                print(f"   - Conversion time: {data.get('conversion_time_ms', 0)}ms")
                print(f"   - Conversion ID: {data.get('id', 'N/A')}")
                return data.get('id')
            else:
                print(f"❌ Dashboard conversion failed: {data.get('error_message', 'Unknown error')}")
                return None
        else:
            print(f"❌ Dashboard conversion request failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Dashboard conversion error: {e}")
        return None

def test_web_upload():
    """Test web interface upload"""
    print("Testing web interface upload...")
    try:
        with open(SAMPLE_DASHBOARD_PATH, 'rb') as f:
            files = {'file': (SAMPLE_DASHBOARD_PATH, f, 'application/json')}
            data = {
                'preserve_panel_ids': True,
                'convert_queries': True,
                'convert_visualizations': True,
                'convert_variables': True,
                'convert_annotations': True,
                'target_kibana_version': '8.11.0'
            }
            
            response = requests.post(f"{BASE_URL}/upload", files=files, data=data)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✅ Web interface upload passed")
                    print(f"   - File ID: {result.get('file_id', 'N/A')}")
                    print(f"   - Conversion time: {result.get('conversion_time_ms', 0)}ms")
                    return result.get('file_id')
                else:
                    print(f"❌ Web interface upload failed: {result.get('error', 'Unknown error')}")
                    return None
            else:
                print(f"❌ Web interface upload request failed: {response.status_code}")
                return None
    except Exception as e:
        print(f"❌ Web interface upload error: {e}")
        return None

def test_download(file_id):
    """Test file download"""
    if not file_id:
        print("❌ No file ID provided for download test")
        return False
    
    print(f"Testing file download for ID: {file_id}")
    try:
        response = requests.get(f"{BASE_URL}/download/{file_id}")
        if response.status_code == 200:
            # Save the downloaded file
            output_path = f"converted_dashboard_{file_id}.json"
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ File download successful: {output_path}")
            
            # Validate the downloaded file
            try:
                kibana_dashboard = json.loads(response.content)
                if kibana_dashboard.get('type') == 'dashboard':
                    print("✅ Downloaded file is valid Kibana dashboard")
                    return True
                else:
                    print("❌ Downloaded file is not a valid Kibana dashboard")
                    return False
            except json.JSONDecodeError:
                print("❌ Downloaded file is not valid JSON")
                return False
        else:
            print(f"❌ File download failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ File download error: {e}")
        return False

def test_batch_conversion():
    """Test batch conversion"""
    print("Testing batch conversion...")
    try:
        with open(SAMPLE_DASHBOARD_PATH, 'r') as f:
            dashboard_data = json.load(f)
        
        # Create multiple dashboards for batch testing
        dashboards = [
            {**dashboard_data, "title": f"Dashboard {i+1}"}
            for i in range(3)
        ]
        
        batch_request = {
            "dashboards": dashboards,
            "options": {
                "preserve_panel_ids": True,
                "convert_queries": True,
                "convert_visualizations": True,
                "convert_variables": True,
                "convert_annotations": True,
                "target_kibana_version": "8.11.0"
            }
        }
        
        response = requests.post(f"{BASE_URL}/mcp/batch", json=batch_request)
        if response.status_code == 200:
            data = response.json()
            batch_id = data.get('batch_id')
            print(f"✅ Batch conversion started: {batch_id}")
            
            # Wait for batch completion
            max_wait = 30
            wait_time = 0
            while wait_time < max_wait:
                time.sleep(2)
                wait_time += 2
                
                status_response = requests.get(f"{BASE_URL}/mcp/batch/{batch_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if status_data.get('completed_at'):
                        print(f"✅ Batch conversion completed: {status_data.get('completed')} successful, {status_data.get('failed')} failed")
                        return True
            
            print("❌ Batch conversion timed out")
            return False
        else:
            print(f"❌ Batch conversion request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Batch conversion error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Grafana to Kibana Converter Tests")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("MCP Status", test_mcp_status),
        ("MCP Capabilities", test_mcp_capabilities),
        ("Dashboard Validation", test_dashboard_validation),
        ("MCP Conversion", test_dashboard_conversion),
        ("Web Upload", test_web_upload),
        ("Batch Conversion", test_batch_conversion),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            result = test_func()
            results[test_name] = result
            
            if test_name == "MCP Conversion" and result:
                # Test download for MCP conversion
                print("\n📥 Testing MCP conversion download...")
                download_result = test_download(result)
                results["MCP Download"] = download_result
            
            elif test_name == "Web Upload" and result:
                # Test download for web upload
                print("\n📥 Testing web upload download...")
                download_result = test_download(result)
                results["Web Download"] = download_result
                
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The converter is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the application logs.")

if __name__ == "__main__":
    main() 