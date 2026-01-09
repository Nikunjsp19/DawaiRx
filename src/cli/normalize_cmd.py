"""CLI command for normalizing input files"""

import click
from pathlib import Path
import logging

from src.ingestion.processor import process_file
from src.normalization.processor import normalize_dataframe

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
    "--output-dir",
    type=click.Path(),
    default="out/normalized",
    help="Output directory for normalized CSVs (default: out/normalized)"
)
def normalize(ordered, sold, mapping, output_dir):
    """Normalize input data (NDC, text fields, dates, quantities)."""
    click.echo("🔄 Normalizing input files...\n")
    
    try:
        # Load mapping config if provided
        ordered_mapping = None
        sold_mapping = None
        
        if mapping:
            from src.ingestion.config_loader import load_mapping_config
            config = load_mapping_config(mapping)
            ordered_mapping = config.get("ordered")
            sold_mapping = config.get("sold")
        
        # Process and normalize ordered file
        click.echo("Processing ordered file...")
        ordered_result = process_file(ordered, "ordered", ordered_mapping)
        ordered_df = ordered_result["dataframe"]
        ordered_normalized = normalize_dataframe(ordered_df, "ordered")
        
        # Process and normalize sold file
        click.echo("Processing sold file...")
        sold_result = process_file(sold, "sold", sold_mapping)
        sold_df = sold_result["dataframe"]
        sold_normalized = normalize_dataframe(sold_df, "sold")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save normalized CSVs
        ordered_output = output_path / "ordered_normalized.csv"
        sold_output = output_path / "sold_normalized.csv"
        
        ordered_normalized.to_csv(ordered_output, index=False)
        sold_normalized.to_csv(sold_output, index=False)
        
        click.echo("\n✅ Normalization complete!")
        click.echo(f"\n📊 Statistics:")
        click.echo(f"  Ordered: {len(ordered_normalized):,} rows")
        click.echo(f"  Sold: {len(sold_normalized):,} rows")
        
        # Show medicine key stats
        ordered_keys = ordered_normalized["medicine_key"].nunique()
        sold_keys = sold_normalized["medicine_key"].nunique()
        click.echo(f"  Unique medicines (ordered): {ordered_keys}")
        click.echo(f"  Unique medicines (sold): {sold_keys}")
        
        # Show NDC normalization stats
        if "ndc_normalized" in ordered_normalized.columns:
            ordered_valid_ndc = ordered_normalized["ndc_normalized"].notna().sum()
            click.echo(f"  Valid NDC codes (ordered): {ordered_valid_ndc}/{len(ordered_normalized)}")
        
        if "ndc_normalized" in sold_normalized.columns:
            sold_valid_ndc = sold_normalized["ndc_normalized"].notna().sum()
            click.echo(f"  Valid NDC codes (sold): {sold_valid_ndc}/{len(sold_normalized)}")
        
        click.echo(f"\n💾 Output files:")
        click.echo(f"  {ordered_output}")
        click.echo(f"  {sold_output}")
        
        return 0
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        logger.exception("Normalization failed")
        return 1

