"""Main CLI entry point"""

import click
import logging

from src.cli.validate_cmd import validate
from src.cli.normalize_cmd import normalize
from src.cli.run_cmd import run
from src.cli.runs_cmd import runs
from src.cli.web_cmd import web

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """DawaiRx - Pharmacy Audit & Reconciliation Tool"""
    pass


cli.add_command(validate)
cli.add_command(normalize)
cli.add_command(run)
cli.add_command(runs)
cli.add_command(web)


if __name__ == "__main__":
    cli()

