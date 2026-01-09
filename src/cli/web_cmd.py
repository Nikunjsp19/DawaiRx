"""CLI command to start web server"""

import click
import subprocess
import sys


@click.command()
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host to bind to (default: 127.0.0.1)"
)
@click.option(
    "--port",
    default=8000,
    type=int,
    help="Port to bind to (default: 8000)"
)
def web(host, port):
    """Start web UI server"""
    click.echo(f"🚀 Starting DawaiRx web server...")
    click.echo(f"   URL: http://{host}:{port}")
    click.echo(f"   Press Ctrl+C to stop\n")
    
    try:
        from src.web.app import app
        import uvicorn
        uvicorn.run(app, host=host, port=port, log_level="info")
    except ImportError:
        click.echo("❌ FastAPI dependencies not installed. Run: pip install fastapi uvicorn jinja2 python-multipart")
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n👋 Server stopped")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)

