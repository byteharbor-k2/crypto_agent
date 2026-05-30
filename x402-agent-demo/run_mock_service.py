#!/usr/bin/env python3
"""
Run the mock x402 service
"""

import sys
import os
from dotenv import load_dotenv

# Add mock-service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "mock-service"))
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app import app

if __name__ == "__main__":
    port = int(os.getenv("MOCK_SERVICE_PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
