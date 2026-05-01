"""
Integration test utilities for SSL/mTLS testing.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
import contextlib
import functools
import logging
import ssl
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable, AsyncGenerator

import aiohttp
from aiohttp import ClientSession, ClientTimeout, TCPConnector
from aiohttp.web import Application, Request, Response, RouteTableDef

from ai_admin.core.ssl_context_manager import SSLContextManager
from ai_admin.core.mtls_auth_manager import MTLSAuthManager
from ai_admin.security.ssl_error_handler import SSLErrorHandler


logger = logging.getLogger(__name__)


class IntegrationTestClient:
    """
    HTTP client with SSL/mTLS support for integration tests.

    Provides methods for making HTTP requests with various authentication modes
    and SSL configurations for testing purposes.
    """

    def __init__(
        self,
        base_url: str = "https://localhost:8443",
        ssl_context: Optional[ssl.SSLContext] = None,
        client_cert: Optional[tuple] = None,
        timeout: float = 30.0,
        verify_ssl: bool = True,
    ):
        """
        Initialize integration test client.

        Args:
            base_url: Base URL for the server
            ssl_context: SSL context for HTTPS connections
            client_cert: Client certificate tuple (cert_file, key_file)
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip("/")
        self.ssl_context = ssl_context
        self.client_cert = client_cert
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._session: Optional[ClientSession] = None

    async def __aenter__(self) -> "IntegrationTestClient":
        """Async context manager entry."""
        await self._create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _create_session(self):
        """Create aiohttp session with SSL configuration."""
        connector = TCPConnector(ssl=self.ssl_context, verify_ssl=self.verify_ssl)

        timeout = ClientTimeout(total=self.timeout)

        self._session = ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"User-Agent": "IntegrationTestClient/1.0"},
        )

    async def close(self):
        """Close the HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None

    async def get(
        self,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> aiohttp.ClientResponse:
        """
        Make GET request.

        Args:
            path: Request path
            headers: Additional headers
            params: Query parameters

        Returns:
            HTTP response
        """
        if not self._session:
            await self._create_session()

        url = f"{self.base_url}{path}"
        return await self._session.get(url, headers=headers, params=params)

    async def post(
        self,
        path: str,
        data: Optional[Union[str, Dict, bytes]] = None,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> aiohttp.ClientResponse:
        """
        Make POST request.

        Args:
            path: Request path
            data: Request data
            json_data: JSON data
            headers: Additional headers

        Returns:
            HTTP response
        """
        if not self._session:
            await self._create_session()

        url = f"{self.base_url}{path}"

        if json_data:
            return await self._session.post(url, json=json_data, headers=headers)
        else:
            return await self._session.post(url, data=data, headers=headers)

    async def put(
        self,
        path: str,
        data: Optional[Union[str, Dict, bytes]] = None,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> aiohttp.ClientResponse:
        """
        Make PUT request.

        Args:
            path: Request path
            data: Request data
            json_data: JSON data
            headers: Additional headers

        Returns:
            HTTP response
        """
        if not self._session:
            await self._create_session()

        url = f"{self.base_url}{path}"

        if json_data:
            return await self._session.put(url, json=json_data, headers=headers)
        else:
            return await self._session.put(url, data=data, headers=headers)

    async def delete(
        self, path: str, headers: Optional[Dict[str, str]] = None
    ) -> aiohttp.ClientResponse:
        """
        Make DELETE request.

        Args:
            path: Request path
            headers: Additional headers

        Returns:
            HTTP response
        """
        if not self._session:
            await self._create_session()

        url = f"{self.base_url}{path}"
        return await self._session.delete(url, headers=headers)


class IntegrationTestServer:
    """
    Test server for integration tests.

    Provides a mock server with SSL/mTLS support for testing client interactions.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8443,
        ssl_context: Optional[ssl.SSLContext] = None,
        middleware: Optional[List] = None,
    ):
        """
        Initialize integration test server.

        Args:
            host: Server host
            port: Server port
            ssl_context: SSL context for HTTPS
            middleware: List of middleware to use
        """
        self.host = host
        self.port = port
        self.ssl_context = ssl_context
        self.middleware = middleware or []
        self.app = Application(middlewares=self.middleware)
        self.routes = RouteTableDef()
        self._runner: Optional[aiohttp.web.AppRunner] = None
        self._site: Optional[aiohttp.web.TCPSite] = None

    def setup_routes(self):
        """Setup test routes."""

        @self.routes.get("/health")
        async def health_check(request: Request) -> Response:
            """Health check endpoint."""
            return Response(text="OK", status=200)

        @self.routes.get("/test")
        async def test_endpoint(request: Request) -> Response:
            """Test endpoint."""
            return Response(text="Test OK", status=200)

        @self.routes.post("/test")
        async def test_post(request: Request) -> Response:
            """Test POST endpoint."""
            data = await request.json()
            return Response(json=data, status=200)

        @self.routes.get("/protected")
        async def protected_endpoint(request: Request) -> Response:
            """Protected endpoint for testing authentication."""
            return Response(text="Protected OK", status=200)

        self.app.router.add_routes(self.routes)

    async def start(self):
        """Start the test server."""
        self.setup_routes()

        self._runner = aiohttp.web.AppRunner(self.app)
        await self._runner.setup()

        self._site = aiohttp.web.TCPSite(
            self._runner, self.host, self.port, ssl_context=self.ssl_context
        )

        await self._site.start()
        logger.info(f"Test server started on {self.host}:{self.port}")

    async def stop(self):
        """Stop the test server."""
        if self._site:
            await self._site.stop()
        if self._runner:
            await self._runner.cleanup()
        logger.info("Test server stopped")


