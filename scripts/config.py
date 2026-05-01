"""
Configuration file for GPU test application
Contains FTP settings and other parameters
"""

import os
import json

# Load configuration from config.json
def load_config():
    """Load configuration from config.json"""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: config.json not found at {config_path}")
        return {}

# Load main config
MAIN_CONFIG = load_config()

# FTP Configuration from config.json
FTP_CONFIG = MAIN_CONFIG.get('ftp', {
    'host': 'testing.techsup.od.ua',
    'user': 'aidata',
    'password': 'lkhvvssvfasDsrvr234523--!fwevrwe',
    'port': 21,
    'timeout': 30,
    'passive_mode': True
})

# GPU Test Configuration
GPU_CONFIG = {
    'test_duration_seconds': 60,
    'memory_test_size_gb': 1,
    'compute_test_iterations': 1000,
    'output_filename': 'gpu_test_results.txt'
}

# Application Configuration
APP_CONFIG = {
    'log_level': 'INFO',
    'max_retries': 3,
    'retry_delay_seconds': 5
}

# Get environment variables if available
def get_env_config():
    """Get configuration from environment variables"""
    return {
        'ftp_host': os.getenv('FTP_HOST', FTP_CONFIG['host']),
        'ftp_user': os.getenv('FTP_USER', FTP_CONFIG['user']),
        'ftp_password': os.getenv('FTP_PASSWORD', FTP_CONFIG['password']),
        'ftp_port': int(os.getenv('FTP_PORT', FTP_CONFIG['port'])),
        'ftp_timeout': int(os.getenv('FTP_TIMEOUT', FTP_CONFIG['timeout'])),
        'ftp_passive': os.getenv('FTP_PASSIVE', str(FTP_CONFIG['passive_mode'])).lower() == 'true',
        'gpu_test_duration': int(os.getenv('GPU_TEST_DURATION', GPU_CONFIG['test_duration_seconds']))
    } 