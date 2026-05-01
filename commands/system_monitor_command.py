from mcp_proxy_adapter.core.errors import CommandError as CustomError, InternalError, AuthorizationError
"""System monitoring command for MCP server.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import psutil
from datetime import datetime
from typing import Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult, CommandResult
from base_unified_command import BaseUnifiedCommand

from security import (
    SystemSecurityAdapter,
    SystemOperation,
)

class SystemMonitorCommand(BaseUnifiedCommand):
    """Command to monitor system resources and performance."""

    name = "system_monitor"

    def _get_default_operation(self) -> str:
        """Get default operation name for SystemMonitorCommand."""
        return "system:monitor"

    def __init__(self) -> None:
        """Initialize system monitor command with security adapter."""
        super().__init__()
        self.system_security_adapter = SystemSecurityAdapter()

    async def execute(
        self,
        action: str = "status",
        interval: int = 1,
        duration: int = 60,
        metrics: Optional[List[str]] = None,
        output_format: str = "json",
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ):
        """
        Monitor system resources and performance.

        Args:
            action: Action to perform (status, cpu, memory, disk, network, processes, all)
            interval: Monitoring interval in seconds
            duration: Total monitoring duration in seconds
            metrics: List of specific metrics to monitor
            output_format: Output format (json, table, csv)
            user_roles: List of user roles for security validation
        """
        try:
            # Security validation
            user_roles = user_roles or []

            # Validate system operation
            operation_params = {
                "action": action,
                "interval": interval,
                "duration": duration,
                "metrics": metrics,
            }

            is_valid, error_msg = self.system_security_adapter.validate_system_operation(
                SystemOperation.MONITOR, user_roles, operation_params
            )

            if not is_valid:
                return ErrorResult(
                    message=f"Security validation failed: {error_msg}",
                    code="SECURITY_VALIDATION_FAILED",
                    details={"error": error_msg, "user_roles": user_roles},
                )

            if action == "status":
                return await self._get_system_status()
            elif action == "cpu":
                return await self._monitor_cpu(interval, duration)
            elif action == "memory":
                return await self._monitor_memory(interval, duration)
            elif action == "disk":
                return await self._monitor_disk()
            elif action == "network":
                return await self._monitor_network(interval, duration)
            elif action == "processes":
                return await self._monitor_processes()
            elif action == "all":
                return await self._monitor_all(interval, duration)
            else:
                return ErrorResult(
                    message=f"Unknown action: {action}",
                    code="UNKNOWN_ACTION",
                    details={
                        "supported_actions": [
                            "status",
                            "cpu",
                            "memory",
                            "disk",
                            "network",
                            "processes",
                            "all",
                        ]
                    },
                )

        except CustomError as e:
            return ErrorResult(
                message=f"System monitoring failed: {str(e)}",
                code="SYSTEM_MONITORING_FAILED",
                details={"exception": str(e)},
            )

    async def _get_system_status(self) -> CommandResult:
        """Get overall system status."""
        try:
            # Get system information
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            # Get CPU information
            cpu_count = psutil.cpu_count()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get memory information
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Get disk information
            disk = psutil.disk_usage('/')
            
            # Get network information
            network = psutil.net_io_counters()
            
            return SuccessResult(
                data={
                    "message": "System status retrieved",
                    "system_info": {
                        "boot_time": boot_time.isoformat(),
                        "uptime_seconds": uptime.total_seconds(),
                        "uptime_human": str(uptime),
                    },
                    "cpu_info": {
                        "cpu_count": cpu_count,
                        "cpu_percent": cpu_percent,
                    },
                    "memory_info": {
                        "total": memory.total,
                        "available": memory.available,
                        "used": memory.used,
                        "percent": memory.percent,
                    },
                    "swap_info": {
                        "total": swap.total,
                        "used": swap.used,
                        "free": swap.free,
                        "percent": swap.percent,
                    },
                    "disk_info": {
                        "total": disk.total,
                        "used": disk.used,
                        "free": disk.free,
                        "percent": (disk.used / disk.total) * 100,
                    },
                    "network_info": {
                        "bytes_sent": network.bytes_sent,
                        "bytes_recv": network.bytes_recv,
                        "packets_sent": network.packets_sent,
                        "packets_recv": network.packets_recv,
                    },
                }
            )
            
        except CustomError as e:
            return ErrorResult(
                message=f"Failed to get system status: {str(e)}",
                code="SYSTEM_STATUS_FAILED",
                details={"exception": str(e)}
            )

    async def _monitor_cpu(self, interval: int, duration: int) -> CommandResult:
        """Monitor CPU usage."""
        try:
            import asyncio
            
            cpu_data = []
            end_time = datetime.now().timestamp() + duration
            
            while datetime.now().timestamp() < end_time:
                cpu_percent = psutil.cpu_percent(interval=interval, percpu=True)
                cpu_data.append({
                    "timestamp": datetime.now().isoformat(),
                    "cpu_percent": cpu_percent,
                    "cpu_percent_avg": sum(cpu_percent) / len(cpu_percent),
                })
                await asyncio.sleep(interval)
            
            return SuccessResult(
                data={
                    "message": "CPU monitoring completed",
                    "duration": duration,
                    "interval": interval,
                    "cpu_data": cpu_data,
                }
            )
            
        except CustomError as e:
            return ErrorResult(
                message=f"CPU monitoring failed: {str(e)}",
                code="CPU_MONITORING_FAILED",
                details={"exception": str(e)}
            )

    async def _monitor_memory(self, interval: int, duration: int) -> CommandResult:
        """Monitor memory usage."""
        try:
            import asyncio
            
            memory_data = []
            end_time = datetime.now().timestamp() + duration
            
            while datetime.now().timestamp() < end_time:
                memory = psutil.virtual_memory()
                swap = psutil.swap_memory()
                
                memory_data.append({
                    "timestamp": datetime.now().isoformat(),
                    "memory_percent": memory.percent,
                    "memory_used": memory.used,
                    "memory_available": memory.available,
                    "swap_percent": swap.percent,
                    "swap_used": swap.used,
                })
                await asyncio.sleep(interval)
            
            return SuccessResult(
                data={
                    "message": "Memory monitoring completed",
                    "duration": duration,
                    "interval": interval,
                    "memory_data": memory_data,
                }
            )
            
        except CustomError as e:
            return ErrorResult(
                message=f"Memory monitoring failed: {str(e)}",
                code="MEMORY_MONITORING_FAILED",
                details={"exception": str(e)}
            )

    async def _monitor_disk(self) -> CommandResult:
        """Monitor disk usage."""
        try:
            disk_data = []
            
            # Get all disk partitions
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_data.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": (usage.used / usage.total) * 100,
                    })
                except AuthorizationError:
                    # Skip partitions we can't access
                    continue
            
            return SuccessResult(
                data={
                    "message": "Disk monitoring completed",
                    "disk_data": disk_data,
                }
            )
            
        except CustomError as e:
            return ErrorResult(
                message=f"Disk monitoring failed: {str(e)}",
                code="DISK_MONITORING_FAILED",
                details={"exception": str(e)}
            )

    async def _monitor_network(self, interval: int, duration: int) -> CommandResult:
        """Monitor network usage."""
        try:
            import asyncio
            
            network_data = []
            end_time = datetime.now().timestamp() + duration
            
            # Get initial network stats
            initial_stats = psutil.net_io_counters()
            
            while datetime.now().timestamp() < end_time:
                await asyncio.sleep(interval)
                current_stats = psutil.net_io_counters()
                
                network_data.append({
                    "timestamp": datetime.now().isoformat(),
                    "bytes_sent": current_stats.bytes_sent,
                    "bytes_recv": current_stats.bytes_recv,
                    "packets_sent": current_stats.packets_sent,
                    "packets_recv": current_stats.packets_recv,
                    "bytes_sent_delta": current_stats.bytes_sent - initial_stats.bytes_sent,
                    "bytes_recv_delta": current_stats.bytes_recv - initial_stats.bytes_recv,
                })
                
                initial_stats = current_stats
            
            return SuccessResult(
                data={
                    "message": "Network monitoring completed",
                    "duration": duration,
                    "interval": interval,
                    "network_data": network_data,
                }
            )
            
        except InternalError as e:
            return ErrorResult(
                message=f"Network monitoring failed: {str(e)}",
                code="NETWORK_MONITORING_FAILED",
                details={"exception": str(e)}
            )

    async def _monitor_processes(self) -> CommandResult:
        """Monitor running processes."""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            
            return SuccessResult(
                data={
                    "message": "Process monitoring completed",
                    "process_count": len(processes),
                    "processes": processes[:20],  # Top 20 processes
                }
            )
            
        except CustomError as e:
            return ErrorResult(
                message=f"Process monitoring failed: {str(e)}",
                code="PROCESS_MONITORING_FAILED",
                details={"exception": str(e)}
            )

    async def _monitor_all(self, interval: int, duration: int) -> CommandResult:
        """Monitor all system resources."""
        try:
            import asyncio
            
            all_data = []
            end_time = datetime.now().timestamp() + duration
            
            while datetime.now().timestamp() < end_time:
                # Get all system information
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                network = psutil.net_io_counters()
                
                all_data.append({
                    "timestamp": datetime.now().isoformat(),
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_used": memory.used,
                    "disk_percent": (disk.used / disk.total) * 100,
                    "disk_used": disk.used,
                    "network_bytes_sent": network.bytes_sent,
                    "network_bytes_recv": network.bytes_recv,
                })
                
                await asyncio.sleep(interval)
            
            return SuccessResult(
                data={
                    "message": "Complete system monitoring completed",
                    "duration": duration,
                    "interval": interval,
                    "monitoring_data": all_data,
                }
            )
            
        except CustomError as e:
            return ErrorResult(
                message=f"Complete system monitoring failed: {str(e)}",
                code="COMPLETE_MONITORING_FAILED",
                details={"exception": str(e)}
            )