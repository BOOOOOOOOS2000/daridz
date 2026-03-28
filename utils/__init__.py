# -*- coding: utf-8 -*-
"""Package utils pour ZKTeco Manager"""

from .export import (
    export_attendance_to_excel,
    export_attendance_to_pdf,
    export_users_to_excel,
    generate_report_pdf
)

# Import conditionnel des modules de sécurité et logging
try:
    from .security import (
        PasswordManager,
        InputValidator,
        SecurityConfig,
        secure_hash,
        secure_verify,
        is_safe_input
    )
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False

try:
    from .logger import (
        ZKTecoLogger,
        LogContext,
        init_logging,
        get_logger,
        log_function_call,
        log_device_operation
    )
    LOGGING_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False

__all__ = [
    # Export
    'export_attendance_to_excel',
    'export_attendance_to_pdf',
    'export_users_to_excel',
    'generate_report_pdf',
    # Security
    'PasswordManager',
    'InputValidator', 
    'SecurityConfig',
    'secure_hash',
    'secure_verify',
    'is_safe_input',
    'SECURITY_AVAILABLE',
    # Logging
    'ZKTecoLogger',
    'LogContext',
    'init_logging',
    'get_logger',
    'log_function_call',
    'log_device_operation',
    'LOGGING_AVAILABLE'
]
