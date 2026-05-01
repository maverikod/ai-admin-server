#!/usr/bin/env python3
"""
Download and view FTP file
"""

import ftplib
import json

def download_ftp_file(filename):
    """Download file from FTP server"""
    ftp_config = {
        'host': 'testing.techsup.od.ua',
        'user': 'aidata',
        'password': 'lkhvvssvfasDsrvr234523--!fwevrwe',
        'port': 21,
        'timeout': 30,
        'passive_mode': True
    }
    
    try:
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
        
        # Download file
        with open(filename, 'wb') as f:
            ftp.retrbinary(f'RETR {filename}', f.write)
        
        print(f"File downloaded: {filename}")
        
        # Read and display content
        with open(filename, 'r') as f:
            data = json.load(f)
        
        print("\n=== CUDA Test Results ===")
        print(f"Timestamp: {data['timestamp']}")
        print(f"Hostname: {data['hostname']}")
        print(f"CUDA Available: {data['cuda_available']}")
        
        if data['cuda_available']:
            print(f"CUDA Version: {data['cuda_version']}")
            print(f"GPU Count: {data['gpu_count']}")
            
            for gpu in data['gpus']:
                print(f"\nGPU {gpu['id']}: {gpu['name']}")
                print(f"  Memory Total: {gpu['memory_total_gb']:.1f} GB")
                print(f"  Memory Allocated: {gpu['memory_allocated_gb']:.1f} GB")
                print(f"  Memory Cached: {gpu['memory_cached_gb']:.1f} GB")
                print(f"  Compute Capability: {gpu['compute_capability']}")
                print(f"  Multiprocessor Count: {gpu['multiprocessor_count']}")
        
        print(f"\nNVIDIA-SMI Info:")
        print(data['nvidia_smi'])
        
        if 'performance_tests' in data:
            perf = data['performance_tests']
            print(f"\nPerformance Tests:")
            print(f"  Success: {perf.get('success', 'N/A')}")
            if 'error' in perf:
                print(f"  Error: {perf['error']}")
            else:
                print(f"  Memory Allocation Time: {perf.get('memory_allocation_time', 'N/A'):.6f}s")
                print(f"  Matrix Multiplication Time: {perf.get('matrix_multiplication_time', 'N/A'):.6f}s")
                print(f"  Element-wise Operations Time: {perf.get('element_wise_operations_time', 'N/A'):.6f}s")
                print(f"  CPU to GPU Transfer Time: {perf.get('cpu_to_gpu_transfer_time', 'N/A'):.6f}s")
                print(f"  Large Tensor Success: {perf.get('large_tensor_success', 'N/A')}")
                if 'large_matrix_multiplication_time' in perf:
                    print(f"  Large Matrix Multiplication Time: {perf['large_matrix_multiplication_time']:.6f}s")
        
        ftp.quit()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    download_ftp_file("cuda_test_results_20250811_171912.json") 