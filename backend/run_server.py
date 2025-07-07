#!/usr/bin/env python3
"""
FastAPI Server Runner
Starts the TKA Voice Agent API server with proper configuration
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Set environment variables
os.environ.setdefault("PYTHONPATH", str(current_dir))

def main():
    """Run the FastAPI server"""
    try:
        import uvicorn
        from main import app
        
        print("🚀 Starting TKA Voice Agent API Server...")
        print("📍 API Documentation: http://localhost:8000/docs")
        print("🔍 Health Check: http://localhost:8000/health")
        
        # Run server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Make sure you're in the backend directory and dependencies are installed")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Server Error: {e}")
        print("💡 Check if PostgreSQL is running: docker-compose up -d postgres")
        sys.exit(1)

if __name__ == "__main__":
    main() 