class IntegrationTestRunner:
    """
    Runner for integration tests.

    Provides utilities for running integration tests with proper setup and teardown.
    """

    def __init__(self, test_config: Optional[Dict] = None):
        """
        Initialize integration test runner.

        Args:
            test_config: Test configuration
        """
        self.test_config = test_config or {}
        self.servers: List[IntegrationTestServer] = []
        self.clients: List[IntegrationTestClient] = []

    async def setup_test_environment(self):
        """Setup test environment."""
        # Create test certificates if needed
        await self._create_test_certificates()

        # Setup SSL context
        ssl_context = await self._create_ssl_context()

        # Create test server
        server = IntegrationTestServer(ssl_context=ssl_context)
        await server.start()
        self.servers.append(server)

    async def teardown_test_environment(self):
        """Teardown test environment."""
        # Stop all servers
        for server in self.servers:
            await server.stop()
        self.servers.clear()

        # Close all clients
        for client in self.clients:
            await client.close()
        self.clients.clear()

    async def _create_test_certificates(self):
        """Create test certificates for integration tests."""
        # This would create temporary certificates for testing
        # Implementation depends on your certificate creation logic
        pass

    async def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context for testing."""
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context

    def create_client(self, **kwargs) -> IntegrationTestClient:
        """
        Create a test client.

        Args:
            **kwargs: Client configuration

        Returns:
            Integration test client
        """
        client = IntegrationTestClient(**kwargs)
        self.clients.append(client)
        return client


@contextlib.asynccontextmanager
async def integration_test_context(
    test_config: Optional[Dict] = None,
) -> AsyncGenerator[IntegrationTestRunner, None]:
    """
    Context manager for integration tests.

    Args:
        test_config: Test configuration

    Yields:
        Integration test runner
    """
    runner = IntegrationTestRunner(test_config)

    try:
        await runner.setup_test_environment()
        yield runner
    finally:
        await runner.teardown_test_environment()


def measure_performance(func: Callable) -> Callable:
    """
    Decorator for measuring performance of test functions.

    Args:
        func: Function to measure

    Returns:
        Wrapped function with performance measurement
    """

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()

        duration = end_time - start_time
        logger.info(f"Performance: {func.__name__} took {duration:.3f} seconds")

        # Store performance data for analysis
        if hasattr(args[0], "performance_data"):
            args[0].performance_data[func.__name__] = duration

        return result

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        duration = end_time - start_time
        logger.info(f"Performance: {func.__name__} took {duration:.3f} seconds")

        # Store performance data for analysis
        if hasattr(args[0], "performance_data"):
            args[0].performance_data[func.__name__] = duration

        return result

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


async def assert_ssl_response(
    response: aiohttp.ClientResponse,
    expected_status: int = 200,
    expected_content_type: Optional[str] = None,
) -> None:
    """
    Assert SSL response properties.

    Args:
        response: HTTP response
        expected_status: Expected status code
        expected_content_type: Expected content type
    """
    assert (
        response.status == expected_status
    ), f"Expected status {expected_status}, got {response.status}"

    if expected_content_type:
        content_type = response.headers.get("Content-Type", "")
        assert (
            expected_content_type in content_type
        ), f"Expected content type {expected_content_type}, got {content_type}"


async def assert_mtls_response(
    response: aiohttp.ClientResponse,
    expected_status: int = 200,
    expected_headers: Optional[Dict[str, str]] = None,
) -> None:
    """
    Assert mTLS response properties.

    Args:
        response: HTTP response
        expected_status: Expected status code
        expected_headers: Expected headers
    """
    assert (
        response.status == expected_status
    ), f"Expected status {expected_status}, got {response.status}"

    if expected_headers:
        for header_name, expected_value in expected_headers.items():
            actual_value = response.headers.get(header_name)
            assert (
                actual_value == expected_value
            ), f"Expected header {header_name}={expected_value}, got {actual_value}"


class SSLTestEnvironment:
    """
    SSL test environment for integration tests.

    Provides utilities for creating and managing SSL test environments.
    """

    def __init__(self, temp_dir: Optional[Path] = None):
        """
        Initialize SSL test environment.

        Args:
            temp_dir: Temporary directory for test files
        """
        self.temp_dir = temp_dir or Path(tempfile.mkdtemp())
        self.cert_dir = self.temp_dir / "certs"
        self.cert_dir.mkdir(exist_ok=True)

        self.ssl_context_manager = SSLContextManager()
        self.mtls_auth_manager = MTLSAuthManager()
        self.ssl_error_handler = SSLErrorHandler()

    async def setup(self):
        """Setup SSL test environment."""
        # Create test certificates
        await self._create_test_certificates()

        # Setup SSL context
        await self._setup_ssl_context()

    async def teardown(self):
        """Teardown SSL test environment."""
        # Cleanup temporary files
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    async def _create_test_certificates(self):
        """Create test certificates."""
        # Implementation for creating test certificates
        # This would use your certificate creation logic
        pass

    async def _setup_ssl_context(self):
        """Setup SSL context."""
        # Implementation for setting up SSL context
        pass


@contextlib.asynccontextmanager
async def ssl_test_environment(
    temp_dir: Optional[Path] = None,
) -> AsyncGenerator[SSLTestEnvironment, None]:
    """
    Context manager for SSL test environment.

    Args:
        temp_dir: Temporary directory for test files

    Yields:
        SSL test environment
    """
    env = SSLTestEnvironment(temp_dir)

    try:
        await env.setup()
        yield env
    finally:
        await env.teardown()


class PerformanceMetrics:
    """
    Performance metrics collector for integration tests.
    """

    def __init__(self):
        """Initialize performance metrics."""
        self.metrics: Dict[str, List[float]] = {}

    def record(self, operation: str, duration: float):
        """
        Record performance metric.

        Args:
            operation: Operation name
            duration: Duration in seconds
        """
        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(duration)

    def get_average(self, operation: str) -> float:
        """
        Get average duration for operation.

        Args:
            operation: Operation name

        Returns:
            Average duration
        """
        if operation not in self.metrics or not self.metrics[operation]:
            return 0.0
        return sum(self.metrics[operation]) / len(self.metrics[operation])

    def get_summary(self) -> Dict[str, Dict[str, float]]:
        """
        Get performance summary.

        Returns:
            Performance summary
        """
        summary = {}
        for operation, durations in self.metrics.items():
            summary[operation] = {
                "average": sum(durations) / len(durations),
                "min": min(durations),
                "max": max(durations),
                "count": len(durations),
            }
        return summary
