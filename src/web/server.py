"""Server startup script"""

import uvicorn
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    
    print(f"🚀 Starting DawaiRx web server...")
    print(f"   URL: http://{host}:{port}")
    print(f"   Press Ctrl+C to stop")
    
    uvicorn.run(
        "src.web.app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

