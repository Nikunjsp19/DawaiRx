#!/usr/bin/env python3
"""
End-to-end QA Test Script for DawaiRx
Tests all user-facing functionality systematically
"""

import requests
import json
import time
import sys
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
TEST_USER_ID = "test_user_qa"
TEST_PASSWORD = "test_password_123"
auth_token = None

def log(message, level="INFO"):
    """Log test messages"""
    prefix = {
        "INFO": "ℹ️",
        "PASS": "✅",
        "FAIL": "❌",
        "WARN": "⚠️"
    }.get(level, "ℹ️")
    print(f"{prefix} {message}")

def test_server_running():
    """Test 1: Check if server is running"""
    log("Testing server startup...")
    try:
        response = requests.get(f"{BASE_URL}/login", timeout=5)
        if response.status_code == 200:
            log("Server is running and responding", "PASS")
            return True
        else:
            log(f"Server returned status {response.status_code}", "FAIL")
            return False
    except requests.exceptions.ConnectionError:
        log("Server is not running. Please start it first.", "FAIL")
        return False
    except Exception as e:
        log(f"Error checking server: {e}", "FAIL")
        return False

def test_user_registration():
    """Test 2: User registration"""
    log("Testing user registration...")
    global auth_token
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "user_id": TEST_USER_ID,
                "password": TEST_PASSWORD,
                "email": "test@example.com"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("access_token")
            log(f"User registered successfully. Token received: {bool(auth_token)}", "PASS")
            return True
        elif response.status_code == 400:
            # User might already exist, try login
            log("User may already exist, trying login...", "WARN")
            return test_user_login()
        else:
            log(f"Registration failed: {response.status_code} - {response.text}", "FAIL")
            return False
    except Exception as e:
        log(f"Registration error: {e}", "FAIL")
        return False

def test_user_login():
    """Test 3: User login"""
    log("Testing user login...")
    global auth_token
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "user_id": TEST_USER_ID,
                "password": TEST_PASSWORD
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("access_token")
            log(f"Login successful. Token received: {bool(auth_token)}", "PASS")
            return True
        else:
            log(f"Login failed: {response.status_code} - {response.text}", "FAIL")
            return False
    except Exception as e:
        log(f"Login error: {e}", "FAIL")
        return False

def get_auth_headers():
    """Get authentication headers"""
    if auth_token:
        return {"Authorization": f"Bearer {auth_token}"}
    return {}

