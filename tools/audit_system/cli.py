"""Command-line interface for the audit system."""

import argparse
import sys
from pathlib import Path
from .config import AuditConfig
from .orchestrator import AuditOrchestrator
from .logging_config import setup_logging


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Project Evaluation and Audit System"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for reports (overrides config)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        help="Path to log file (optional)"
    )
    
    parser.add_argument(
        "--analyzers",
        type=str,
        nargs="+",
        help="Specific analyzers to run (default: all enabled in config)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level, log_file=args.log_file)
    
    # Load configuration
    try:
        config = AuditConfig.from_file(args.config)
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {args.config}")
        print("Create a config file or use --config to specify a different path")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)
    
    # Override config with CLI arguments
    if args.output_dir:
        config.output_dir = args.output_dir
    
    if args.analyzers:
        config.enabled_analyzers = args.analyzers
    
    # Create orchestrator
    orchestrator = AuditOrchestrator(config)
    
    # Register analyzers
    from .analyzers import (
        CodeQualityAnalyzer, SecurityScanner, PerformanceProfiler,
        DatabaseAnalyzer, APIEvaluator, TestCoverageAnalyzer,
        InfrastructureAuditor, DependencyChecker, DocumentationEvaluator,
        ScalabilityAssessor
    )
    
    analyzer_map = {
        "code_quality": CodeQualityAnalyzer,
        "security": SecurityScanner,
        "performance": PerformanceProfiler,
        "database": DatabaseAnalyzer,
        "api": APIEvaluator,
        "test_coverage": TestCoverageAnalyzer,
        "infrastructure": InfrastructureAuditor,
        "dependencies": DependencyChecker,
        "documentation": DocumentationEvaluator,
        "scalability": ScalabilityAssessor,
    }
    
    # Register enabled analyzers
    for analyzer_name in config.enabled_analyzers:
        if analyzer_name in analyzer_map:
            analyzer_class = analyzer_map[analyzer_name]
            orchestrator.register_analyzer(analyzer_class(config.to_dict()))
            print(f"Registered analyzer: {analyzer_name}")
        else:
            print(f"Warning: Unknown analyzer '{analyzer_name}' in config")
    
    # Run audit
    try:
        print(f"\nStarting audit for project: {config.project_root}")
        print("=" * 60)
        report = orchestrator.run_audit()
        
        # Create output directory
        output_path = Path(config.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Export reports
        print("\n" + "=" * 60)
        print(f"Audit completed in {report.execution_time:.2f} seconds")
        print(f"Total findings: {report.summary.total_findings}")
        print(f"Overall score: {report.summary.overall_score:.1f}/100")
        print("=" * 60)
        
        # Export in configured formats
        for fmt in config.output_formats:
            if fmt == "json":
                json_path = output_path / "audit_report.json"
                report.export_json(str(json_path))
                print(f"JSON report saved to: {json_path}")
            elif fmt == "markdown":
                md_path = output_path / "audit_report.md"
                report.export_markdown(str(md_path))
                print(f"Markdown report saved to: {md_path}")
            elif fmt == "html":
                html_path = output_path / "audit_report.html"
                report.export_html(str(html_path))
                print(f"HTML report saved to: {html_path}")
        
    except Exception as e:
        print(f"Error running audit: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
