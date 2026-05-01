from ai_admin.core.custom_exceptions import CustomError
"""
Dependency Injection system for AI Admin.

This module provides a simple dependency injection container
for managing services and dependencies in AI Admin commands.
"""

import logging
from typing import Any, Dict, Type, TypeVar, Optional, Callable
from functools import lru_cache

logger = logging.getLogger("ai_admin.di")

T = TypeVar('T')


class DependencyContainer:
    """Simple dependency injection container."""
    
    def __init__(self) -> None:
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._singletons: Dict[Type, Any] = {}
        self._initialized = False
    
    def register_singleton(self, service_type: Type[T], instance: T) -> None:
        """Register a singleton instance."""
        self._singletons[service_type] = instance
        logger.debug(f"Registered singleton: {service_type.__name__}")
    
    def register_factory(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """Register a factory function for creating instances."""
        self._factories[service_type] = factory
        logger.debug(f"Registered factory: {service_type.__name__}")
    
    def register_transient(self, service_type: Type[T], implementation_type: Type[T]) -> None:
        """Register a transient service (new instance each time)."""
        self._services[service_type] = implementation_type
        logger.debug(f"Registered transient: {service_type.__name__} -> {implementation_type.__name__}")
    
    def get(self, service_type: Type[T]) -> T:
        """Get a service instance."""
        # Check singletons first
        if service_type in self._singletons:
            return self._singletons[service_type]  # type: ignore
        
        # Check factories
        if service_type in self._factories:
            instance = self._factories[service_type]()
            logger.debug(f"Created instance from factory: {service_type.__name__}")
            return instance  # type: ignore
        
        # Check transient services
        if service_type in self._services:
            implementation_type = self._services[service_type]
            instance = implementation_type()
            logger.debug(f"Created transient instance: {service_type.__name__}")
            return instance  # type: ignore
        
        # Try to instantiate the type directly
        try:
            instance = service_type()
            logger.debug(f"Created direct instance: {service_type.__name__}")
            return instance  # type: ignore
        except CustomError as e:
            logger.error(f"Failed to create instance of {service_type.__name__}: {e}")
            raise ValueError(f"Service {service_type.__name__} not registered and cannot be instantiated")
    
    def is_registered(self, service_type: Type) -> bool:
        """Check if a service is registered."""
        return (service_type in self._singletons or 
                service_type in self._factories or 
                service_type in self._services)
    
    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        self._initialized = False
        logger.info("Dependency container cleared")


# Global container instance
_container: Optional[DependencyContainer] = None


def get_container() -> DependencyContainer:
    """Get the global dependency container."""
    global _container
    if _container is None:
        _container = DependencyContainer()
        _initialize_default_services()
    return _container


def _initialize_default_services() -> None:
    """Initialize default services in the container."""
    container = get_container()
    
    # Register configuration services
    try:
        from mcp_proxy_adapter.config import config, Config
        container.register_singleton(Config, config)
        logger.info("Registered config service")
    except ImportError:
        logger.warning("Could not register config service")
    
    # Register settings manager
    try:
        from ai_admin.settings_manager import get_settings_manager, AIAdminSettingsManager
        settings_manager = get_settings_manager()
        container.register_singleton(AIAdminSettingsManager, settings_manager)
        logger.info("Registered settings manager service")
    except ImportError:
        logger.warning("Could not register settings manager service")
    
    # Register security integration
    try:
        from ai_admin.security_integration import get_security_integration, AISecurityIntegration
        security = get_security_integration()
        if security:
            container.register_singleton(AISecurityIntegration, security)
            logger.info("Registered security integration service")
    except (ImportError, Exception) as e:
        logger.warning(f"Could not register security integration service: {e}")
    
    # Queue manager is automatically initialized by adapter when queue_manager.enabled: true in config
    # No manual registration needed
    
    logger.info("Default services initialized")


def register_service(service_type: Type[T], instance: T) -> None:
    """Register a service instance."""
    get_container().register_singleton(service_type, instance)


def register_factory(service_type: Type[T], factory: Callable[[], T]) -> None:
    """Register a factory function."""
    get_container().register_factory(service_type, factory)


def register_transient(service_type: Type[T], implementation_type: Type[T]) -> None:
    """Register a transient service."""
    get_container().register_transient(service_type, implementation_type)


@lru_cache(maxsize=128)
def get_service(service_type: Type[T]) -> T:
    """Get a service instance (cached)."""
    return get_container().get(service_type)


def inject(service_type: Type[T]) -> Callable:
    """Decorator for dependency injection."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            service = get_service(service_type)
            return func(service, *args, **kwargs)
        return wrapper
    return decorator


class ServiceLocator:
    """Service locator pattern for accessing services."""
    
    @staticmethod
    def get_config() -> Any:
        """Get configuration service."""
        try:
            from mcp_proxy_adapter.config import config
            return config
        except ImportError:
            return None
    
    @staticmethod
    def get_settings_manager() -> Any:
        """Get settings manager service."""
        try:
            from ai_admin.settings_manager import get_settings_manager
            return get_settings_manager()
        except ImportError:
            return None
    
    @staticmethod
    def get_security_integration() -> Any:
        """Get security integration service."""
        try:
            from ai_admin.security_integration import get_security_integration
            return get_security_integration()
        except (ImportError, Exception):
            return None
    
    @staticmethod
    def get_queue_manager() -> Any:
        """Get queue manager service."""
        try:
            from mcp_proxy_adapter.integrations.queuemgr_integration import get_global_queue_manager
            import asyncio
            # Note: This is async, but ServiceLocator is sync
            # For async code, use get_global_queue_manager() directly
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, return None and let caller use async version
                return None
            return loop.run_until_complete(get_global_queue_manager())
        except (ImportError, RuntimeError):
            return None


# Convenience functions that use the DI container
def get_config() -> Any:
    """Get configuration service."""
    try:
        from mcp_proxy_adapter.config import Config
        return get_service(Config)
    except CustomError:
        return None


def get_settings_manager() -> Any:
    """Get settings manager service."""
    try:
        from ai_admin.settings_manager import AIAdminSettingsManager
        return get_service(AIAdminSettingsManager)
    except CustomError:
        return None


def get_security_integration() -> Any:
    """Get security integration service."""
    try:
        from ai_admin.security_integration import AISecurityIntegration
        return get_service(AISecurityIntegration)
    except CustomError:
        return None


def get_queue_manager() -> Any:
    """Get queue manager service."""
    try:
        from mcp_proxy_adapter.integrations.queuemgr_integration import get_global_queue_manager
        import asyncio
        # Note: This is async, but ServiceLocator is sync
        # For async code, use get_global_queue_manager() directly
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, return None and let caller use async version
                return None
            return loop.run_until_complete(get_global_queue_manager())
        except RuntimeError:
            # No event loop, create new one
            return asyncio.run(get_global_queue_manager())
    except (ImportError, RuntimeError):
        return None
