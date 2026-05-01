"""Module severity."""

from ai_admin.core.custom_exceptions import CustomError
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from ai_admin.settings_manager import get_settings_manager
pass  # SecurityEventType imported where needed
pass  # SecurityEvent imported where needed
pass  # SecurityAlert imported where needed
pass  # SecurityMonitor
pass  # SecurityMetrics

class SecuritySeverity(Enum):
    """Security severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

