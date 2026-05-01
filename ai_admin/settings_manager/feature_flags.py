"""Feature flag helpers for AI Admin settings manager."""

from mcp_proxy_adapter.core.settings import get_custom_setting_value


def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled."""
    return bool(get_custom_setting_value(f"ai_admin.features.{feature_name}", False))
