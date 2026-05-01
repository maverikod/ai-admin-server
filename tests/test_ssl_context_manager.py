"""Tests for SSL Context Manager.

This module provides comprehensive tests for the SSLContextManager class,
including tests for all SSL modes with real certificates.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import ssl
import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any

from ai_admin.core.ssl_context_manager import (
    SSLContextManager,
    SSLContextType,
    SSLContextInfo,
)
from ai_admin.config.ssl_config import SSLConfig


class TestSSLContextManager:
    """Test cases for SSLContextManager class."""

    @pytest.fixture
    def test_cert_dir(self) -> str:
        """Get path to test certificates directory."""
        return str(Path(__file__).parent.parent / "test_environment" / "ssl_test_certs")

    @pytest.fixture
    def ssl_config_data(self, test_cert_dir: str) -> Dict[str, Any]:
        """Create SSL configuration data for testing."""
        return {
            "ssl": {
                "enabled": True,
                "cert_file": os.path.join(test_cert_dir, "server-cert.pem"),
                "key_file": os.path.join(test_cert_dir, "server-key.pem"),
                "ca_cert_file": os.path.join(test_cert_dir, "ca-cert.pem"),
                "client_cert_file": os.path.join(test_cert_dir, "client-cert.pem"),
                "client_key_file": os.path.join(test_cert_dir, "client-key.pem"),
                "min_tls_version": "TLSv1.2",
                "verify_mode": "CERT_NONE",
                "check_hostname": False,
            },
            "certificates": {
                "cert_storage_path": test_cert_dir,
                "key_storage_path": test_cert_dir,
                "key_size": 2048,
                "hash_algorithm": "sha256",
            },
        }

    @pytest.fixture
    def ssl_config(self, ssl_config_data: Dict[str, Any]) -> SSLConfig:
        """Create SSL configuration instance for testing."""
        return SSLConfig(ssl_config_data, auto_validate=False)

    @pytest.fixture
    def ssl_context_manager(self, ssl_config: SSLConfig) -> SSLContextManager:
        """Create SSL context manager instance for testing."""
        return SSLContextManager(ssl_config)

    @pytest.mark.asyncio
    async def test_ssl_context_manager_initialization(
        self, ssl_context_manager: SSLContextManager
    ):
        """Test SSL context manager initialization."""
        assert ssl_context_manager is not None
        assert ssl_context_manager.ssl_config is not None
        assert len(ssl_context_manager._contexts) == 0

    @pytest.mark.asyncio
    async def test_create_https_context(self, ssl_context_manager: SSLContextManager):
        """Test creation of HTTPS SSL context."""
        context = await ssl_context_manager.create_ssl_context(SSLContextType.HTTPS)

        assert context is not None
        assert isinstance(context, ssl.SSLContext)
        assert SSLContextType.HTTPS in ssl_context_manager._contexts

        context_info = ssl_context_manager._contexts[SSLContextType.HTTPS]
        assert context_info.context_type == SSLContextType.HTTPS
        assert context_info.ssl_context == context
        assert context_info.is_valid is True

    @pytest.mark.asyncio
    async def test_create_mtls_context(self, ssl_context_manager: SSLContextManager):
        """Test creation of mTLS SSL context."""
        context = await ssl_context_manager.create_ssl_context(SSLContextType.MTLS)

        assert context is not None
        assert isinstance(context, ssl.SSLContext)
        assert SSLContextType.MTLS in ssl_context_manager._contexts

        context_info = ssl_context_manager._contexts[SSLContextType.MTLS]
        assert context_info.context_type == SSLContextType.MTLS
        assert context_info.ssl_context == context
        assert context_info.is_valid is True

    @pytest.mark.asyncio
    async def test_create_token_auth_context(
        self, ssl_context_manager: SSLContextManager
    ):
        """Test creation of token authentication SSL context."""
        context = await ssl_context_manager.create_ssl_context(
            SSLContextType.TOKEN_AUTH
        )

        assert context is not None
        assert isinstance(context, ssl.SSLContext)
        assert SSLContextType.TOKEN_AUTH in ssl_context_manager._contexts

        context_info = ssl_context_manager._contexts[SSLContextType.TOKEN_AUTH]
        assert context_info.context_type == SSLContextType.TOKEN_AUTH
        assert context_info.ssl_context == context
        assert context_info.is_valid is True

    @pytest.mark.asyncio
    async def test_create_mixed_context(self, ssl_context_manager: SSLContextManager):
        """Test creation of mixed authentication SSL context."""
        context = await ssl_context_manager.create_ssl_context(SSLContextType.MIXED)

        assert context is not None
        assert isinstance(context, ssl.SSLContext)
        assert SSLContextType.MIXED in ssl_context_manager._contexts

        context_info = ssl_context_manager._contexts[SSLContextType.MIXED]
        assert context_info.context_type == SSLContextType.MIXED
        assert context_info.ssl_context == context
        assert context_info.is_valid is True

    @pytest.mark.asyncio
    async def test_get_ssl_context(self, ssl_context_manager: SSLContextManager):
        """Test getting SSL context."""
        # Create context first
        created_context = await ssl_context_manager.create_ssl_context(
            SSLContextType.HTTPS
        )

        # Get context
        retrieved_context = await ssl_context_manager.get_ssl_context(
            SSLContextType.HTTPS
        )

        assert retrieved_context is not None
        assert retrieved_context == created_context

    @pytest.mark.asyncio
    async def test_get_nonexistent_ssl_context(
        self, ssl_context_manager: SSLContextManager
    ):
        """Test getting non-existent SSL context."""
        context = await ssl_context_manager.get_ssl_context(SSLContextType.HTTPS)
        assert context is None

    @pytest.mark.asyncio
    async def test_get_context_summary(self, ssl_context_manager: SSLContextManager):
        """Test getting context summary."""
        # Create some contexts
        await ssl_context_manager.create_ssl_context(SSLContextType.HTTPS)
        await ssl_context_manager.create_ssl_context(SSLContextType.MTLS)

        summary = await ssl_context_manager.get_context_summary()

        assert summary["total_contexts"] == 2
        assert "https" in summary["contexts"]
        assert "mtls" in summary["contexts"]
        assert summary["contexts"]["https"]["is_valid"] is True
        assert summary["contexts"]["mtls"]["is_valid"] is True

    @pytest.mark.asyncio
    async def test_clear_context(self, ssl_context_manager: SSLContextManager):
        """Test clearing SSL context."""
        # Create context
        await ssl_context_manager.create_ssl_context(SSLContextType.HTTPS)
        assert SSLContextType.HTTPS in ssl_context_manager._contexts

        # Clear context
        await ssl_context_manager.clear_context(SSLContextType.HTTPS)
        assert SSLContextType.HTTPS not in ssl_context_manager._contexts

    @pytest.mark.asyncio
    async def test_clear_all_contexts(self, ssl_context_manager: SSLContextManager):
        """Test clearing all SSL contexts."""
        # Create multiple contexts
        await ssl_context_manager.create_ssl_context(SSLContextType.HTTPS)
        await ssl_context_manager.create_ssl_context(SSLContextType.MTLS)
        await ssl_context_manager.create_ssl_context(SSLContextType.TOKEN_AUTH)

        assert len(ssl_context_manager._contexts) == 3

        # Clear all contexts
        await ssl_context_manager.clear_all_contexts()
        assert len(ssl_context_manager._contexts) == 0

    @pytest.mark.asyncio
    async def test_recreate_context(self, ssl_context_manager: SSLContextManager):
        """Test recreating SSL context."""
        # Create context
        original_context = await ssl_context_manager.create_ssl_context(
            SSLContextType.HTTPS
        )

        # Recreate context
        new_context = await ssl_context_manager.recreate_context(SSLContextType.HTTPS)

        assert new_context is not None
        assert new_context != original_context
        assert isinstance(new_context, ssl.SSLContext)

    @pytest.mark.asyncio
    async def test_validate_all_contexts(self, ssl_context_manager: SSLContextManager):
        """Test validating all contexts."""
        # Create contexts
        await ssl_context_manager.create_ssl_context(SSLContextType.HTTPS)
        await ssl_context_manager.create_ssl_context(SSLContextType.MTLS)

        # Validate all contexts
        validation_results = await ssl_context_manager.validate_all_contexts()

        assert validation_results["total_contexts"] == 2
        assert validation_results["valid_contexts"] == 2
        assert validation_results["invalid_contexts"] == 0
        assert "https" in validation_results["contexts"]
        assert "mtls" in validation_results["contexts"]

    @pytest.mark.asyncio
    async def test_get_available_context_types(
        self, ssl_context_manager: SSLContextManager
    ):
        """Test getting available context types."""
        # Initially no contexts
        available_types = ssl_context_manager.get_available_context_types()
        assert len(available_types) == 0

        # Create contexts
        await ssl_context_manager.create_ssl_context(SSLContextType.HTTPS)
        await ssl_context_manager.create_ssl_context(SSLContextType.MTLS)

        # Check available types
        available_types = ssl_context_manager.get_available_context_types()
        assert len(available_types) == 2
        assert SSLContextType.HTTPS in available_types
        assert SSLContextType.MTLS in available_types

    @pytest.mark.asyncio
    async def test_is_context_available(self, ssl_context_manager: SSLContextManager):
        """Test checking if context is available."""
        # Initially not available
        assert ssl_context_manager.is_context_available(SSLContextType.HTTPS) is False

        # Create context
        await ssl_context_manager.create_ssl_context(SSLContextType.HTTPS)

        # Should be available
        assert ssl_context_manager.is_context_available(SSLContextType.HTTPS) is True

    @pytest.mark.asyncio
    async def test_get_server_ssl_config(self, ssl_context_manager: SSLContextManager):
        """Test getting server SSL configuration."""
        # Create context
        await ssl_context_manager.create_ssl_context(SSLContextType.HTTPS)

        # Get server config
        config = await ssl_context_manager.get_server_ssl_config(SSLContextType.HTTPS)

        assert "ssl_context" in config
        assert "cert_file" in config
        assert "key_file" in config
        assert "ca_cert" in config
        assert "verify_mode" in config
        assert "check_hostname" in config
        assert "min_tls_version" in config
        assert "max_tls_version" in config

    @pytest.mark.asyncio
    async def test_force_recreate_context(self, ssl_context_manager: SSLContextManager):
        """Test forcing recreation of existing context."""
        # Create context
        original_context = await ssl_context_manager.create_ssl_context(
            SSLContextType.HTTPS
        )

        # Force recreate
        new_context = await ssl_context_manager.create_ssl_context(
            SSLContextType.HTTPS, force_recreate=True
        )

        assert new_context is not None
        assert new_context != original_context
        assert isinstance(new_context, ssl.SSLContext)

    @pytest.mark.asyncio
    async def test_context_with_invalid_certificates(self, test_cert_dir: str):
        """Test SSL context creation with invalid certificate paths."""
        # Create config with invalid certificate paths
        invalid_config_data = {
            "ssl": {
                "enabled": True,
                "cert_file": os.path.join(test_cert_dir, "nonexistent-cert.pem"),
                "key_file": os.path.join(test_cert_dir, "nonexistent-key.pem"),
                "ca_cert_file": os.path.join(test_cert_dir, "nonexistent-ca.pem"),
                "verify_mode": "CERT_NONE",
                "check_hostname": False,
            },
        }

        ssl_config = SSLConfig(invalid_config_data, auto_validate=False)
        ssl_context_manager = SSLContextManager(ssl_config)

        # Should raise FileNotFoundError when trying to load certificates
        with pytest.raises(FileNotFoundError):
            await ssl_context_manager.create_ssl_context(SSLContextType.HTTPS)

    @pytest.mark.asyncio
    async def test_context_validation_errors(
        self, ssl_context_manager: SSLContextManager
    ):
        """Test context validation with errors."""
        # Create context
        context = await ssl_context_manager.create_ssl_context(SSLContextType.HTTPS)

        # Validate context
        is_valid, errors = await ssl_context_manager._validate_ssl_context(
            context, SSLContextType.HTTPS
        )

        assert is_valid is True
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_security_params_configuration(
        self, ssl_context_manager: SSLContextManager
    ):
        """Test security parameters configuration."""
        # Create context
        context = await ssl_context_manager.create_ssl_context(SSLContextType.HTTPS)

        # Check security parameters
        assert context.minimum_version == ssl.TLSVersion.TLSv1_2
        assert context.check_hostname is False  # For HTTPS context (server mode)
        assert context.verify_mode == ssl.CERT_NONE  # For HTTPS context

    @pytest.mark.asyncio
    async def test_mtls_security_params(self, ssl_context_manager: SSLContextManager):
        """Test mTLS security parameters."""
        # Create mTLS context
        context = await ssl_context_manager.create_ssl_context(SSLContextType.MTLS)

        # Check mTLS specific parameters
        assert context.minimum_version == ssl.TLSVersion.TLSv1_2
        assert context.verify_mode == ssl.CERT_REQUIRED
        assert context.check_hostname is False  # Based on test config

    @pytest.mark.asyncio
    async def test_mixed_context_security_params(
        self, ssl_context_manager: SSLContextManager
    ):
        """Test mixed context security parameters."""
        # Create mixed context
        context = await ssl_context_manager.create_ssl_context(SSLContextType.MIXED)

        # Check mixed context parameters
        assert context.minimum_version == ssl.TLSVersion.TLSv1_2
        assert context.verify_mode == ssl.CERT_OPTIONAL
        assert context.check_hostname is False  # Based on test config

    @pytest.mark.asyncio
    async def test_context_info_structure(self, ssl_context_manager: SSLContextManager):
        """Test SSL context info structure."""
        # Create context
        await ssl_context_manager.create_ssl_context(SSLContextType.HTTPS)

        context_info = ssl_context_manager._contexts[SSLContextType.HTTPS]

        assert isinstance(context_info, SSLContextInfo)
        assert context_info.context_type == SSLContextType.HTTPS
        assert isinstance(context_info.ssl_context, ssl.SSLContext)
        assert isinstance(context_info.certificate_paths, object)
        assert isinstance(context_info.security_params, object)
        assert isinstance(context_info.created_at, str)
        assert isinstance(context_info.is_valid, bool)
        assert isinstance(context_info.validation_errors, list)

    @pytest.mark.asyncio
    async def test_concurrent_context_creation(
        self, ssl_context_manager: SSLContextManager
    ):
        """Test concurrent SSL context creation."""
        # Create multiple contexts concurrently
        tasks = [
            ssl_context_manager.create_ssl_context(SSLContextType.HTTPS),
            ssl_context_manager.create_ssl_context(SSLContextType.MTLS),
            ssl_context_manager.create_ssl_context(SSLContextType.TOKEN_AUTH),
            ssl_context_manager.create_ssl_context(SSLContextType.MIXED),
        ]

        results = await asyncio.gather(*tasks)

        # All contexts should be created successfully
        for result in results:
            assert result is not None
            assert isinstance(result, ssl.SSLContext)

        # All contexts should be available
        assert len(ssl_context_manager._contexts) == 4
        assert ssl_context_manager.is_context_available(SSLContextType.HTTPS)
        assert ssl_context_manager.is_context_available(SSLContextType.MTLS)
        assert ssl_context_manager.is_context_available(SSLContextType.TOKEN_AUTH)
        assert ssl_context_manager.is_context_available(SSLContextType.MIXED)


class TestSSLContextManagerIntegration:
    """Integration tests for SSLContextManager with real server scenarios."""

    @pytest.fixture
    def test_cert_dir(self) -> str:
        """Get path to test certificates directory."""
        return str(Path(__file__).parent.parent / "test_environment" / "ssl_test_certs")

    @pytest.fixture
    def production_like_config(self, test_cert_dir: str) -> Dict[str, Any]:
        """Create production-like SSL configuration."""
        return {
            "ssl": {
                "enabled": True,
                "cert_file": os.path.join(test_cert_dir, "server-cert.pem"),
                "key_file": os.path.join(test_cert_dir, "server-key.pem"),
                "ca_cert_file": os.path.join(test_cert_dir, "ca-cert.pem"),
                "min_tls_version": "TLSv1.2",
                "max_tls_version": "TLSv1.3",
                "verify_mode": "CERT_NONE",
                "check_hostname": False,
                "check_expiry": True,
                "expiry_warning_days": 30,
            },
            "certificates": {
                "cert_storage_path": test_cert_dir,
                "key_storage_path": test_cert_dir,
                "key_size": 2048,
                "hash_algorithm": "sha256",
                "default_validity_days": 365,
                "auto_renewal": False,
                "renewal_threshold_days": 30,
            },
        }

    @pytest.mark.asyncio
    async def test_production_https_setup(self, production_like_config: Dict[str, Any]):
        """Test production-like HTTPS setup."""
        ssl_config = SSLConfig(production_like_config, auto_validate=False)
        ssl_context_manager = SSLContextManager(ssl_config)

        # Create HTTPS context
        context = await ssl_context_manager.create_ssl_context(SSLContextType.HTTPS)

        assert context is not None
        assert context.minimum_version == ssl.TLSVersion.TLSv1_2
        assert context.maximum_version == ssl.TLSVersion.TLSv1_3

        # Get server config
        server_config = await ssl_context_manager.get_server_ssl_config(
            SSLContextType.HTTPS
        )
        assert server_config["ssl_context"] == context
        assert server_config["min_tls_version"] == "TLSv1.2"
        assert server_config["max_tls_version"] == "TLSv1.3"

    @pytest.mark.asyncio
    async def test_production_mtls_setup(self, production_like_config: Dict[str, Any]):
        """Test production-like mTLS setup."""
        ssl_config = SSLConfig(production_like_config, auto_validate=False)
        ssl_context_manager = SSLContextManager(ssl_config)

        # Create mTLS context
        context = await ssl_context_manager.create_ssl_context(SSLContextType.MTLS)

        assert context is not None
        assert context.verify_mode == ssl.CERT_REQUIRED
        assert context.check_hostname is False  # Based on production config

        # Get server config
        server_config = await ssl_context_manager.get_server_ssl_config(
            SSLContextType.MTLS
        )
        assert server_config["ssl_context"] == context
        assert server_config["verify_mode"] == "CERT_NONE"  # Based on production config
        assert server_config["check_hostname"] is False

    @pytest.mark.asyncio
    async def test_certificate_chain_validation(self, test_cert_dir: str):
        """Test certificate chain validation."""
        config_data = {
            "ssl": {
                "enabled": True,
                "cert_file": os.path.join(test_cert_dir, "server-cert.pem"),
                "key_file": os.path.join(test_cert_dir, "server-key.pem"),
                "ca_cert_file": os.path.join(test_cert_dir, "ca-cert.pem"),
                "verify_mode": "CERT_REQUIRED",
                "check_hostname": True,
            },
        }

        ssl_config = SSLConfig(config_data, auto_validate=False)
        ssl_context_manager = SSLContextManager(ssl_config)

        # Create mTLS context (requires CA cert)
        context = await ssl_context_manager.create_ssl_context(SSLContextType.MTLS)

        assert context is not None
        assert context.verify_mode == ssl.CERT_REQUIRED

        # Verify that CA certificate is loaded
        context_info = ssl_context_manager._contexts[SSLContextType.MTLS]
        assert context_info.certificate_paths.ca_cert is not None
        assert os.path.exists(context_info.certificate_paths.ca_cert)

    @pytest.mark.asyncio
    async def test_context_lifecycle_management(
        self, production_like_config: Dict[str, Any]
    ):
        """Test complete context lifecycle management."""
        ssl_config = SSLConfig(production_like_config, auto_validate=False)
        ssl_context_manager = SSLContextManager(ssl_config)

        # 1. Create contexts
        https_context = await ssl_context_manager.create_ssl_context(
            SSLContextType.HTTPS
        )
        mtls_context = await ssl_context_manager.create_ssl_context(SSLContextType.MTLS)

        assert https_context is not None
        assert mtls_context is not None
        assert len(ssl_context_manager._contexts) == 2

        # 2. Validate contexts
        validation_results = await ssl_context_manager.validate_all_contexts()
        assert validation_results["valid_contexts"] == 2
        assert validation_results["invalid_contexts"] == 0

        # 3. Get context summary
        summary = await ssl_context_manager.get_context_summary()
        assert summary["total_contexts"] == 2

        # 4. Recreate one context
        new_https_context = await ssl_context_manager.recreate_context(
            SSLContextType.HTTPS
        )
        assert new_https_context != https_context
        assert len(ssl_context_manager._contexts) == 2

        # 5. Clear specific context
        await ssl_context_manager.clear_context(SSLContextType.MTLS)
        assert SSLContextType.MTLS not in ssl_context_manager._contexts
        assert SSLContextType.HTTPS in ssl_context_manager._contexts

        # 6. Clear all contexts
        await ssl_context_manager.clear_all_contexts()
        assert len(ssl_context_manager._contexts) == 0
