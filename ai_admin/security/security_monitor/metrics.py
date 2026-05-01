"""Module metrics."""

from ai_admin.core.custom_exceptions import CustomError
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from ai_admin.settings_manager import get_settings_manager
from .event_type import SecurityEventType
from .severity import SecuritySeverity
from .event import SecurityEvent
from .alert import SecurityAlert

class SecurityMetrics:
    """Unified security metrics for all components."""

    def __init__(self):
        """Initialize Security Metrics."""
        self.operation_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.role_usage = defaultdict(int)
        self.component_usage = defaultdict(int)
        self.success_rates = defaultdict(list)
        self.response_times = defaultdict(list)

    def record_operation(
        self, component: str, operation: str, user_roles: List[str], success: bool
    ) -> None:
        """
        Record security operation.

        Args:
            component: Component name
            operation: Operation name
            user_roles: List of user roles
            success: Whether operation was successful
        """
        try:
            # Record operation count
            self.operation_counts[f"{component}.{operation}"] += 1

            # Record error count
            if not success:
                self.error_counts[f"{component}.{operation}"] += 1

            # Record role usage
            for role in user_roles:
                self.role_usage[role] += 1

            # Record component usage
            self.component_usage[component] += 1

            # Record success rate
            self.success_rates[f"{component}.{operation}"].append(success)

        except CustomError as e:
            # Use basic logging if logger not available
            print(f"Error recording operation metrics: {str(e)}")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get security metrics.

        Returns:
            Dictionary of security metrics
        """
        try:
            # Calculate success rates
            success_rates = {}
            for key, successes in self.success_rates.items():
                if successes:
                    success_rates[key] = sum(successes) / len(successes)

            return {
                "operation_counts": dict(self.operation_counts),
                "error_counts": dict(self.error_counts),
                "role_usage": dict(self.role_usage),
                "component_usage": dict(self.component_usage),
                "success_rates": success_rates,
                "total_operations": sum(self.operation_counts.values()),
                "total_errors": sum(self.error_counts.values()),
                "overall_success_rate": self._calculate_overall_success_rate(),
            }

        except CustomError as e:
            return {"error": str(e)}

    def _calculate_overall_success_rate(self) -> float:
        """Calculate overall success rate."""
        try:
            total_operations = sum(self.operation_counts.values())
            total_errors = sum(self.error_counts.values())

            if total_operations == 0:
                return 1.0

            return (total_operations - total_errors) / total_operations

        except CustomError:
            return 0.0

