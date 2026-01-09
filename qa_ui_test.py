#!/usr/bin/env python3
"""
UI Flow Test - Simulates user interactions
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
TEST_USER_ID = "test_user_qa"
TEST_PASSWORD = "test_password_123"

def log(message, level="INFO"):
    prefix = {"INFO": "ℹ️", "PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}.get(level, "ℹ️")
    print(f"{prefix} {message}")

def login():
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"user_id": TEST_USER_ID, "password": TEST_PASSWORD},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("access_token")
    except:
        pass
    return None

def test_complete_workflow():
    """Test complete user workflow"""
    log("Testing complete user workflow...")
    
    # 1. Login
    token = login()
    if not token:
        log("Cannot login", "FAIL")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    log("Step 1: Login successful", "PASS")
    
    # 2. Upload files
    inventory_file = Path("sample_data/inventory_report.csv")
    supplier_file = Path("sample_data/1.akron_generics.csv")
    
    if not inventory_file.exists() or not supplier_file.exists():
        log("Sample files not found", "FAIL")
        return False
    
    files = {
        'sold_file': (inventory_file.name, open(inventory_file, 'rb'), 'text/csv'),
        'ordered_files': (supplier_file.name, open(supplier_file, 'rb'), 'text/csv')
    }
    
    response = requests.post(
        f"{BASE_URL}/api/upload",
        headers=headers,
        files=files,
        timeout=30
    )
    
    for f in files.values():
        f[1].close()
    
    if response.status_code != 200:
        log(f"Upload failed: {response.status_code}", "FAIL")
        return False
    
    session_id = response.json().get("session_id")
    log("Step 2: File upload successful", "PASS")
    
    # 3. Generate report
    data = {
        'session_id': session_id,
        'date_from': '2025-01-01',
        'date_to': '2025-12-31'
    }
    
    response = requests.post(
        f"{BASE_URL}/api/run",
        headers=headers,
        data=data,
        timeout=120
    )
    
    if response.status_code != 200:
        log(f"Report generation failed: {response.status_code}", "FAIL")
        return False
    
    run_id = response.json().get("run_id")
    log("Step 3: Report generation successful", "PASS")
    
    # 4. View report via API
    response = requests.get(
        f"{BASE_URL}/api/runs/{run_id}",
        headers=headers,
        timeout=30
    )
    
    if response.status_code != 200:
        log(f"View report failed: {response.status_code}", "FAIL")
        return False
    
    data = response.json()
    has_report = bool(data.get("batchrx_report"))
    has_columns = bool(data.get("batchrx_columns"))
    row_count = data.get("batchrx_row_count", 0)
    
    log(f"Step 4: View report - Has data: {has_report}, Columns: {has_columns}, Rows: {row_count}", 
        "PASS" if has_report and has_columns else "FAIL")
    
    # 5. List runs
    response = requests.get(
        f"{BASE_URL}/api/runs?limit=10&offset=0",
        headers=headers,
        timeout=10
    )
    
    if response.status_code != 200:
        log(f"List runs failed: {response.status_code}", "FAIL")
        return False
    
    runs = response.json().get("runs", [])
    found_run = any(r.get("run_id") == run_id for r in runs)
    log(f"Step 5: List runs - Found {len(runs)} runs, Our run present: {found_run}", 
        "PASS" if found_run else "WARN")
    
    # 6. Download report
    response = requests.get(
        f"{BASE_URL}/api/download/{run_id}/inventory_report",
        headers=headers,
        timeout=30
    )
    
    if response.status_code != 200:
        log(f"Download failed: {response.status_code}", "FAIL")
        return False
    
    log("Step 6: Download successful", "PASS")
    
    # 7. Test report page URL
    response = requests.get(
        f"{BASE_URL}/new-report?run_id={run_id}",
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        # Check if page contains report data indicators
        content = response.text
        has_results = 'results' in content.lower() or 'dataTables' in content
        log(f"Step 7: Report page accessible - Has results section: {has_results}", 
            "PASS" if has_results else "WARN")
    else:
        log(f"Report page failed: {response.status_code}", "FAIL")
        return False
    
    log("=" * 60)
    log("Complete workflow test: PASSED", "PASS")
    return True

if __name__ == "__main__":
    test_complete_workflow()

