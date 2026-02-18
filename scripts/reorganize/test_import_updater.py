"""
Unit tests for import_updater module.

Tests the functionality of finding, parsing, and updating Python import statements.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from .import_updater import (
    find_import_statements,
    update_import_path,
    rewrite_file_imports,
    ImportStatement
)


class TestFindImportStatements:
    """Tests for find_import_statements function."""
    
    def test_find_simple_import(self, tmp_path):
        """Test finding a simple import statement."""
        test_file = tmp_path / "test.py"
        test_file.write_text("import os\n")
        
        imports = find_import_statements(test_file)
        
        assert len(imports) == 1
        assert imports[0].module_path == "os"
        assert imports[0].import_type == "import"
        assert not imports[0].is_relative
    
    def test_find_import_with_alias(self, tmp_path):
        """Test finding import with alias."""
        test_file = tmp_path / "test.py"
        test_file.write_text("import numpy as np\n")
        
        imports = find_import_statements(test_file)
        
        assert len(imports) == 1
        assert imports[0].module_path == "numpy"
        assert imports[0].aliases["numpy"] == "np"
    
    def test_find_from_import(self, tmp_path):
        """Test finding from...import statement."""
        test_file = tmp_path / "test.py"
        test_file.write_text("from os import path\n")
        
        imports = find_import_statements(test_file)
        
        assert len(imports) == 1
        assert imports[0].module_path == "os"
        assert imports[0].import_type == "from"
        assert "path" in imports[0].names
    
    def test_find_from_import_multiple(self, tmp_path):
        """Test finding from...import with multiple names."""
        test_file = tmp_path / "test.py"
        test_file.write_text("from os import path, environ, getcwd\n")
        
        imports = find_import_statements(test_file)
        
        assert len(imports) == 1
        assert imports[0].module_path == "os"
        assert len(imports[0].names) == 3
        assert "path" in imports[0].names
        assert "environ" in imports[0].names
        assert "getcwd" in imports[0].names
    
    def test_find_from_import_with_alias(self, tmp_path):
        """Test finding from...import with alias."""
        test_file = tmp_path / "test.py"
        test_file.write_text("from os import path as p\n")
        
        imports = find_import_statements(test_file)
        
        assert len(imports) == 1
        assert imports[0].module_path == "os"
        assert imports[0].aliases["path"] == "p"
    
    def test_find_relative_import(self, tmp_path):
        """Test finding relative import."""
        test_file = tmp_path / "test.py"
        test_file.write_text("from . import module\n")
        
        imports = find_import_statements(test_file)
        
        assert len(imports) == 1
        assert imports[0].is_relative
        assert imports[0].module_path == "."
    
    def test_find_relative_import_with_module(self, tmp_path):
        """Test finding relative import with module path."""
        test_file = tmp_path / "test.py"
        test_file.write_text("from ..utils import helper\n")
        
        imports = find_import_statements(test_file)
        
        assert len(imports) == 1
        assert imports[0].is_relative
        assert imports[0].module_path == "..utils"
        assert "helper" in imports[0].names
    
    def test_find_multiple_imports(self, tmp_path):
        """Test finding multiple import statements."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "import os\n"
            "import sys\n"
            "from pathlib import Path\n"
        )
        
        imports = find_import_statements(test_file)
        
        assert len(imports) == 3
    
    def test_find_imports_with_code(self, tmp_path):
        """Test finding imports in file with other code."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "import os\n"
            "\n"
            "def main():\n"
            "    print('hello')\n"
            "\n"
            "from pathlib import Path\n"
        )
        
        imports = find_import_statements(test_file)
        
        assert len(imports) == 2
    
    def test_file_not_found(self):
        """Test error handling for non-existent file."""
        with pytest.raises(FileNotFoundError):
            find_import_statements(Path("/nonexistent/file.py"))
    
    def test_syntax_error(self, tmp_path):
        """Test error handling for invalid Python syntax."""
        test_file = tmp_path / "test.py"
        test_file.write_text("import os\nthis is not valid python\n")
        
        with pytest.raises(SyntaxError):
            find_import_statements(test_file)


class TestUpdateImportPath:
    """Tests for update_import_path function."""
    
    def test_update_absolute_import(self):
        """Test updating absolute import path."""
        import_stmt = ImportStatement(
            line_number=1,
            col_offset=0,
            original_text="import tests.backend.unit.test_auth",
            module_path="tests.backend.unit.test_auth",
            is_relative=False,
            import_type="import",
            names=["tests.backend.unit.test_auth"],
            aliases={"tests.backend.unit.test_auth": None}
        )
        
        updated = update_import_path(
            import_stmt,
            "tests.backend",
            "apps.backend.tests"
        )
        
        assert updated.module_path == "apps.backend.tests.unit.test_auth"
        assert "apps.backend.tests.unit.test_auth" in updated.original_text
    
    def test_update_from_import(self):
        """Test updating from...import statement."""
        import_stmt = ImportStatement(
            line_number=1,
            col_offset=0,
            original_text="from tests.backend.unit import test_auth",
            module_path="tests.backend.unit",
            is_relative=False,
            import_type="from",
            names=["test_auth"],
            aliases={"test_auth": None}
        )
        
        updated = update_import_path(
            import_stmt,
            "tests.backend",
            "apps.backend.tests"
        )
        
        assert updated.module_path == "apps.backend.tests.unit"
        assert "from apps.backend.tests.unit import test_auth" == updated.original_text
    
    def test_update_relative_import(self):
        """Test updating relative import."""
        import_stmt = ImportStatement(
            line_number=1,
            col_offset=0,
            original_text="from ..backend.unit import test_auth",
            module_path="..backend.unit",
            is_relative=True,
            import_type="from",
            names=["test_auth"],
            aliases={"test_auth": None}
        )
        
        updated = update_import_path(
            import_stmt,
            "backend",
            "apps.backend.tests"
        )
        
        assert updated.module_path == "..apps.backend.tests.unit"
    
    def test_update_import_with_alias(self):
        """Test updating import with alias."""
        import_stmt = ImportStatement(
            line_number=1,
            col_offset=0,
            original_text="from tests.backend import conftest as conf",
            module_path="tests.backend",
            is_relative=False,
            import_type="from",
            names=["conftest"],
            aliases={"conftest": "conf"}
        )
        
        updated = update_import_path(
            import_stmt,
            "tests.backend",
            "apps.backend.tests"
        )
        
        assert updated.module_path == "apps.backend.tests"
        assert "from apps.backend.tests import conftest as conf" == updated.original_text
    
    def test_no_update_needed(self):
        """Test that unmatched imports are not updated."""
        import_stmt = ImportStatement(
            line_number=1,
            col_offset=0,
            original_text="import os",
            module_path="os",
            is_relative=False,
            import_type="import",
            names=["os"],
            aliases={"os": None}
        )
        
        updated = update_import_path(
            import_stmt,
            "tests.backend",
            "apps.backend.tests"
        )
        
        assert updated.module_path == "os"
        assert updated.original_text == "import os"


class TestRewriteFileImports:
    """Tests for rewrite_file_imports function."""
    
    def test_rewrite_single_import(self, tmp_path):
        """Test rewriting a single import in a file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("from tests.backend import conftest\n")
        
        updates = {"tests.backend": "apps.backend.tests"}
        rewrite_file_imports(test_file, updates)
        
        content = test_file.read_text()
        assert "from apps.backend.tests import conftest" in content
    
    def test_rewrite_multiple_imports(self, tmp_path):
        """Test rewriting multiple imports in a file."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "from tests.backend.unit import test_auth\n"
            "from tests.backend.integration import test_api\n"
        )
        
        updates = {"tests.backend": "apps.backend.tests"}
        rewrite_file_imports(test_file, updates)
        
        content = test_file.read_text()
        assert "from apps.backend.tests.unit import test_auth" in content
        assert "from apps.backend.tests.integration import test_api" in content
    
    def test_rewrite_preserves_other_code(self, tmp_path):
        """Test that rewriting preserves non-import code."""
        test_file = tmp_path / "test.py"
        original_content = (
            "from tests.backend import conftest\n"
            "\n"
            "def test_something():\n"
            "    assert True\n"
        )
        test_file.write_text(original_content)
        
        updates = {"tests.backend": "apps.backend.tests"}
        rewrite_file_imports(test_file, updates)
        
        content = test_file.read_text()
        assert "def test_something():" in content
        assert "assert True" in content
    
    def test_rewrite_preserves_indentation(self, tmp_path):
        """Test that rewriting preserves indentation."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "def func():\n"
            "    from tests.backend import conftest\n"
        )
        
        updates = {"tests.backend": "apps.backend.tests"}
        rewrite_file_imports(test_file, updates)
        
        content = test_file.read_text()
        lines = content.splitlines()
        assert lines[1].startswith("    ")
        assert "from apps.backend.tests import conftest" in lines[1]
    
    def test_rewrite_no_matching_imports(self, tmp_path):
        """Test rewriting file with no matching imports."""
        test_file = tmp_path / "test.py"
        original_content = "import os\nimport sys\n"
        test_file.write_text(original_content)
        
        updates = {"tests.backend": "apps.backend.tests"}
        rewrite_file_imports(test_file, updates)
        
        content = test_file.read_text()
        assert content == original_content
    
    def test_rewrite_file_not_found(self):
        """Test error handling for non-existent file."""
        with pytest.raises(FileNotFoundError):
            rewrite_file_imports(
                Path("/nonexistent/file.py"),
                {"old": "new"}
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
