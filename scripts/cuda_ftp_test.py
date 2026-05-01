#!/usr/bin/env python3
"""
CUDA GPU Test with FTP Upload

This script:
1. Queries CUDA/GPU information
2. Performs GPU tests
3. Uploads results to FTP using config data
"""

import torch
import numpy as np
import time
import subprocess
import sys
import json
import ftplib
import os
from datetime import datetime
import configparser

def load_config():
    """Load FTP configuration from config file"""
    try:
        # Try to load from config.json first
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                ftp_config = config.get('ftp', {})
                return {
                    'host': ftp_config.get('host', 'testing.techsup.od.ua'),
                    'user': ftp_config.get('user', 'aidata'),
                    'password': ftp_config.get('password', 'lkhvvssvfasDsrvr234523--!fwevrwe'),
                    'port': ftp_config.get('port', 21),
                    'timeout': ftp_config.get('timeout', 30),
                    'passive_mode': ftp_config.get('passive_mode', True)
                }
    except Exception as e:
        print(f"Warning: Could not load config.json: {e}")
    
    # Fallback to hardcoded values
    return {
        'host': 'testing.techsup.od.ua',
        'user': 'aidata',
        'password': 'lkhvvssvfasDsrvr234523--!fwevrwe',
        'port': 21,
        'timeout': 30,
        'passive_mode': True
    }

def get_gpu_info():
    """Get comprehensive GPU information"""
    gpu_info = {
        'timestamp': datetime.now().isoformat(),
        'hostname': os.uname().nodename if hasattr(os, 'uname') else 'unknown',
        'cuda_available': torch.cuda.is_available(),
        'gpus': []
    }
    
    if torch.cuda.is_available():
        gpu_info['cuda_version'] = torch.version.cuda
        gpu_info['gpu_count'] = torch.cuda.device_count()
        
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            gpu_data = {
                'id': i,
                'name': torch.cuda.get_device_name(i),
                'memory_total_gb': props.total_memory / 1024**3,
                'memory_allocated_gb': torch.cuda.memory_allocated(i) / 1024**3,
                'memory_cached_gb': torch.cuda.memory_reserved(i) / 1024**3,
                'compute_capability': f"{props.major}.{props.minor}",
                'multiprocessor_count': props.multi_processor_count
            }
            gpu_info['gpus'].append(gpu_data)
    
    return gpu_info

def get_nvidia_smi_info():
    """Get nvidia-smi information"""
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used,memory.free,temperature.gpu,utilization.gpu', '--format=csv,noheader,nounits'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        return f"nvidia-smi failed: {e}"

def test_gpu_performance():
    """Test GPU performance with various operations"""
    if not torch.cuda.is_available():
        return {"error": "CUDA not available"}
    
    device = torch.device('cuda:0')
    results = {}
    
    try:
        # Test 1: Memory allocation and basic operations
        print("Testing GPU memory allocation...")
        start_time = time.time()
        tensor = torch.randn(1000, 1000, device=device)
        allocation_time = time.time() - start_time
        results['memory_allocation_time'] = allocation_time
        results['tensor_size'] = list(tensor.shape)
        
        # Test 2: Matrix multiplication
        print("Testing matrix multiplication...")
        start_time = time.time()
        result = torch.matmul(tensor, tensor.T)
        matmul_time = time.time() - start_time
        results['matrix_multiplication_time'] = matmul_time
        
        # Test 3: Element-wise operations
        print("Testing element-wise operations...")
        start_time = time.time()
        element_ops = tensor * 2 + 1
        element_time = time.time() - start_time
        results['element_wise_operations_time'] = element_time
        
        # Test 4: Memory transfer (CPU to GPU)
        print("Testing memory transfer...")
        cpu_tensor = torch.randn(1000, 1000)
        start_time = time.time()
        gpu_tensor = cpu_tensor.to(device)
        transfer_time = time.time() - start_time
        results['cpu_to_gpu_transfer_time'] = transfer_time
        
        # Test 5: Large tensor operations
        print("Testing large tensor operations...")
        try:
            # Try to allocate a larger tensor
            large_tensor = torch.randn(2000, 2000, device=device)
            start_time = time.time()
            large_result = torch.matmul(large_tensor, large_tensor.T)
            large_matmul_time = time.time() - start_time
            results['large_matrix_multiplication_time'] = large_matmul_time
            results['large_tensor_success'] = True
        except Exception as e:
            results['large_tensor_success'] = False
            results['large_tensor_error'] = str(e)
        
        # Clean up
        del tensor, result, element_ops, cpu_tensor, gpu_tensor
        if 'large_tensor' in locals():
            del large_tensor, large_result
        torch.cuda.empty_cache()
        
        results['success'] = True
        
    except Exception as e:
        results['success'] = False
        results['error'] = str(e)
    
    return results

