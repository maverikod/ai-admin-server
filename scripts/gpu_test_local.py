#!/usr/bin/env python3
"""
Local GPU Test Script
Simplified version for testing on local GPU
"""

import os
import sys
import time
import json
import logging
import torch
import numpy as np
import psutil
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('gpu_test_local.log')
    ]
)
logger = logging.getLogger(__name__)

class LocalGPUTester:
    """Local GPU testing class"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'hostname': os.uname().nodename if hasattr(os, 'uname') else 'unknown',
            'gpu_info': {},
            'system_info': {},
            'test_results': {}
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
            
            # Test memory allocation (smaller size for MX150)
            start_time = time.time()
            tensor_size = 256 * 1024 * 1024 // 4  # 256MB for float32
            tensor = torch.randn(tensor_size, device=device)
            
            # Get memory info
            memory_allocated = torch.cuda.memory_allocated(device) / (1024**3)
            memory_reserved = torch.cuda.memory_reserved(device) / (1024**3)
            
            # Perform some operations
            result = torch.matmul(tensor, tensor.T)
            end_time = time.time()
            
            # Clean up
            del tensor, result
            torch.cuda.empty_cache()
            
            self.results['test_results']['memory_test'] = {
                'success': True,
                'tensor_size_mb': 256,
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
            
            # Create test tensors (smaller size for MX150)
            size = 512  # Reduced from 1024
            a = torch.randn(size, size, device=device)
            b = torch.randn(size, size, device=device)
            
            # Warm up
            for _ in range(5):  # Reduced from 10
                _ = torch.matmul(a, b)
            
            torch.cuda.synchronize()
            
            # Benchmark matrix multiplication
            start_time = time.time()
            iterations = 100  # Reduced from 1000
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
    
    def test_gpu_tensor_operations(self):
        """Test basic GPU tensor operations"""
        logger.info("Testing GPU tensor operations...")
        
        if not torch.cuda.is_available():
            logger.warning("Skipping GPU tensor test - CUDA not available")
            return
        
        try:
            device = torch.device('cuda:0')
            
            # Test various tensor operations
            start_time = time.time()
            
            # Create tensors
            x = torch.randn(1000, 1000, device=device)
            y = torch.randn(1000, 1000, device=device)
            
            # Test operations
            z1 = x + y  # Addition
            z2 = x * y  # Element-wise multiplication
            z3 = torch.matmul(x, y)  # Matrix multiplication
            z4 = torch.exp(x)  # Exponential
            z5 = torch.sin(x)  # Trigonometric
            
            torch.cuda.synchronize()
            end_time = time.time()
            
            self.results['test_results']['tensor_operations'] = {
                'success': True,
                'tensor_size': '1000x1000',
                'operations_tested': ['addition', 'multiplication', 'matmul', 'exp', 'sin'],
                'execution_time_seconds': round(end_time - start_time, 3)
            }
            
            logger.info(f"GPU tensor operations test completed: {self.results['test_results']['tensor_operations']}")
            
        except Exception as e:
            logger.error(f"GPU tensor operations test failed: {e}")
            self.results['test_results']['tensor_operations'] = {
                'success': False,
                'error': str(e)
            }
    
    def run_all_tests(self):
        """Run all GPU tests"""
        logger.info("Starting local GPU test suite...")
        
        try:
            # Collect system and GPU info
            self.get_system_info()
            self.get_gpu_info()
            
            # Run GPU tests
            self.test_gpu_memory()
            self.test_gpu_compute()
            self.test_gpu_tensor_operations()
            
            # Save results
            with open('gpu_test_results_local.json', 'w') as f:
                json.dump(self.results, f, indent=2)
            
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
            
            logger.info("Results saved to gpu_test_results_local.json")
            logger.info("Local GPU test suite completed successfully!")
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            sys.exit(1)

def main():
    """Main function"""
    tester = LocalGPUTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main() 