"""
Project Evaluation and Audit System

A comprehensive analysis tool for evaluating code quality, security, performance,
architecture, and operational readiness across the MueJam Library application.
"""

__version__ = "0.1.0"

from .base import BaseAnalyzer
from .config import AuditConfig
from .models import (
    Finding,
    AnalysisResult,
    AuditReport,
    AuditSummary,
    ActionPlan,
    Severity,
    Category,
)
from .orchestrator import AuditOrchestrator
from .exceptions import (
    AuditError,
    ToolExecutionError,
    FileAccessError,
    ConfigurationError,
    AnalysisError,
    ReportGenerationError,
)

__all__ = [
    "BaseAnalyzer",
    "AuditConfig",
    "Finding",
    "AnalysisResult",
    "AuditReport",
    "AuditSummary",
    "ActionPlan",
    "Severity",
    "Category",
    "AuditOrchestrator",
    "AuditError",
    "ToolExecutionError",
    "FileAccessError",
    "ConfigurationError",
    "AnalysisError",
    "ReportGenerationError",
]
