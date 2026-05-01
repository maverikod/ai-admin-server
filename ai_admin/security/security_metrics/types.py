"""Module types."""

from ai_admin.core.custom_exceptions import CustomError
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from ai_admin.settings_manager import get_settings_manager

class MetricType(Enum):
    """Metric types."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"



class MetricCategory(Enum):
    """Metric categories."""

    OPERATION = "operation"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ERROR = "error"
    USER = "user"
    SYSTEM = "system"



class MetricPoint:
    """Metric data point."""

    name: str
    value: float
    timestamp: datetime
    labels: Optional[Dict[str, str]] = None
    category: MetricCategory = MetricCategory.OPERATION
    metric_type: MetricType = MetricType.GAUGE

    def __post_init__(self) -> None:
        if self.labels is None:
            self.labels = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["category"] = self.category.value
        data["metric_type"] = self.metric_type.value
        data["timestamp"] = self.timestamp.isoformat()
        return data



class MetricSummary:
    """Metric summary statistics."""

    name: str
    count: int
    sum: float
    min: float
    max: float
    avg: float
    p50: float
    p95: float
    p99: float
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data



