"""Exception classes for the audit system."""


class AuditError(Exception):
    """Base exception for audit system errors."""
    pass


class ToolExecutionError(AuditError):
    """Raised when external tool execution fails."""
    pass


class FileAccessError(AuditError):
    """Raised when file cannot be read or parsed."""
    pass


class ConfigurationError(AuditError):
    """Raised when configuration is invalid."""
    pass


class AnalysisError(AuditError):
    """Raised when analysis encounters unexpected conditions."""
    pass


class ReportGenerationError(AuditError):
    """Raised when report generation fails."""
    pass
