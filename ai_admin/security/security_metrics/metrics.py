"""Module metrics."""

from ai_admin.core.custom_exceptions import CustomError
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from ai_admin.settings_manager import get_settings_manager
from .types import MetricCategory, MetricPoint, MetricSummary, MetricType

class SecurityMetrics:
    """Unified security metrics for all components.

    This class provides:
    - Real-time metrics collection
    - Metric aggregation and analysis
    - Performance monitoring
    - Security event tracking
    - User activity metrics
    - System health metrics
    """

    def __init__(self, settings_manager: Optional[Any] = None):
        """
        Initialize Security Metrics.

        Args:
            settings_manager: Settings manager instance
        """
        self.settings_manager = settings_manager or get_settings_manager()
        self.logger = logging.getLogger("ai_admin.security_metrics")

        # Metrics storage
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(lambda: 0.0)
        self.histograms: Dict[str, List[float]] = defaultdict(list)

        # Metric categories
        self.operation_counts: Dict[str, int] = defaultdict(int)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.role_usage: Dict[str, int] = defaultdict(int)
        self.component_usage: Dict[str, int] = defaultdict(int)
        self.success_rates: Dict[str, List[float]] = defaultdict(list)
        self.response_times: Dict[str, List[float]] = defaultdict(list)

        # Security-specific metrics
        self.auth_attempts: Dict[str, int] = defaultdict(int)
        self.auth_failures: Dict[str, int] = defaultdict(int)
        self.permission_denials: Dict[str, int] = defaultdict(int)
        self.ssl_errors: Dict[str, int] = defaultdict(int)
        self.certificate_issues: Dict[str, int] = defaultdict(int)

        # Performance metrics
        self.operation_durations: Dict[str, List[float]] = defaultdict(list)
        self.memory_usage: Dict[str, List[float]] = defaultdict(list)
        self.cpu_usage: Dict[str, List[float]] = defaultdict(list)

        # User metrics
        self.user_activity: Dict[str, int] = defaultdict(int)
        self.user_sessions: Dict[str, int] = defaultdict(int)
        self.user_roles: Dict[str, int] = defaultdict(int)

    def record_operation(
        self,
        component: str,
        operation: str,
        user_roles: List[str],
        success: bool,
        duration: Optional[float] = None,
        memory_usage: Optional[float] = None,
        cpu_usage: Optional[float] = None,
    ) -> None:
        """
        Record security operation.

        Args:
            component: Component name
            operation: Operation name
            user_roles: List of user roles
            success: Whether operation was successful
            duration: Operation duration in seconds
            memory_usage: Memory usage in MB
            cpu_usage: CPU usage percentage
        """
        try:
            timestamp = datetime.utcnow()
            operation_key = f"{component}.{operation}"

            # Record operation count
            self.operation_counts[operation_key] += 1

            # Record error count
            if not success:
                self.error_counts[operation_key] += 1

            # Record role usage
            for role in user_roles:
                self.role_usage[role] += 1

            # Record component usage
            self.component_usage[component] += 1

            # Record success rate
            self.success_rates[operation_key].append(success)

            # Record performance metrics
            if duration is not None:
                self.operation_durations[operation_key].append(duration)
                self.response_times[operation_key].append(duration)

            if memory_usage is not None:
                self.memory_usage[operation_key].append(memory_usage)

            if cpu_usage is not None:
                self.cpu_usage[operation_key].append(cpu_usage)

            # Create metric point
            metric_point = MetricPoint(
                name="operation_count",
                value=1.0,
                timestamp=timestamp,
                labels={
                    "component": component,
                    "operation": operation,
                    "success": str(success),
                },
                category=MetricCategory.OPERATION,
                metric_type=MetricType.COUNTER,
            )

            self.metrics["operation_count"].append(metric_point)

            # Record duration metric if available
            if duration is not None:
                duration_metric = MetricPoint(
                    name="operation_duration",
                    value=duration,
                    timestamp=timestamp,
                    labels={"component": component, "operation": operation},
                    category=MetricCategory.PERFORMANCE,
                    metric_type=MetricType.HISTOGRAM,
                )

                self.metrics["operation_duration"].append(duration_metric)

        except CustomError as e:
            self.logger.error(f"Error recording operation metrics: {str(e)}")

    def record_security_event(
        self,
        event_type: str,
        component: str,
        severity: str,
        user_roles: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record security event.

        Args:
            event_type: Type of security event
            component: Component name
            severity: Event severity
            user_roles: List of user roles
            details: Additional event details
        """
        try:
            timestamp = datetime.utcnow()

            # Record security event counts
            if event_type == "auth_attempt":
                self.auth_attempts[component] += 1
            elif event_type == "auth_failure":
                self.auth_failures[component] += 1
            elif event_type == "permission_denied":
                self.permission_denials[component] += 1
            elif event_type == "ssl_error":
                self.ssl_errors[component] += 1
            elif event_type == "certificate_issue":
                self.certificate_issues[component] += 1

            # Create security metric point
            metric_point = MetricPoint(
                name="security_event",
                value=1.0,
                timestamp=timestamp,
                labels={
                    "event_type": event_type,
                    "component": component,
                    "severity": severity,
                },
                category=MetricCategory.SECURITY,
                metric_type=MetricType.COUNTER,
            )

            self.metrics["security_event"].append(metric_point)

            # Record user activity if roles provided
            if user_roles:
                for role in user_roles:
                    self.user_activity[role] += 1

        except CustomError as e:
            self.logger.error(f"Error recording security event: {str(e)}")

    def record_user_activity(
        self,
        user_id: str,
        user_roles: List[str],
        component: str,
        operation: str,
        success: bool,
    ) -> None:
        """
        Record user activity.

        Args:
            user_id: User identifier
            user_roles: List of user roles
            component: Component name
            operation: Operation name
            success: Whether operation was successful
        """
        try:
            timestamp = datetime.utcnow()

            # Record user activity
            self.user_activity[user_id] += 1

            # Record user roles
            for role in user_roles:
                self.user_roles[role] += 1

            # Create user activity metric
            metric_point = MetricPoint(
                name="user_activity",
                value=1.0,
                timestamp=timestamp,
                labels={
                    "user_id": user_id,
                    "component": component,
                    "operation": operation,
                    "success": str(success),
                },
                category=MetricCategory.USER,
                metric_type=MetricType.COUNTER,
            )

            self.metrics["user_activity"].append(metric_point)

        except CustomError as e:
            self.logger.error(f"Error recording user activity: {str(e)}")

    def record_system_metrics(
        self,
        component: str,
        memory_usage: float,
        cpu_usage: float,
        disk_usage: Optional[float] = None,
        network_usage: Optional[float] = None,
    ) -> None:
        """
        Record system metrics.

        Args:
            component: Component name
            memory_usage: Memory usage in MB
            cpu_usage: CPU usage percentage
            disk_usage: Disk usage percentage
            network_usage: Network usage in MB/s
        """
        try:
            timestamp = datetime.utcnow()

            # Record system metrics
            self.memory_usage[component].append(memory_usage)
            self.cpu_usage[component].append(cpu_usage)

            # Create system metric points
            memory_metric = MetricPoint(
                name="memory_usage",
                value=memory_usage,
                timestamp=timestamp,
                labels={"component": component},
                category=MetricCategory.SYSTEM,
                metric_type=MetricType.GAUGE,
            )

            cpu_metric = MetricPoint(
                name="cpu_usage",
                value=cpu_usage,
                timestamp=timestamp,
                labels={"component": component},
                category=MetricCategory.SYSTEM,
                metric_type=MetricType.GAUGE,
            )

            self.metrics["memory_usage"].append(memory_metric)
            self.metrics["cpu_usage"].append(cpu_metric)

            # Record disk usage if provided
            if disk_usage is not None:
                disk_metric = MetricPoint(
                    name="disk_usage",
                    value=disk_usage,
                    timestamp=timestamp,
                    labels={"component": component},
                    category=MetricCategory.SYSTEM,
                    metric_type=MetricType.GAUGE,
                )
                self.metrics["disk_usage"].append(disk_metric)

            # Record network usage if provided
            if network_usage is not None:
                network_metric = MetricPoint(
                    name="network_usage",
                    value=network_usage,
                    timestamp=timestamp,
                    labels={"component": component},
                    category=MetricCategory.SYSTEM,
                    metric_type=MetricType.GAUGE,
                )
                self.metrics["network_usage"].append(network_metric)

        except CustomError as e:
            self.logger.error(f"Error recording system metrics: {str(e)}")

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

            # Calculate performance metrics
            avg_durations = {}
            for key, durations in self.operation_durations.items():
                if durations:
                    avg_durations[key] = sum(durations) / len(durations)

            avg_memory = {}
            for key, memory_values in self.memory_usage.items():
                if memory_values:
                    avg_memory[key] = sum(memory_values) / len(memory_values)

            avg_cpu = {}
            for key, cpu_values in self.cpu_usage.items():
                if cpu_values:
                    avg_cpu[key] = sum(cpu_values) / len(cpu_values)

            return {
                "operation_counts": dict(self.operation_counts),
                "error_counts": dict(self.error_counts),
                "role_usage": dict(self.role_usage),
                "component_usage": dict(self.component_usage),
                "success_rates": success_rates,
                "avg_durations": avg_durations,
                "avg_memory_usage": avg_memory,
                "avg_cpu_usage": avg_cpu,
                "security_events": {
                    "auth_attempts": dict(self.auth_attempts),
                    "auth_failures": dict(self.auth_failures),
                    "permission_denials": dict(self.permission_denials),
                    "ssl_errors": dict(self.ssl_errors),
                    "certificate_issues": dict(self.certificate_issues),
                },
                "user_metrics": {
                    "user_activity": dict(self.user_activity),
                    "user_roles": dict(self.user_roles),
                },
                "total_operations": sum(self.operation_counts.values()),
                "total_errors": sum(self.error_counts.values()),
                "overall_success_rate": self._calculate_overall_success_rate(),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except CustomError as e:
            self.logger.error(f"Error getting metrics: {str(e)}")
            return {"error": str(e)}

    def get_metric_summary(
        self, metric_name: str, time_window: Optional[timedelta] = None
    ) -> Optional[MetricSummary]:
        """
        Get metric summary statistics.

        Args:
            metric_name: Name of the metric
            time_window: Time window for filtering (optional)

        Returns:
            Metric summary or None if not found
        """
        try:
            if metric_name not in self.metrics:
                return None

            metric_data = self.metrics[metric_name]

            # Filter by time window if provided
            if time_window:
                cutoff_time = datetime.utcnow() - time_window
                metric_data = deque(
                    [m for m in metric_data if m.timestamp >= cutoff_time]
                )

            if not metric_data:
                return None

            # Extract values
            values = [m.value for m in metric_data]
            values.sort()

            # Calculate statistics
            count = len(values)
            total = sum(values)
            min_val = min(values)
            max_val = max(values)
            avg_val = total / count if count > 0 else 0

            # Calculate percentiles
            p50 = self._calculate_percentile(values, 50)
            p95 = self._calculate_percentile(values, 95)
            p99 = self._calculate_percentile(values, 99)

            return MetricSummary(
                name=metric_name,
                count=count,
                sum=total,
                min=min_val,
                max=max_val,
                avg=avg_val,
                p50=p50,
                p95=p95,
                p99=p99,
                timestamp=datetime.utcnow(),
            )

        except CustomError as e:
            self.logger.error(
                f"Error getting metric summary for {metric_name}: {str(e)}"
            )
            return None

    def get_metrics_by_category(
        self, category: MetricCategory
    ) -> Dict[str, List[MetricPoint]]:
        """
        Get metrics by category.

        Args:
            category: Metric category

        Returns:
            Dictionary of metrics grouped by name
        """
        try:
            category_metrics = defaultdict(list)

            for metric_name, metric_points in self.metrics.items():
                for point in metric_points:
                    if point.category == category:
                        category_metrics[metric_name].append(point)

            return dict(category_metrics)

        except CustomError as e:
            self.logger.error(f"Error getting metrics by category {category}: {str(e)}")
            return {}

    def get_metrics_by_component(self, component: str) -> Dict[str, Any]:
        """
        Get metrics for specific component.

        Args:
            component: Component name

        Returns:
            Dictionary of component metrics
        """
        try:
            component_metrics: Dict[str, Any] = {
                "operation_counts": {},
                "error_counts": {},
                "success_rates": {},
                "avg_durations": {},
                "avg_memory_usage": {},
                "avg_cpu_usage": {},
                "security_events": {
                    "auth_attempts": 0,
                    "auth_failures": 0,
                    "permission_denials": 0,
                    "ssl_errors": 0,
                    "certificate_issues": 0,
                },
            }

            # Filter metrics by component
            for key, value in self.operation_counts.items():
                if key.startswith(f"{component}."):
                    component_metrics["operation_counts"][key] = value

            for key, value in self.error_counts.items():
                if key.startswith(f"{component}."):
                    component_metrics["error_counts"][key] = value

            for key, successes in self.success_rates.items():
                if key.startswith(f"{component}.") and successes:
                    component_metrics["success_rates"][key] = sum(successes) / len(
                        successes
                    )

            for key, durations in self.operation_durations.items():
                if key.startswith(f"{component}.") and durations:
                    component_metrics["avg_durations"][key] = sum(durations) / len(
                        durations
                    )

            for key, memory_values in self.memory_usage.items():
                if key.startswith(f"{component}.") and memory_values:
                    component_metrics["avg_memory_usage"][key] = sum(
                        memory_values
                    ) / len(memory_values)

            for key, cpu_values in self.cpu_usage.items():
                if key.startswith(f"{component}.") and cpu_values:
                    component_metrics["avg_cpu_usage"][key] = sum(cpu_values) / len(
                        cpu_values
                    )

            # Security events
            component_metrics["security_events"]["auth_attempts"] = (
                self.auth_attempts.get(component, 0)
            )
            component_metrics["security_events"]["auth_failures"] = (
                self.auth_failures.get(component, 0)
            )
            component_metrics["security_events"]["permission_denials"] = (
                self.permission_denials.get(component, 0)
            )
            component_metrics["security_events"]["ssl_errors"] = self.ssl_errors.get(
                component, 0
            )
            component_metrics["security_events"]["certificate_issues"] = (
                self.certificate_issues.get(component, 0)
            )

            return component_metrics

        except CustomError as e:
            self.logger.error(
                f"Error getting metrics for component {component}: {str(e)}"
            )
            return {"error": str(e)}

    def export_metrics(self, format: str = "json") -> Union[str, Dict[str, Any]]:
        """
        Export metrics in specified format.

        Args:
            format: Export format ("json" or "prometheus")

        Returns:
            Exported metrics
        """
        try:
            if format == "json":
                return self.get_metrics()
            elif format == "prometheus":
                return self._export_prometheus_format()
            else:
                raise ValueError(f"Unsupported export format: {format}")

        except CustomError as e:
            self.logger.error(f"Error exporting metrics: {str(e)}")
            return {"error": str(e)}

    def clear_metrics(self) -> None:
        """Clear all metrics."""
        try:
            self.metrics.clear()
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.operation_counts.clear()
            self.error_counts.clear()
            self.role_usage.clear()
            self.component_usage.clear()
            self.success_rates.clear()
            self.response_times.clear()
            self.auth_attempts.clear()
            self.auth_failures.clear()
            self.permission_denials.clear()
            self.ssl_errors.clear()
            self.certificate_issues.clear()
            self.operation_durations.clear()
            self.memory_usage.clear()
            self.cpu_usage.clear()
            self.user_activity.clear()
            self.user_sessions.clear()
            self.user_roles.clear()

            self.logger.info("All metrics cleared")

        except CustomError as e:
            self.logger.error(f"Error clearing metrics: {str(e)}")

    def _calculate_overall_success_rate(self) -> float:
        """Calculate overall success rate."""
        try:
            total_operations = sum(self.operation_counts.values())
            total_errors = sum(self.error_counts.values())

            if total_operations == 0:
                return 1.0

            return (total_operations - total_errors) / total_operations

        except CustomError as e:
            self.logger.error(f"Error calculating overall success rate: {str(e)}")
            return 0.0

    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value."""
        try:
            if not values:
                return 0.0

            sorted_values = sorted(values)
            index = int((percentile / 100) * len(sorted_values))
            index = min(index, len(sorted_values) - 1)

            return sorted_values[index]

        except CustomError as e:
            self.logger.error(f"Error calculating percentile {percentile}: {str(e)}")
            return 0.0

    def _export_prometheus_format(self) -> str:
        """Export metrics in Prometheus format."""
        try:
            lines: List[str] = []

            # Export counters
            for name, value in self.counters.items():
                lines.append(f"# TYPE {name} counter")
                lines.append(f"{name} {value}")

            # Export gauges
            for name, value in self.gauges.items():  # type: ignore
                lines.append(f"# TYPE {name} gauge")
                lines.append(f"{name} {float(value)}")

            # Export histograms
            for name, values in self.histograms.items():
                if values:
                    lines.append(f"# TYPE {name} histogram")
                    lines.append(f"{name}_count {len(values)}")
                    lines.append(f"{name}_sum {sum(values)}")
                    lines.append(f"{name}_avg {sum(values) / len(values)}")

            return "\n".join(lines)

        except CustomError as e:
            self.logger.error(f"Error exporting Prometheus format: {str(e)}")
            return ""

