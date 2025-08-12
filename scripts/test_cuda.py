#!/usr/bin/env python3
"""
Simple CUDA GPU Test
"""

import torch
import numpy as np
import time
import subprocess
import sys

def test_cuda_availability():
    """Test if CUDA is available"""
    print("=== CUDA Availability Test ===")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"Number of GPUs: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
            print(f"GPU {i} memory: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.1f} GB")
    else:
        print("CUDA is not available")
    print()

def test_gpu_memory():
    """Test GPU memory operations"""
    print("=== GPU Memory Test ===")
    if not torch.cuda.is_available():
        print("CUDA not available, skipping GPU memory test")
        return
    
    device = torch.device('cuda:0')
    
    # Test memory allocation
    print("Testing memory allocation...")
    try:
        # Allocate 1GB of GPU memory
        tensor = torch.randn(1024, 1024, 256, device=device)
        print(f"Successfully allocated tensor of size: {tensor.shape}")
        print(f"Tensor memory usage: {tensor.element_size() * tensor.nelement() / 1024**3:.2f} GB")
        
        # Test basic operations
        print("Testing basic operations...")
        start_time = time.time()
        result = torch.matmul(tensor, tensor.T)
        end_time = time.time()
        print(f"Matrix multiplication completed in {end_time - start_time:.3f} seconds")
        
        # Clear memory
        del tensor, result
        torch.cuda.empty_cache()
        print("Memory cleared successfully")
        
    except Exception as e:
        print(f"GPU memory test failed: {e}")
    print()

def test_nvidia_smi():
    """Test nvidia-smi command"""
    print("=== NVIDIA-SMI Test ===")
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, check=True)
        print("nvidia-smi output:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"nvidia-smi failed: {e}")
        print(f"Error output: {e.stderr}")
    except FileNotFoundError:
        print("nvidia-smi not found")
    print()

def test_pytorch_operations():
    """Test PyTorch operations on GPU"""
    print("=== PyTorch GPU Operations Test ===")
    if not torch.cuda.is_available():
        print("CUDA not available, skipping PyTorch GPU test")
        return
    
    device = torch.device('cuda:0')
    
    try:
        # Create tensors
        print("Creating test tensors...")
        a = torch.randn(1000, 1000, device=device)
        b = torch.randn(1000, 1000, device=device)
        
        # Test operations
        print("Testing tensor operations...")
        
        # Addition
        start_time = time.time()
        c = a + b
        end_time = time.time()
        print(f"Addition: {end_time - start_time:.6f} seconds")
        
        # Multiplication
        start_time = time.time()
        d = a * b
        end_time = time.time()
        print(f"Element-wise multiplication: {end_time - start_time:.6f} seconds")
        
        # Matrix multiplication
        start_time = time.time()
        e = torch.matmul(a, b)
        end_time = time.time()
        print(f"Matrix multiplication: {end_time - start_time:.6f} seconds")
        
        # Transpose
        start_time = time.time()
        f = a.T
        end_time = time.time()
        print(f"Transpose: {end_time - start_time:.6f} seconds")
        
        print("All PyTorch operations completed successfully")
        
    except Exception as e:
        print(f"PyTorch operations test failed: {e}")
    print()

def main():
    """Run all tests"""
    print("Starting CUDA GPU Tests...")
    print("=" * 50)
    
    test_cuda_availability()
    test_nvidia_smi()
    test_gpu_memory()
    test_pytorch_operations()
    
    print("=" * 50)
    print("CUDA GPU Tests completed!")

if __name__ == "__main__":
    main() 