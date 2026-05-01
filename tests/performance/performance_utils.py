"""Performance testing utilities for SSL/mTLS and SCP/SSH operations.

This module provides comprehensive utilities for performance testing including
monitoring, reporting, comparison, and resource tracking.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import logging
import statistics
import time
import psutil
import threading
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from pathlib import Path
import json
import csv
from datetime import datetime


logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    
    operation: str
    duration: float
    timestamp: float = field(default_factory=time.time)
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceUsage:
    """Resource usage data structure."""
    
    timestamp: float = field(default_factory=time.time)
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_mb: float = 0.0
    disk_io_read: int = 0
    disk_io_write: int = 0
    network_sent: int = 0
    network_recv: int = 0


class PerformanceMonitor:
    """Performance monitoring utility for operations."""
    
    def __init__(self, enable_resource_monitoring: bool = True):
        """
        Initialize performance monitor.
        
        Args:
            enable_resource_monitoring: Enable system resource monitoring
        """
        self.metrics: List[PerformanceMetric] = []
        self.resource_usage: List[ResourceUsage] = []
        self.enable_resource_monitoring = enable_resource_monitoring
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Initialize resource monitoring
        if self.enable_resource_monitoring:
            self._initial_network = psutil.net_io_counters()
            self._initial_disk = psutil.disk_io_counters()
    
    def start_monitoring(self, interval: float = 1.0) -> None:
        """
        Start resource monitoring.
        
        Args:
            interval: Monitoring interval in seconds
        """
        if not self.enable_resource_monitoring:
            return
            
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_resources,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop resource monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
        logger.info("Performance monitoring stopped")
    
    def _monitor_resources(self, interval: float) -> None:
        """Monitor system resources in background thread."""
        while self._monitoring:
            try:
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                disk_io = psutil.disk_io_counters()
                network_io = psutil.net_io_counters()
                
                # Calculate deltas for I/O
                disk_read_delta = disk_io.read_bytes - (self._initial_disk.read_bytes if self._initial_disk else 0)
                disk_write_delta = disk_io.write_bytes - (self._initial_disk.write_bytes if self._initial_disk else 0)
                network_sent_delta = network_io.bytes_sent - (self._initial_network.bytes_sent if self._initial_network else 0)
                network_recv_delta = network_io.bytes_recv - (self._initial_network.bytes_recv if self._initial_network else 0)
                
                resource_usage = ResourceUsage(
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    memory_mb=memory.used / 1024 / 1024,
                    disk_io_read=disk_read_delta,
                    disk_io_write=disk_write_delta,
                    network_sent=network_sent_delta,
                    network_recv=network_recv_delta,
                )
                
                with self._lock:
                    self.resource_usage.append(resource_usage)
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error monitoring resources: {e}")
                time.sleep(interval)
    
    def record_metric(self, operation: str, duration: float, success: bool = True, 
                     error_message: Optional[str] = None, **metadata) -> None:
        """
        Record a performance metric.
        
        Args:
            operation: Operation name
            duration: Duration in seconds
            success: Whether operation was successful
            error_message: Error message if operation failed
            **metadata: Additional metadata
        """
        metric = PerformanceMetric(
            operation=operation,
            duration=duration,
            success=success,
            error_message=error_message,
            metadata=metadata
        )
        
        with self._lock:
            self.metrics.append(metric)
        
        logger.debug(f"Recorded metric: {operation} - {duration:.3f}s")
    
    def measure_operation(self, operation: str) -> Callable:
        """
        Decorator to measure operation performance.
        
        Args:
            operation: Operation name
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            if asyncio.iscoroutinefunction(func):
                async def async_wrapper(*args, **kwargs):
                    start_time = time.time()
                    success = True
                    error_message = None
                    
                    try:
                        result = await func(*args, **kwargs)
                        return result
                    except Exception as e:
                        success = False
                        error_message = str(e)
                        raise
                    finally:
                        duration = time.time() - start_time
                        self.record_metric(operation, duration, success, error_message)
                
                return async_wrapper
            else:
                def sync_wrapper(*args, **kwargs):
                    start_time = time.time()
                    success = True
                    error_message = None
                    
                    try:
                        result = func(*args, **kwargs)
                        return result
                    except Exception as e:
                        success = False
                        error_message = str(e)
                        raise
                    finally:
                        duration = time.time() - start_time
                        self.record_metric(operation, duration, success, error_message)
                
                return sync_wrapper
        
        return decorator
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get summary of all metrics.
        
        Returns:
            Metrics summary
        """
        if not self.metrics:
            return {}
        
        operations = {}
        
        for metric in self.metrics:
            if metric.operation not in operations:
                operations[metric.operation] = {
                    "count": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "durations": [],
                    "success_durations": [],
                    "failure_durations": [],
                }
            
            op_data = operations[metric.operation]
            op_data["count"] += 1
            op_data["durations"].append(metric.duration)
            
            if metric.success:
                op_data["success_count"] += 1
                op_data["success_durations"].append(metric.duration)
            else:
                op_data["failure_count"] += 1
                op_data["failure_durations"].append(metric.duration)
        
        # Calculate statistics
        summary = {}
        for operation, data in operations.items():
            durations = data["durations"]
            success_durations = data["success_durations"]
            
            summary[operation] = {
                "total_count": data["count"],
                "success_count": data["success_count"],
                "failure_count": data["failure_count"],
                "success_rate": data["success_count"] / data["count"] if data["count"] > 0 else 0,
                "average_duration": statistics.mean(durations) if durations else 0,
                "median_duration": statistics.median(durations) if durations else 0,
                "min_duration": min(durations) if durations else 0,
                "max_duration": max(durations) if durations else 0,
                "std_deviation": statistics.stdev(durations) if len(durations) > 1 else 0,
                "average_success_duration": statistics.mean(success_durations) if success_durations else 0,
            }
        
        return summary
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """
        Get summary of resource usage.
        
        Returns:
            Resource usage summary
        """
        if not self.resource_usage:
            return {}
        
        cpu_values = [r.cpu_percent for r in self.resource_usage]
        memory_values = [r.memory_percent for r in self.resource_usage]
        memory_mb_values = [r.memory_mb for r in self.resource_usage]
        
        return {
            "monitoring_duration": self.resource_usage[-1].timestamp - self.resource_usage[0].timestamp if len(self.resource_usage) > 1 else 0,
            "sample_count": len(self.resource_usage),
            "cpu": {
                "average": statistics.mean(cpu_values),
                "median": statistics.median(cpu_values),
                "min": min(cpu_values),
                "max": max(cpu_values),
                "std_deviation": statistics.stdev(cpu_values) if len(cpu_values) > 1 else 0,
            },
            "memory": {
                "average_percent": statistics.mean(memory_values),
                "median_percent": statistics.median(memory_values),
                "min_percent": min(memory_values),
                "max_percent": max(memory_values),
                "average_mb": statistics.mean(memory_mb_values),
                "max_mb": max(memory_mb_values),
            },
        }


class PerformanceReporter:
    """Performance reporting utility."""
    
    def __init__(self, monitor: PerformanceMonitor):
        """
        Initialize performance reporter.
        
        Args:
            monitor: Performance monitor instance
        """
        self.monitor = monitor
    
    def generate_text_report(self) -> str:
        """
        Generate text performance report.
        
        Returns:
            Text report
        """
        metrics_summary = self.monitor.get_metrics_summary()
        resource_summary = self.monitor.get_resource_summary()
        
        report = []
        report.append("=" * 80)
        report.append("PERFORMANCE TEST REPORT")
        report.append("=" * 80)
        report.append(f"Generated at: {datetime.now().isoformat()}")
        report.append("")
        
        # Metrics summary
        if metrics_summary:
            report.append("OPERATION METRICS")
            report.append("-" * 40)
            for operation, data in metrics_summary.items():
                report.append(f"Operation: {operation}")
                report.append(f"  Total Count: {data['total_count']}")
                report.append(f"  Success Count: {data['success_count']}")
                report.append(f"  Failure Count: {data['failure_count']}")
                report.append(f"  Success Rate: {data['success_rate']:.2%}")
                report.append(f"  Average Duration: {data['average_duration']:.3f}s")
                report.append(f"  Median Duration: {data['median_duration']:.3f}s")
                report.append(f"  Min Duration: {data['min_duration']:.3f}s")
                report.append(f"  Max Duration: {data['max_duration']:.3f}s")
                report.append(f"  Std Deviation: {data['std_deviation']:.3f}s")
                report.append("")
        
        # Resource summary
        if resource_summary:
            report.append("RESOURCE USAGE")
            report.append("-" * 40)
            report.append(f"Monitoring Duration: {resource_summary['monitoring_duration']:.1f}s")
            report.append(f"Sample Count: {resource_summary['sample_count']}")
            report.append("")
            
            if "cpu" in resource_summary:
                cpu = resource_summary["cpu"]
                report.append("CPU Usage:")
                report.append(f"  Average: {cpu['average']:.1f}%")
                report.append(f"  Median: {cpu['median']:.1f}%")
                report.append(f"  Min: {cpu['min']:.1f}%")
                report.append(f"  Max: {cpu['max']:.1f}%")
                report.append("")
            
            if "memory" in resource_summary:
                memory = resource_summary["memory"]
                report.append("Memory Usage:")
                report.append(f"  Average: {memory['average_percent']:.1f}% ({memory['average_mb']:.1f} MB)")
                report.append(f"  Median: {memory['median_percent']:.1f}%")
                report.append(f"  Min: {memory['min_percent']:.1f}%")
                report.append(f"  Max: {memory['max_percent']:.1f}% ({memory['max_mb']:.1f} MB)")
                report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def generate_json_report(self) -> Dict[str, Any]:
        """
        Generate JSON performance report.
        
        Returns:
            JSON report
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": self.monitor.get_metrics_summary(),
            "resources": self.monitor.get_resource_summary(),
            "raw_metrics": [
                {
                    "operation": m.operation,
                    "duration": m.duration,
                    "timestamp": m.timestamp,
                    "success": m.success,
                    "error_message": m.error_message,
                    "metadata": m.metadata,
                }
                for m in self.monitor.metrics
            ],
            "raw_resources": [
                {
                    "timestamp": r.timestamp,
                    "cpu_percent": r.cpu_percent,
                    "memory_percent": r.memory_percent,
                    "memory_mb": r.memory_mb,
                    "disk_io_read": r.disk_io_read,
                    "disk_io_write": r.disk_io_write,
                    "network_sent": r.network_sent,
                    "network_recv": r.network_recv,
                }
                for r in self.monitor.resource_usage
            ],
        }
    
    def save_report(self, file_path: Union[str, Path], format: str = "text") -> None:
        """
        Save performance report to file.
        
        Args:
            file_path: Output file path
            format: Report format ("text", "json", "csv")
        """
        file_path = Path(file_path)
        
        if format == "text":
            report = self.generate_text_report()
            file_path.write_text(report, encoding="utf-8")
        elif format == "json":
            report = self.generate_json_report()
            file_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        elif format == "csv":
            self._save_csv_report(file_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Performance report saved to: {file_path}")
    
    def _save_csv_report(self, file_path: Path) -> None:
        """Save CSV performance report."""
        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            
            # Write metrics
            writer.writerow(["Type", "Operation", "Duration", "Success", "Timestamp", "Error"])
            for metric in self.monitor.metrics:
                writer.writerow([
                    "metric",
                    metric.operation,
                    metric.duration,
                    metric.success,
                    metric.timestamp,
                    metric.error_message or "",
                ])
            
            # Write resource usage
            writer.writerow([])  # Empty row separator
            writer.writerow(["Type", "Timestamp", "CPU%", "Memory%", "MemoryMB", "DiskRead", "DiskWrite", "NetSent", "NetRecv"])
            for resource in self.monitor.resource_usage:
                writer.writerow([
                    "resource",
                    resource.timestamp,
                    resource.cpu_percent,
                    resource.memory_percent,
                    resource.memory_mb,
                    resource.disk_io_read,
                    resource.disk_io_write,
                    resource.network_sent,
                    resource.network_recv,
                ])


class PerformanceComparator:
    """Performance comparison utility."""
    
    def __init__(self):
        """Initialize performance comparator."""
        self.baseline_reports: Dict[str, Dict[str, Any]] = {}
    
    def set_baseline(self, name: str, report: Dict[str, Any]) -> None:
        """
        Set baseline performance report.
        
        Args:
            name: Baseline name
            report: Performance report
        """
        self.baseline_reports[name] = report
        logger.info(f"Baseline '{name}' set")
    
    def compare_with_baseline(self, current_report: Dict[str, Any], 
                            baseline_name: str) -> Dict[str, Any]:
        """
        Compare current report with baseline.
        
        Args:
            current_report: Current performance report
            baseline_name: Baseline name
            
        Returns:
            Comparison results
        """
        if baseline_name not in self.baseline_reports:
            raise ValueError(f"Baseline '{baseline_name}' not found")
        
        baseline = self.baseline_reports[baseline_name]
        comparison = {
            "baseline_name": baseline_name,
            "comparison_timestamp": datetime.now().isoformat(),
            "operations": {},
        }
        
        # Compare metrics
        current_metrics = current_report.get("metrics", {})
        baseline_metrics = baseline.get("metrics", {})
        
        for operation in set(current_metrics.keys()) | set(baseline_metrics.keys()):
            current_op = current_metrics.get(operation, {})
            baseline_op = baseline_metrics.get(operation, {})
            
            comparison["operations"][operation] = self._compare_operation_metrics(
                current_op, baseline_op
            )
        
        # Compare resources
        current_resources = current_report.get("resources", {})
        baseline_resources = baseline.get("resources", {})
        
        comparison["resources"] = self._compare_resource_metrics(
            current_resources, baseline_resources
        )
        
        return comparison
    
    def _compare_operation_metrics(self, current: Dict[str, Any], 
                                 baseline: Dict[str, Any]) -> Dict[str, Any]:
        """Compare operation metrics."""
        comparison = {}
        
        # Compare average duration
        current_avg = current.get("average_duration", 0)
        baseline_avg = baseline.get("average_duration", 0)
        
        if baseline_avg > 0:
            comparison["duration_change_percent"] = ((current_avg - baseline_avg) / baseline_avg) * 100
            comparison["duration_change_absolute"] = current_avg - baseline_avg
        else:
            comparison["duration_change_percent"] = 0
            comparison["duration_change_absolute"] = 0
        
        # Compare success rate
        current_success = current.get("success_rate", 0)
        baseline_success = baseline.get("success_rate", 0)
        
        comparison["success_rate_change"] = current_success - baseline_success
        
        # Compare throughput (if available)
        current_count = current.get("total_count", 0)
        baseline_count = baseline.get("total_count", 0)
        
        comparison["throughput_change_percent"] = ((current_count - baseline_count) / baseline_count) * 100 if baseline_count > 0 else 0
        
        return comparison
    
    def _compare_resource_metrics(self, current: Dict[str, Any], 
                                baseline: Dict[str, Any]) -> Dict[str, Any]:
        """Compare resource metrics."""
        comparison = {}
        
        # Compare CPU usage
        current_cpu = current.get("cpu", {})
        baseline_cpu = baseline.get("cpu", {})
        
        if current_cpu and baseline_cpu:
            current_avg_cpu = current_cpu.get("average", 0)
            baseline_avg_cpu = baseline_cpu.get("average", 0)
            
            if baseline_avg_cpu > 0:
                comparison["cpu_change_percent"] = ((current_avg_cpu - baseline_avg_cpu) / baseline_avg_cpu) * 100
            else:
                comparison["cpu_change_percent"] = 0
        
        # Compare memory usage
        current_memory = current.get("memory", {})
        baseline_memory = baseline.get("memory", {})
        
        if current_memory and baseline_memory:
            current_avg_memory = current_memory.get("average_percent", 0)
            baseline_avg_memory = baseline_memory.get("average_percent", 0)
            
            if baseline_avg_memory > 0:
                comparison["memory_change_percent"] = ((current_avg_memory - baseline_avg_memory) / baseline_avg_memory) * 100
            else:
                comparison["memory_change_percent"] = 0
        
        return comparison


class ResourceMonitor:
    """System resource monitoring utility."""
    
    def __init__(self):
        """Initialize resource monitor."""
        self.process = psutil.Process()
        self.initial_cpu_times = self.process.cpu_times()
        self.initial_memory_info = self.process.memory_info()
    
    def get_current_usage(self) -> Dict[str, Any]:
        """
        Get current resource usage.
        
        Returns:
            Current resource usage
        """
        cpu_times = self.process.cpu_times()
        memory_info = self.process.memory_info()
        
        # Calculate CPU usage
        cpu_delta = sum(cpu_times) - sum(self.initial_cpu_times)
        cpu_percent = (cpu_delta / time.time()) * 100 if time.time() > 0 else 0
        
        return {
            "cpu_percent": cpu_percent,
            "memory_rss_mb": memory_info.rss / 1024 / 1024,
            "memory_vms_mb": memory_info.vms / 1024 / 1024,
            "memory_percent": self.process.memory_percent(),
            "num_threads": self.process.num_threads(),
            "num_fds": self.process.num_fds() if hasattr(self.process, 'num_fds') else 0,
        }
    
    def get_system_usage(self) -> Dict[str, Any]:
        """
        Get system-wide resource usage.
        
        Returns:
            System resource usage
        """
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory": {
                "total_mb": psutil.virtual_memory().total / 1024 / 1024,
                "available_mb": psutil.virtual_memory().available / 1024 / 1024,
                "used_mb": psutil.virtual_memory().used / 1024 / 1024,
                "percent": psutil.virtual_memory().percent,
            },
            "disk": {
                "total_mb": psutil.disk_usage('/').total / 1024 / 1024,
                "used_mb": psutil.disk_usage('/').used / 1024 / 1024,
                "free_mb": psutil.disk_usage('/').free / 1024 / 1024,
                "percent": (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100,
            },
        }


# Convenience functions
def create_performance_monitor(enable_resource_monitoring: bool = True) -> PerformanceMonitor:
    """
    Create a performance monitor instance.
    
    Args:
        enable_resource_monitoring: Enable system resource monitoring
        
    Returns:
        Performance monitor instance
    """
    return PerformanceMonitor(enable_resource_monitoring)


def create_performance_reporter(monitor: PerformanceMonitor) -> PerformanceReporter:
    """
    Create a performance reporter instance.
    
    Args:
        monitor: Performance monitor instance
        
    Returns:
        Performance reporter instance
    """
    return PerformanceReporter(monitor)


def create_performance_comparator() -> PerformanceComparator:
    """
    Create a performance comparator instance.
    
    Returns:
        Performance comparator instance
    """
    return PerformanceComparator()


def create_resource_monitor() -> ResourceMonitor:
    """
    Create a resource monitor instance.
    
    Returns:
        Resource monitor instance
    """
    return ResourceMonitor()