def upload_to_ftp(data, filename, ftp_config):
    """Upload data to FTP server"""
    try:
        print(f"Connecting to FTP server: {ftp_config['host']}:{ftp_config['port']}")
        
        # Connect to FTP
        ftp = ftplib.FTP()
        ftp.connect(
            host=ftp_config['host'],
            port=ftp_config['port'],
            timeout=ftp_config['timeout']
        )
        ftp.login(
            user=ftp_config['user'],
            passwd=ftp_config['password']
        )
        
        if ftp_config['passive_mode']:
            ftp.set_pasv(True)
            print("Using passive mode")
        
        # Get server welcome message
        welcome = ftp.getwelcome()
        print(f"FTP Server: {welcome}")
        
        # Create temporary file
        temp_file = f"/tmp/{filename}"
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Upload file
        with open(temp_file, 'rb') as f:
            ftp.storbinary(f'STOR {filename}', f)
        
        print(f"File uploaded successfully: {filename}")
        
        # Clean up
        os.remove(temp_file)
        ftp.quit()
        
        return True
        
    except Exception as e:
        print(f"FTP upload failed: {e}")
        return False

def create_completion_marker(success, ftp_config):
    """Create completion marker file and upload to FTP"""
    marker_data = {
        'timestamp': datetime.now().isoformat(),
        'status': 'SUCCESS' if success else 'FAILED',
        'instance_id': os.getenv('VAST_INSTANCE_ID', 'unknown'),
        'hostname': os.uname().nodename if hasattr(os, 'uname') else 'unknown'
    }
    
    marker_filename = 'WORK_COMPLETED.txt' if success else 'WORK_FAILED.txt'
    
    # Create local marker file
    with open(marker_filename, 'w') as f:
        json.dump(marker_data, f, indent=2)
    
    print(f"Created completion marker: {marker_filename}")
    
    # Upload marker to FTP
    try:
        upload_to_ftp(marker_data, marker_filename, ftp_config)
        print(f"Completion marker uploaded to FTP: {marker_filename}")
        return True
    except Exception as e:
        print(f"Failed to upload completion marker: {e}")
        return False

def main():
    """Main function"""
    print("=== CUDA GPU Test with FTP Upload ===")
    
    # Load FTP configuration
    ftp_config = load_config()
    print(f"FTP Configuration loaded: {ftp_config['host']}:{ftp_config['port']}")
    
    try:
        # Collect GPU information
        print("\nCollecting GPU information...")
        gpu_info = get_gpu_info()
        
        # Get nvidia-smi info
        print("Getting nvidia-smi information...")
        nvidia_smi_info = get_nvidia_smi_info()
        gpu_info['nvidia_smi'] = nvidia_smi_info
        
        # Test GPU performance
        print("Testing GPU performance...")
        performance_results = test_gpu_performance()
        gpu_info['performance_tests'] = performance_results
        
        # Create timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cuda_test_results_{timestamp}.json"
        
        # Upload to FTP
        print(f"\nUploading results to FTP as {filename}...")
        success = upload_to_ftp(gpu_info, filename, ftp_config)
        
        if success:
            print("=== Test completed successfully! ===")
            print(f"Results uploaded to FTP: {filename}")
            
            # Create completion marker
            create_completion_marker(True, ftp_config)
            
            return 0
        else:
            print("=== Test failed! ===")
            create_completion_marker(False, ftp_config)
            return 1
            
    except Exception as e:
        print(f"=== Test failed with error: {e} ===")
        create_completion_marker(False, ftp_config)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 