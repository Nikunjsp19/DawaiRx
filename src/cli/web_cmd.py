"""CLI command to start web server"""

import click
import subprocess
import sys
import os


@click.command()
@click.option(
    "--host",
    default=None,
    help="Host to bind to (default: 0.0.0.0 in Docker, 127.0.0.1 locally)"
)
@click.option(
    "--port",
    default=None,
    type=int,
    help="Port to bind to (default: from PORT env var or 8000)"
)
def web(host, port):
    """Start web UI server"""
    # Get host from environment or use defaults
    if host is None:
        # In Docker/Azure, bind to 0.0.0.0 to accept external connections
        # Check if we're in a container (Azure sets WEBSITE_SITE_NAME or PORT)
        if os.environ.get("PORT") or os.environ.get("WEBSITE_SITE_NAME"):
            host = "0.0.0.0"
        else:
            host = "127.0.0.1"
    
    # Get port from environment (Azure provides PORT) or use default
    if port is None:
        port = int(os.environ.get("PORT", 8000))
    
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

