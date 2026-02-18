"""Configuration management for the audit system."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
import yaml
import json


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass


@dataclass
class AuditConfig:
    """Configuration for audit execution."""
    
    # Project paths
    project_root: str
    backend_path: str = "apps"
    frontend_path: str = "packages"
    infra_path: str = "infra"
    docs_path: str = "docs"
    
    # Analyzer enablement
    enabled_analyzers: List[str] = field(default_factory=lambda: [
        "code_quality",
        "security",
        "performance",
        "architecture",
        "database",
        "api",
        "test_coverage",
        "infrastructure",
        "dependencies",
        "documentation",
        "scalability"
    ])
    
    # Thresholds
    min_code_coverage: float = 80.0
    max_complexity: int = 10
    max_function_length: int = 50
    
    # Output configuration
    output_dir: str = "audit_reports"
    output_formats: List[str] = field(default_factory=lambda: ["markdown", "json", "html"])
    
    # External tool paths
    pylint_config: Optional[str] = None
    eslint_config: Optional[str] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate configuration values.
        
        Raises:
            ConfigurationError: If configuration is invalid.
        """
        # Validate project_root
        if not self.project_root:
            raise ConfigurationError("project_root cannot be empty")
        
        # Validate paths are strings
        for path_name in ['backend_path', 'frontend_path', 'infra_path', 'docs_path', 'output_dir']:
            path_value = getattr(self, path_name)
            if not isinstance(path_value, str):
                raise ConfigurationError(f"{path_name} must be a string, got {type(path_value)}")
        
        # Validate enabled_analyzers
        if not isinstance(self.enabled_analyzers, list):
            raise ConfigurationError("enabled_analyzers must be a list")
        
        valid_analyzers = {
            "code_quality", "security", "performance", "architecture",
            "database", "api", "test_coverage", "infrastructure",
            "dependencies", "documentation", "scalability"
        }
        
        for analyzer in self.enabled_analyzers:
            if analyzer not in valid_analyzers:
                raise ConfigurationError(
                    f"Invalid analyzer '{analyzer}'. Valid analyzers: {', '.join(sorted(valid_analyzers))}"
                )
        
        # Validate thresholds
        if not isinstance(self.min_code_coverage, (int, float)):
            raise ConfigurationError("min_code_coverage must be a number")
        
        if not 0 <= self.min_code_coverage <= 100:
            raise ConfigurationError("min_code_coverage must be between 0 and 100")
        
        if not isinstance(self.max_complexity, int):
            raise ConfigurationError("max_complexity must be an integer")
        
        if self.max_complexity < 1:
            raise ConfigurationError("max_complexity must be at least 1")
        
        if not isinstance(self.max_function_length, int):
            raise ConfigurationError("max_function_length must be an integer")
        
        if self.max_function_length < 1:
            raise ConfigurationError("max_function_length must be at least 1")
        
        # Validate output_formats
        if not isinstance(self.output_formats, list):
            raise ConfigurationError("output_formats must be a list")
        
        valid_formats = {"markdown", "json", "html"}
        for fmt in self.output_formats:
            if fmt not in valid_formats:
                raise ConfigurationError(
                    f"Invalid output format '{fmt}'. Valid formats: {', '.join(sorted(valid_formats))}"
                )
        
        if not self.output_formats:
            raise ConfigurationError("At least one output format must be specified")
        
        # Validate external tool paths if provided
        if self.pylint_config is not None:
            if not isinstance(self.pylint_config, str):
                raise ConfigurationError("pylint_config must be a string or None")
            pylint_path = Path(self.pylint_config)
            if not pylint_path.exists():
                raise ConfigurationError(f"pylint_config file not found: {self.pylint_config}")
        
        if self.eslint_config is not None:
            if not isinstance(self.eslint_config, str):
                raise ConfigurationError("eslint_config must be a string or None")
            eslint_path = Path(self.eslint_config)
            if not eslint_path.exists():
                raise ConfigurationError(f"eslint_config file not found: {self.eslint_config}")
    
    @classmethod
    def from_file(cls, config_path: str) -> 'AuditConfig':
        """Load configuration from YAML or JSON file.
        
        Args:
            config_path: Path to configuration file (.yaml, .yml, or .json)
            
        Returns:
            AuditConfig instance
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If file format is not supported
            ConfigurationError: If configuration is invalid
        """
        path = Path(config_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(path, 'r') as f:
                if path.suffix in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                elif path.suffix == '.json':
                    data = json.load(f)
                else:
                    raise ValueError(f"Unsupported config file format: {path.suffix}. Use .yaml, .yml, or .json")
            
            if data is None:
                data = {}
            
            if not isinstance(data, dict):
                raise ConfigurationError(f"Configuration file must contain a dictionary, got {type(data)}")
            
            # Ensure project_root is provided
            if 'project_root' not in data:
                raise ConfigurationError("Configuration must specify 'project_root'")
            
            return cls(**data)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration file: {e}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file: {e}")
        except TypeError as e:
            raise ConfigurationError(f"Invalid configuration parameters: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of configuration
        """
        return {
            'project_root': self.project_root,
            'backend_path': self.backend_path,
            'frontend_path': self.frontend_path,
            'infra_path': self.infra_path,
            'docs_path': self.docs_path,
            'enabled_analyzers': self.enabled_analyzers,
            'min_code_coverage': self.min_code_coverage,
            'max_complexity': self.max_complexity,
            'max_function_length': self.max_function_length,
            'output_dir': self.output_dir,
            'output_formats': self.output_formats,
            'pylint_config': self.pylint_config,
            'eslint_config': self.eslint_config,
        }
    
    def save(self, config_path: str) -> None:
        """Save configuration to file.
        
        Args:
            config_path: Path where configuration should be saved
            
        Raises:
            ValueError: If file format is not supported
        """
        path = Path(config_path)
        
        # Create parent directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            if path.suffix in ['.yaml', '.yml']:
                yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)
            elif path.suffix == '.json':
                json.dump(self.to_dict(), f, indent=2)
            else:
                raise ValueError(f"Unsupported config file format: {path.suffix}. Use .yaml, .yml, or .json")
