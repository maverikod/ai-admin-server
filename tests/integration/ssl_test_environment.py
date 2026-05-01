"""SSL test environment management.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from .environment_exceptions import (
    CertificateGenerationError,
    ConfigGenerationError,
    EnvironmentSetupError,
    EnvironmentValidationError,
    TestEnvironmentError,
)
from .test_certificates import TestCertificateGenerator
from .test_configs import TestConfigGenerator


class SSLTestEnvironment:
    """SSL test environment manager.

    This class provides comprehensive management of SSL/mTLS test environments,
    including certificate generation, configuration creation, and environment
    validation.
    """

    def __init__(
        self, base_dir: Optional[Path] = None, cleanup_on_exit: bool = True
    ) -> None:
        """Initialize SSL test environment.

        Args:
            base_dir: Base directory for test environment (uses temp dir if None)
            cleanup_on_exit: Whether to cleanup environment on exit

        Raises:
            EnvironmentSetupError: If environment setup fails
        """
        self.cleanup_on_exit = cleanup_on_exit
        self.base_dir = base_dir or Path(tempfile.mkdtemp(prefix="ssl_test_env_"))
        self.certificates_dir = self.base_dir / "certificates"
        self.configs_dir = self.base_dir / "configs"
        self.logs_dir = self.base_dir / "logs"

        # Initialize generators
        self.cert_generator: Optional[TestCertificateGenerator] = None
        self.config_generator: Optional[TestConfigGenerator] = None

        # Store generated paths
        self.certificates: Dict[str, Dict[str, Path]] = {}
        self.configs: Dict[str, Path] = {}

        # Environment state
        self._is_setup = False
        self._is_validated = False

    def setup_environment(self) -> None:
        """Setup the test environment.

        Creates necessary directories and initializes generators.

        Raises:
            EnvironmentSetupError: If environment setup fails
        """
        try:
            # Create directories
            self.certificates_dir.mkdir(parents=True, exist_ok=True)
            self.configs_dir.mkdir(parents=True, exist_ok=True)
            self.logs_dir.mkdir(parents=True, exist_ok=True)

            # Initialize generators
            self.cert_generator = TestCertificateGenerator(self.certificates_dir)
            self.config_generator = TestConfigGenerator(self.configs_dir)

            self._is_setup = True

        except Exception as e:
            raise EnvironmentSetupError(
                "Failed to setup test environment",
                component="directories",
                details=str(e),
                error_code="SETUP_ERROR",
            )

    def cleanup_environment(self) -> None:
        """Cleanup the test environment.

        Removes all generated files and directories.
        """
        try:
            if self.base_dir.exists() and self.cleanup_on_exit:
                shutil.rmtree(self.base_dir)

            # Reset state
            self._is_setup = False
            self._is_validated = False
            self.certificates.clear()
            self.configs.clear()

        except Exception as e:
            # Log error but don't raise exception during cleanup
            print(f"Warning: Failed to cleanup test environment: {e}")

    def generate_test_certificates(
        self,
        ca_name: str = "Test CA",
        server_name: str = "localhost",
        client_names: Optional[List[str]] = None,
        validity_days: int = 365,
        key_size: int = 2048,
    ) -> Dict[str, Dict[str, Path]]:
        """Generate test certificates.

        Args:
            ca_name: Name for the CA certificate
            server_name: Name for the server certificate
            client_names: List of client certificate names
            validity_days: Certificate validity period in days
            key_size: RSA key size in bits

        Returns:
            Dictionary with certificate paths organized by type

        Raises:
            EnvironmentSetupError: If environment is not setup
            CertificateGenerationError: If certificate generation fails
        """
        if not self._is_setup:
            raise EnvironmentSetupError(
                "Environment not setup. Call setup_environment() first.",
                component="certificates",
                error_code="NOT_SETUP",
            )

        if not self.cert_generator:
            raise EnvironmentSetupError(
                "Certificate generator not initialized",
                component="certificates",
                error_code="GENERATOR_NOT_INIT",
            )

        try:
            self.certificates = self.cert_generator.generate_certificate_chain(
                ca_name=ca_name,
                server_name=server_name,
                client_names=client_names or ["test-client"],
                validity_days=validity_days,
                key_size=key_size,
            )

            return self.certificates

        except CertificateGenerationError:
            raise
        except Exception as e:
            raise CertificateGenerationError(
                "Unexpected error generating test certificates",
                certificate_type="chain",
                details=str(e),
                error_code="UNEXPECTED_CERT_ERROR",
            )

    def generate_test_configs(
        self,
        server_host: str = "127.0.0.1",
        server_port: int = 20000,
        ssl_enabled: bool = True,
        security_enabled: bool = True,
        registration_enabled: bool = False,
    ) -> Dict[str, Path]:
        """Generate test configurations.

        Args:
            server_host: Server host address
            server_port: Server port
            ssl_enabled: Whether SSL is enabled
            security_enabled: Whether security is enabled
            registration_enabled: Whether registration is enabled

        Returns:
            Dictionary mapping config type to file path

        Raises:
            EnvironmentSetupError: If environment is not setup
            ConfigGenerationError: If configuration generation fails
        """
        if not self._is_setup:
            raise EnvironmentSetupError(
                "Environment not setup. Call setup_environment() first.",
                component="configs",
                error_code="NOT_SETUP",
            )

        if not self.config_generator:
            raise EnvironmentSetupError(
                "Configuration generator not initialized",
                component="configs",
                error_code="GENERATOR_NOT_INIT",
            )

        try:
            self.configs = self.config_generator.generate_all_configs(
                server_host=server_host,
                server_port=server_port,
                ssl_enabled=ssl_enabled,
                security_enabled=security_enabled,
                registration_enabled=registration_enabled,
            )

            return self.configs

        except ConfigGenerationError:
            raise
        except Exception as e:
            raise ConfigGenerationError(
                "Unexpected error generating test configurations",
                config_type="all",
                details=str(e),
                error_code="UNEXPECTED_CONFIG_ERROR",
            )

    def create_test_data(self) -> Dict[str, Path]:
        """Create additional test data files.

        Returns:
            Dictionary mapping data type to file path

        Raises:
            EnvironmentSetupError: If environment is not setup
        """
        if not self._is_setup:
            raise EnvironmentSetupError(
                "Environment not setup. Call setup_environment() first.",
                component="test_data",
                error_code="NOT_SETUP",
            )

        try:
            test_data = {}

            # Create sample log file
            log_file = self.logs_dir / "test.log"
            log_file.write_text(
                """2025-09-13 13:30:00,000 - INFO - Test log entry 1
