"""Module system_operation."""

from ai_admin.core.custom_exceptions import ConfigurationError, CustomError, PermissionError, SSLError, ValidationError
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum
import logging
from ai_admin.settings_manager import get_settings_manager
from ai_admin.config.roles_config import RolesConfig

class SystemOperation(Enum):
    """System operation types."""

    MONITOR = "monitor"
    PROCESSES = "processes"
    RESOURCES = "resources"
    TEMPERATURE = "temperature"
    GPU_METRICS = "gpu_metrics"
    NETWORK = "network"
    DISK_USAGE = "disk_usage"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    SYSTEM_INFO = "system_info"
    BOOT_TIME = "boot_time"
    UPTIME = "uptime"
    LOAD_AVERAGE = "load_average"
    SYSTEM_LOGS = "system_logs"
    KERNEL_INFO = "kernel_info"
    HARDWARE_INFO = "hardware_info"
    SERVICES = "services"
    CONFIGURATION = "configuration"
    SECURITY_AUDIT = "security_audit"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    SYSTEM_MAINTENANCE = "system_maintenance"



