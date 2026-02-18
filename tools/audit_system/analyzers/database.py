"""Database Analyzer for evaluating database schema and queries."""

import re
from pathlib import Path
from typing import List, Dict, Any

from ..base import BaseAnalyzer
from ..models import AnalysisResult, Finding, Severity, Category


class DatabaseAnalyzer(BaseAnalyzer):
    """Analyzes database schema and query efficiency."""

    def get_name(self) -> str:
        """Return the analyzer name."""
        return "DatabaseAnalyzer"

    def analyze(self) -> AnalysisResult:
        """Run database analysis."""
        self.logger.info("Starting database analysis")
        
        findings = []
        
        # Analyze schema design
        findings.extend(self._analyze_schema())
        
        # Check Prisma/Django consistency
        findings.extend(self._check_model_consistency())
        
        # Analyze migrations
        findings.extend(self._analyze_migrations())
        
        self.logger.info(f"Database analysis complete. Found {len(findings)} issues")
        
        return AnalysisResult(
            analyzer_name=self.get_name(),
            findings=findings,
            metrics={
                "total_issues": len(findings),
                "schema_issues": len([f for f in findings if "schema" in f.title.lower()]),
            },
            success=True
        )

    def _analyze_schema(self) -> List[Finding]:
        """Analyze database schema design."""
        findings = []
        backend_path = Path(self.config.get("backend_path", "backend"))
        
        for model_file in backend_path.rglob("models.py"):
            try:
                content = model_file.read_text()
                
                # Check for models without primary key
                model_pattern = r'class\s+(\w+)\(models\.Model\):'
                pk_pattern = r'primary_key=True'
                
                models = re.finditer(model_pattern, content)
                for model_match in models:
                    model_name = model_match.group(1)
                    # Get model body
                    model_start = model_match.end()
                    next_class = re.search(r'\nclass\s+', content[model_start:])
                    model_end = model_start + next_class.start() if next_class else len(content)
                    model_body = content[model_start:model_end]
                    
                    # Check for explicit primary key
                    if not re.search(pk_pattern, model_body) and "id" not in model_body.lower():
                        line_num = content[:model_match.start()].count('\n') + 1
                        findings.append(Finding(
                            category=Category.DATABASE,
                            severity=Severity.MEDIUM,
                            title=f"Model without explicit primary key: {model_name}",
                            description="Model relies on default primary key",
                            file_path=str(model_file),
                            line_number=line_num,
                            recommendation="Consider adding explicit primary key field",
                            effort_estimate="low"
                        ))
                
                # Check for missing foreign key constraints
                fk_pattern = r'models\.ForeignKey\([^)]+on_delete=models\.SET_NULL[^)]*\)(?!.*null=True)'
                matches = re.finditer(fk_pattern, content)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    findings.append(Finding(
                        category=Category.DATABASE,
                        severity=Severity.HIGH,
                        title="Foreign key with SET_NULL without null=True",
                        description="Foreign key constraint mismatch",
                        file_path=str(model_file),
                        line_number=line_num,
                        recommendation="Add null=True to foreign key field",
                        effort_estimate="low"
                    ))
            except Exception as e:
                self.logger.debug(f"Error analyzing schema in {model_file}: {e}")
        
        return findings

    def _check_model_consistency(self) -> List[Finding]:
        """Check Prisma schema and Django model consistency."""
        findings = []
        project_root = Path(self.config.get("project_root", "."))
        prisma_schema = project_root / "prisma" / "schema.prisma"
        
        if not prisma_schema.exists():
            return findings
        
        try:
            prisma_content = prisma_schema.read_text()
            # Extract Prisma models
            prisma_models = set(re.findall(r'model\s+(\w+)\s*{', prisma_content))
            
            # Extract Django models
            backend_path = Path(self.config.get("backend_path", "backend"))
            django_models = set()
            for model_file in backend_path.rglob("models.py"):
                content = model_file.read_text()
                django_models.update(re.findall(r'class\s+(\w+)\(models\.Model\):', content))
            
            # Find inconsistencies
            only_in_prisma = prisma_models - django_models
            only_in_django = django_models - prisma_models
            
            if only_in_prisma:
                findings.append(Finding(
                    category=Category.DATABASE,
                    severity=Severity.MEDIUM,
                    title="Models in Prisma but not Django",
                    description=f"Models: {', '.join(only_in_prisma)}",
                    file_path=str(prisma_schema),
                    recommendation="Ensure schema consistency between Prisma and Django",
                    effort_estimate="medium"
                ))
            
            if only_in_django:
                findings.append(Finding(
                    category=Category.DATABASE,
                    severity=Severity.MEDIUM,
                    title="Models in Django but not Prisma",
                    description=f"Models: {', '.join(only_in_django)}",
                    file_path=str(prisma_schema),
                    recommendation="Ensure schema consistency between Prisma and Django",
                    effort_estimate="medium"
                ))
        except Exception as e:
            self.logger.debug(f"Error checking model consistency: {e}")
        
        return findings

    def _analyze_migrations(self) -> List[Finding]:
        """Analyze database migrations."""
        findings = []
        backend_path = Path(self.config.get("backend_path", "backend"))
        
        dangerous_operations = [
            (r'RemoveField', "Removing field", Severity.HIGH),
            (r'DeleteModel', "Deleting model", Severity.HIGH),
            (r'AlterField.*db_column', "Changing column name", Severity.MEDIUM),
            (r'RunSQL.*DROP', "Dropping table/column", Severity.CRITICAL),
        ]
        
        for migration_file in backend_path.rglob("migrations/*.py"):
            if migration_file.name == "__init__.py":
                continue
            try:
                content = migration_file.read_text()
                for pattern, operation, severity in dangerous_operations:
                    if re.search(pattern, content, re.IGNORECASE):
                        findings.append(Finding(
                            category=Category.DATABASE,
                            severity=severity,
                            title=f"Dangerous migration operation: {operation}",
                            description="Migration contains potentially dangerous operation",
                            file_path=str(migration_file),
                            recommendation="Review migration carefully and ensure data backup",
                            effort_estimate="low"
                        ))
            except Exception as e:
                self.logger.debug(f"Error analyzing migration {migration_file}: {e}")
        
        return findings
