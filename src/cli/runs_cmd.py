"""CLI commands for managing runs"""

import click
import json
import pandas as pd
from pathlib import Path
import logging

from src.persistence.store import RunStore
from src.reporting.excel import create_audit_report

logger = logging.getLogger(__name__)


@click.group()
def runs():
    """Manage reconciliation runs"""
    pass


@runs.command()
@click.option("--limit", default=10, help="Number of runs to show")
def list(limit):
    """List previous runs."""
    try:
        store = RunStore()
        runs_list = store.list_runs(limit=limit)
        store.close()
        
        if not runs_list:
            click.echo("No runs found.")
            return
        
        click.echo(f"\n📋 Recent Runs (showing {len(runs_list)}):\n")
        click.echo(f"{'Run ID':<25} {'Created':<25} {'Medicines':<12} {'Issues':<10}")
        click.echo("-" * 75)
        
        for run in runs_list:
            run_id = run.get("run_id", "unknown")
            created = run.get("created_at", "")
            if isinstance(created, str):
                # Parse ISO format and show date only
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    created = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            stats = run.get("stats", {})
            medicines = stats.get("total_medicines", 0)
            issues = stats.get("total_issues", 0)
            
            click.echo(f"{run_id:<25} {created:<25} {medicines:<12} {issues:<10}")
        
        click.echo()
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        logger.exception("Failed to list runs")


@runs.command()
@click.argument("run_id")
def show(run_id):
    """Show details of a specific run."""
    try:
        store = RunStore()
        run = store.get_run(run_id)
        
        if not run:
            click.echo(f"❌ Run not found: {run_id}")
            store.close()
            return
        
        store.close()
        
        click.echo(f"\n📊 Run Details: {run_id}\n")
        click.echo(f"Created: {run.get('created_at', 'Unknown')}")
        
        # Input metadata
        input_meta = run.get("input_metadata", {})
        click.echo(f"\n📁 Input Files:")
        click.echo(f"  Ordered: {input_meta.get('ordered_file', 'Unknown')}")
        click.echo(f"  Sold: {input_meta.get('sold_file', 'Unknown')}")
        if input_meta.get("mapping_file"):
            click.echo(f"  Mapping: {input_meta.get('mapping_file')}")
        
        # Stats
        stats = run.get("stats", {})
        click.echo(f"\n📈 Statistics:")
        click.echo(f"  Total medicines: {stats.get('total_medicines', 0)}")
        click.echo(f"  Total ordered: {stats.get('total_ordered', 0):,.0f}")
        click.echo(f"  Total sold: {stats.get('total_sold', 0):,.0f}")
        click.echo(f"  Total remaining: {stats.get('total_remaining', 0):,.0f}")
        click.echo(f"  Medicines with shortage: {stats.get('medicines_with_shortage', 0)}")
        click.echo(f"  Medicines with leftover: {stats.get('medicines_with_leftover', 0)}")
        click.echo(f"  Total issues: {stats.get('total_issues', 0)}")
        
        if stats.get("issues_by_severity"):
            sev = stats["issues_by_severity"]
            click.echo(f"    High: {sev.get('high', 0)}")
            click.echo(f"    Medium: {sev.get('medium', 0)}")
            click.echo(f"    Low: {sev.get('low', 0)}")
        
        click.echo()
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        logger.exception("Failed to show run")


@runs.command()
@click.argument("run_id")
@click.option(
    "--output-dir",
    type=click.Path(),
    default=None,
    help="Output directory (default: out/<run_id>)"
)
def export(run_id, output_dir):
    """Export a previous run (rebuild outputs from DB)."""
    try:
        store = RunStore()
        
        # Get run
        run = store.get_run(run_id)
        if not run:
            click.echo(f"❌ Run not found: {run_id}")
            store.close()
            return
        
        # Get run items and issues
        items = store.get_run_items(run_id)
        issues = store.get_run_issues(run_id)
        store.close()
        
        if not items:
            click.echo(f"❌ No data found for run: {run_id}")
            return
        
        # Create output directory
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = Path("out") / run_id
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Reconstruct DataFrame from items
        reconciled_df = pd.DataFrame(items)
        # Rename columns to match expected format
        column_map = {
            "ordered_qty": "ordered_total",
            "sold_qty": "sold_total",
        }
        reconciled_df = reconciled_df.rename(columns=column_map)
        
        # Convert issues to DataFrame
        issues_df = pd.DataFrame(issues) if issues else pd.DataFrame()
        
        # Get summary from run stats
        summary = run.get("stats", {})
        
        # Generate outputs (same as run command)
        # Remaining inventory
        remaining = reconciled_df[reconciled_df["leftover_qty"] > 0].copy()
        remaining_file = output_path / "remaining_inventory.csv"
        remaining.to_csv(remaining_file, index=False)
        
        # Shortages
        shortages = reconciled_df[reconciled_df["shortage_qty"] > 0].copy()
        shortages_file = output_path / "shortages.csv"
        shortages.to_csv(shortages_file, index=False)
        
        # Leftovers
        leftovers = reconciled_df[reconciled_df["leftover_qty"] > 0].copy()
        leftovers_file = output_path / "leftovers.csv"
        leftovers.to_csv(leftovers_file, index=False)
        
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
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Excel audit report
        excel_file = output_path / "audit_report.xlsx"
        create_audit_report(str(excel_file), reconciled_df, issues_df, summary)
        
        click.echo(f"✅ Exported run {run_id} to {output_path}")
        click.echo(f"\n💾 Output files:")
        click.echo(f"  {remaining_file} ({len(remaining)} rows)")
        click.echo(f"  {shortages_file} ({len(shortages)} rows)")
        click.echo(f"  {leftovers_file} ({len(leftovers)} rows)")
        click.echo(f"  {issues_file} ({len(issues_df)} rows)")
        click.echo(f"  {summary_file}")
        click.echo(f"  {excel_file}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        logger.exception("Failed to export run")

