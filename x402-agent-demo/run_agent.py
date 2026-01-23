#!/usr/bin/env python3
"""
Run the AI agent client
"""

import sys
import os

# Add agent-client to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agent-client"))

from agent import main

if __name__ == "__main__":
    main()
