"""Tests for configuration management."""

import pytest
import tempfile
import json
import yaml
from pathlib import Path
from audit_system.config import AuditConfig, ConfigurationError


def test_audit_config_defaults():
    """Test that AuditConfig has sensible defaults."""
    config = AuditConfig(project_root=".")
    
    assert config.project_root == "."
    assert config.backend_path == "apps"
    assert config.frontend_path == "packages"
    assert config.min_code_coverage == 80.0
    assert config.max_complexity == 10
    assert "code_quality" in config.enabled_analyzers
    assert "markdown" in config.output_formats


def test_audit_config_to_dict():
    """Test converting config to dictionary."""
    config = AuditConfig(project_root="/test")
    config_dict = config.to_dict()
    
    assert isinstance(config_dict, dict)
    assert config_dict['project_root'] == "/test"
    assert 'enabled_analyzers' in config_dict
    assert 'min_code_coverage' in config_dict


def test_audit_config_from_yaml():
    """Test loading configuration from YAML file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml_config = {
            'project_root': '/test/project',
            'backend_path': 'backend',
            'min_code_coverage': 85.0,
            'max_complexity': 15
        }
        yaml.dump(yaml_config, f)
        temp_path = f.name
    
    try:
        config = AuditConfig.from_file(temp_path)
        assert config.project_root == '/test/project'
        assert config.backend_path == 'backend'
        assert config.min_code_coverage == 85.0
        assert config.max_complexity == 15
    finally:
        Path(temp_path).unlink()


def test_audit_config_from_json():
    """Test loading configuration from JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json_config = {
            'project_root': '/test/project',
            'frontend_path': 'client',
            'max_function_length': 100
        }
        json.dump(json_config, f)
        temp_path = f.name
    
    try:
        config = AuditConfig.from_file(temp_path)
        assert config.project_root == '/test/project'
        assert config.frontend_path == 'client'
        assert config.max_function_length == 100
    finally:
        Path(temp_path).unlink()


def test_audit_config_file_not_found():
    """Test that FileNotFoundError is raised for missing config file."""
    with pytest.raises(FileNotFoundError):
        AuditConfig.from_file('/nonexistent/config.yaml')


def test_audit_config_unsupported_format():
    """Test that ValueError is raised for unsupported file format."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("invalid config")
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Unsupported config file format"):
            AuditConfig.from_file(temp_path)
    finally:
        Path(temp_path).unlink()


def test_audit_config_save_yaml():
    """Test saving configuration to YAML file."""
    config = AuditConfig(project_root="/test", max_complexity=20)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name
    
    try:
        config.save(temp_path)
        
        # Load and verify
        loaded_config = AuditConfig.from_file(temp_path)
        assert loaded_config.project_root == "/test"
        assert loaded_config.max_complexity == 20
    finally:
        Path(temp_path).unlink()


def test_audit_config_save_json():
    """Test saving configuration to JSON file."""
    config = AuditConfig(project_root="/test", min_code_coverage=90.0)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        config.save(temp_path)
        
        # Load and verify
        loaded_config = AuditConfig.from_file(temp_path)
        assert loaded_config.project_root == "/test"
        assert loaded_config.min_code_coverage == 90.0
    finally:
        Path(temp_path).unlink()



# Validation tests

def test_audit_config_validation_empty_project_root():
    """Test that empty project_root raises ConfigurationError."""
    with pytest.raises(ConfigurationError, match="project_root cannot be empty"):
        AuditConfig(project_root="")


def test_audit_config_validation_invalid_analyzer():
    """Test that invalid analyzer name raises ConfigurationError."""
    with pytest.raises(ConfigurationError, match="Invalid analyzer"):
        AuditConfig(project_root=".", enabled_analyzers=["invalid_analyzer"])


def test_audit_config_validation_coverage_range():
    """Test that min_code_coverage must be between 0 and 100."""
    with pytest.raises(ConfigurationError, match="must be between 0 and 100"):
        AuditConfig(project_root=".", min_code_coverage=150.0)
    
    with pytest.raises(ConfigurationError, match="must be between 0 and 100"):
        AuditConfig(project_root=".", min_code_coverage=-10.0)


def test_audit_config_validation_coverage_type():
    """Test that min_code_coverage must be a number."""
    with pytest.raises(ConfigurationError, match="must be a number"):
        AuditConfig(project_root=".", min_code_coverage="80")


def test_audit_config_validation_complexity_positive():
    """Test that max_complexity must be at least 1."""
    with pytest.raises(ConfigurationError, match="must be at least 1"):
        AuditConfig(project_root=".", max_complexity=0)


def test_audit_config_validation_complexity_type():
    """Test that max_complexity must be an integer."""
    with pytest.raises(ConfigurationError, match="must be an integer"):
        AuditConfig(project_root=".", max_complexity=10.5)


def test_audit_config_validation_function_length_positive():
    """Test that max_function_length must be at least 1."""
    with pytest.raises(ConfigurationError, match="must be at least 1"):
        AuditConfig(project_root=".", max_function_length=-5)


def test_audit_config_validation_invalid_output_format():
    """Test that invalid output format raises ConfigurationError."""
    with pytest.raises(ConfigurationError, match="Invalid output format"):
        AuditConfig(project_root=".", output_formats=["pdf"])


def test_audit_config_validation_empty_output_formats():
    """Test that at least one output format must be specified."""
    with pytest.raises(ConfigurationError, match="At least one output format"):
        AuditConfig(project_root=".", output_formats=[])


def test_audit_config_validation_output_formats_type():
    """Test that output_formats must be a list."""
    with pytest.raises(ConfigurationError, match="must be a list"):
        AuditConfig(project_root=".", output_formats="markdown")


def test_audit_config_validation_enabled_analyzers_type():
    """Test that enabled_analyzers must be a list."""
    with pytest.raises(ConfigurationError, match="must be a list"):
        AuditConfig(project_root=".", enabled_analyzers="code_quality")


def test_audit_config_validation_path_types():
    """Test that path fields must be strings."""
    with pytest.raises(ConfigurationError, match="must be a string"):
        AuditConfig(project_root=".", backend_path=123)


def test_audit_config_validation_pylint_config_not_found():
    """Test that non-existent pylint_config raises ConfigurationError."""
    with pytest.raises(ConfigurationError, match="pylint_config file not found"):
        AuditConfig(project_root=".", pylint_config="/nonexistent/pylintrc")


def test_audit_config_validation_eslint_config_not_found():
    """Test that non-existent eslint_config raises ConfigurationError."""
    with pytest.raises(ConfigurationError, match="eslint_config file not found"):
        AuditConfig(project_root=".", eslint_config="/nonexistent/.eslintrc")


def test_audit_config_validation_pylint_config_type():
    """Test that pylint_config must be a string or None."""
    with pytest.raises(ConfigurationError, match="must be a string or None"):
        AuditConfig(project_root=".", pylint_config=123)


def test_audit_config_validation_valid_config():
    """Test that valid configuration passes validation."""
    config = AuditConfig(
        project_root=".",
        min_code_coverage=85.5,
        max_complexity=15,
        max_function_length=100,
        enabled_analyzers=["code_quality", "security"],
        output_formats=["json", "html"]
    )
    assert config.min_code_coverage == 85.5
    assert config.max_complexity == 15


def test_audit_config_from_file_missing_project_root():
    """Test that configuration without project_root raises ConfigurationError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml_config = {
            'backend_path': 'backend',
            'min_code_coverage': 85.0
        }
        yaml.dump(yaml_config, f)
        temp_path = f.name
    
    try:
        with pytest.raises(ConfigurationError, match="must specify 'project_root'"):
            AuditConfig.from_file(temp_path)
    finally:
        Path(temp_path).unlink()


