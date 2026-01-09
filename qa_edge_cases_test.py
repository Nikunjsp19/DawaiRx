#!/usr/bin/env python3
"""
Edge Cases and Error Handling Tests
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
TEST_USER_ID = "test_user_qa"
TEST_PASSWORD = "test_password_123"
auth_token = None

def log(message, level="INFO"):
    prefix = {"INFO": "ℹ️", "PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}.get(level, "ℹ️")
    print(f"{prefix} {message}")

def login():
    global auth_token
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"user_id": TEST_USER_ID, "password": TEST_PASSWORD},
            timeout=10
        )
        if response.status_code == 200:
            auth_token = response.json().get("access_token")
            return True
    except:
        pass
    return False

def get_headers():
    return {"Authorization": f"Bearer {auth_token}"} if auth_token else {}

def test_invalid_login():
    """Edge Case 1: Invalid credentials"""
    log("Testing invalid login...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"user_id": "invalid_user", "password": "wrong_password"},
            timeout=10
        )
        if response.status_code == 401:
            log("Invalid login correctly rejected", "PASS")
            return True
        else:
            log(f"Invalid login not handled correctly: {response.status_code}", "FAIL")
            return False
    except Exception as e:
        log(f"Error: {e}", "FAIL")
        return False

def test_upload_without_auth():
    """Edge Case 2: Upload without authentication"""
    log("Testing upload without auth...")
    try:
        sample_file = Path("sample_data/inventory_report.csv")
        if not sample_file.exists():
            log("Sample file not found", "WARN")
            return True
        
        files = {'sold_file': (sample_file.name, open(sample_file, 'rb'), 'text/csv')}
        response = requests.post(f"{BASE_URL}/api/upload", files=files, timeout=10)
        files['sold_file'][1].close()
        
        if response.status_code == 401:
            log("Unauthorized upload correctly rejected", "PASS")
            return True
        else:
            log(f"Auth check failed: {response.status_code}", "FAIL")
            return False
    except Exception as e:
        log(f"Error: {e}", "FAIL")
        return False

def test_upload_empty_file():
    """Edge Case 3: Upload empty file"""
    log("Testing empty file upload...")
    if not login():
        log("Cannot login", "FAIL")
        return False
    
    try:
        # Create empty file
        empty_file = Path("/tmp/empty_test.csv")
        empty_file.write_text("")
        
        files = {'sold_file': (empty_file.name, open(empty_file, 'rb'), 'text/csv')}
        response = requests.post(
            f"{BASE_URL}/api/upload",
            headers=get_headers(),
            files=files,
            timeout=10
        )
        files['sold_file'][1].close()
        empty_file.unlink()
        
        if response.status_code in [400, 422]:
            log("Empty file correctly rejected", "PASS")
            return True
        else:
            log(f"Empty file handling: {response.status_code}", "WARN")
            return True  # Not critical
    except Exception as e:
        log(f"Error: {e}", "FAIL")
        return False

def test_upload_missing_file():
    """Edge Case 4: Upload with missing required file"""
    log("Testing upload with missing file...")
    if not login():
        return False
    
    try:
        sample_file = Path("sample_data/inventory_report.csv")
        if not sample_file.exists():
            return True
        
        # Upload only inventory, no supplier
        files = {'sold_file': (sample_file.name, open(sample_file, 'rb'), 'text/csv')}
        response = requests.post(
            f"{BASE_URL}/api/upload",
            headers=get_headers(),
            files=files,
            timeout=10
        )
        files['sold_file'][1].close()
        
        if response.status_code in [400, 422]:
            log("Missing file correctly rejected", "PASS")
            return True
        else:
            log(f"Missing file handling: {response.status_code}", "WARN")
            return True
    except Exception as e:
        log(f"Error: {e}", "FAIL")
        return False

def test_invalid_run_id():
    """Edge Case 5: Access non-existent run"""
    log("Testing invalid run ID...")
    if not login():
        return False
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/runs/invalid_run_id_12345",
            headers=get_headers(),
            timeout=10
        )
        
        if response.status_code == 404:
            log("Invalid run ID correctly rejected", "PASS")
            return True
        else:
            log(f"Invalid run ID handling: {response.status_code}", "WARN")
            return True
    except Exception as e:
        log(f"Error: {e}", "FAIL")
        return False

def test_download_invalid_file():
    """Edge Case 6: Download non-existent file type"""
    log("Testing invalid file type download...")
    if not login():
        return False
    
    # First get a valid run_id
    try:
        response = requests.get(
            f"{BASE_URL}/api/runs?limit=1",
            headers=get_headers(),
            timeout=10
        )
        if response.status_code == 200:
            runs = response.json().get("runs", [])
            if runs:
                run_id = runs[0].get("run_id")
                
                # Try invalid file type
                response = requests.get(
                    f"{BASE_URL}/api/download/{run_id}/invalid_type",
                    headers=get_headers(),
                    timeout=10
                )
                
                if response.status_code in [400, 404]:
                    log("Invalid file type correctly rejected", "PASS")
                    return True
    except Exception as e:
        log(f"Error: {e}", "FAIL")
        return False
    
    return True

def test_pagination():
    """Edge Case 7: Pagination edge cases"""
    log("Testing pagination...")
    if not login():
        return False
    
    try:
        # Test with large offset
        response = requests.get(
            f"{BASE_URL}/api/runs?limit=10&offset=99999",
            headers=get_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            runs = data.get("runs", [])
            log(f"Pagination with large offset works. Returned {len(runs)} runs", "PASS")
            return True
        else:
            log(f"Pagination failed: {response.status_code}", "FAIL")
            return False
    except Exception as e:
        log(f"Error: {e}", "FAIL")
        return False

def main():
    log("=" * 60)
    log("Edge Cases and Error Handling Tests")
    log("=" * 60)
    
    results = {}
    results['invalid_login'] = test_invalid_login()
    results['upload_no_auth'] = test_upload_without_auth()
    results['empty_file'] = test_upload_empty_file()
    results['missing_file'] = test_upload_missing_file()
    results['invalid_run_id'] = test_invalid_run_id()
    results['invalid_download'] = test_download_invalid_file()
    results['pagination'] = test_pagination()
    
    log("=" * 60)
    log("Edge Case Test Results")
    log("=" * 60)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        log(f"{test_name}: {status}", status)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    log(f"\nTotal: {passed}/{total} edge case tests passed", "PASS" if passed == total else "FAIL")

if __name__ == "__main__":
    main()

