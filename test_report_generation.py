#!/usr/bin/env python3
"""Test script to generate a report and compare with BatchRX"""

import requests
import json
import pandas as pd
from pathlib import Path
import time

# Configuration
BASE_URL = "http://127.0.0.1:8000"
USER_ID = "nikunjpatel19081999@gmail.com"
PASSWORD = "Niks@1908"

# File paths
SAMPLE_DATA_DIR = Path("sample_data")
INVENTORY_FILE = SAMPLE_DATA_DIR / "inventory_report.csv"
SUPPLIER_FILES = [
    SAMPLE_DATA_DIR / "1.akron_generics.csv",
    SAMPLE_DATA_DIR / "2_alpine_health.csv",
    SAMPLE_DATA_DIR / "3_kinray.csv",
    SAMPLE_DATA_DIR / "4 supplier_legacy_health.csv",
    SAMPLE_DATA_DIR / "5_supplier_smith_drugs.csv",
]
BATCHRX_REFERENCE = SAMPLE_DATA_DIR / "BatchRX_report.csv"

def login():
    """Login and get auth token"""
    print("🔐 Logging in...")
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"user_id": USER_ID, "password": PASSWORD}
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login successful")
        return token
    elif response.status_code == 401:
        print("⚠️ User not found, registering...")
        # Register first
        reg_response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "user_id": USER_ID,
                "email": USER_ID,
                "password": PASSWORD
            }
        )
        if reg_response.status_code == 200:
            token = reg_response.json()["access_token"]
            print(f"✅ Registration successful")
            return token
        elif "already exists" in reg_response.text:
            print("⚠️ User already exists, trying login again...")
            # User exists, try login again (maybe password was wrong)
            login_response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"user_id": USER_ID, "password": PASSWORD}
            )
            if login_response.status_code == 200:
                token = login_response.json()["access_token"]
                print(f"✅ Login successful after registration attempt")
                return token
            else:
                print(f"❌ Login still failed: {login_response.status_code} - {login_response.text}")
                return None
        else:
            print(f"❌ Registration failed: {reg_response.status_code} - {reg_response.text}")
            return None
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