def test_audit_config_from_file_invalid_yaml():
    """Test that invalid YAML raises ConfigurationError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("invalid: yaml: content: [")
        temp_path = f.name
    
    try:
        with pytest.raises(ConfigurationError, match="Invalid YAML"):
            AuditConfig.from_file(temp_path)
    finally:
        Path(temp_path).unlink()


def test_audit_config_from_file_invalid_json():
    """Test that invalid JSON raises ConfigurationError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{invalid json")
        temp_path = f.name
    
    try:
        with pytest.raises(ConfigurationError, match="Invalid JSON"):
            AuditConfig.from_file(temp_path)
    finally:
        Path(temp_path).unlink()


def test_audit_config_from_file_not_dict():
    """Test that non-dictionary configuration raises ConfigurationError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(["list", "of", "items"], f)
        temp_path = f.name
    
    try:
        with pytest.raises(ConfigurationError, match="must contain a dictionary"):
            AuditConfig.from_file(temp_path)
    finally:
        Path(temp_path).unlink()


def test_audit_config_from_file_empty():
    """Test that empty configuration file raises ConfigurationError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("")
        temp_path = f.name
    
    try:
        with pytest.raises(ConfigurationError, match="must specify 'project_root'"):
            AuditConfig.from_file(temp_path)
    finally:
        Path(temp_path).unlink()


def test_audit_config_from_file_invalid_parameters():
    """Test that invalid parameters in config file raise ConfigurationError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml_config = {
            'project_root': '/test',
            'min_code_coverage': 'invalid'
        }
        yaml.dump(yaml_config, f)
        temp_path = f.name
    
    try:
        with pytest.raises(ConfigurationError, match="must be a number"):
            AuditConfig.from_file(temp_path)
    finally:
        Path(temp_path).unlink()


def test_audit_config_save_creates_directory():
    """Test that save creates parent directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = AuditConfig(project_root="/test")
        save_path = Path(tmpdir) / "subdir" / "config.yaml"
        
        config.save(str(save_path))
        
        assert save_path.exists()
        loaded_config = AuditConfig.from_file(str(save_path))
        assert loaded_config.project_root == "/test"


def test_audit_config_valid_coverage_boundaries():
    """Test that coverage at boundaries (0 and 100) is valid."""
    config1 = AuditConfig(project_root=".", min_code_coverage=0.0)
    assert config1.min_code_coverage == 0.0
    
    config2 = AuditConfig(project_root=".", min_code_coverage=100.0)
    assert config2.min_code_coverage == 100.0
