"""CLI command for running reconciliation"""

import click
import json
import pandas as pd
from pathlib import Path
import logging

from src.ingestion.processor import process_file
from src.normalization.processor import normalize_dataframe
from src.reconciliation.engine import reconcile_inventory, generate_summary
from src.rules.implementations import create_default_registry
try:
    from src.rules.implementations_extended import create_extended_registry
    USE_EXTENDED_RULES = True
except ImportError:
    USE_EXTENDED_RULES = False
from src.reporting.excel import create_audit_report
from src.persistence.store import RunStore

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--ordered",
    required=True,
    multiple=True,
    type=click.Path(exists=True),
    help="Path to supplier/ordered report file(s) (CSV or XLSX). Can specify multiple times for multiple supplier files."
)
@click.option(
    "--sold",
    required=True,
    type=click.Path(exists=True),
    help="Path to inventory report file (CSV or XLSX) - single file with all sold/inventory data"
)
@click.option(
    "--mapping",
    type=click.Path(exists=True),
    help="Path to mapping configuration file (YAML or JSON)"
)
@click.option(
    "--output-dir",
    type=click.Path(),
    default="out/run",
    help="Output directory for results (default: out/run)"
)
def run(ordered, sold, mapping, output_dir):
    """Run reconciliation: normalize, reconcile, and generate reports."""
    click.echo("🚀 Running reconciliation...\n")
    
    try:
        # Load mapping config if provided
        ordered_mapping = None
        sold_mapping = None
        
        if mapping:
            from src.ingestion.config_loader import load_mapping_config
            config = load_mapping_config(mapping)
            ordered_mapping = config.get("ordered")
            sold_mapping = config.get("sold")
        
        # Step 1: Process and normalize ordered file(s) from suppliers
        if isinstance(ordered, tuple):
            # Multiple supplier files
            click.echo(f"📦 Processing {len(ordered)} supplier file(s)...")
            ordered_dfs = []
            for i, ordered_file in enumerate(ordered):
                click.echo(f"  Processing supplier {i+1}/{len(ordered)}: {Path(ordered_file).name}")
                ordered_result = process_file(ordered_file, "ordered", ordered_mapping)
                ordered_dfs.append(ordered_result["dataframe"])
            
            # Combine all ordered DataFrames
            ordered_df = pd.concat(ordered_dfs, ignore_index=True)
            click.echo(f"  Combined {len(ordered_dfs)} supplier files: {len(ordered_df)} total rows")
        else:
            # Single file
            click.echo("📦 Processing supplier file...")
            ordered_result = process_file(ordered, "ordered", ordered_mapping)
            ordered_df = ordered_result["dataframe"]
        
        ordered_normalized = normalize_dataframe(ordered_df, "ordered")
        
        # Step 2: Process and normalize inventory report (sold file)
        click.echo("💰 Processing inventory report...")
        sold_result = process_file(sold, "sold", sold_mapping)
        sold_df = sold_result["dataframe"]
        sold_normalized = normalize_dataframe(sold_df, "sold")
        
        # Step 3: Reconcile
        click.echo("🔄 Reconciling inventory...")
        reconciled = reconcile_inventory(ordered_normalized, sold_normalized)
        
        # Step 4: Generate summary
        summary = generate_summary(reconciled)
        
        # Step 5: Run audit rules
        click.echo("🔍 Running audit rules...")
        if USE_EXTENDED_RULES:
            rule_registry = create_extended_registry()
            click.echo("  Using extended rule set (15 rules)")
        else:
            rule_registry = create_default_registry()
            click.echo("  Using standard rule set (7 rules)")
        issues = rule_registry.run_all({
            "ordered": ordered_normalized,
            "sold": sold_normalized,
            "reconciled": reconciled,
        })
        
        # Convert issues to DataFrame
        issues_df = pd.DataFrame(issues) if issues else pd.DataFrame()
        
        # Step 6: Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Step 7: Save outputs
        # Remaining inventory
        remaining = reconciled[reconciled["leftover_qty"] > 0].copy()
        remaining_file = output_path / "remaining_inventory.csv"
        remaining.to_csv(remaining_file, index=False)
        
        # Shortages
        shortages = reconciled[reconciled["shortage_qty"] > 0].copy()
        shortages_file = output_path / "shortages.csv"
        shortages.to_csv(shortages_file, index=False)
        
        # Leftovers
        leftovers = reconciled[reconciled["leftover_qty"] > 0].copy()
        leftovers_file = output_path / "leftovers.csv"
        leftovers.to_csv(leftovers_file, index=False)
        
        # Full reconciliation
        full_file = output_path / "reconciliation_full.csv"
        reconciled.to_csv(full_file, index=False)
        
        # Issues CSV
        issues_file = output_path / "issues.csv"
        if len(issues_df) > 0:
            issues_df.to_csv(issues_file, index=False)
        else:
            pd.DataFrame(columns=["rule_id", "severity", "medicine_key", "details"]).to_csv(
                issues_file, index=False
            )
        
        # Summary JSON
        summary_file = output_path / "summary.json"
        summary_with_issues = summary.copy()
        summary_with_issues["total_issues"] = len(issues_df)
        summary_with_issues["issues_by_severity"] = {
            "high": int((issues_df["severity"] == "high").sum()) if len(issues_df) > 0 else 0,
            "medium": int((issues_df["severity"] == "medium").sum()) if len(issues_df) > 0 else 0,
            "low": int((issues_df["severity"] == "low").sum()) if len(issues_df) > 0 else 0,
        }
        with open(summary_file, 'w') as f:
            json.dump(summary_with_issues, f, indent=2)
        
        # Excel audit report
        excel_file = output_path / "audit_report.xlsx"
        create_audit_report(str(excel_file), reconciled, issues_df, summary_with_issues)
        
        # PDF audit report (detailed)
        try:
            from src.reporting.pdf import create_detailed_pdf_report
            pdf_file = output_path / "audit_report_detailed.pdf"
            create_detailed_pdf_report(
                str(pdf_file),
                reconciled,
                issues_df,
                summary_with_issues,
                ordered_normalized,
                sold_normalized
            )
            click.echo(f"  {pdf_file}")
        except ImportError:
            logger.warning("PDF generation not available - install reportlab")
        except Exception as e:
            logger.warning(f"PDF generation failed: {e}")
        
        # Step 8: Save to MongoDB
        click.echo("💾 Saving to MongoDB...")
        try:
            store = RunStore()
            # Handle multiple ordered files - convert tuple to comma-separated string
            ordered_file_str = ", ".join(ordered) if isinstance(ordered, tuple) else ordered
            saved_run_id = store.save_run(
                ordered_file=ordered_file_str,
                sold_file=sold,
                mapping_file=mapping,
                reconciled_df=reconciled,
                issues=issues,
                summary=summary_with_issues
            )
            store.close()
            click.echo(f"  ✅ Saved run: {saved_run_id}")
        except Exception as e:
            logger.warning(f"Failed to save to MongoDB: {e}")
            click.echo(f"  ⚠️  MongoDB save failed: {e}")
        
        # Display results
        click.echo("\n✅ Reconciliation complete!")
        click.echo(f"\n📊 Summary:")
        click.echo(f"  Total medicines: {summary['total_medicines']}")
        click.echo(f"  Total ordered: {summary['total_ordered']:,.0f}")
        click.echo(f"  Total sold: {summary['total_sold']:,.0f}")
        click.echo(f"  Total remaining: {summary['total_remaining']:,.0f}")
        click.echo(f"  Sold percentage: {summary.get('sold_percentage', 0):.1f}%")
        click.echo(f"  Medicines with shortage: {summary['medicines_with_shortage']}")
        click.echo(f"  Medicines with leftover: {summary['medicines_with_leftover']}")
        click.echo(f"  Total issues found: {summary_with_issues['total_issues']}")
        if summary_with_issues['total_issues'] > 0:
            click.echo(f"    High: {summary_with_issues['issues_by_severity']['high']}")
            click.echo(f"    Medium: {summary_with_issues['issues_by_severity']['medium']}")
            click.echo(f"    Low: {summary_with_issues['issues_by_severity']['low']}")
        
        click.echo(f"\n💾 Output files:")
        click.echo(f"  {remaining_file} ({len(remaining)} rows)")
        click.echo(f"  {shortages_file} ({len(shortages)} rows)")
        click.echo(f"  {leftovers_file} ({len(leftovers)} rows)")
        click.echo(f"  {issues_file} ({len(issues_df)} rows)")
        click.echo(f"  {full_file} ({len(reconciled)} rows)")
        click.echo(f"  {summary_file}")
        click.echo(f"  {excel_file}")
        pdf_file = output_path / "audit_report_detailed.pdf"
        if pdf_file.exists():
            click.echo(f"  {pdf_file}")
        
        return 0
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        logger.exception("Reconciliation failed")
        return 1