def test_dashboard_access():
    """Test 4: Dashboard access"""
    log("Testing dashboard access...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/",
            headers=get_auth_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            log("Dashboard accessible", "PASS")
            return True
        elif response.status_code == 401:
            log("Dashboard requires authentication (expected)", "PASS")
            return True
        else:
            log(f"Dashboard access failed: {response.status_code}", "FAIL")
            return False
    except Exception as e:
        log(f"Dashboard access error: {e}", "FAIL")
        return False

def test_file_upload():
    """Test 5: File upload"""
    log("Testing file upload...")
    
    sample_dir = Path("sample_data")
    inventory_file = sample_dir / "inventory_report.csv"
    supplier_file = sample_dir / "1.akron_generics.csv"
    
    if not inventory_file.exists():
        log(f"Inventory file not found: {inventory_file}", "FAIL")
        return False
    if not supplier_file.exists():
        log(f"Supplier file not found: {supplier_file}", "FAIL")
        return False
    
    try:
        files = {
            'sold_file': (inventory_file.name, open(inventory_file, 'rb'), 'text/csv'),
            'ordered_files': (supplier_file.name, open(supplier_file, 'rb'), 'text/csv')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/upload",
            headers=get_auth_headers(),
            files=files,
            timeout=30
        )
        
        # Close files
        for f in files.values():
            if hasattr(f[1], 'close'):
                f[1].close()
        
        if response.status_code == 200:
            data = response.json()
            session_id = data.get("session_id")
            log(f"File upload successful. Session ID: {session_id}", "PASS")
            return session_id
        else:
            log(f"File upload failed: {response.status_code} - {response.text[:200]}", "FAIL")
            return None
    except Exception as e:
        log(f"File upload error: {e}", "FAIL")
        return None

def test_report_generation(session_id):
    """Test 6: Report generation"""
    log("Testing report generation...")
    
    if not session_id:
        log("No session ID available", "FAIL")
        return None
    
    try:
        data = {
            'session_id': session_id,
            'date_from': '2025-01-01',
            'date_to': '2025-12-31'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/run",
            headers=get_auth_headers(),
            data=data,
            timeout=120  # Report generation can take time
        )
        
        if response.status_code == 200:
            result = response.json()
            run_id = result.get("run_id")
            log(f"Report generation successful. Run ID: {run_id}", "PASS")
            return run_id
        else:
            log(f"Report generation failed: {response.status_code} - {response.text[:500]}", "FAIL")
            return None
    except Exception as e:
        log(f"Report generation error: {e}", "FAIL")
        return None

def test_view_report(run_id):
    """Test 7: View report"""
    log("Testing view report...")
    
    if not run_id:
        log("No run ID available", "FAIL")
        return False
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/runs/{run_id}",
            headers=get_auth_headers(),
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            has_report = bool(data.get("batchrx_report"))
            log(f"Report view successful. Has report data: {has_report}", "PASS")
            return True
        else:
            log(f"Report view failed: {response.status_code} - {response.text[:200]}", "FAIL")
            return False
    except Exception as e:
        log(f"Report view error: {e}", "FAIL")
        return False

def test_list_runs():
    """Test 8: List runs"""
    log("Testing list runs...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/runs?limit=10&offset=0",
            headers=get_auth_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            runs = data.get("runs", [])
            log(f"List runs successful. Found {len(runs)} runs", "PASS")
            return True
        else:
            log(f"List runs failed: {response.status_code} - {response.text[:200]}", "FAIL")
            return False
    except Exception as e:
        log(f"List runs error: {e}", "FAIL")
        return False

def test_download_report(run_id):
    """Test 9: Download report"""
    log("Testing download report...")
    
    if not run_id:
        log("No run ID available", "FAIL")
        return False
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/download/{run_id}/inventory_report",
            headers=get_auth_headers(),
            timeout=30
        )
        
        if response.status_code == 200:
            log("Download successful", "PASS")
            return True
        else:
            log(f"Download failed: {response.status_code} - {response.text[:200]}", "FAIL")
            return False
    except Exception as e:
        log(f"Download error: {e}", "FAIL")
        return False

def main():
    """Run all tests"""
    log("=" * 60)
    log("Starting End-to-End QA Testing")
    log("=" * 60)
    
    results = {}
    
    # Test 1: Server running
    results['server'] = test_server_running()
    if not results['server']:
        log("Server is not running. Please start it with: python3 -m src.cli.main web", "FAIL")
        return
    
    # Test 2: Registration/Login
    results['registration'] = test_user_registration()
    if not results['registration']:
        results['login'] = test_user_login()
        if not results['login']:
            log("Cannot proceed without authentication", "FAIL")
            return
    
    # Test 3: Dashboard
    results['dashboard'] = test_dashboard_access()
    
    # Test 4: File upload
    session_id = test_file_upload()
    results['upload'] = session_id is not None
    
    # Test 5: Report generation
    run_id = None
    if session_id:
        run_id = test_report_generation(session_id)
        results['generation'] = run_id is not None
    else:
        results['generation'] = False
    
    # Test 6: View report
    if run_id:
        results['view'] = test_view_report(run_id)
    else:
        results['view'] = False
    
    # Test 7: List runs
    results['list'] = test_list_runs()
    
    # Test 8: Download
    if run_id:
        results['download'] = test_download_report(run_id)
    else:
        results['download'] = False
    
    # Summary
    log("=" * 60)
    log("Test Results Summary")
    log("=" * 60)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        log(f"{test_name}: {status}", status)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    log(f"\nTotal: {passed}/{total} tests passed", "PASS" if passed == total else "FAIL")
    
    return results

if __name__ == "__main__":
    main()