def upload_files_and_generate_report(token, date_from="2025-05-01", date_to="2025-12-01"):
    """Upload files and generate report"""
    print("\n📤 Step 1: Uploading files...")
    
    # Prepare files
    files = []
    
    # Inventory file (sold_file)
    if not INVENTORY_FILE.exists():
        print(f"❌ Inventory file not found: {INVENTORY_FILE}")
        return None
    files.append(("sold_file", (INVENTORY_FILE.name, open(INVENTORY_FILE, "rb"), "text/csv")))
    
    # Supplier files (ordered_files - multiple)
    for supplier_file in SUPPLIER_FILES:
        if not supplier_file.exists():
            print(f"⚠️ Supplier file not found: {supplier_file}, skipping...")
            continue
        files.append(("ordered_files", (supplier_file.name, open(supplier_file, "rb"), "text/csv")))
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"   Uploading {len(files)} files...")
    
    try:
        # Step 1: Upload files
        response = requests.post(
            f"{BASE_URL}/api/upload",
            files=files,
            headers=headers,
            timeout=300  # 5 minutes timeout
        )
        
        # Close file handles
        for _, file_tuple in files:
            file_tuple[1].close()
        
        if response.status_code != 200:
            print(f"❌ File upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
        
        upload_result = response.json()
        session_id = upload_result.get("session_id")
        print(f"✅ Files uploaded successfully!")
        print(f"   Session ID: {session_id}")
        
        # Step 2: Generate report
        print(f"\n📊 Step 2: Generating report...")
        print(f"   Date range: {date_from} to {date_to}")
        
        run_response = requests.post(
            f"{BASE_URL}/api/run",
            data={
                "session_id": session_id,
                "date_from": date_from,
                "date_to": date_to,
            },
            headers=headers,
            timeout=300  # 5 minutes timeout
        )
        
        if run_response.status_code == 200:
            result = run_response.json()
            run_id = result.get("run_id")
            print(f"✅ Report generated successfully!")
            print(f"   Run ID: {run_id}")
            return run_id
        else:
            print(f"❌ Report generation failed: {run_response.status_code}")
            print(f"   Response: {run_response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error during report generation: {e}")
        import traceback
        traceback.print_exc()
        # Close file handles in case of error
        for _, file_tuple in files:
            try:
                file_tuple[1].close()
            except:
                pass
        return None

def download_report(token, run_id, output_file):
    """Download the generated report"""
    print(f"\n📥 Downloading report {run_id}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Use correct download endpoint
    response = requests.get(
        f"{BASE_URL}/api/download/{run_id}/inventory_report",
        headers=headers,
        stream=True
    )
    
    if response.status_code == 200:
        with open(output_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✅ Report downloaded to: {output_file}")
        return True
    else:
        print(f"❌ Download failed: {response.status_code} - {response.text}")
        return False

def compare_reports(generated_file, reference_file):
    """Compare generated report with BatchRX reference"""
    print(f"\n🔍 Comparing reports...")
    print(f"   Generated: {generated_file}")
    print(f"   Reference: {reference_file}")
    
    try:
        # Read both files
        gen_df = pd.read_csv(generated_file)
        ref_df = pd.read_csv(reference_file)
        
        print(f"\n📊 Report Statistics:")
        print(f"   Generated rows: {len(gen_df)}")
        print(f"   Reference rows: {len(ref_df)}")
        print(f"   Generated columns: {len(gen_df.columns)}")
        print(f"   Reference columns: {len(ref_df.columns)}")
        
        # Compare column names
        gen_cols = set(gen_df.columns)
        ref_cols = set(ref_df.columns)
        
        missing_in_gen = ref_cols - gen_cols
        extra_in_gen = gen_cols - ref_cols
        
        if missing_in_gen:
            print(f"\n⚠️ Columns missing in generated report: {missing_in_gen}")
        if extra_in_gen:
            print(f"⚠️ Extra columns in generated report: {extra_in_gen}")
        
        # Compare by NDC
        gen_ndcs = set(gen_df['NDC'].astype(str) if 'NDC' in gen_df.columns else set())
        ref_ndcs = set(ref_df['NDC'].astype(str) if 'NDC' in ref_df.columns else set())
        
        missing_ndcs = ref_ndcs - gen_ndcs
        extra_ndcs = gen_ndcs - ref_ndcs
        
        if missing_ndcs:
            print(f"\n⚠️ NDCs missing in generated report ({len(missing_ndcs)}): {list(missing_ndcs)[:10]}")
        if extra_ndcs:
            print(f"⚠️ Extra NDCs in generated report ({len(extra_ndcs)}): {list(extra_ndcs)[:10]}")
        
        # Compare common NDCs
        common_ndcs = gen_ndcs & ref_ndcs
        print(f"\n📋 Common NDCs: {len(common_ndcs)}")
        
        if len(common_ndcs) > 0:
            # Compare key columns for common NDCs
            gen_common = gen_df[gen_df['NDC'].astype(str).isin(common_ndcs)].set_index('NDC')
            ref_common = ref_df[ref_df['NDC'].astype(str).isin(common_ndcs)].set_index('NDC')
            
            # Compare AMOUNT
            if 'AMOUNT' in gen_common.columns and 'AMOUNT' in ref_common.columns:
                amount_diff = (gen_common['AMOUNT'] - ref_common['AMOUNT']).abs()
                amount_mismatches = amount_diff[amount_diff > 0.01]
                if len(amount_mismatches) > 0:
                    print(f"\n⚠️ AMOUNT mismatches ({len(amount_mismatches)}):")
                    for ndc in amount_mismatches.head(10).index:
                        print(f"   {ndc}: Generated={gen_common.loc[ndc, 'AMOUNT']}, Reference={ref_common.loc[ndc, 'AMOUNT']}")
            
            # Compare COST
            if 'COST' in gen_common.columns and 'COST' in ref_common.columns:
                cost_diff = (gen_common['COST'] - ref_common['COST']).abs()
                cost_mismatches = cost_diff[cost_diff > 0.01]
                if len(cost_mismatches) > 0:
                    print(f"\n⚠️ COST mismatches ({len(cost_mismatches)}):")
                    for ndc in cost_mismatches.head(10).index:
                        print(f"   {ndc}: Generated={gen_common.loc[ndc, 'COST']}, Reference={ref_common.loc[ndc, 'COST']}")
            
            # Compare RANK
            if 'RANK' in gen_common.columns and 'RANK' in ref_common.columns:
                rank_diff = (gen_common['RANK'] - ref_common['RANK']).abs()
                rank_mismatches = rank_diff[rank_diff > 0]
                if len(rank_mismatches) > 0:
                    print(f"\n⚠️ RANK mismatches ({len(rank_mismatches)}):")
                    for ndc in rank_mismatches.head(10).index:
                        print(f"   {ndc}: Generated={gen_common.loc[ndc, 'RANK']}, Reference={ref_common.loc[ndc, 'RANK']}")
        
        print(f"\n✅ Comparison complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error comparing reports: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("🧪 DawaiRx Report Generation Test")
    print("=" * 60)
    
    # Step 1: Login
    token = login()
    if not token:
        print("❌ Cannot proceed without authentication")
        return
    
    # Step 2: Generate report
    run_id = upload_files_and_generate_report(token)
    if not run_id:
        print("❌ Cannot proceed without run_id")
        return
    
    # Wait a bit for processing
    print("\n⏳ Waiting for report processing...")
    time.sleep(5)
    
    # Step 3: Download report
    output_file = Path("generated_report.csv")
    if not download_report(token, run_id, output_file):
        print("❌ Cannot proceed without downloaded report")
        return
    
    # Step 4: Compare with reference
    if BATCHRX_REFERENCE.exists():
        compare_reports(output_file, BATCHRX_REFERENCE)
    else:
        print(f"⚠️ Reference file not found: {BATCHRX_REFERENCE}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()

