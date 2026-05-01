#!/usr/bin/env python3
"""
Vast.ai Instance Monitor
Monitors GPU test instances and manages their lifecycle
"""

import os
import sys
import time
import json
import logging
import ftplib
import requests
from datetime import datetime
from config import get_env_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VastInstanceMonitor:
    """Monitor Vast.ai instances for completion"""
    
    def __init__(self):
        self.config = get_env_config()
        self.vast_api_key = os.getenv('VAST_API_KEY', '')
        self.vast_api_url = "https://console.vast.ai/api/v0"
        self.instance_id = os.getenv('VAST_INSTANCE_ID', '')
        
    def check_ftp_completion(self):
        """Check FTP server for completion markers"""
        try:
            ftp = ftplib.FTP()
            ftp.connect(
                host=self.config['ftp_host'],
                port=self.config['ftp_port'],
                timeout=self.config['ftp_timeout']
            )
            ftp.login(
                user=self.config['ftp_user'],
                passwd=self.config['ftp_password']
            )
            
            if self.config['ftp_passive']:
                ftp.set_pasv(True)
            
            # List files and look for completion markers
            files = ftp.nlst()
            completion_files = [f for f in files if f.startswith('WORK_COMPLETED') or f.startswith('WORK_FAILED')]
            
            ftp.quit()
            
            if completion_files:
                logger.info(f"Found completion markers: {completion_files}")
                return True, completion_files
            
            return False, []
            
        except Exception as e:
            logger.error(f"Failed to check FTP: {e}")
            return False, []
    
    def destroy_vast_instance(self):
        """Destroy Vast.ai instance via API"""
        if not self.vast_api_key or not self.instance_id:
            logger.warning("VAST_API_KEY or VAST_INSTANCE_ID not set, cannot destroy instance")
            return False
        
        try:
            url = f"{self.vast_api_url}/instances/{self.instance_id}/destroy/"
            headers = {
                'Authorization': f'Bearer {self.vast_api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, headers=headers)
            
            if response.status_code == 200:
                logger.info(f"Successfully destroyed instance {self.instance_id}")
                return True
            else:
                logger.error(f"Failed to destroy instance: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error destroying instance: {e}")
            return False
    
    def monitor_instance(self, check_interval=60, max_wait_time=3600):
        """Monitor instance for completion"""
        logger.info(f"Starting instance monitor (check every {check_interval}s, max wait {max_wait_time}s)")
        
        start_time = time.time()
        
        while True:
            elapsed = time.time() - start_time
            
            if elapsed > max_wait_time:
                logger.warning(f"Max wait time exceeded ({max_wait_time}s), destroying instance")
                self.destroy_vast_instance()
                break
            
            logger.info(f"Checking for completion... (elapsed: {elapsed:.0f}s)")
            
            completed, markers = self.check_ftp_completion()
            
            if completed:
                logger.info("Work completed! Destroying instance...")
                self.destroy_vast_instance()
                break
            
            time.sleep(check_interval)

def main():
    """Main function"""
    monitor = VastInstanceMonitor()
    
    # Get parameters from environment
    check_interval = int(os.getenv('CHECK_INTERVAL', '60'))
    max_wait_time = int(os.getenv('MAX_WAIT_TIME', '3600'))
    
    monitor.monitor_instance(check_interval, max_wait_time)

if __name__ == "__main__":
    main() 