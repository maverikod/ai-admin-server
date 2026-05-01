"""Module monitor."""

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
from .metrics import SecurityMetrics

class SecurityMonitor:
    """Unified security monitoring for all components.

    This class provides:
    - Real-time security event monitoring
    - Anomaly detection and alerting
    - Security metrics collection
    - Event correlation and analysis
    - Security reporting and dashboards
    """

    def __init__(self, settings_manager: Optional[Any] = None):
        """
        Initialize Security Monitor.

        Args:
            settings_manager: Settings manager instance
        """
        self.settings_manager = settings_manager or get_settings_manager()
        self.logger = logging.getLogger("ai_admin.security_monitor")

        # Event storage
        self.events: deque = deque(maxlen=10000)  # Keep last 10k events
        self.alerts: List[SecurityAlert] = []

        # Metrics storage
        self.metrics = SecurityMetrics()

        # Anomaly detection thresholds
        self.thresholds = self._load_thresholds()

        # Rate limiting
        self.rate_limits = defaultdict(lambda: deque(maxlen=100))

        # Event correlation
        self.correlation_rules = self._load_correlation_rules()

    def _load_thresholds(self) -> Dict[str, Any]:
        """
        Load security monitoring thresholds.

        Returns:
            Dictionary of monitoring thresholds
        """
        return {
            "failed_auth_per_minute": 10,
            "failed_operations_per_minute": 20,
            "permission_denied_per_minute": 15,
            "suspicious_operations_per_hour": 5,
            "rate_limit_per_minute": 100,
            "error_rate_threshold": 0.1,  # 10% error rate
            "unusual_time_access": True,
            "multiple_failed_attempts": 3,
        }

    def _load_correlation_rules(self) -> List[Dict[str, Any]]:
        """
        Load event correlation rules.

        Returns:
            List of correlation rules
        """
        return [
            {
                "name": "multiple_failed_auth",
                "pattern": [SecurityEventType.AUTHENTICATION_FAILURE],
                "threshold": 3,
                "time_window": 300,  # 5 minutes
                "severity": SecuritySeverity.HIGH,
                "description": "Multiple failed authentication attempts",
            },
            {
                "name": "rapid_permission_denials",
                "pattern": [SecurityEventType.PERMISSION_DENIED],
                "threshold": 10,
                "time_window": 60,  # 1 minute
                "severity": SecuritySeverity.MEDIUM,
                "description": "Rapid permission denials",
            },
            {
                "name": "ssl_certificate_issues",
                "pattern": [
                    SecurityEventType.CERTIFICATE_ISSUE,
                    SecurityEventType.SSL_ERROR,
                ],
                "threshold": 2,
                "time_window": 600,  # 10 minutes
                "severity": SecuritySeverity.HIGH,
                "description": "SSL certificate issues detected",
            },
            {
                "name": "suspicious_activity_pattern",
                "pattern": [SecurityEventType.SUSPICIOUS_ACTIVITY],
                "threshold": 1,
                "time_window": 3600,  # 1 hour
                "severity": SecuritySeverity.CRITICAL,
                "description": "Suspicious activity detected",
            },
        ]

    async def monitor_operation(
        self,
        component: str,
        operation: str,
        user_roles: List[str],
        result: Any,
        user_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Monitor security operation.

        Args:
            component: Component name
            operation: Operation name
            user_roles: List of user roles
            result: Operation result
            user_id: User identifier
            source_ip: Source IP address
            details: Additional details
        """
        try:
            # Determine event type and severity
            event_type, severity = self._classify_operation_result(result)

            # Create security event
            event = SecurityEvent(
                event_id=self._generate_event_id(),
                event_type=event_type,
                severity=severity,
                component=component,
                operation=operation,
                user_roles=user_roles,
                user_id=user_id,
                source_ip=source_ip,
                details=details or {},
                result=result,
            )

            # Store event
            self.events.append(event)

            # Update metrics
            self.metrics.record_operation(
                component, operation, user_roles, result is not None
            )

            # Check for anomalies
            await self._check_anomalies(event)

            # Check rate limits
            await self._check_rate_limits(event)

            # Correlate events
            await self._correlate_events(event)

            # Log event
            self.logger.info(
                f"Security event: {event_type.value} for {component}.{operation}"
            )

        except CustomError as e:
            self.logger.error(f"Error monitoring operation: {str(e)}", exc_info=True)

    async def detect_anomalies(
        self, component: str, operation: str, user_roles: List[str]
    ) -> bool:
        """
        Detect security anomalies.

        Args:
            component: Component name
            operation: Operation name
            user_roles: List of user roles

        Returns:
            True if anomalies detected
        """
        try:
            current_time = datetime.utcnow()
            time_window = timedelta(minutes=5)

            # Get recent events
            recent_events = [
                event
                for event in self.events
                if current_time - event.timestamp <= time_window
            ]

            # Check for failed authentication attempts
            failed_auth_events = [
                event
                for event in recent_events
                if (
                    event.event_type == SecurityEventType.AUTHENTICATION_FAILURE
                    and event.component == component
                )
            ]

            if len(failed_auth_events) >= self.thresholds["failed_auth_per_minute"]:
                await self._create_alert(
                    "high_failed_auth",
                    SecuritySeverity.HIGH,
                    component,
                    f"High number of failed authentication attempts: {len(failed_auth_events)}",
                )
                return True

            # Check for permission denials
            permission_denied_events = [
                event
                for event in recent_events
                if (
                    event.event_type == SecurityEventType.PERMISSION_DENIED
                    and event.component == component
                )
            ]

            if (
                len(permission_denied_events)
                >= self.thresholds["permission_denied_per_minute"]
            ):
                await self._create_alert(
                    "high_permission_denials",
                    SecuritySeverity.MEDIUM,
                    component,
                    f"High number of permission denials: {len(permission_denied_events)}",
                )
                return True

            # Check for unusual time access
            if self.thresholds.get("unusual_time_access", False):
                current_hour = current_time.hour
                if current_hour < 6 or current_hour > 22:  # Outside business hours
                    unusual_events = [
                        event
                        for event in recent_events
                        if (
                            event.component == component
                            and event.event_type
                            in [
                                SecurityEventType.OPERATION_SUCCESS,
                                SecurityEventType.AUTHORIZATION_SUCCESS,
                            ]
                        )
                    ]

                    if len(unusual_events) > 0:
                        await self._create_alert(
                            "unusual_time_access",
                            SecuritySeverity.MEDIUM,
                            component,
                            f"Unusual time access detected: {len(unusual_events)} operations",
                        )
                        return True

            return False

        except CustomError as e:
            self.logger.error(f"Error detecting anomalies: {str(e)}", exc_info=True)
            return False

    async def generate_security_report(self) -> Dict[str, Any]:
        """
        Generate security report.

        Returns:
            Security report data
        """
        try:
            current_time = datetime.utcnow()
            last_24h = current_time - timedelta(hours=24)
            last_7d = current_time - timedelta(days=7)

            # Filter events by time
            events_24h = [e for e in self.events if e.timestamp >= last_24h]
            events_7d = [e for e in self.events if e.timestamp >= last_7d]

            # Generate report
            report = {
                "report_timestamp": current_time.isoformat(),
                "time_period": "24h",
                "summary": {
                    "total_events_24h": len(events_24h),
                    "total_events_7d": len(events_7d),
                    "total_alerts": len(self.alerts),
                    "active_alerts": len([a for a in self.alerts if not a.resolved]),
                    "security_score": self._calculate_security_score(events_24h),
                },
                "events_by_type": self._count_events_by_type(events_24h),
                "events_by_component": self._count_events_by_component(events_24h),
                "events_by_severity": self._count_events_by_severity(events_24h),
                "top_operations": self._get_top_operations(events_24h),
                "security_trends": self._analyze_security_trends(events_7d),
                "alerts_summary": self._get_alerts_summary(),
                "recommendations": self._generate_recommendations(events_24h),
            }

            return report

        except CustomError as e:
            self.logger.error(
                f"Error generating security report: {str(e)}", exc_info=True
            )
            return {"error": str(e)}

    def _classify_operation_result(
        self, result: Any
    ) -> Tuple[SecurityEventType, SecuritySeverity]:
        """
        Classify operation result.

        Args:
            result: Operation result

        Returns:
            Tuple of (event_type, severity)
        """
        try:
            if result is None:
                return SecurityEventType.OPERATION_FAILURE, SecuritySeverity.MEDIUM

            # Check if result indicates success or failure
            if hasattr(result, "success"):
                if result.success:
                    return SecurityEventType.OPERATION_SUCCESS, SecuritySeverity.LOW
                else:
                    return SecurityEventType.OPERATION_FAILURE, SecuritySeverity.MEDIUM

            if hasattr(result, "error"):
                if result.error:
                    return SecurityEventType.OPERATION_FAILURE, SecuritySeverity.MEDIUM
                else:
                    return SecurityEventType.OPERATION_SUCCESS, SecuritySeverity.LOW

            # Default to success if no clear indication
            return SecurityEventType.OPERATION_SUCCESS, SecuritySeverity.LOW

        except CustomError as e:
            self.logger.error(f"Error classifying operation result: {str(e)}")
            return SecurityEventType.SYSTEM_ERROR, SecuritySeverity.HIGH

    async def _check_anomalies(self, event: SecurityEvent) -> None:
        """
        Check for anomalies in the event.

        Args:
            event: Security event
        """
        try:
            # Check for suspicious patterns
            if event.event_type == SecurityEventType.AUTHENTICATION_FAILURE:
                await self._check_auth_failure_pattern(event)

            elif event.event_type == SecurityEventType.PERMISSION_DENIED:
                await self._check_permission_denial_pattern(event)

            elif event.event_type in [
                SecurityEventType.CERTIFICATE_ISSUE,
                SecurityEventType.SSL_ERROR,
            ]:
                await self._check_ssl_issues(event)

        except CustomError as e:
            self.logger.error(f"Error checking anomalies: {str(e)}")

    async def _check_rate_limits(self, event: SecurityEvent) -> None:
        """
        Check rate limits for the event.

        Args:
            event: Security event
        """
        try:
            current_time = datetime.utcnow()
            time_window = timedelta(minutes=1)

            # Get rate limit key
            rate_key = f"{event.component}:{event.user_id or 'anonymous'}"

            # Clean old events
            while (
                self.rate_limits[rate_key]
                and current_time - self.rate_limits[rate_key][0] > time_window
            ):
                self.rate_limits[rate_key].popleft()

            # Add current event
            self.rate_limits[rate_key].append(current_time)

            # Check if rate limit exceeded
            if (
                len(self.rate_limits[rate_key])
                > self.thresholds["rate_limit_per_minute"]
            ):
                await self._create_alert(
                    "rate_limit_exceeded",
                    SecuritySeverity.HIGH,
                    event.component,
                    f"Rate limit exceeded for {rate_key}: {len(self.rate_limits[rate_key])} requests",
                )

        except CustomError as e:
            self.logger.error(f"Error checking rate limits: {str(e)}")

    async def _correlate_events(self, event: SecurityEvent) -> None:
        """
        Correlate events for pattern detection.

        Args:
            event: Security event
        """
        try:
            current_time = datetime.utcnow()

            for rule in self.correlation_rules:
                # Check if event matches rule pattern
                if event.event_type in rule["pattern"]:
                    time_window = timedelta(seconds=rule["time_window"])

                    # Get matching events within time window
                    matching_events = [
                        e
                        for e in self.events
                        if (
                            e.event_type in rule["pattern"]
                            and current_time - e.timestamp <= time_window
                            and e.component == event.component
                        )
                    ]

                    # Check if threshold exceeded
                    if len(matching_events) >= rule["threshold"]:
                        await self._create_alert(
                            rule["name"],
                            rule["severity"],
                            event.component,
                            rule["description"],
                            matching_events,
                        )

        except CustomError as e:
            self.logger.error(f"Error correlating events: {str(e)}")

    async def _create_alert(
        self,
        alert_type: str,
        severity: SecuritySeverity,
        component: str,
        description: str,
        events: Optional[List[SecurityEvent]] = None,
    ) -> None:
        """
        Create security alert.

        Args:
            alert_type: Alert type
            severity: Alert severity
            component: Component name
            description: Alert description
            events: Related events
        """
        try:
            alert = SecurityAlert(
                alert_id=self._generate_alert_id(),
                alert_type=alert_type,
                severity=severity,
                component=component,
                description=description,
                events=events or [],
            )

            self.alerts.append(alert)

            # Log alert
            self.logger.warning(f"Security alert: {alert_type} - {description}")

            # Store alert in settings
            alert_key = f"security.alerts.{alert.alert_id}"
            self.settings_manager.set_custom_setting(alert_key, alert.to_dict())

        except CustomError as e:
            self.logger.error(f"Error creating alert: {str(e)}")

    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        return f"evt_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{len(self.events)}"

    def _generate_alert_id(self) -> str:
        """Generate unique alert ID."""
        return f"alert_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{len(self.alerts)}"

    def _calculate_security_score(self, events: List[SecurityEvent]) -> float:
        """
        Calculate security score based on events.

        Args:
            events: List of events

        Returns:
            Security score (0-100)
        """
        try:
            if not events:
                return 100.0

            # Weight events by severity
            severity_weights = {
                SecuritySeverity.LOW: 1,
                SecuritySeverity.MEDIUM: 3,
                SecuritySeverity.HIGH: 7,
                SecuritySeverity.CRITICAL: 10,
            }

            total_weight = sum(
                severity_weights.get(event.severity, 1) for event in events
            )
            max_possible_weight = len(events) * 10  # All critical events

            if max_possible_weight == 0:
                return 100.0

            score = max(0, 100 - (total_weight / max_possible_weight) * 100)
            return round(score, 2)

        except CustomError as e:
            self.logger.error(f"Error calculating security score: {str(e)}")
            return 50.0

    def _count_events_by_type(self, events: List[SecurityEvent]) -> Dict[str, int]:
        """Count events by type."""
        counts = defaultdict(int)
        for event in events:
            counts[event.event_type.value] += 1
        return dict(counts)

    def _count_events_by_component(self, events: List[SecurityEvent]) -> Dict[str, int]:
        """Count events by component."""
        counts = defaultdict(int)
        for event in events:
            counts[event.component] += 1
        return dict(counts)

    def _count_events_by_severity(self, events: List[SecurityEvent]) -> Dict[str, int]:
        """Count events by severity."""
        counts = defaultdict(int)
        for event in events:
            counts[event.severity.value] += 1
        return dict(counts)

    def _get_top_operations(self, events: List[SecurityEvent]) -> List[Dict[str, Any]]:
        """Get top operations by frequency."""
        operation_counts = defaultdict(int)
        for event in events:
            operation_counts[f"{event.component}.{event.operation}"] += 1

        return [
            {"operation": op, "count": count}
            for op, count in sorted(
                operation_counts.items(), key=lambda x: x[1], reverse=True
            )[:10]
        ]

    def _analyze_security_trends(self, events: List[SecurityEvent]) -> Dict[str, Any]:
        """Analyze security trends."""
        try:
            # Group events by day
            daily_events = defaultdict(list)
            for event in events:
                day = event.timestamp.date()
                daily_events[day].append(event)

            # Calculate daily metrics
            trends = []
            for day, day_events in sorted(daily_events.items()):
                trends.append(
                    {
                        "date": day.isoformat(),
                        "total_events": len(day_events),
                        "security_score": self._calculate_security_score(day_events),
                        "critical_events": len(
                            [
                                e
                                for e in day_events
                                if e.severity == SecuritySeverity.CRITICAL
                            ]
                        ),
                    }
                )

            return {"daily_trends": trends}

        except CustomError as e:
            self.logger.error(f"Error analyzing security trends: {str(e)}")
            return {"error": str(e)}

    def _get_alerts_summary(self) -> Dict[str, Any]:
        """Get alerts summary."""
        try:
            active_alerts = [a for a in self.alerts if not a.resolved]
            resolved_alerts = [a for a in self.alerts if a.resolved]

            return {
                "total_alerts": len(self.alerts),
                "active_alerts": len(active_alerts),
                "resolved_alerts": len(resolved_alerts),
                "alerts_by_severity": self._count_events_by_severity(active_alerts),
                "recent_alerts": [a.to_dict() for a in active_alerts[-5:]],
            }

        except CustomError as e:
            self.logger.error(f"Error getting alerts summary: {str(e)}")
            return {"error": str(e)}

    def _generate_recommendations(self, events: List[SecurityEvent]) -> List[str]:
        """Generate security recommendations."""
        recommendations = []

        try:
            # Check for high failure rates
            failure_events = [
                e for e in events if e.event_type == SecurityEventType.OPERATION_FAILURE
            ]
            if len(failure_events) > len(events) * 0.1:  # More than 10% failures
                recommendations.append(
                    "High operation failure rate detected. Review system health and configuration."
                )

            # Check for permission denials
            permission_denied = [
                e for e in events if e.event_type == SecurityEventType.PERMISSION_DENIED
            ]
            if len(permission_denied) > 0:
                recommendations.append(
                    "Permission denials detected. Review user roles and permissions."
                )

            # Check for SSL issues
            ssl_issues = [
                e
                for e in events
                if e.event_type
                in [SecurityEventType.CERTIFICATE_ISSUE, SecurityEventType.SSL_ERROR]
            ]
            if len(ssl_issues) > 0:
                recommendations.append(
                    "SSL/TLS issues detected. Review certificate configuration and validity."
                )

            # Check for suspicious activity
            suspicious = [
                e
                for e in events
                if e.event_type == SecurityEventType.SUSPICIOUS_ACTIVITY
            ]
            if len(suspicious) > 0:
                recommendations.append(
                    "Suspicious activity detected. Review security logs and consider additional monitoring."
                )

            return recommendations

        except CustomError as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            return ["Error generating recommendations"]

    async def _check_auth_failure_pattern(self, event: SecurityEvent) -> None:
        """Check authentication failure patterns."""
        # Implementation for auth failure pattern detection
        pass

    async def _check_permission_denial_pattern(self, event: SecurityEvent) -> None:
        """Check permission denial patterns."""
        # Implementation for permission denial pattern detection
        pass

    async def _check_ssl_issues(self, event: SecurityEvent) -> None:
        """Check SSL issues."""
        # Implementation for SSL issue detection
        pass



