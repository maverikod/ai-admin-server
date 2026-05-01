"""Module cert_helpers."""

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

class CertGeneratorHelpers:
    """Command to generate SSL certificates and keys."""

    def __init__(self):
        self.certGeneratorHelpers = None

    async def _generate_self_signed_cert(
        self,
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
        key_usage,
        extended_key_usage,
        subject_alt_names,
        basic_constraints,
        extensions,
    ):
        return self.certGeneratorHelpers._generate_self_signed_cert(
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
            key_usage,
            extended_key_usage,
            subject_alt_names,
            basic_constraints,
            extensions,
        )

    async def _generate_ca_signed_cert(
        self,
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
        key_usage,
        extended_key_usage,
        subject_alt_names,
        basic_constraints,
        extensions,
    ):
        return self.certGeneratorHelpers._generate_ca_signed_cert(
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
            key_usage,
            extended_key_usage,
            subject_alt_names,
            basic_constraints,
            extensions,
        )

    async def _generate_wildcard_cert(
        self,
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
        key_usage,
        extended_key_usage,
        subject_alt_names,
        basic_constraints,
        extensions,
    ):
        return self.certGeneratorHelpers._generate_wildcard_cert(
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
            key_usage,
            extended_key_usage,
            subject_alt_names,
            basic_constraints,
            extensions,
        )

    def _create_openssl_config(
        self,
        common_name,
        country,
        state,
        locality,
        organization,
        organizational_unit,
        email,
        key_usage,
        extended_key_usage,
        subject_alt_names,
        basic_constraints,
        extensions,
    ):
        return self.certGeneratorHelpers._create_openssl_config(
            common_name,
            country,
            state,
            locality,
            organization,
            organizational_unit,
            email,
            key_usage,
            extended_key_usage,
            subject_alt_names,
            basic_constraints,
            extensions,
        )

    async def _generate_ca_certificate(
        self,
        common_name,
        country,
        state,
        locality,
        organization,
        organizational_unit,
        key_size,
        days_valid,
        output_dir,
    ):
        return self.certGeneratorHelpers._generate_ca_certificate(
            common_name,
            country,
            state,
            locality,
            organization,
            organizational_unit,
            key_size,
            days_valid,
            output_dir,
        )

    async def _generate_server_certificate(
        self,
        common_name,
        country,
        state,
        locality,
        organization,
        organizational_unit,
        key_size,
        days_valid,
        output_dir,
        roles,
        ca_cert_path,
        ca_key_path,
    ):
        return self.certGeneratorHelpers._generate_server_certificate(
            common_name,
            country,
            state,
            locality,
            organization,
            organizational_unit,
            key_size,
            days_valid,
            output_dir,
            roles,
            ca_cert_path,
            ca_key_path,
        )

    async def _generate_client_certificate(
        self,
        common_name,
        country,
        state,
        locality,
        organization,
        organizational_unit,
        key_size,
        days_valid,
        output_dir,
        roles,
        ca_cert_path,
        ca_key_path,
    ):
        return self.certGeneratorHelpers._generate_client_certificate(
            common_name,
            country,
            state,
            locality,
            organization,
            organizational_unit,
            key_size,
            days_valid,
            output_dir,
            roles,
            ca_cert_path,
            ca_key_path,
        )



