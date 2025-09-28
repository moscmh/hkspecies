#!/usr/bin/env python3
"""
Memory optimization for HK Species predictions
"""
import gc
import torch
import psutil
import os

def clear_memory():
    """Clear Python and PyTorch memory"""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def memory_limit_decorator(max_memory_mb=1500):
    """Decorator to limit memory usage of functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            initial_memory = get_memory_usage()
            
            try:
                result = func(*args, **kwargs)
                
                # Check memory after function
                current_memory = get_memory_usage()
                if current_memory > max_memory_mb:
                    print(f"⚠️ High memory usage: {current_memory:.1f}MB, clearing...")
                    clear_memory()
                
                return result
                
            except Exception as e:
                print(f"❌ Function failed, clearing memory: {e}")
                clear_memory()
                raise
                
        return wrapper
    return decorator

class MemoryMonitor:
    """Monitor and manage memory usage"""
    
    def __init__(self, warning_threshold=1200, critical_threshold=1800):
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
    
    def check_memory(self):
        """Check current memory status"""
        usage = get_memory_usage()
        
        if usage > self.critical_threshold:
            print(f"🚨 CRITICAL: Memory usage {usage:.1f}MB")
            clear_memory()
            return "critical"
        elif usage > self.warning_threshold:
            print(f"⚠️ WARNING: Memory usage {usage:.1f}MB")
            return "warning"
        else:
            return "normal"
    
    def force_cleanup(self):
        """Force memory cleanup"""
        print("🧹 Forcing memory cleanup...")
        clear_memory()
        print(f"✅ Memory after cleanup: {get_memory_usage():.1f}MB")