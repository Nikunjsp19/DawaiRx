"""CLI command for validating input files"""

import click
import json
from pathlib import Path
import logging

from src.ingestion.processor import validate_inputs
from src.ingestion.config_loader import save_mapping_config

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--ordered",
    required=True,
    type=click.Path(exists=True),
    help="Path to ordered report file (CSV or XLSX)"
)
@click.option(
    "--sold",
    required=True,
    type=click.Path(exists=True),
    help="Path to sold report file (CSV or XLSX)"
)
@click.option(
    "--mapping",
    type=click.Path(exists=True),
    help="Path to mapping configuration file (YAML or JSON)"
)
@click.option(
    "--output-preview",
    type=click.Path(),
    help="Output directory for preview CSVs (default: out/preview)"
)
@click.option(
    "--generate-mapping",
    type=click.Path(),
    help="Generate and save auto-detected mapping to this file"
)
def validate(ordered, sold, mapping, output_preview, generate_mapping):
    """Validate input files and column mappings."""
    click.echo("🔍 Validating input files...\n")
    
    try:
        # Validate inputs
        results = validate_inputs(ordered, sold, mapping)
        
        # Display results
        click.echo("=" * 60)
        click.echo("VALIDATION RESULTS")
        click.echo("=" * 60)
        
        # Ordered file results
        click.echo("\n📦 ORDERED REPORT")
        click.echo(f"  File: {ordered}")
        ordered_result = results["ordered"]
        click.echo(f"  Rows: {ordered_result['stats']['row_count']:,}")
        click.echo(f"  Columns: {ordered_result['stats']['column_count']}")
        
        if ordered_result["mapping_valid"]:
            click.echo("  ✅ Mapping: Valid")
        else:
            click.echo("  ❌ Mapping: Invalid")
            if ordered_result["missing_fields"]:
                click.echo(f"     Missing fields: {', '.join(ordered_result['missing_fields'])}")
        
        if ordered_result["validation"]["valid"]:
            click.echo("  ✅ Data: Valid")
        else:
            click.echo("  ❌ Data: Invalid")
            for error in ordered_result["validation"]["errors"]:
                click.echo(f"     {error}")
        
        if ordered_result["validation"]["warnings"]:
            click.echo("  ⚠️  Warnings:")
            for warning in ordered_result["validation"]["warnings"]:
                click.echo(f"     {warning}")
        
        # Sold file results
        click.echo("\n💰 SOLD REPORT")
        click.echo(f"  File: {sold}")
        sold_result = results["sold"]
        click.echo(f"  Rows: {sold_result['stats']['row_count']:,}")
        click.echo(f"  Columns: {sold_result['stats']['column_count']}")
        
        if sold_result["mapping_valid"]:
            click.echo("  ✅ Mapping: Valid")
        else:
            click.echo("  ❌ Mapping: Invalid")
            if sold_result["missing_fields"]:
                click.echo(f"     Missing fields: {', '.join(sold_result['missing_fields'])}")
        
        if sold_result["validation"]["valid"]:
            click.echo("  ✅ Data: Valid")
        else:
            click.echo("  ❌ Data: Invalid")
            for error in sold_result["validation"]["errors"]:
                click.echo(f"     {error}")
        
        if sold_result["validation"]["warnings"]:
            click.echo("  ⚠️  Warnings:")
            for warning in sold_result["validation"]["warnings"]:
                click.echo(f"     {warning}")
        
        # Overall status
        click.echo("\n" + "=" * 60)
        if results["valid"]:
            click.echo("✅ OVERALL: VALID - Ready for processing")
        else:
            click.echo("❌ OVERALL: INVALID - Please fix issues above")
        click.echo("=" * 60)
        
        # Generate mapping if requested
        if generate_mapping:
            mapping_config = {
                "ordered": ordered_result["mapping"],
                "sold": sold_result["mapping"],
            }
            save_mapping_config(mapping_config, generate_mapping)
            click.echo(f"\n💾 Generated mapping config: {generate_mapping}")
        
        # Save preview CSVs if requested
        if output_preview:
            output_dir = Path(output_preview)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            ordered_df = ordered_result["dataframe"]
            sold_df = sold_result["dataframe"]
            
            ordered_preview = output_dir / "ordered_preview.csv"
            sold_preview = output_dir / "sold_preview.csv"
            
            ordered_df.head(100).to_csv(ordered_preview, index=False)
            sold_df.head(100).to_csv(sold_preview, index=False)
            
            click.echo(f"\n💾 Preview CSVs saved:")
            click.echo(f"   {ordered_preview}")
            click.echo(f"   {sold_preview}")
        
        # Exit code
        exit_code = 0 if results["valid"] else 1
        return exit_code
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        logger.exception("Validation failed")
        return 1

