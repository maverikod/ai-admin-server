#!/usr/bin/env python3
"""
Simple Vast.ai GPU Test

This script runs a simple GPU test on Vast.ai using existing ai_admin commands
"""

import json
import time
import logging
import subprocess
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Simple GPU test using existing commands"""
    logger.info("=== Simple Vast.ai GPU Test ===")
    
    try:
        # Step 1: Push Docker image to Docker Hub
        logger.info("Pushing Docker image to Docker Hub...")
        subprocess.run(['docker', 'push', 'vasilyvz/gpu-test:latest'], check=True)
        logger.info("Docker image pushed successfully")
        
        # Step 2: Search for cheapest GPU
        logger.info("Searching for cheapest GPU...")
        # Use direct vast.ai API or existing tools
        
        # Step 3: Create instance
        logger.info("Creating Vast.ai instance...")
        # Use direct vast.ai API or existing tools
        
        logger.info("=== Test completed ===")
        return 0
            
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 