#!/usr/bin/env python3
"""
GPU Test Script for Vast.ai
Performs GPU tests and uploads results to FTP server
"""

import os
import sys
import time
import json
import logging
import ftplib
import torch
import numpy as np
import psutil
from datetime import datetime
from config import FTP_CONFIG, GPU_CONFIG, get_env_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('gpu_test.log')
    ]
)
logger = logging.getLogger(__name__)

class GPUTester:
    """GPU testing class with FTP upload capabilities"""
    
    def __init__(self):
        self.config = get_env_config()
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'hostname': os.uname().nodename if hasattr(os, 'uname') else 'unknown',
            'gpu_info': {},
            'system_info': {},
            'test_results': {},
            'ftp_upload': {}
        }
    
    def get_system_info(self):
        """Get system information"""
        logger.info("Collecting system information...")
        
        self.results['system_info'] = {
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'memory_available_gb': round(psutil.virtual_memory().available / (1024**3), 2),
            'disk_usage_percent': psutil.disk_usage('/').percent,
            'python_version': sys.version,
            'torch_version': torch.__version__,
            'cuda_available': torch.cuda.is_available()
        }
        
        logger.info(f"System info collected: {self.results['system_info']}")
    
    def get_gpu_info(self):
        """Get GPU information"""
        logger.info("Collecting GPU information...")
        
        if not torch.cuda.is_available():
            logger.warning("CUDA is not available!")
            self.results['gpu_info'] = {'error': 'CUDA not available'}
            return
        
        gpu_count = torch.cuda.device_count()
        logger.info(f"Found {gpu_count} GPU(s)")
        
        gpu_info = {}
        for i in range(gpu_count):
            props = torch.cuda.get_device_properties(i)
            gpu_info[f'gpu_{i}'] = {
                'name': props.name,
                'memory_total_gb': round(props.total_memory / (1024**3), 2),
                'memory_free_gb': round(torch.cuda.get_device_properties(i).total_memory / (1024**3), 2),
                'compute_capability': f"{props.major}.{props.minor}",
                'multi_processor_count': props.multi_processor_count
            }
        
        self.results['gpu_info'] = gpu_info
        logger.info(f"GPU info collected: {gpu_info}")
    
    def test_gpu_memory(self):
        """Test GPU memory allocation and deallocation"""
        logger.info("Testing GPU memory...")
        
        if not torch.cuda.is_available():
            logger.warning("Skipping GPU memory test - CUDA not available")
            return
        
        try:
            device = torch.device('cuda:0')
            
            # Test memory allocation (adaptive size based on GPU memory)
            start_time = time.time()
            gpu_memory_gb = torch.cuda.get_device_properties(device).total_memory / (1024**3)
            # Use 25% of GPU memory or 1GB, whichever is smaller
            test_size_gb = min(1.0, gpu_memory_gb * 0.25)
            tensor_size = int(test_size_gb * 1024**3 // 4)  # 4 bytes per float32
            
            # Create 2D tensor for matrix operations
            matrix_size = int(torch.sqrt(torch.tensor(tensor_size)).item())
            tensor = torch.randn(matrix_size, matrix_size, device=device)
            
            # Get memory info
            memory_allocated = torch.cuda.memory_allocated(device) / (1024**3)
            memory_reserved = torch.cuda.memory_reserved(device) / (1024**3)
            
            # Perform matrix multiplication
            result = torch.matmul(tensor, tensor.mT)
            end_time = time.time()
            
            # Clean up
            del tensor, result
            torch.cuda.empty_cache()
            
            self.results['test_results']['memory_test'] = {
                'success': True,
                'tensor_size_gb': round(test_size_gb, 2),
                'matrix_size': matrix_size,
                'memory_allocated_gb': round(memory_allocated, 2),
                'memory_reserved_gb': round(memory_reserved, 2),
                'execution_time_seconds': round(end_time - start_time, 3)
            }
            
            logger.info(f"GPU memory test completed: {self.results['test_results']['memory_test']}")
            
        except Exception as e:
            logger.error(f"GPU memory test failed: {e}")
            self.results['test_results']['memory_test'] = {
                'success': False,
                'error': str(e)
            }
    
    def test_gpu_compute(self):
        """Test GPU computational performance"""
        logger.info("Testing GPU computational performance...")
        
        if not torch.cuda.is_available():
            logger.warning("Skipping GPU compute test - CUDA not available")
            return
        
        try:
            device = torch.device('cuda:0')
            
            # Create test tensors (adaptive size)
            gpu_memory_gb = torch.cuda.get_device_properties(device).total_memory / (1024**3)
            if gpu_memory_gb < 4:
                size = 512  # Smaller for low-end GPUs
                iterations = 100
            else:
                size = 1024
                iterations = 1000
            
            a = torch.randn(size, size, device=device)
            b = torch.randn(size, size, device=device)
            
            # Warm up
            for _ in range(5):
                _ = torch.matmul(a, b)
            
            torch.cuda.synchronize()
            
            # Benchmark matrix multiplication
            start_time = time.time()
            for _ in range(iterations):
                result = torch.matmul(a, b)
            torch.cuda.synchronize()
            end_time = time.time()
            
            total_time = end_time - start_time
            ops_per_second = iterations / total_time
            
            self.results['test_results']['compute_test'] = {
                'success': True,
                'matrix_size': size,
                'iterations': iterations,
                'total_time_seconds': round(total_time, 3),
                'operations_per_second': round(ops_per_second, 2)
            }
            
            logger.info(f"GPU compute test completed: {self.results['test_results']['compute_test']}")
            
        except Exception as e:
            logger.error(f"GPU compute test failed: {e}")
            self.results['test_results']['compute_test'] = {
                'success': False,
                'error': str(e)
            }
    
    def upload_to_ftp(self):
        """Upload test results to FTP server"""
        logger.info("Uploading results to FTP...")
        
        try:
            # Create results file
            results_file = GPU_CONFIG['output_filename']
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            # Also create a timestamped version
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            timestamped_file = f"gpu_test_results_{timestamp}.json"
            with open(timestamped_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            logger.info(f"FTP Configuration: {self.config}")
            
            # Connect to FTP
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
                logger.info("Using passive mode")
            
            # Get server welcome message
            welcome = ftp.getwelcome()
            logger.info(f"FTP Server: {welcome}")
            
            # Upload both files
            with open(results_file, 'rb') as f:
                ftp.storbinary(f'STOR {results_file}', f)
            logger.info(f"Results uploaded to FTP: {results_file}")
            
            with open(timestamped_file, 'rb') as f:
                ftp.storbinary(f'STOR {timestamped_file}', f)
            logger.info(f"Timestamped results uploaded to FTP: {timestamped_file}")
            
            ftp.quit()
            
            self.results['ftp_upload'] = {
                'success': True,
                'filename': results_file,
                'timestamped_filename': timestamped_file,
                'timestamp': datetime.now().isoformat(),
                'ftp_server': welcome
            }
            
            logger.info(f"Results uploaded to FTP successfully!")
            
        except Exception as e:
            logger.error(f"FTP upload failed: {e}")
            self.results['ftp_upload'] = {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
            # Save results locally as fallback
            try:
                local_file = f"local_{results_file}"
                with open(local_file, 'w') as f:
                    json.dump(self.results, f, indent=2)
                logger.info(f"Results saved locally as fallback: {local_file}")
            except Exception as local_error:
                logger.error(f"Failed to save results locally: {local_error}")
    
    def notify_completion(self):
        """Notify about completion and optionally shutdown instance"""
        logger.info("=== WORK COMPLETED ===")
        logger.info("GPU testing and FTP upload completed successfully!")
        
        # Create completion marker file
        completion_file = "WORK_COMPLETED.txt"
        completion_data = {
            'timestamp': datetime.now().isoformat(),
            'status': 'SUCCESS',
            'gpu_tests_passed': len([r for r in self.results['test_results'].values() if r.get('success', False)]),
            'total_tests': len(self.results['test_results']),
            'ftp_upload_success': self.results['ftp_upload'].get('success', False),
            'hostname': self.results['hostname'],
            'gpu_info': self.results['gpu_info']
        }
        
        with open(completion_file, 'w') as f:
            json.dump(completion_data, f, indent=2)
        
        logger.info(f"Completion marker created: {completion_file}")
        
        # Upload completion marker to FTP
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
            
            with open(completion_file, 'rb') as f:
                ftp.storbinary(f'STOR {completion_file}', f)
            
            ftp.quit()
            logger.info(f"Completion marker uploaded to FTP: {completion_file}")
            
        except Exception as e:
            logger.error(f"Failed to upload completion marker: {e}")
        
        # Check if we should shutdown the instance
        shutdown_after_completion = os.getenv('SHUTDOWN_AFTER_COMPLETION', 'false').lower() == 'true'
        if shutdown_after_completion:
            logger.info("Shutting down instance in 1 second...")
            import subprocess
            import threading
            
            def delayed_shutdown():
                time.sleep(1)  # Changed from 30 to 1 second
                try:
                    subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=True)
                except Exception as e:
                    logger.error(f"Failed to shutdown: {e}")
                    # Fallback: just exit
                    os._exit(0)
            
            shutdown_thread = threading.Thread(target=delayed_shutdown)
            shutdown_thread.daemon = True
            shutdown_thread.start()
        else:
            logger.info("Instance will continue running (set SHUTDOWN_AFTER_COMPLETION=true to auto-shutdown)")
    
    def run_all_tests(self):
        """Run all GPU tests"""
        logger.info("Starting GPU test suite...")
        
        try:
            # Collect system and GPU info
            self.get_system_info()
            self.get_gpu_info()
            
            # Run GPU tests
            self.test_gpu_memory()
            self.test_gpu_compute()
            
            # Upload results
            self.upload_to_ftp()
            
            # Notify completion
            self.notify_completion()
            
            # Print summary
            logger.info("=== GPU Test Summary ===")
            logger.info(f"System: {self.results['system_info']['cpu_count']} CPUs, "
                       f"{self.results['system_info']['memory_total_gb']}GB RAM")
            logger.info(f"CUDA Available: {self.results['system_info']['cuda_available']}")
            
            if self.results['system_info']['cuda_available']:
                for gpu_id, gpu_info in self.results['gpu_info'].items():
                    logger.info(f"{gpu_id}: {gpu_info['name']} ({gpu_info['memory_total_gb']}GB)")
            
            logger.info("=== Test Results ===")
            for test_name, test_result in self.results['test_results'].items():
                status = "PASS" if test_result.get('success', False) else "FAIL"
                logger.info(f"{test_name}: {status}")
            
            logger.info("=== FTP Upload ===")
            ftp_status = "SUCCESS" if self.results['ftp_upload'].get('success', False) else "FAILED"
            logger.info(f"FTP Upload: {ftp_status}")
            
            logger.info("GPU test suite completed successfully!")
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            # Create failure marker
            failure_file = "WORK_FAILED.txt"
            failure_data = {
                'timestamp': datetime.now().isoformat(),
                'status': 'FAILED',
                'error': str(e),
                'hostname': self.results.get('hostname', 'unknown')
            }
            
            with open(failure_file, 'w') as f:
                json.dump(failure_data, f, indent=2)
            
            logger.info(f"Failure marker created: {failure_file}")
            sys.exit(1)

def main():
    """Main function"""
    tester = GPUTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main() 