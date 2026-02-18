"""Base classes and interfaces for analyzers."""

import logging
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .models import Finding, AnalysisResult


class BaseAnalyzer(ABC):
    """Base class for all analysis modules."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the analyzer with configuration.
        
        Args:
            config: Configuration dictionary for the analyzer
        """
        self.config = config
        self.findings: List[Finding] = []
        self.logger = logging.getLogger(f"audit_system.{self.__class__.__name__}")
    
    def run_analysis(self) -> AnalysisResult:
        """
        Run the analysis with timing.
        
        Returns:
            AnalysisResult with execution time
        """
        start_time = time.time()
        try:
            result = self.analyze()
            execution_time = time.time() - start_time
            
            # If the analyzer didn't set execution_time, set it now
            if not hasattr(result, 'execution_time') or result.execution_time == 0:
                # Create a new result with execution_time
                return AnalysisResult(
                    analyzer_name=result.analyzer_name,
                    execution_time=execution_time,
                    findings=result.findings,
                    metrics=result.metrics,
                    success=result.success,
                    error_message=result.error_message
                )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Analysis failed: {e}")
            return AnalysisResult(
                analyzer_name=self.get_name(),
                execution_time=execution_time,
                findings=[],
                metrics={},
                success=False,
                error_message=str(e)
            )
    
    @abstractmethod
    def analyze(self) -> AnalysisResult:
        """
        Perform the analysis and return results.
        
        Returns:
            AnalysisResult containing findings and metrics
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Return the analyzer name.
        
        Returns:
            String identifier for the analyzer
        """
        pass
    
    def add_finding(self, finding: Finding) -> None:
        """
        Add a finding to the results.
        
        Args:
            finding: Finding object to add
        """
        self.findings.append(finding)
    
    def clear_findings(self) -> None:
        """Clear all findings."""
        self.findings = []