2025-09-13 13:30:01,000 - INFO - Test log entry 2
2025-09-13 13:30:02,000 - ERROR - Test error entry
2025-09-13 13:30:03,000 - DEBUG - Test debug entry
"""
            )
            test_data["log_file"] = log_file

            # Create sample data file
            data_file = self.base_dir / "test_data.json"
            data_file.write_text('{"test": "data", "number": 42, "list": [1, 2, 3]}')
            test_data["data_file"] = data_file

            # Create sample text file
            text_file = self.base_dir / "test_data.txt"
            text_file.write_text(
                "This is a test data file.\nIt contains multiple lines.\n"
                "For testing purposes."
            )
            test_data["text_file"] = text_file

            return test_data

        except Exception as e:
            raise EnvironmentSetupError(
                "Failed to create test data",
                component="test_data",
                details=str(e),
                error_code="TEST_DATA_ERROR",
            )

    def validate_environment(self) -> Dict[str, bool]:
        """Validate the test environment.

        Checks that all required files exist and are accessible.

        Returns:
            Dictionary with validation results for each component

        Raises:
            EnvironmentValidationError: If validation fails
        """
        if not self._is_setup:
            raise EnvironmentValidationError(
                "Environment not setup. Call setup_environment() first.",
                validation_type="setup",
                error_code="NOT_SETUP",
            )

        try:
            validation_results = {}

            # Validate directories
            validation_results["directories"] = all(
                [
                    self.base_dir.exists(),
                    self.certificates_dir.exists(),
                    self.configs_dir.exists(),
                    self.logs_dir.exists(),
                ]
            )

            # Validate certificates
            cert_validation = True
            if self.certificates:
                for cert_type, cert_files in self.certificates.items():
                    if isinstance(cert_files, dict):
                        for file_type, file_path in cert_files.items():
                            if isinstance(file_path, Path) and not file_path.exists():
                                cert_validation = False
                                break
                    elif isinstance(cert_files, Path) and not cert_files.exists():
                        cert_validation = False
                        break
            validation_results["certificates"] = cert_validation

            # Validate configurations
            config_validation = True
            if self.configs:
                for config_type, config_path in self.configs.items():
                    if not config_path.exists():
                        config_validation = False
                        break
            validation_results["configurations"] = config_validation

            # Validate generators
            validation_results["generators"] = (
                self.cert_generator is not None and self.config_generator is not None
            )

            # Overall validation
            validation_results["overall"] = all(validation_results.values())

            self._is_validated = validation_results["overall"]

            return validation_results

        except Exception as e:
            raise EnvironmentValidationError(
                "Failed to validate environment",
                validation_type="general",
                details=str(e),
                error_code="VALIDATION_ERROR",
            )

    def get_certificate_paths(self) -> Dict[str, Dict[str, Path]]:
        """Get generated certificate paths.

        Returns:
            Dictionary with certificate paths organized by type

        Raises:
            TestEnvironmentError: If certificates not generated
        """
        if not self.certificates:
            raise TestEnvironmentError(
                "No certificates generated. Call generate_test_certificates() first.",
                error_code="NO_CERTIFICATES",
            )

        return self.certificates.copy()

    def get_config_paths(self) -> Dict[str, Path]:
        """Get generated configuration paths.

        Returns:
            Dictionary mapping config type to file path

        Raises:
            TestEnvironmentError: If configurations not generated
        """
        if not self.configs:
            raise TestEnvironmentError(
                "No configurations generated. Call generate_test_configs() first.",
                error_code="NO_CONFIGS",
            )

        return self.configs.copy()

    def get_base_directory(self) -> Path:
        """Get the base directory of the test environment.

        Returns:
            Path to the base directory
        """
        return self.base_dir

    def is_setup(self) -> bool:
        """Check if environment is setup.

        Returns:
            True if environment is setup, False otherwise
        """
        return self._is_setup

    def is_validated(self) -> bool:
        """Check if environment is validated.

        Returns:
            True if environment is validated, False otherwise
        """
        return self._is_validated

    def __enter__(self) -> "SSLTestEnvironment":
        """Context manager entry.

        Returns:
            Self for use in with statement
        """
        self.setup_environment()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Context manager exit.

        Cleans up the environment if cleanup_on_exit is True.
        """
        self.cleanup_environment()

    def __repr__(self) -> str:
        """String representation of the environment.

        Returns:
            String representation with environment status
        """
        status = "setup" if self._is_setup else "not setup"
        validated = "validated" if self._is_validated else "not validated"
        return (
            f"SSLTestEnvironment(base_dir={self.base_dir}, status={status}, "
            f"{validated})"
        )
