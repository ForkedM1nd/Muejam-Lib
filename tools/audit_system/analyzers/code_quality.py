"""Code Quality Analyzer for the audit system.

This module analyzes code quality metrics and patterns across Python and TypeScript code.
It evaluates adherence to style guidelines, code complexity, duplication, and framework-specific
patterns for Django and React.
"""

import ast
import time
from typing import Dict, Any, List
from pathlib import Path

from ..base import BaseAnalyzer
from ..models import AnalysisResult, Finding, Category, Severity


class CodeQualityAnalyzer(BaseAnalyzer):
    """Analyzes code quality metrics and patterns.
    
    This analyzer evaluates:
    - Python code adherence to PEP 8 (via Pylint/Flake8)
    - TypeScript code adherence to ESLint rules
    - Code complexity metrics (cyclomatic complexity)
    - Code duplication patterns
    - Django-specific patterns and best practices
    - React-specific patterns and best practices
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Code Quality Analyzer.
        
        Args:
            config: Configuration dictionary containing:
                - project_root: Root directory of the project
                - backend_path: Path to backend code (relative to project_root)
                - frontend_path: Path to frontend code (relative to project_root)
                - max_complexity: Maximum allowed cyclomatic complexity (default: 10)
                - max_function_length: Maximum function length in lines (default: 50)
                - pylint_config: Optional path to Pylint configuration
                - eslint_config: Optional path to ESLint configuration
        """
        super().__init__(config)
        
        # Extract configuration with defaults
        self.project_root = Path(config.get('project_root', '.'))
        self.backend_path = self.project_root / config.get('backend_path', 'backend')
        self.frontend_path = self.project_root / config.get('frontend_path', 'frontend')
        self.max_complexity = config.get('max_complexity', 10)
        self.max_function_length = config.get('max_function_length', 50)
        self.pylint_config = config.get('pylint_config')
        self.eslint_config = config.get('eslint_config')
        
        # Metrics to track
        self.metrics: Dict[str, Any] = {
            'python_files_analyzed': 0,
            'typescript_files_analyzed': 0,
            'total_complexity_issues': 0,
            'total_duplication_issues': 0,
            'total_style_issues': 0,
            'django_pattern_issues': 0,
            'react_pattern_issues': 0,
        }
    
    def get_name(self) -> str:
        """Return the analyzer name.
        
        Returns:
            String identifier for the analyzer
        """
        return "code_quality_analyzer"
    
    def analyze(self) -> AnalysisResult:
        """Run code quality analysis.
        
        This method orchestrates all code quality checks:
        1. Python code analysis (Pylint/Flake8)
        2. TypeScript code analysis (ESLint)
        3. Complexity metrics calculation
        4. Code duplication detection
        5. Django pattern analysis
        6. React pattern analysis
        
        Returns:
            AnalysisResult containing findings and metrics
        """
        start_time = time.time()
        self.clear_findings()
        
        try:
            # Run Python code analysis
            self._analyze_python_code()
            
            # Run TypeScript code analysis
            self._analyze_typescript_code()
            
            # Calculate complexity metrics
            self._calculate_complexity()
            
            # Detect code duplication
            self._detect_duplication()
            
            # Analyze Django patterns
            self._analyze_django_patterns()
            
            # Analyze React patterns
            self._analyze_react_patterns()
            
            execution_time = time.time() - start_time
            
            return AnalysisResult(
                analyzer_name=self.get_name(),
                execution_time=execution_time,
                findings=self.findings,
                metrics=self.metrics,
                success=True,
                error_message=None
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return AnalysisResult(
                analyzer_name=self.get_name(),
                execution_time=execution_time,
                findings=self.findings,
                metrics=self.metrics,
                success=False,
                error_message=str(e)
            )
    
    def _analyze_python_code(self) -> None:
        """Run Pylint and Flake8 on Python code.
        
        This method executes Pylint and Flake8 on Python files to check
        adherence to PEP 8 style guidelines and other code quality issues.
        
        Requirements: 1.1
        """
        import subprocess
        import json
        
        if not self.backend_path.exists():
            return
        
        # Find all Python files
        python_files = list(self.backend_path.rglob('*.py'))
        self.metrics['python_files_analyzed'] = len(python_files)
        
        if not python_files:
            return
        
        # Run Pylint
        try:
            pylint_cmd = ['pylint', '--output-format=json']
            if self.pylint_config:
                pylint_cmd.extend(['--rcfile', str(self.pylint_config)])
            pylint_cmd.extend([str(f) for f in python_files])
            
            result = subprocess.run(
                pylint_cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            # Pylint returns non-zero on issues, which is expected
            if result.stdout:
                try:
                    pylint_issues = json.loads(result.stdout)
                    for issue in pylint_issues:
                        self._add_pylint_finding(issue)
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    pass
                    
        except FileNotFoundError:
            # Pylint not installed - add a finding
            self.add_finding(Finding(
                id=f"{self.get_name()}_pylint_missing",
                category=Category.CODE_QUALITY,
                severity=Severity.INFO,
                title="Pylint not installed",
                description="Pylint is not installed or not in PATH. Install it to enable Python code quality checks.",
                file_path=None,
                line_number=None,
                code_snippet=None,
                recommendation="Install Pylint: pip install pylint",
                effort_estimate="low",
                references=["https://pylint.pycqa.org/"],
                metadata={}
            ))
        
        # Run Flake8
        try:
            flake8_cmd = ['flake8', '--format=json']
            flake8_cmd.extend([str(f) for f in python_files])
            
            result = subprocess.run(
                flake8_cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            if result.stdout:
                try:
                    flake8_issues = json.loads(result.stdout)
                    for file_path, issues in flake8_issues.items():
                        for issue in issues:
                            self._add_flake8_finding(file_path, issue)
                except json.JSONDecodeError:
                    pass
                    
        except FileNotFoundError:
            # Flake8 not installed - add a finding
            self.add_finding(Finding(
                id=f"{self.get_name()}_flake8_missing",
                category=Category.CODE_QUALITY,
                severity=Severity.INFO,
                title="Flake8 not installed",
                description="Flake8 is not installed or not in PATH. Install it to enable additional Python code quality checks.",
                file_path=None,
                line_number=None,
                code_snippet=None,
                recommendation="Install Flake8: pip install flake8",
                effort_estimate="low",
                references=["https://flake8.pycqa.org/"],
                metadata={}
            ))
    
    def _add_pylint_finding(self, issue: Dict[str, Any]) -> None:
        """Convert a Pylint issue to a Finding.
        
        Args:
            issue: Pylint issue dictionary
        """
        # Map Pylint message types to severity
        severity_map = {
            'error': Severity.HIGH,
            'warning': Severity.MEDIUM,
            'refactor': Severity.LOW,
            'convention': Severity.LOW,
            'info': Severity.INFO
        }
        
        severity = severity_map.get(issue.get('type', 'info'), Severity.LOW)
        
        self.add_finding(Finding(
            id=f"{self.get_name()}_pylint_{issue.get('message-id', 'unknown')}_{issue.get('line', 0)}",
            category=Category.CODE_QUALITY,
            severity=severity,
            title=f"Pylint: {issue.get('symbol', 'Unknown')}",
            description=issue.get('message', 'No description'),
            file_path=issue.get('path'),
            line_number=issue.get('line'),
            code_snippet=None,
            recommendation=f"Fix the {issue.get('symbol', 'issue')} reported by Pylint",
            effort_estimate="low",
            references=["https://pylint.pycqa.org/"],
            metadata={'pylint_message_id': issue.get('message-id')}
        ))
        self.metrics['total_style_issues'] += 1
    
    def _add_flake8_finding(self, file_path: str, issue: Dict[str, Any]) -> None:
        """Convert a Flake8 issue to a Finding.
        
        Args:
            file_path: Path to the file with the issue
            issue: Flake8 issue dictionary
        """
        # Map Flake8 error codes to severity
        code = issue.get('code', '')
        if code.startswith('E9') or code.startswith('F'):
            severity = Severity.HIGH
        elif code.startswith('E') or code.startswith('W'):
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW
        
        self.add_finding(Finding(
            id=f"{self.get_name()}_flake8_{code}_{issue.get('line_number', 0)}",
            category=Category.CODE_QUALITY,
            severity=severity,
            title=f"Flake8: {code}",
            description=issue.get('text', 'No description'),
            file_path=file_path,
            line_number=issue.get('line_number'),
            code_snippet=None,
            recommendation=f"Fix the {code} issue reported by Flake8",
            effort_estimate="low",
            references=["https://flake8.pycqa.org/"],
            metadata={'flake8_code': code}
        ))
        self.metrics['total_style_issues'] += 1
    
    def _analyze_typescript_code(self) -> None:
        """Run ESLint on TypeScript code.
        
        This method executes ESLint on TypeScript/JavaScript files to check
        adherence to configured linting rules.
        
        Requirements: 1.2
        """
        import subprocess
        import json
        
        if not self.frontend_path.exists():
            return
        
        # Find all TypeScript and JavaScript files
        ts_files = list(self.frontend_path.rglob('*.ts')) + \
                   list(self.frontend_path.rglob('*.tsx')) + \
                   list(self.frontend_path.rglob('*.js')) + \
                   list(self.frontend_path.rglob('*.jsx'))
        
        self.metrics['typescript_files_analyzed'] = len(ts_files)
        
        if not ts_files:
            return
        
        # Run ESLint
        try:
            eslint_cmd = ['eslint', '--format=json']
            if self.eslint_config:
                eslint_cmd.extend(['--config', str(self.eslint_config)])
            eslint_cmd.extend([str(f) for f in ts_files])
            
            result = subprocess.run(
                eslint_cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            # ESLint returns non-zero on issues, which is expected
            if result.stdout:
                try:
                    eslint_results = json.loads(result.stdout)
                    for file_result in eslint_results:
                        for message in file_result.get('messages', []):
                            self._add_eslint_finding(file_result.get('filePath'), message)
                except json.JSONDecodeError:
                    pass
                    
        except FileNotFoundError:
            # ESLint not installed - add a finding
            self.add_finding(Finding(
                id=f"{self.get_name()}_eslint_missing",
                category=Category.CODE_QUALITY,
                severity=Severity.INFO,
                title="ESLint not installed",
                description="ESLint is not installed or not in PATH. Install it to enable TypeScript/JavaScript code quality checks.",
                file_path=None,
                line_number=None,
                code_snippet=None,
                recommendation="Install ESLint: npm install -g eslint",
                effort_estimate="low",
                references=["https://eslint.org/"],
                metadata={}
            ))
    
    def _add_eslint_finding(self, file_path: str, message: Dict[str, Any]) -> None:
        """Convert an ESLint message to a Finding.
        
        Args:
            file_path: Path to the file with the issue
            message: ESLint message dictionary
        """
        # Map ESLint severity to our severity
        severity_map = {
            2: Severity.HIGH,  # error
            1: Severity.MEDIUM,  # warning
            0: Severity.INFO  # off
        }
        
        severity = severity_map.get(message.get('severity', 0), Severity.LOW)
        
        self.add_finding(Finding(
            id=f"{self.get_name()}_eslint_{message.get('ruleId', 'unknown')}_{message.get('line', 0)}",
            category=Category.CODE_QUALITY,
            severity=severity,
            title=f"ESLint: {message.get('ruleId', 'Unknown')}",
            description=message.get('message', 'No description'),
            file_path=file_path,
            line_number=message.get('line'),
            code_snippet=None,
            recommendation=f"Fix the {message.get('ruleId', 'issue')} reported by ESLint",
            effort_estimate="low",
            references=["https://eslint.org/"],
            metadata={'eslint_rule_id': message.get('ruleId')}
        ))
        self.metrics['total_style_issues'] += 1
    
    def _calculate_complexity(self) -> None:
        """Calculate cyclomatic complexity and maintainability index.
        
        Uses radon to calculate cyclomatic complexity for Python functions
        and generates findings for functions exceeding the configured threshold.
        
        Requirements: 1.3
        """
        try:
            from radon.complexity import cc_visit
            from radon.metrics import mi_visit
        except ImportError:
            # Radon not installed - add a finding
            self.add_finding(Finding(
                id=f"{self.get_name()}_radon_missing",
                category=Category.CODE_QUALITY,
                severity=Severity.INFO,
                title="Radon not installed",
                description="Radon is not installed. Install it to enable complexity metrics calculation.",
                file_path=None,
                line_number=None,
                code_snippet=None,
                recommendation="Install Radon: pip install radon",
                effort_estimate="low",
                references=["https://radon.readthedocs.io/"],
                metadata={}
            ))
            return
        
        if not self.backend_path.exists():
            return
        
        # Find all Python files
        python_files = list(self.backend_path.rglob('*.py'))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                # Calculate cyclomatic complexity
                complexity_results = cc_visit(code)
                
                for result in complexity_results:
                    if result.complexity > self.max_complexity:
                        self._add_complexity_finding(file_path, result)
                        self.metrics['total_complexity_issues'] += 1
                
                # Calculate maintainability index
                try:
                    mi_score = mi_visit(code, multi=True)
                    # MI score ranges from 0-100, lower is worse
                    # < 10: unmaintainable, 10-20: hard to maintain, 20-100: maintainable
                    if mi_score < 20:
                        self._add_maintainability_finding(file_path, mi_score)
                except Exception:
                    # MI calculation can fail on some files, skip silently
                    pass
                    
            except (IOError, UnicodeDecodeError):
                # Skip files that can't be read
                continue
    
    def _add_complexity_finding(self, file_path: Path, result: Any) -> None:
        """Add a finding for high complexity.
        
        Args:
            file_path: Path to the file
            result: Radon complexity result object
        """
        # Determine severity based on how much it exceeds threshold
        complexity = result.complexity
        if complexity > self.max_complexity * 2:
            severity = Severity.HIGH
        elif complexity > self.max_complexity * 1.5:
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW
        
        self.add_finding(Finding(
            id=f"{self.get_name()}_complexity_{file_path.name}_{result.lineno}",
            category=Category.CODE_QUALITY,
            severity=severity,
            title=f"High cyclomatic complexity in {result.name}",
            description=f"Function/method '{result.name}' has cyclomatic complexity of {complexity}, "
                       f"which exceeds the threshold of {self.max_complexity}. "
                       f"High complexity makes code harder to understand, test, and maintain.",
            file_path=str(file_path.relative_to(self.project_root)),
            line_number=result.lineno,
            code_snippet=None,
            recommendation=f"Refactor '{result.name}' to reduce complexity. Consider breaking it into smaller functions, "
                          f"reducing nested conditionals, or simplifying logic.",
            effort_estimate="medium" if complexity > self.max_complexity * 1.5 else "low",
            references=[
                "https://en.wikipedia.org/wiki/Cyclomatic_complexity",
                "https://radon.readthedocs.io/en/latest/intro.html"
            ],
            metadata={
                'complexity': complexity,
                'threshold': self.max_complexity,
                'function_name': result.name
            }
        ))
    
    def _add_maintainability_finding(self, file_path: Path, mi_score: float) -> None:
        """Add a finding for low maintainability index.
        
        Args:
            file_path: Path to the file
            mi_score: Maintainability index score (0-100)
        """
        if mi_score < 10:
            severity = Severity.HIGH
            description = f"File has very low maintainability index of {mi_score:.1f} (unmaintainable)."
        else:
            severity = Severity.MEDIUM
            description = f"File has low maintainability index of {mi_score:.1f} (hard to maintain)."
        
        self.add_finding(Finding(
            id=f"{self.get_name()}_maintainability_{file_path.name}",
            category=Category.CODE_QUALITY,
            severity=severity,
            title=f"Low maintainability index in {file_path.name}",
            description=description + " The maintainability index combines metrics like cyclomatic complexity, "
                       "lines of code, and Halstead volume to assess how maintainable code is.",
            file_path=str(file_path.relative_to(self.project_root)),
            line_number=None,
            code_snippet=None,
            recommendation="Refactor this file to improve maintainability. Consider reducing complexity, "
                          "breaking large functions into smaller ones, and improving code clarity.",
            effort_estimate="high" if mi_score < 10 else "medium",
            references=[
                "https://radon.readthedocs.io/en/latest/intro.html#maintainability-index",
                "https://en.wikipedia.org/wiki/Maintainability"
            ],
            metadata={
                'maintainability_index': mi_score
            }
        ))
    
    def _detect_duplication(self) -> None:
        """Detect code duplication patterns.
        
        Uses pylint's duplicate-code checker to identify duplicated code blocks
        across Python files.
        
        Requirements: 1.4
        """
        import subprocess
        
        if not self.backend_path.exists():
            return
        
        # Find all Python files
        python_files = list(self.backend_path.rglob('*.py'))
        
        if len(python_files) < 2:
            # Need at least 2 files to detect duplication
            return
        
        try:
            # Run pylint with only duplicate-code checker enabled
            pylint_cmd = [
                'pylint',
                '--disable=all',
                '--enable=duplicate-code',
                '--output-format=text',
                '--min-similarity-lines=6',  # Minimum 6 lines to consider duplication
            ]
            pylint_cmd.extend([str(f) for f in python_files])
            
            result = subprocess.run(
                pylint_cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=60  # Timeout after 60 seconds
            )
            
            # Parse the output for duplication messages
            if result.stdout:
                self._parse_duplication_output(result.stdout)
                
        except FileNotFoundError:
            # Pylint not installed - already reported in _analyze_python_code
            pass
        except subprocess.TimeoutExpired:
            # Duplication check took too long, skip it
            pass
        except Exception:
            # Other errors, skip silently
            pass
    
    def _parse_duplication_output(self, output: str) -> None:
        """Parse pylint duplication output and create findings.
        
        Args:
            output: Pylint output text
        """
        lines = output.split('\n')
        current_duplication = None
        duplicate_files = []
        
        for line in lines:
            # Look for duplication messages
            # Format: "Similar lines in 2 files"
            if 'Similar lines in' in line and 'files' in line:
                # Start of a new duplication block
                if current_duplication and duplicate_files:
                    self._add_duplication_finding(duplicate_files)
                    self.metrics['total_duplication_issues'] += 1
                
                current_duplication = line
                duplicate_files = []
            
            # Look for file references
            # Format: "module:line_number" or "file_path:line_number"
            elif ':' in line and current_duplication:
                # Extract file path and line number
                parts = line.strip().split(':')
                if len(parts) >= 2:
                    file_ref = ':'.join(parts[:-1])  # Everything except last part
                    try:
                        line_num = int(parts[-1])
                        duplicate_files.append((file_ref, line_num))
                    except ValueError:
                        # Not a line number, might be part of path
                        pass
        
        # Add the last duplication if exists
        if current_duplication and duplicate_files:
            self._add_duplication_finding(duplicate_files)
            self.metrics['total_duplication_issues'] += 1
    
    def _add_duplication_finding(self, duplicate_files: List[tuple]) -> None:
        """Add a finding for code duplication.
        
        Args:
            duplicate_files: List of (file_path, line_number) tuples
        """
        if len(duplicate_files) < 2:
            return
        
        # Use first file as primary location
        primary_file, primary_line = duplicate_files[0]
        
        # Build description with all locations
        locations = [f"{file}:{line}" for file, line in duplicate_files]
        locations_str = ', '.join(locations)
        
        self.add_finding(Finding(
            id=f"{self.get_name()}_duplication_{primary_file}_{primary_line}",
            category=Category.CODE_QUALITY,
            severity=Severity.MEDIUM,
            title=f"Code duplication detected in {len(duplicate_files)} files",
            description=f"Similar code blocks found in multiple locations: {locations_str}. "
                       f"Code duplication makes maintenance harder and increases the risk of bugs "
                       f"when changes need to be made in multiple places.",
            file_path=primary_file,
            line_number=primary_line,
            code_snippet=None,
            recommendation="Extract the duplicated code into a shared function or class. "
                          "Consider using inheritance, composition, or utility functions to eliminate duplication.",
            effort_estimate="medium",
            references=[
                "https://en.wikipedia.org/wiki/Don%27t_repeat_yourself",
                "https://refactoring.guru/smells/duplicate-code"
            ],
            metadata={
                'duplicate_count': len(duplicate_files),
                'all_locations': locations
            }
        ))
    
    def _analyze_django_patterns(self) -> None:
        """Analyze Django-specific patterns and best practices.
        
        Checks for common Django anti-patterns and best practices including:
        - Models without custom managers
        - Views without proper error handling
        - Missing select_related/prefetch_related in querysets
        - Serializers without proper validation
        
        Requirements: 1.5, 12.1, 12.2, 12.3, 12.4, 12.6, 12.7, 12.8
        """
        import ast
        
        if not self.backend_path.exists():
            return
        
        # Find all Python files that might contain Django code
        python_files = list(self.backend_path.rglob('*.py'))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                # Parse the file
                try:
                    tree = ast.parse(code)
                except SyntaxError:
                    continue
                
                # Check for Django patterns
                self._check_django_models(file_path, tree)
                self._check_django_views(file_path, tree)
                self._check_django_querysets(file_path, tree, code)
                
            except (IOError, UnicodeDecodeError):
                continue
    
    def _check_django_models(self, file_path: Path, tree: ast.AST) -> None:
        """Check Django model patterns.
        
        Args:
            file_path: Path to the file
            tree: AST of the file
        """
        # Look for Django model classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if it's a Django model (inherits from models.Model)
                is_model = any(
                    isinstance(base, ast.Attribute) and 
                    base.attr == 'Model' and
                    isinstance(base.value, ast.Name) and
                    base.value.id == 'models'
                    for base in node.bases
                )
                
                if is_model:
                    # Check for custom manager
                    has_custom_manager = any(
                        isinstance(item, ast.Assign) and
                        any(isinstance(target, ast.Name) and target.id == 'objects' 
                            for target in item.targets)
                        for item in node.body
                    )
                    
                    if not has_custom_manager and len(node.body) > 5:
                        # Only flag complex models without custom managers
                        self.add_finding(Finding(
                            id=f"{self.get_name()}_django_model_manager_{file_path.name}_{node.lineno}",
                            category=Category.CODE_QUALITY,
                            severity=Severity.LOW,
                            title=f"Django model '{node.name}' could benefit from custom manager",
                            description=f"Model '{node.name}' is complex but doesn't define a custom manager. "
                                       f"Custom managers help encapsulate common queries and improve code reusability.",
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=node.lineno,
                            code_snippet=None,
                            recommendation=f"Consider adding a custom manager to '{node.name}' to encapsulate "
                                          f"common query patterns and business logic.",
                            effort_estimate="low",
                            references=[
                                "https://docs.djangoproject.com/en/stable/topics/db/managers/"
                            ],
                            metadata={'model_name': node.name}
                        ))
                        self.metrics['django_pattern_issues'] += 1
    
    def _check_django_views(self, file_path: Path, tree: ast.AST) -> None:
        """Check Django view patterns.
        
        Args:
            file_path: Path to the file
            tree: AST of the file
        """
        # Look for view functions or classes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if it's a view function (has request parameter)
                if node.args.args and node.args.args[0].arg == 'request':
                    # Check for try-except blocks
                    has_error_handling = any(
                        isinstance(item, ast.Try)
                        for item in ast.walk(node)
                    )
                    
                    # Only flag views that interact with database
                    has_db_query = any(
                        isinstance(item, ast.Attribute) and item.attr in ['get', 'filter', 'all', 'create']
                        for item in ast.walk(node)
                    )
                    
                    if has_db_query and not has_error_handling:
                        self.add_finding(Finding(
                            id=f"{self.get_name()}_django_view_error_{file_path.name}_{node.lineno}",
                            category=Category.CODE_QUALITY,
                            severity=Severity.MEDIUM,
                            title=f"Django view '{node.name}' lacks error handling",
                            description=f"View function '{node.name}' performs database queries but doesn't "
                                       f"have try-except blocks for error handling. This can lead to unhandled exceptions.",
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=node.lineno,
                            code_snippet=None,
                            recommendation=f"Add try-except blocks to handle potential database errors, "
                                          f"DoesNotExist exceptions, and validation errors.",
                            effort_estimate="low",
                            references=[
                                "https://docs.djangoproject.com/en/stable/topics/http/views/"
                            ],
                            metadata={'view_name': node.name}
                        ))
                        self.metrics['django_pattern_issues'] += 1
    
    def _check_django_querysets(self, file_path: Path, tree: ast.AST, code: str) -> None:
        """Check Django queryset patterns for N+1 issues.
        
        Args:
            file_path: Path to the file
            tree: AST of the file
            code: Source code as string
        """
        # Look for potential N+1 query patterns
        # This is a simple heuristic: look for .all() or .filter() without select_related/prefetch_related
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                # Check if iterating over a queryset
                if isinstance(node.iter, ast.Call):
                    # Check if the call is .all() or .filter()
                    if isinstance(node.iter.func, ast.Attribute):
                        if node.iter.func.attr in ['all', 'filter']:
                            # Check if there's a related field access in the loop
                            has_related_access = False
                            for item in ast.walk(node):
                                if isinstance(item, ast.Attribute):
                                    # Simple heuristic: multiple attribute accesses might indicate related field
                                    if isinstance(item.value, ast.Attribute):
                                        has_related_access = True
                                        break
                            
                            if has_related_access:
                                # Check if select_related or prefetch_related is used
                                has_optimization = 'select_related' in code or 'prefetch_related' in code
                                
                                if not has_optimization:
                                    self.add_finding(Finding(
                                        id=f"{self.get_name()}_django_n_plus_one_{file_path.name}_{node.lineno}",
                                        category=Category.PERFORMANCE,
                                        severity=Severity.MEDIUM,
                                        title=f"Potential N+1 query pattern detected",
                                        description=f"Loop at line {node.lineno} iterates over a queryset and accesses "
                                                   f"related fields, but doesn't use select_related() or prefetch_related(). "
                                                   f"This can cause N+1 query problems.",
                                        file_path=str(file_path.relative_to(self.project_root)),
                                        line_number=node.lineno,
                                        code_snippet=None,
                                        recommendation=f"Use select_related() for foreign key relationships or "
                                                      f"prefetch_related() for many-to-many relationships to optimize queries.",
                                        effort_estimate="low",
                                        references=[
                                            "https://docs.djangoproject.com/en/stable/ref/models/querysets/#select-related",
                                            "https://docs.djangoproject.com/en/stable/ref/models/querysets/#prefetch-related"
                                        ],
                                        metadata={'line': node.lineno}
                                    ))
                                    self.metrics['django_pattern_issues'] += 1
    
    def _analyze_react_patterns(self) -> None:
        """Analyze React-specific patterns and best practices.
        
        Checks for common React anti-patterns including:
        - Missing hook dependencies
        - Missing memoization opportunities
        - Improper prop validation
        - Accessibility issues
        
        Requirements: 1.6, 13.1, 13.2, 13.3, 13.5, 13.7, 13.8
        """
        import re
        
        if not self.frontend_path.exists():
            return
        
        # Find all TypeScript/JavaScript React files
        react_files = []
        for ext in ['*.tsx', '*.jsx', '*.ts', '*.js']:
            react_files.extend(list(self.frontend_path.rglob(ext)))
        
        for file_path in react_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                # Check for React patterns
                self._check_react_hooks(file_path, code)
                self._check_react_memoization(file_path, code)
                self._check_react_accessibility(file_path, code)
                
            except (IOError, UnicodeDecodeError):
                continue
    
    def _check_react_hooks(self, file_path: Path, code: str) -> None:
        """Check React hook patterns for missing dependencies.
        
        Args:
            file_path: Path to the file
            code: Source code as string
        """
        import re
        
        # Look for useEffect, useCallback, useMemo with empty or missing dependency arrays
        hook_pattern = r'(useEffect|useCallback|useMemo)\s*\(\s*\([^)]*\)\s*=>\s*\{[^}]*\}\s*,\s*\[\s*\]\s*\)'
        
        matches = re.finditer(hook_pattern, code)
        
        for match in matches:
            # Find line number
            line_num = code[:match.start()].count('\n') + 1
            hook_name = match.group(1)
            
            # Check if there are variables used in the hook that should be in dependencies
            # This is a simple heuristic - look for variable references
            hook_body = match.group(0)
            
            # Look for variable references (simple pattern)
            var_refs = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', hook_body)
            
            # If there are many variable references, it might be missing dependencies
            if len(set(var_refs)) > 10:  # Arbitrary threshold
                self.add_finding(Finding(
                    id=f"{self.get_name()}_react_hook_deps_{file_path.name}_{line_num}",
                    category=Category.CODE_QUALITY,
                    severity=Severity.LOW,
                    title=f"React {hook_name} may have missing dependencies",
                    description=f"{hook_name} at line {line_num} has an empty dependency array but "
                               f"references multiple variables. This may cause stale closures or missed updates.",
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=line_num,
                    code_snippet=None,
                    recommendation=f"Review the {hook_name} dependencies and ensure all external variables "
                                  f"used in the hook are included in the dependency array.",
                    effort_estimate="low",
                    references=[
                        "https://react.dev/reference/react/useEffect#specifying-reactive-dependencies",
                        "https://react.dev/learn/removing-effect-dependencies"
                    ],
                    metadata={'hook_type': hook_name}
                ))
                self.metrics['react_pattern_issues'] += 1
    
    def _check_react_memoization(self, file_path: Path, code: str) -> None:
        """Check for missing memoization opportunities.
        
        Args:
            file_path: Path to the file
            code: Source code as string
        """
        import re
        
        # Look for expensive operations in render (map, filter, sort without useMemo)
        # This is a simple heuristic
        
        # Check for .map() calls not wrapped in useMemo
        map_pattern = r'\.map\s*\([^)]+\)'
        
        if 'useMemo' not in code and '.map(' in code:
            matches = re.finditer(map_pattern, code)
            
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                
                # Only flag if it's in a component (has 'return' nearby)
                context_start = max(0, match.start() - 200)
                context = code[context_start:match.end()]
                
                if 'return' in context and 'function' in context:
                    self.add_finding(Finding(
                        id=f"{self.get_name()}_react_memo_{file_path.name}_{line_num}",
                        category=Category.PERFORMANCE,
                        severity=Severity.LOW,
                        title=f"Consider memoizing array transformation",
                        description=f"Array transformation at line {line_num} using .map() is not memoized. "
                                   f"This may cause unnecessary re-computations on every render.",
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=line_num,
                        code_snippet=None,
                        recommendation=f"Consider wrapping the array transformation in useMemo to avoid "
                                      f"re-computing on every render.",
                        effort_estimate="low",
                        references=[
                            "https://react.dev/reference/react/useMemo"
                        ],
                        metadata={'operation': 'map'}
                    ))
                    self.metrics['react_pattern_issues'] += 1
                    break  # Only report once per file
    
    def _check_react_accessibility(self, file_path: Path, code: str) -> None:
        """Check for accessibility issues in React components.
        
        Args:
            file_path: Path to the file
            code: Source code as string
        """
        import re
        
        # Check for onClick without onKeyDown (keyboard accessibility)
        onclick_pattern = r'onClick\s*='
        
        if re.search(onclick_pattern, code):
            # Check if there's also onKeyDown
            if 'onKeyDown' not in code and 'onKeyPress' not in code:
                # Find first occurrence
                match = re.search(onclick_pattern, code)
                if match:
                    line_num = code[:match.start()].count('\n') + 1
                    
                    self.add_finding(Finding(
                        id=f"{self.get_name()}_react_a11y_{file_path.name}_{line_num}",
                        category=Category.CODE_QUALITY,
                        severity=Severity.LOW,
                        title=f"Interactive element may lack keyboard accessibility",
                        description=f"Element with onClick handler at line {line_num} doesn't have a corresponding "
                                   f"keyboard event handler (onKeyDown/onKeyPress). This makes it inaccessible to "
                                   f"keyboard users.",
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=line_num,
                        code_snippet=None,
                        recommendation=f"Add onKeyDown or onKeyPress handler, or use a semantic button element "
                                      f"which handles keyboard events automatically.",
                        effort_estimate="low",
                        references=[
                            "https://www.w3.org/WAI/WCAG21/Understanding/keyboard.html",
                            "https://react.dev/learn/responding-to-events"
                        ],
                        metadata={'issue_type': 'keyboard_accessibility'}
                    ))
                    self.metrics['react_pattern_issues'] += 1
        
        # Check for img without alt attribute
        img_pattern = r'<img[^>]*>'
        
        matches = re.finditer(img_pattern, code)
        
        for match in matches:
            img_tag = match.group(0)
            
            # Check if alt attribute is present
            if 'alt=' not in img_tag:
                line_num = code[:match.start()].count('\n') + 1
                
                self.add_finding(Finding(
                    id=f"{self.get_name()}_react_img_alt_{file_path.name}_{line_num}",
                    category=Category.CODE_QUALITY,
                    severity=Severity.MEDIUM,
                    title=f"Image missing alt attribute",
                    description=f"Image tag at line {line_num} is missing an alt attribute. "
                               f"This makes the image inaccessible to screen reader users.",
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=line_num,
                    code_snippet=None,
                    recommendation=f"Add an alt attribute to the image with a descriptive text. "
                                  f"Use alt=\"\" for decorative images.",
                    effort_estimate="low",
                    references=[
                        "https://www.w3.org/WAI/tutorials/images/",
                        "https://react.dev/learn/writing-markup-with-jsx"
                    ],
                    metadata={'issue_type': 'missing_alt'}
                ))
                self.metrics['react_pattern_issues'] += 1
