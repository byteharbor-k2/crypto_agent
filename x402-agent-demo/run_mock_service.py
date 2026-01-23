#!/usr/bin/env python3
"""
Run the mock x402 service
"""

import sys
import os

# Add mock-service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "mock-service"))

from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
