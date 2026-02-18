"""Performance Profiler for analyzing performance bottlenecks."""

import re
from pathlib import Path
from typing import List, Dict, Any

from ..base import BaseAnalyzer
from ..models import AnalysisResult, Finding, Severity, Category


class PerformanceProfiler(BaseAnalyzer):
    """Analyzes performance bottlenecks and optimization opportunities."""

    def get_name(self) -> str:
        """Return the analyzer name."""
        return "PerformanceProfiler"

    def analyze(self) -> AnalysisResult:
        """Run performance analysis."""
        self.logger.info("Starting performance analysis")
        
        findings = []
        
        # Analyze database queries
        findings.extend(self._analyze_database_queries())
        
        # Check caching strategies
        findings.extend(self._analyze_caching())
        
        # Analyze bundle sizes
        findings.extend(self._analyze_bundle_sizes())
        
        # Check React performance patterns
        findings.extend(self._analyze_react_performance())
        
        # Analyze image optimization
        findings.extend(self._analyze_images())
        
        self.logger.info(f"Performance analysis complete. Found {len(findings)} issues")
        
        return AnalysisResult(
            analyzer_name=self.get_name(),
            findings=findings,
            metrics={
                "total_issues": len(findings),
                "n_plus_one_queries": len([f for f in findings if "N+1" in f.title]),
                "missing_indexes": len([f for f in findings if "index" in f.title.lower()]),
            },
            success=True
        )

    def _analyze_database_queries(self) -> List[Finding]:
        """Analyze database queries for N+1 and missing indexes."""
        findings = []
        backend_path = Path(self.config.get("backend_path", "backend"))
        
        # Patterns indicating N+1 queries
        n_plus_one_patterns = [
            (r'for\s+\w+\s+in\s+\w+\.all\(\).*\n.*\.\w+\.all\(\)', "N+1 query in loop"),
            (r'for\s+\w+\s+in\s+\w+\.filter\(.*\).*\n.*\.\w+\.(?:all|filter)\(\)', "N+1 query in loop"),
        ]
        
        # Patterns indicating missing select_related/prefetch_related
        missing_optimization_patterns = [
            (r'\.all\(\)(?!.*select_related|.*prefetch_related)', "Query without select_related/prefetch_related"),
            (r'\.filter\([^)]+\)(?!.*select_related|.*prefetch_related)', "Filter without select_related/prefetch_related"),
        ]
        
        for py_file in backend_path.rglob("*.py"):
            if "test" in str(py_file) or "migration" in str(py_file):
                continue
            try:
                content = py_file.read_text()
                
                # Check for N+1 patterns
                for pattern, message in n_plus_one_patterns:
                    matches = re.finditer(pattern, content, re.MULTILINE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        findings.append(Finding(
                            category=Category.PERFORMANCE,
                            severity=Severity.HIGH,
                            title=f"Potential N+1 query detected",
                            description=message,
                            file_path=str(py_file),
                            line_number=line_num,
                            recommendation="Use select_related() or prefetch_related() to optimize query",
                            effort_estimate="medium"
                        ))
                
                # Check for missing foreign key indexes
                if "models.py" in py_file.name:
                    foreign_key_pattern = r'models\.ForeignKey\([^)]+\)(?!.*db_index=True)'
                    matches = re.finditer(foreign_key_pattern, content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        findings.append(Finding(
                            category=Category.PERFORMANCE,
                            severity=Severity.MEDIUM,
                            title="Missing database index on foreign key",
                            description="Foreign key field without explicit index",
                            file_path=str(py_file),
                            line_number=line_num,
                            recommendation="Add db_index=True to foreign key field",
                            effort_estimate="low"
                        ))
            except Exception as e:
                self.logger.debug(f"Error analyzing queries in {py_file}: {e}")
        
        return findings

    def _analyze_caching(self) -> List[Finding]:
        """Analyze caching strategies."""
        findings = []
        backend_path = Path(self.config.get("backend_path", "backend"))
        
        # Check for views without caching
        for py_file in backend_path.rglob("views.py"):
            try:
                content = py_file.read_text()
                
                # Find API views without cache decorators
                view_pattern = r'@api_view\([^)]*\)\s*\n\s*def\s+(\w+)'
                cache_pattern = r'@cache_page|@method_decorator.*cache'
                
                view_matches = list(re.finditer(view_pattern, content))
                for view_match in view_matches:
                    view_name = view_match.group(1)
                    # Check if there's a cache decorator before this view
                    preceding_text = content[max(0, view_match.start() - 200):view_match.start()]
                    if not re.search(cache_pattern, preceding_text):
                        line_num = content[:view_match.start()].count('\n') + 1
                        findings.append(Finding(
                            category=Category.PERFORMANCE,
                            severity=Severity.LOW,
                            title=f"API view without caching: {view_name}",
                            description="Consider adding caching for frequently accessed endpoints",
                            file_path=str(py_file),
                            line_number=line_num,
                            recommendation="Add @cache_page decorator or implement caching strategy",
                            effort_estimate="low"
                        ))
            except Exception as e:
                self.logger.debug(f"Error analyzing caching in {py_file}: {e}")
        
        return findings

    def _analyze_bundle_sizes(self) -> List[Finding]:
        """Analyze JavaScript bundle sizes."""
        findings = []
        frontend_path = Path(self.config.get("frontend_path", "frontend"))
        
        # Check for large imports without code splitting
        for tsx_file in frontend_path.rglob("*.tsx"):
            try:
                content = tsx_file.read_text()
                
                # Check for large library imports without lazy loading
                large_libs = ["@mui/material", "lodash", "moment", "chart.js"]
                for lib in large_libs:
                    if f'from "{lib}"' in content or f"from '{lib}'" in content:
                        # Check if lazy loading is used
                        if "React.lazy" not in content and "lazy(" not in content:
                            findings.append(Finding(
                                category=Category.PERFORMANCE,
                                severity=Severity.MEDIUM,
                                title=f"Large library import without code splitting: {lib}",
                                description="Importing large library without lazy loading",
                                file_path=str(tsx_file),
                                recommendation="Use React.lazy() or dynamic imports for code splitting",
                                effort_estimate="medium"
                            ))
            except Exception as e:
                self.logger.debug(f"Error analyzing bundle size in {tsx_file}: {e}")
        
        return findings

    def _analyze_react_performance(self) -> List[Finding]:
        """Analyze React component performance."""
        findings = []
        frontend_path = Path(self.config.get("frontend_path", "frontend"))
        
        for tsx_file in frontend_path.rglob("*.tsx"):
            try:
                content = tsx_file.read_text()
                
                # Check for expensive operations without memoization
                expensive_patterns = [
                    (r'\.map\(.*=>.*\.filter\(', "Nested array operations without useMemo"),
                    (r'\.sort\([^)]*\)(?!.*useMemo)', "Array sort without useMemo"),
                    (r'\.reduce\([^)]*\)(?!.*useMemo)', "Array reduce without useMemo"),
                ]
                
                for pattern, message in expensive_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        findings.append(Finding(
                            category=Category.PERFORMANCE,
                            severity=Severity.MEDIUM,
                            title="Expensive operation without memoization",
                            description=message,
                            file_path=str(tsx_file),
                            line_number=line_num,
                            recommendation="Wrap expensive computation in useMemo hook",
                            effort_estimate="low"
                        ))
                
                # Check for components without React.memo
                component_pattern = r'export\s+(?:default\s+)?function\s+(\w+)\s*\('
                memo_pattern = r'React\.memo|memo\('
                
                component_matches = list(re.finditer(component_pattern, content))
                if component_matches and not re.search(memo_pattern, content):
                    # Only flag if component receives props
                    if "props" in content or ": " in content:
                        findings.append(Finding(
                            category=Category.PERFORMANCE,
                            severity=Severity.LOW,
                            title="Component without React.memo",
                            description="Consider memoizing component to prevent unnecessary re-renders",
                            file_path=str(tsx_file),
                            recommendation="Wrap component with React.memo if it receives props",
                            effort_estimate="low"
                        ))
            except Exception as e:
                self.logger.debug(f"Error analyzing React performance in {tsx_file}: {e}")
        
        return findings

    def _analyze_images(self) -> List[Finding]:
        """Analyze image optimization."""
        findings = []
        frontend_path = Path(self.config.get("frontend_path", "frontend"))
        
        # Check for unoptimized image formats
        image_extensions = [".jpg", ".jpeg", ".png", ".gif"]
        for ext in image_extensions:
            for img_file in frontend_path.rglob(f"*{ext}"):
                # Check file size
                size_mb = img_file.stat().st_size / (1024 * 1024)
                if size_mb > 0.5:  # Flag images larger than 500KB
                    findings.append(Finding(
                        category=Category.PERFORMANCE,
                        severity=Severity.LOW,
                        title=f"Large image file: {img_file.name}",
                        description=f"Image size: {size_mb:.2f}MB",
                        file_path=str(img_file),
                        recommendation="Optimize image or convert to WebP format",
                        effort_estimate="low"
                    ))
        
        return findings
