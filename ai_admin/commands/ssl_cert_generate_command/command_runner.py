"""Module command_runner."""

from ai_admin.core.custom_exceptions import CertificateError, SSLError
import os
from pathlib import Path
import subprocess
import tempfile
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.utils.certificate_utils import CertificateUtils
from ai_admin.utils.certificate_exceptions import (
    CertificateCreationError,
    CertificateError,
)
from ai_admin.security.ssl_security_adapter import (
    SSLSecurityAdapter,
    SSLOperation,
    SSLCertificateType,
)
from mcp_security_framework import CertificateManager
from mcp_security_framework.schemas import CertificateConfig

class CommandRunner:
    """Command to generate SSL certificates and keys."""

    def _get_default_operation(self):
        return self.commandRunner._get_default_operation()

    async def execute(
        self,
        cert_type,
        common_name,
        country,
        state,
        locality,
        organization,
        organizational_unit,
        email,
        key_size,
        days_valid,
        output_dir,
        extensions,
        key_usage,
        extended_key_usage,
        subject_alt_names,
        basic_constraints,
        roles,
        ca_cert_path,
        ca_key_path,
        user_roles,
    ):
        return self.commandRunner.execute(
            cert_type,
            common_name,
            country,
            state,
            locality,
            organization,
            organizational_unit,
            email,
            key_size,
            days_valid,
            output_dir,
            extensions,
            key_usage,
            extended_key_usage,
            subject_alt_names,
            basic_constraints,
            roles,
            ca_cert_path,
            ca_key_path,
            user_roles,
        )



