"""DawaiRx-style unified inventory report generation"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd
import logging

from src.normalization.ndc import format_ndc_display

logger = logging.getLogger(__name__)


def create_dawairx_report(
    output_path: str,
    reconciled_df: pd.DataFrame,
    sold_df: pd.DataFrame,
    ordered_df: pd.DataFrame,
    summary: Dict[str, Any],
    all_supplier_names: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Create a unified DawaiRx-style inventory report.
    
    Format:
    - NDC
    - DRUG NAME
    - RANK (by amount/cost)
    - PKG SIZE
    - TOTAL ORDERED-O
    - TOTAL BILLED-B
    - TOTAL SHORTAGE-S
    - HIGHEST SHORTAGE-S
    - AMOUNT (total revenue)
    - COST (total cost)
    - Insurance breakdowns (BILLED/SHORTAGE per insurance)
    
    Args:
        output_path: Path to output CSV file
        reconciled_df: Reconciled inventory DataFrame
        sold_df: Original sold/inventory DataFrame with insurance data
        ordered_df: Original ordered DataFrame
        summary: Summary statistics
        
    Returns:
        DataFrame with DawaiRx format
    """
    logger.info("Creating DawaiRx-style unified report...")
    logger.info(f"   Input: reconciled_df={len(reconciled_df)} rows, sold_df={len(sold_df)} rows, ordered_df={len(ordered_df)} rows")
    
    # Validate inputs
    if len(reconciled_df) == 0:
        logger.warning("⚠️ Reconciled DataFrame is empty - creating empty DawaiRx report")
        # Return empty DataFrame with expected columns instead of raising error
        empty_report = pd.DataFrame(columns=[
            "NDC", "DRUG NAME", "RANK", "PKG SIZE",
            "TOTAL ORDERED-O", "TOTAL BILLED-B", "TOTAL SHORTAGE-S", "HIGHEST SHORTAGE-S",
            "AMOUNT", "COST"
        ])
        # Save empty report
        empty_report.to_csv(output_path, index=False)
        logger.info("   Created empty DawaiRx report (no data to reconcile)")
        return empty_report
    
    if "medicine_key" not in reconciled_df.columns:
        logger.error("❌ medicine_key column missing in reconciled_df")
        logger.error(f"   Available columns: {list(reconciled_df.columns)}")
        raise ValueError(f"medicine_key column is required in reconciled_df. Available columns: {list(reconciled_df.columns)}")
    
    # Validate sold_df has required columns
    if len(sold_df) == 0:
        logger.warning("⚠️ sold_df is empty - will use default values for AMOUNT")
    elif "medicine_key" not in sold_df.columns:
        logger.warning("⚠️ medicine_key missing in sold_df - AMOUNT calculation may be incomplete")
    
    # Validate ordered_df has required columns
    if len(ordered_df) == 0:
        logger.warning("⚠️ ordered_df is empty - TOTAL ORDERED-O and COST will be set to 0")
    elif "medicine_key" not in ordered_df.columns:
        logger.warning("⚠️ medicine_key missing in ordered_df - TOTAL ORDERED-O and COST calculation may be incomplete")
    
    # Start with reconciled data
    report_df = reconciled_df.copy()
    logger.info(f"   Starting with {len(report_df)} rows, columns: {list(report_df.columns)[:10]}...")
    
    # Format NDC to display format (00003-0894-21)
    if "ndc" in report_df.columns:
        report_df["ndc"] = report_df["ndc"].apply(
            lambda x: format_ndc_display(str(x)) if pd.notna(x) and str(x).strip() else x
        )
    
    # CRITICAL: Use original drug_name from sold_df (not normalized) to match DawaiRx format
    # DawaiRx preserves the exact drug name format from the source data
    if len(sold_df) > 0 and "medicine_key" in report_df.columns and "medicine_key" in sold_df.columns:
        # Check for original drug name first (if preserve_originals was used)
        if "drug_name_original" in sold_df.columns:
            # Use original drug name (before normalization)
            drug_name_agg = sold_df.groupby("medicine_key")["drug_name_original"].first().reset_index()
            drug_name_agg = drug_name_agg.rename(columns={"drug_name_original": "drug_name"})
            report_df = report_df.merge(drug_name_agg, on="medicine_key", how="left", suffixes=("", "_from_sold"))
            # Use original from sold_df if available, otherwise keep existing
            if "drug_name_from_sold" in report_df.columns:
                report_df["drug_name"] = report_df["drug_name_from_sold"].fillna(report_df["drug_name"])
                report_df = report_df.drop(columns=["drug_name_from_sold"])
            logger.info("   Using original drug names from sold_df (drug_name_original column)")
        elif "drug_name" in sold_df.columns:
            # Get drug names from sold_df (may be normalized, but better than reconciled)
            drug_name_agg = sold_df.groupby("medicine_key")["drug_name"].first().reset_index()
            report_df = report_df.merge(drug_name_agg, on="medicine_key", how="left", suffixes=("", "_from_sold"))
            # Use drug name from sold_df if available, otherwise keep existing
            if "drug_name_from_sold" in report_df.columns:
                report_df["drug_name"] = report_df["drug_name_from_sold"].fillna(report_df["drug_name"])
                report_df = report_df.drop(columns=["drug_name_from_sold"])
            logger.info("   Using drug names from sold_df (preserving format)")
        elif "DRUG NAME" in sold_df.columns:
            # Handle case where column is already "DRUG NAME"
            drug_name_agg = sold_df.groupby("medicine_key")["DRUG NAME"].first().reset_index()
            drug_name_agg = drug_name_agg.rename(columns={"DRUG NAME": "drug_name"})
            report_df = report_df.merge(drug_name_agg, on="medicine_key", how="left", suffixes=("", "_from_sold"))
            if "drug_name_from_sold" in report_df.columns:
                report_df["drug_name"] = report_df["drug_name_from_sold"].fillna(report_df["drug_name"])
                report_df = report_df.drop(columns=["drug_name_from_sold"])
            logger.info("   Using drug names from sold_df (DRUG NAME column)")
    
    # Get PKG SIZE from sold_df if not in reconciled_df
    if "pkg_size" not in report_df.columns and len(sold_df) > 0 and "medicine_key" in report_df.columns and "medicine_key" in sold_df.columns:
        if "pkg_size" in sold_df.columns:
            pkg_size_agg = sold_df.groupby("medicine_key")["pkg_size"].first().reset_index()
            report_df = report_df.merge(pkg_size_agg, on="medicine_key", how="left")
            logger.info("   Added PKG SIZE from sold_df")
        elif "PKG SIZE" in sold_df.columns:
            pkg_size_agg = sold_df.groupby("medicine_key")["PKG SIZE"].first().reset_index()
            pkg_size_agg = pkg_size_agg.rename(columns={"PKG SIZE": "pkg_size"})
            report_df = report_df.merge(pkg_size_agg, on="medicine_key", how="left")
            logger.info("   Added PKG SIZE from sold_df (PKG SIZE column)")
    
    # Rename columns to DawaiRx format (exact format with line breaks)
    column_mapping = {
        "ndc": "NDC",
        "drug_name": "DRUG NAME",
        "ordered_total": "TOTAL\nORDERED-O",
        "sold_total": "TOTAL\nBILLED-B",
        "shortage_qty": "TOTAL\nSHORTAGE-S",
        "pkg_size": "PKG SIZE",
    }
    
    # Rename existing columns
    for old_col, new_col in column_mapping.items():
        if old_col in report_df.columns:
            report_df = report_df.rename(columns={old_col: new_col})
    
    # Ensure PKG SIZE exists (fill with 1 if missing)
    if "PKG SIZE" not in report_df.columns:
        report_df["PKG SIZE"] = 1
        logger.warning("   PKG SIZE not found - defaulting to 1")
    
    # Fix TOTAL ORDERED-O: DawaiRx CRITICAL LOGIC
    # DawaiRx only includes ordered quantities for medicines that were BILLED (sold)
    # If a medicine has TOTAL BILLED-B = 0, then TOTAL ORDERED-O = 0 (even if ordered)
    # This is the key difference: ordered data is filtered by sold data presence
    if len(ordered_df) > 0 and "medicine_key" in ordered_df.columns and "medicine_key" in report_df.columns:
        # Get list of medicines that appear in sold data (these are the only ones we should count)
        medicines_with_sales = set(report_df["medicine_key"].unique())
        logger.info(f"   DawaiRx logic: Only {len(medicines_with_sales)} medicines have sales (will filter ordered data)")
        
        # Filter ordered_df to only include medicines that have sales
        ordered_df_filtered = ordered_df[ordered_df["medicine_key"].isin(medicines_with_sales)].copy()
        logger.info(f"   Filtered ordered data: {len(ordered_df)} → {len(ordered_df_filtered)} rows (removed medicines with no sales)")
        
        if "ordered_qty" in ordered_df_filtered.columns and "pkg_size" in ordered_df_filtered.columns:
            # Calculate total units ordered (ordered_qty * pkg_size) per medicine
            ordered_df_filtered["total_units"] = ordered_df_filtered["ordered_qty"] * ordered_df_filtered["pkg_size"].fillna(1)
            ordered_units_agg = ordered_df_filtered.groupby("medicine_key")["total_units"].sum().reset_index()
            ordered_units_agg = ordered_units_agg.rename(columns={"total_units": "TOTAL\nORDERED-O"})
            
            # Update TOTAL ORDERED-O with total units (only for medicines with sales)
            if "TOTAL\nORDERED-O" in report_df.columns:
                report_df = report_df.drop(columns=["TOTAL\nORDERED-O"])
            report_df = report_df.merge(ordered_units_agg, on="medicine_key", how="left")
            # CRITICAL: Set to 0 for medicines not in ordered data (DawaiRx behavior)
            report_df["TOTAL\nORDERED-O"] = report_df["TOTAL\nORDERED-O"].fillna(0)
            logger.info("   Recalculated TOTAL ORDERED-O: only for medicines with sales (DawaiRx logic)")
        elif "ordered_qty" in ordered_df_filtered.columns and "PKG SIZE" in ordered_df_filtered.columns:
            # Same but with PKG SIZE column name
            ordered_df_filtered["total_units"] = ordered_df_filtered["ordered_qty"] * ordered_df_filtered["PKG SIZE"].fillna(1)
            ordered_units_agg = ordered_df_filtered.groupby("medicine_key")["total_units"].sum().reset_index()
            ordered_units_agg = ordered_units_agg.rename(columns={"total_units": "TOTAL\nORDERED-O"})
            
            if "TOTAL\nORDERED-O" in report_df.columns:
                report_df = report_df.drop(columns=["TOTAL\nORDERED-O"])
            report_df = report_df.merge(ordered_units_agg, on="medicine_key", how="left")
            report_df["TOTAL\nORDERED-O"] = report_df["TOTAL\nORDERED-O"].fillna(0)
            logger.info("   Recalculated TOTAL ORDERED-O: only for medicines with sales (DawaiRx logic, PKG SIZE)")
        else:
            # No ordered data available - set all to 0
            report_df["TOTAL\nORDERED-O"] = 0
            logger.warning("   No ordered_qty or pkg_size found - setting TOTAL ORDERED-O to 0")
    
    # Fix TOTAL SHORTAGE-S: should be TOTAL ORDERED - TOTAL BILLED (not shortage_qty)
    if "TOTAL\nORDERED-O" in report_df.columns and "TOTAL\nBILLED-B" in report_df.columns:
        report_df["TOTAL\nSHORTAGE-S"] = (
            report_df["TOTAL\nORDERED-O"] - report_df["TOTAL\nBILLED-B"]
        )
        logger.info("   Recalculated TOTAL SHORTAGE-S = TOTAL ORDERED - TOTAL BILLED")
    
    # Calculate HIGHEST SHORTAGE-S (DawaiRx logic)
    # CRITICAL: DawaiRx behavior is OPPOSITE of what seems logical:
    # - When TOTAL SHORTAGE-S is NEGATIVE (leftover), HIGHEST SHORTAGE-S = TOTAL SHORTAGE-S
    # - When TOTAL SHORTAGE-S is POSITIVE (shortage) or ZERO, HIGHEST SHORTAGE-S = NaN
    # This appears to track "highest negative shortage" (biggest leftover) per insurance/supplier
    if "TOTAL\nSHORTAGE-S" in report_df.columns:
        highest_col = "HIGHEST\nSHORTAGE-S"
        report_df[highest_col] = report_df["TOTAL\nSHORTAGE-S"].apply(
            lambda x: x if pd.notna(x) and x < 0 else pd.NA  # Set to value when negative, NaN when positive/zero
        )
        nan_count = report_df[highest_col].isna().sum()
        value_count = report_df[highest_col].notna().sum()
        logger.info(f"   HIGHEST SHORTAGE-S: {value_count} rows with values (negative shortages), {nan_count} rows with NaN (positive/zero)")
    
    # Calculate AMOUNT and COST from sold data
    # AMOUNT = sum of insurance paid amounts
    # COST = total cost (can be calculated from ordered data or estimated)
    
    # Aggregate insurance data from sold_df
    import numpy as np
    
    if len(sold_df) > 0 and "medicine_key" in sold_df.columns and "primary_insurance_paid" in sold_df.columns:
        try:
            # Group by medicine_key and sum insurance payments
            agg_dict = {"primary_insurance_paid": "sum"}
            if "secondary_insurance_paid" in sold_df.columns:
                agg_dict["secondary_insurance_paid"] = "sum"
            
            insurance_agg = sold_df.groupby("medicine_key").agg(agg_dict).reset_index()
            logger.info(f"   Aggregated insurance data: {len(insurance_agg)} medicines")
            
            if len(insurance_agg) > 0:
                # Calculate total amount (primary + secondary insurance paid)
                # DawaiRx rounds AMOUNT to whole number using FLOOR (not standard rounding)
                # CRITICAL: DawaiRx uses floor() - always rounds down (11.75 -> 11, not 12)
                primary_paid = insurance_agg["primary_insurance_paid"].fillna(0)
                secondary_paid = insurance_agg.get("secondary_insurance_paid", pd.Series([0] * len(insurance_agg))).fillna(0) if "secondary_insurance_paid" in insurance_agg.columns else pd.Series([0] * len(insurance_agg))
                total_amount = primary_paid + secondary_paid
                
                # CRITICAL: Use numpy.floor() to match DawaiRx behavior (always round down)
                # DO NOT use round() - it rounds to nearest (11.75 -> 12), we need floor (11.75 -> 11)
                logger.info(f"   🔍 Calculating AMOUNT using floor() for {len(total_amount)} medicines")
                
                # Log sample calculations for debugging
                if len(total_amount) > 0:
                    for idx in range(min(10, len(total_amount))):
                        sample_total = total_amount.iloc[idx]
                        sample_floor = int(np.floor(sample_total))
                        sample_round = int(round(sample_total))
                        sample_medicine = insurance_agg.iloc[idx]["medicine_key"] if "medicine_key" in insurance_agg.columns else "unknown"
                        if sample_floor != sample_round:  # Only log when floor and round differ
                            logger.info(f"   🔍 AMOUNT[{idx}]: {sample_medicine[:30]}... total={sample_total}, floor={sample_floor}, round={sample_round} (using floor)")
                
                # Apply floor() - this is the critical step
                insurance_agg["AMOUNT"] = np.floor(total_amount).astype(int)
                
                # Verify the calculation worked
                sample_amts = insurance_agg["AMOUNT"].head(5).tolist()
                logger.info(f"   ✅ Applied floor() to AMOUNT. Sample values: {sample_amts}")
                
                # Merge with report
                if "medicine_key" in report_df.columns and "medicine_key" in insurance_agg.columns:
                    # Log sample AMOUNT values before merge
                    sample_before = insurance_agg[insurance_agg["medicine_key"].isin(report_df["medicine_key"].head(5))]["AMOUNT"].tolist() if len(insurance_agg) > 0 else []
                    logger.info(f"   🔍 AMOUNT values before merge (sample): {sample_before}")
                    
                    report_df = report_df.merge(
                        insurance_agg[["medicine_key", "AMOUNT"]],
                        on="medicine_key",
                        how="left"
                    )
                    
                    # Log sample AMOUNT values after merge
                    sample_after = report_df["AMOUNT"].head(5).tolist()
                    logger.info(f"   🔍 AMOUNT values after merge (sample): {sample_after}")
                    
                    report_df["AMOUNT"] = report_df["AMOUNT"].fillna(0)
                    
                    # Log sample AMOUNT values after fillna
                    sample_fillna = report_df["AMOUNT"].head(5).tolist()
                    logger.info(f"   🔍 AMOUNT values after fillna (sample): {sample_fillna}")
                else:
                    logger.warning("medicine_key column missing - cannot merge insurance data")
                    report_df["AMOUNT"] = 0
            else:
                logger.warning("   ⚠️ No insurance data after aggregation - setting AMOUNT to 0")
                report_df["AMOUNT"] = 0
        except Exception as e:
            logger.error(f"❌ Error aggregating insurance data: {e}", exc_info=True)
            report_df["AMOUNT"] = 0
    else:
        logger.warning("Missing medicine_key or primary_insurance_paid in sold_df - setting AMOUNT to 0")
        report_df["AMOUNT"] = 0
    
    # Calculate COST (DawaiRx logic)
    # DawaiRx COST logic:
    # 1. If cost data exists in ordered_df, use total cost of ordered items (only for medicines with sales)
    # 2. Otherwise, COST = AMOUNT (total revenue, not per-unit cost)
    # IMPORTANT: Only calculate cost for medicines that have sales (same filter as TOTAL ORDERED-O)
    # CRITICAL: DawaiRx uses exact cost values from ordered data, preserving decimal precision
    # 
    # Cost field detection: Check for multiple possible cost field names
    # - "cost", "unit_cost", "price", "unit_price", "total_cost", "extended_cost", "amount"
    cost_col = None
    if len(ordered_df) > 0 and "medicine_key" in ordered_df.columns:
        # Try to find cost field (check multiple possible names)
        cost_field_candidates = ["cost", "unit_cost", "price", "unit_price", "total_cost", "extended_cost", "amount", "total_amount"]
        for candidate in cost_field_candidates:
            if candidate in ordered_df.columns:
                cost_col = candidate
                logger.info(f"   Found cost field: {candidate}")
                break
        
        if cost_col:
            # Filter ordered_df to only include medicines with sales (same as TOTAL ORDERED-O logic)
            medicines_with_sales = set(report_df["medicine_key"].unique())
            ordered_df_filtered = ordered_df[ordered_df["medicine_key"].isin(medicines_with_sales)].copy()
            
            # Determine if cost is per-unit or total
            # If field name contains "total" or "extended", it's likely already total cost
            is_total_cost = "total" in cost_col.lower() or "extended" in cost_col.lower()
            
            # Calculate total cost per medicine
            if is_total_cost:
                # Cost is already total (don't multiply by quantity)
                cost_agg = ordered_df_filtered.groupby("medicine_key")[cost_col].sum().reset_index()
                cost_agg = cost_agg.rename(columns={cost_col: "COST"})
                logger.info(f"   Using {cost_col} as total cost (summing directly)")
            elif "ordered_qty" in ordered_df_filtered.columns:
                # Cost is per-unit, multiply by quantity
                ordered_df_filtered["total_cost"] = ordered_df_filtered["ordered_qty"] * ordered_df_filtered[cost_col].fillna(0)
                cost_agg = ordered_df_filtered.groupby("medicine_key")["total_cost"].sum().reset_index()
                cost_agg = cost_agg.rename(columns={"total_cost": "COST"})
                logger.info(f"   Using {cost_col} as unit cost (multiplying by ordered_qty)")
            else:
                # No quantity field, assume cost is already total
                cost_agg = ordered_df_filtered.groupby("medicine_key")[cost_col].sum().reset_index()
                cost_agg = cost_agg.rename(columns={cost_col: "COST"})
                logger.info(f"   Using {cost_col} as total cost (no ordered_qty field)")
            
            if "medicine_key" in report_df.columns:
                report_df = report_df.merge(cost_agg, on="medicine_key", how="left")
                # For medicines without cost data, fall back to AMOUNT
                if "AMOUNT" in report_df.columns:
                    report_df["COST"] = report_df["COST"].fillna(report_df["AMOUNT"])
                else:
                    report_df["COST"] = report_df["COST"].fillna(0)
                # Round COST to 2 decimal places to match DawaiRx format
                report_df["COST"] = report_df["COST"].round(2)
                logger.info("   Used cost data from ordered_df (filtered to medicines with sales, rounded to 2 decimals)")
            else:
                logger.warning("medicine_key missing in report_df - cannot merge cost data")
                if "AMOUNT" in report_df.columns:
                    report_df["COST"] = report_df["AMOUNT"]
                else:
                    report_df["COST"] = 0
        else:
            # No cost field found - fallback to AMOUNT
            if "AMOUNT" in report_df.columns:
                report_df["COST"] = report_df["AMOUNT"]
                logger.info("   COST = AMOUNT (no cost data in ordered_df)")
            else:
                report_df["COST"] = 0
                logger.warning("   AMOUNT not available - setting COST to 0")
    else:
        # No medicine_key in ordered_df - fallback to AMOUNT
        if "AMOUNT" in report_df.columns:
            report_df["COST"] = report_df["AMOUNT"]
            logger.info("   COST = AMOUNT (no medicine_key in ordered_df)")
        else:
            report_df["COST"] = 0
            logger.warning("   AMOUNT not available - setting COST to 0")
    
    # Filter to match DawaiRx: Only show medicines with sales (TOTAL BILLED-B > 0)
    # DawaiRx only displays medicines that have been sold/billed
    # IMPORTANT: Do this BEFORE calculating RANK to ensure continuous ranking
    if "TOTAL\nBILLED-B" in report_df.columns:
        rows_before = len(report_df)
        # Log sample values before filtering to debug
        sample_values = report_df["TOTAL\nBILLED-B"].head(10).tolist()
        non_zero_count = (report_df["TOTAL\nBILLED-B"] > 0).sum()
        total_billed_sum = report_df["TOTAL\nBILLED-B"].sum()
        logger.info(f"   Before filter: {rows_before} rows, {non_zero_count} with TOTAL BILLED-B > 0, total sum: {total_billed_sum}")
        logger.info(f"   Sample TOTAL BILLED-B values: {sample_values}")
        
        # Check if sold_total column exists and has values (for debugging)
        if "sold_total" in report_df.columns:
            sold_total_sum = report_df["sold_total"].sum()
            logger.info(f"   sold_total column sum: {sold_total_sum}")
        
        # Only filter if there are actually rows with sales
        if non_zero_count > 0:
            report_df = report_df[report_df["TOTAL\nBILLED-B"] > 0].copy()
            rows_after = len(report_df)
            logger.info(f"   ✅ Filtered to medicines with sales: {rows_before} → {rows_after} rows (removed {rows_before - rows_after} rows with no sales)")
        else:
            # If all TOTAL BILLED-B are 0, this means no sales data
            # This is a valid case - return empty report but log the issue
            logger.warning(f"   ⚠️ All {rows_before} medicines have TOTAL BILLED-B = 0 (no sales data)")
            logger.warning(f"   This could mean:")
            logger.warning(f"      - No sold quantities in the input data")
            logger.warning(f"      - sold_qty column is missing or all zeros")
            logger.warning(f"      - Date filter removed all sold data")
            # Filter them out - empty report is valid
            report_df = report_df[report_df["TOTAL\nBILLED-B"] > 0].copy()
            rows_after = len(report_df)
            logger.info(f"   Result: {rows_after} rows (empty report - no sales data)")
    
    # Calculate RANK based on AMOUNT (descending)
    # CRITICAL: RANK must be continuous 1-N (no gaps)
    # CRITICAL: Sort by AMOUNT descending, then by COST descending as tiebreaker (to match DawaiRx)
    # DawaiRx appears to use AMOUNT as primary sort, with COST as secondary sort for ties
    if "AMOUNT" in report_df.columns and "COST" in report_df.columns:
        report_df = report_df.sort_values(["AMOUNT", "COST"], ascending=[False, False])
    elif "AMOUNT" in report_df.columns:
        report_df = report_df.sort_values("AMOUNT", ascending=False)
    else:
        logger.warning("AMOUNT column missing - cannot calculate RANK")
    
    # Assign ranks (1-based, continuous)
    report_df["RANK"] = range(1, len(report_df) + 1)
    logger.info(f"   Assigned RANK: 1 to {len(report_df)} (continuous, no gaps, sorted by AMOUNT then COST)")
    
    # Aggregate insurance breakdowns from sold_df
    # CRITICAL: Must check BOTH primary AND secondary insurance
    if len(sold_df) > 0 and "medicine_key" in sold_df.columns:
        # Get unique insurance names from BOTH primary and secondary
        primary_insurances = set()
        secondary_insurances = set()
        
        if "primary_insurance_name" in sold_df.columns:
            primary_insurances = set(sold_df["primary_insurance_name"].dropna().unique())
        if "secondary_insurance_name" in sold_df.columns:
            secondary_insurances = set(sold_df["secondary_insurance_name"].dropna().unique())
        
        # Combine all insurance names (from both primary and secondary)
        insurance_names = primary_insurances.union(secondary_insurances)
        logger.info(f"   Found {len(insurance_names)} unique insurance names")
        logger.info(f"      Primary: {len(primary_insurances)}, Secondary: {len(secondary_insurances)}")
        
        # Insurance name normalization map (to match DawaiRx exactly)
        # DawaiRx uses specific insurance names - map variations to exact names
        insurance_name_map = {
            # SS&C variations
            "SS&C (FORMERLY HUMANA ARGUS AND OPTUMRX)": "SS&C (FORMERLY HUMANA, ARGUS, AND DST)",
            "SS&C (FORMERLY HUMANA, ARGUS, AND OPTUMRX)": "SS&C (FORMERLY HUMANA, ARGUS, AND DST)",
            "ss&c (formerly humana argus and optumrx)": "SS&C (FORMERLY HUMANA, ARGUS, AND DST)",
            # Case-insensitive matching for common insurances
            "cvs caremark": "CVS CAREMARK",
            "express scripts": "EXPRESS SCRIPTS",
            "horizon health": "HORIZON HEALTH",
            "nj medicaid": "NJ MEDICAID",
            "cash": "CASH",
        }
        
        # Log all insurance names found (before normalization)
        logger.info(f"   Insurance names found (before normalization): {sorted(insurance_names)}")
        
        for insurance_name in insurance_names:
            if pd.notna(insurance_name) and insurance_name:
                # Normalize insurance name to match DawaiRx
                # Try exact match first, then case-insensitive match
                normalized_insurance_name = insurance_name_map.get(insurance_name, None)
                if normalized_insurance_name is None:
                    # Try case-insensitive match
                    insurance_upper = str(insurance_name).upper().strip()
                    normalized_insurance_name = insurance_name_map.get(insurance_upper, insurance_name)
                
                # Log normalization if it changed
                if normalized_insurance_name != insurance_name:
                    logger.debug(f"   Normalized insurance name: '{insurance_name}' -> '{normalized_insurance_name}'")
                
                # CRITICAL: Get data from BOTH primary AND secondary insurance
                # Find all rows where this insurance appears in EITHER primary OR secondary
                insurance_mask = pd.Series([False] * len(sold_df))
                
                if "primary_insurance_name" in sold_df.columns:
                    insurance_mask = insurance_mask | (sold_df["primary_insurance_name"] == insurance_name)
                if "secondary_insurance_name" in sold_df.columns:
                    insurance_mask = insurance_mask | (sold_df["secondary_insurance_name"] == insurance_name)
                
                # Filter to rows where this insurance appears
                insurance_data = sold_df[insurance_mask].copy()
                
                if len(insurance_data) > 0 and "medicine_key" in insurance_data.columns and "sold_qty" in insurance_data.columns:
                    # Aggregate by medicine_key
                    # BILLED = sum of sold_qty for rows where this insurance appears (primary or secondary)
                    insurance_agg = insurance_data.groupby("medicine_key").agg({
                        "sold_qty": "sum",
                    }).reset_index()
                    
                    logger.debug(f"   Aggregated {len(insurance_data)} rows for insurance '{insurance_name}' into {len(insurance_agg)} medicines")
                    
                    # BILLED = total sold_qty for this insurance (from both primary and secondary)
                    # Use normalized name for column (to match DawaiRx)
                    billed_col = f"BILLED\n{normalized_insurance_name}-B"
                    shortage_col = f"SHORTAGE\n{normalized_insurance_name}-S"
                    
                    if "medicine_key" in report_df.columns:
                        report_df = report_df.merge(
                            insurance_agg[["medicine_key", "sold_qty"]].rename(columns={"sold_qty": billed_col}),
                            on="medicine_key",
                            how="left"
                        )
                        report_df[billed_col] = report_df[billed_col].fillna(0)
                        logger.debug(f"   ✅ Added insurance column {billed_col} (from primary and/or secondary)")
                    else:
                        logger.warning(f"   Cannot merge insurance data for {insurance_name} - medicine_key missing in report_df")
                        report_df[billed_col] = 0
                else:
                    logger.warning(f"   Missing columns or no data for insurance {insurance_name}: medicine_key or sold_qty")
                    billed_col = f"BILLED\n{normalized_insurance_name}-B"
                    report_df[billed_col] = 0
                
                # SHORTAGE = proportion of total shortage based on this insurance's share of total billed
                # For now, calculate as proportion of total shortage
                if "TOTAL\nSHORTAGE-S" in report_df.columns:
                    report_df[shortage_col] = (
                        report_df[billed_col] / report_df["TOTAL\nBILLED-B"].replace(0, 1) * 
                        report_df["TOTAL\nSHORTAGE-S"]
                    )
                else:
                    report_df[shortage_col] = 0
    
    # Reorder columns: NDC, DRUG NAME, RANK, PKG SIZE, then totals, then insurance
    # Column names with \n will be displayed with line breaks in UI
    base_columns = ["NDC", "DRUG NAME", "RANK", "PKG SIZE", 
                    "TOTAL\nORDERED-O", "TOTAL\nBILLED-B", "TOTAL\nSHORTAGE-S", 
                    "HIGHEST\nSHORTAGE-S", "AMOUNT", "COST"]
    
    # Get insurance columns (group by insurance name)
    insurance_columns = []
    insurance_names_set = set()
    
    # Extract insurance names from column names (handle both with and without line breaks)
    for col in report_df.columns:
        if col.startswith("BILLED\n") or col.startswith("BILLED "):
            # Extract insurance name (everything after "BILLED\n" or "BILLED " and before "-B")
            ins_name = col.replace("BILLED\n", "").replace("BILLED ", "").replace("-B", "")
            insurance_names_set.add(ins_name)
        elif col.startswith("SHORTAGE\n") or col.startswith("SHORTAGE "):
            ins_name = col.replace("SHORTAGE\n", "").replace("SHORTAGE ", "").replace("-S", "")
            insurance_names_set.add(ins_name)
    
    # Order insurance columns: BILLED then SHORTAGE for each insurance (with line breaks)
    for ins_name in sorted(insurance_names_set):
        billed_col = f"BILLED\n{ins_name}-B"
        shortage_col = f"SHORTAGE\n{ins_name}-S"
        if billed_col in report_df.columns:
            insurance_columns.append(billed_col)
        if shortage_col in report_df.columns:
            insurance_columns.append(shortage_col)
    
    # Add supplier columns from ordered_df
    # DawaiRx shows individual supplier orders: ORDERED\nSMITH DRUGS-O, ORDERED\nKINRAY-O, etc.
    # IMPORTANT: Include ALL suppliers from original upload (even if date filtering excluded them)
    # This ensures columns appear even if they have all zeros
    if len(ordered_df) > 0 and "medicine_key" in ordered_df.columns and "supplier_name" in ordered_df.columns:
        # Filter ordered_df to only include medicines with sales (for data population)
        medicines_with_sales = set(report_df["medicine_key"].unique())
        ordered_df_filtered = ordered_df[ordered_df["medicine_key"].isin(medicines_with_sales)].copy()
        
        # Get suppliers from filtered data (for data population)
        supplier_names_with_data = ordered_df_filtered["supplier_name"].dropna().unique()
        
        # Use all_supplier_names if provided (from original upload, before date filtering)
        # Otherwise fall back to suppliers with data
        if all_supplier_names:
            supplier_names = all_supplier_names
            logger.info(f"   ✅ Using all suppliers from original upload ({len(supplier_names)}): {supplier_names}")
            logger.info(f"   📊 Suppliers with data after filtering: {list(supplier_names_with_data)}")
        else:
            supplier_names = supplier_names_with_data
            logger.warning(f"   ⚠️  all_supplier_names not provided! Using suppliers from filtered data only: {list(supplier_names)}")
        
        logger.info(f"   🔍 Will create columns for {len(supplier_names)} suppliers")
        for supplier_name in supplier_names:
            if pd.notna(supplier_name) and supplier_name:
                # Normalize supplier name: remove "SUPPLIER" prefix to match DawaiRx
                # DawaiRx uses: "SMITH DRUGS", "LEGACY HEALTH"
                # We might have: "SUPPLIER SMITH DRUGS", "SUPPLIER LEGACY HEALTH"
                normalized_supplier = supplier_name.replace("SUPPLIER ", "").strip()
                
                # Get ordered quantities for this supplier (in units: ordered_qty * pkg_size)
                supplier_data = ordered_df_filtered[ordered_df_filtered["supplier_name"] == supplier_name]
                supplier_col = f"ORDERED\n{normalized_supplier}-O"
                
                # If supplier has data, calculate totals; otherwise create column with zeros
                if len(supplier_data) > 0 and "medicine_key" in supplier_data.columns:
                    # Calculate total units ordered from this supplier
                    if "ordered_qty" in supplier_data.columns and "pkg_size" in supplier_data.columns:
                        supplier_data_copy = supplier_data.copy()
                        supplier_data_copy["total_units"] = supplier_data_copy["ordered_qty"] * supplier_data_copy["pkg_size"].fillna(1)
                        supplier_agg = supplier_data_copy.groupby("medicine_key")["total_units"].sum().reset_index()
                    elif "ordered_qty" in supplier_data.columns and "PKG SIZE" in supplier_data.columns:
                        supplier_data_copy = supplier_data.copy()
                        supplier_data_copy["total_units"] = supplier_data_copy["ordered_qty"] * supplier_data_copy["PKG SIZE"].fillna(1)
                        supplier_agg = supplier_data_copy.groupby("medicine_key")["total_units"].sum().reset_index()
                    elif "ordered_qty" in supplier_data.columns:
                        supplier_agg = supplier_data.groupby("medicine_key")["ordered_qty"].sum().reset_index()
                        supplier_agg = supplier_agg.rename(columns={"ordered_qty": "total_units"})
                    else:
                        # No quantity data, create empty column
                        supplier_agg = pd.DataFrame(columns=["medicine_key", "total_units"])
                else:
                    # Supplier has no data after filtering, create empty column
                    supplier_agg = pd.DataFrame(columns=["medicine_key", "total_units"])
                
                # Rename and merge (will fill with 0 if no data)
                supplier_agg = supplier_agg.rename(columns={"total_units": supplier_col})
                
                if "medicine_key" in report_df.columns:
                    report_df = report_df.merge(supplier_agg, on="medicine_key", how="left")
                    report_df[supplier_col] = report_df[supplier_col].fillna(0)
                    if len(supplier_data) > 0:
                        logger.info(f"   ✅ Added supplier column: {supplier_col} (from '{supplier_name}', {len(supplier_agg)} medicines with data)")
                    else:
                        logger.info(f"   ✅ Added supplier column: {supplier_col} (from '{supplier_name}', no data after filtering - all zeros)")
                else:
                    logger.error(f"   ❌ Cannot add supplier column {supplier_col}: medicine_key missing in report_df")
    
    # Get supplier columns (ending with -O)
    supplier_columns = [col for col in report_df.columns if col.endswith("-O") and col not in base_columns]
    
    # DawaiRx specific supplier order (not alphabetical)
    # Order: SMITH DRUGS, KINRAY, LEGACY HEALTH, ALPINE HEALTH, AKRON GENERICS
    supplier_order = [
        "ORDERED\nSMITH DRUGS-O",
        "ORDERED\nKINRAY-O",
        "ORDERED\nLEGACY HEALTH-O",
        "ORDERED\nALPINE HEALTH-O",
        "ORDERED\nAKRON GENERICS-O"
    ]
    
    # Sort suppliers: first by predefined order, then alphabetically for any others
    ordered_suppliers = []
    remaining_suppliers = []
    
    for supplier_col in supplier_columns:
        if supplier_col in supplier_order:
            ordered_suppliers.append(supplier_col)
        else:
            remaining_suppliers.append(supplier_col)
    
    # Sort ordered suppliers by their position in supplier_order
    ordered_suppliers.sort(key=lambda x: supplier_order.index(x) if x in supplier_order else 999)
    # Sort remaining suppliers alphabetically
    remaining_suppliers.sort()
    
    supplier_columns = ordered_suppliers + remaining_suppliers
    cleaned_supplier_columns = [
        col.replace("ORDERED\n", "").replace("-O", "") for col in supplier_columns
    ]
    logger.info(f"   Supplier columns order: {cleaned_supplier_columns}")
    
    # Separate CASH columns from other insurance columns (CASH should be at end)
    cash_columns = [col for col in insurance_columns if "CASH" in col.upper()]
    other_insurance_columns = [col for col in insurance_columns if "CASH" not in col.upper()]
    
    # Remove extra columns that DawaiRx doesn't have
    columns_to_remove = ["remaining_qty", "leftover_qty", "ordered_qty", "sold_qty", "medicine_key"]
    for col in columns_to_remove:
        if col in report_df.columns:
            report_df = report_df.drop(columns=[col])
            logger.info(f"   Removed extra column: {col}")
    
    # Get any remaining columns (should be none after removing extras)
    other_columns = [col for col in report_df.columns 
                    if col not in base_columns + other_insurance_columns + cash_columns + supplier_columns]
    
    # Final column order: base, insurance (non-CASH), suppliers, CASH
    final_columns = base_columns + other_insurance_columns + supplier_columns + cash_columns + other_columns
    
    # Select only columns that exist
    final_columns = [col for col in final_columns if col in report_df.columns]
    
    report_df = report_df[final_columns]
    
    # Fill NaN values and round numeric columns to match DawaiRx format
    # IMPORTANT: DawaiRx uses empty cells for 0 values and missing data, not 0.0
    # CRITICAL: Process AMOUNT FIRST (before other columns) to preserve floor() calculation
    # If we process other columns first and do replace(0, pd.NA), it converts columns to object dtype
    # which breaks subsequent operations
    
    # Process AMOUNT column first
    if "AMOUNT" in report_df.columns and report_df["AMOUNT"].dtype in ['float64', 'int64', 'Int64', 'Float64']:
        # Log before processing
        sample_before = report_df["AMOUNT"].head(10).tolist()
        logger.info(f"   🔍 Processing AMOUNT column FIRST. Sample values before: {sample_before}")
        
        # AMOUNT is already calculated with floor() - preserve it!
        # DO NOT use round() - it would overwrite floor() (11.75 -> 12 instead of 11)
        # Convert to int (should already be int from floor(), but ensure it)
        report_df["AMOUNT"] = report_df["AMOUNT"].fillna(0).astype(int)
        
        # Replace 0 with pd.NA (will show as blank in CSV)
        report_df["AMOUNT"] = report_df["AMOUNT"].replace(0, pd.NA)
        
        # Log after processing
        sample_after = report_df["AMOUNT"].head(10).tolist()
        logger.info(f"   🔍 AMOUNT after processing. Sample values: {sample_after}")
    
    # Process other numeric columns
    for col in report_df.columns:
        if col == "AMOUNT":
            continue  # Already processed above
        
        if report_df[col].dtype in ['float64', 'int64', 'Int64', 'Float64']:
            # Don't fill HIGHEST SHORTAGE-S NaN values (they should remain NaN per DawaiRx logic)
            if col == "HIGHEST\nSHORTAGE-S":
                # Keep NaN values as-is (will be written as empty string in CSV)
                report_df[col] = report_df[col].fillna(pd.NA)  # Use pd.NA to preserve NaN in CSV
            # Round COST to 2 decimal places (DawaiRx precision)
            elif col == "COST":
                # Round to 2 decimal places, but preserve actual precision
                report_df[col] = report_df[col].round(2)
                # Convert to float to ensure proper decimal display
                report_df[col] = report_df[col].astype(float)
                # Replace 0.0 with NaN after rounding
                report_df[col] = report_df[col].replace(0.0, pd.NA)
            # For other numeric columns, replace 0 with NaN
            else:
                report_df[col] = report_df[col].replace(0, pd.NA)
                report_df[col] = report_df[col].replace(0.0, pd.NA)
                # Fill remaining NaN with pd.NA (not 0) to show as blank
                report_df[col] = report_df[col].fillna(pd.NA)
        else:
            # For string columns, fill NaN with empty string
            report_df[col] = report_df[col].fillna("")
    
    # Save to CSV
    # IMPORTANT: Use na_rep='' to write NaN as empty string (matches DawaiRx format)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(output_path, index=False, na_rep='')
    
    logger.info(f"Created DawaiRx-style report: {output_path} ({len(report_df)} rows)")
    
    return report_df
