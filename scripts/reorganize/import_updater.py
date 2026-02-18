"""
Python import update utilities for reorganizing project structure.

This module provides functions for parsing Python files to find import statements,
updating import paths to reflect new file locations, and rewriting files with
updated imports.
"""

import ast
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ImportStatement:
    """Represents a Python import statement with its location and details."""
    
    def __init__(
        self,
        line_number: int,
        col_offset: int,
        original_text: str,
        module_path: str,
        is_relative: bool,
        import_type: str,
        names: List[str],
        aliases: Dict[str, Optional[str]]
    ):
        """
        Initialize an ImportStatement.
        
        Args:
            line_number: Line number in the file (1-indexed)
            col_offset: Column offset in the line (0-indexed)
            original_text: Original import statement text
            module_path: The module path being imported
            is_relative: True if this is a relative import
            import_type: Either "import" or "from"
            names: List of names being imported
            aliases: Dict mapping imported names to their aliases (None if no alias)
        """
        self.line_number = line_number
        self.col_offset = col_offset
        self.original_text = original_text
        self.module_path = module_path
        self.is_relative = is_relative
        self.import_type = import_type
        self.names = names
        self.aliases = aliases
    
    def __repr__(self) -> str:
        return (
            f"ImportStatement(line={self.line_number}, "
            f"module='{self.module_path}', "
            f"type='{self.import_type}', "
            f"relative={self.is_relative})"
        )


def find_import_statements(file: Path) -> List[ImportStatement]:
    """
    Parse Python file and extract all import statements.
    
    Args:
        file: Path to Python file to parse
        
    Returns:
        List of ImportStatement objects found in the file
        
    Raises:
        FileNotFoundError: If file doesn't exist
        SyntaxError: If file contains invalid Python syntax
        
    Requirements: 1.3, 4.2, 4.3
    """
    file = Path(file).resolve()
    
    if not file.exists():
        raise FileNotFoundError(f"File does not exist: {file}")
    
    logger.debug(f"Parsing imports from {file}")
    
    try:
        # Read file content
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines()
        
        # Parse AST
        tree = ast.parse(content, filename=str(file))
        
        imports = []
        
        # Walk the AST to find import statements
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                # Handle: import module
                # Handle: import module as alias
                for alias in node.names:
                    import_stmt = _create_import_statement(
                        node, alias, lines, import_type="import"
                    )
                    imports.append(import_stmt)
                    
            elif isinstance(node, ast.ImportFrom):
                # Handle: from module import name
                # Handle: from .module import name (relative)
                import_stmt = _create_from_import_statement(node, lines)
                if import_stmt:
                    imports.append(import_stmt)
        
        logger.info(f"Found {len(imports)} import statements in {file}")
        return imports
        
    except SyntaxError as e:
        logger.error(f"Syntax error parsing {file}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error parsing {file}: {e}")
        raise


def _create_import_statement(
    node: ast.Import,
    alias: ast.alias,
    lines: List[str],
    import_type: str
) -> ImportStatement:
    """Create ImportStatement from ast.Import node."""
    line_num = node.lineno
    original_text = lines[line_num - 1] if line_num <= len(lines) else ""
    
    module_path = alias.name
    asname = alias.asname
    
    return ImportStatement(
        line_number=line_num,
        col_offset=node.col_offset,
        original_text=original_text.strip(),
        module_path=module_path,
        is_relative=False,
        import_type=import_type,
        names=[module_path],
        aliases={module_path: asname}
    )


def _create_from_import_statement(
    node: ast.ImportFrom,
    lines: List[str]
) -> Optional[ImportStatement]:
    """Create ImportStatement from ast.ImportFrom node."""
    line_num = node.lineno
    original_text = lines[line_num - 1] if line_num <= len(lines) else ""
    
    # Get module path (can be None for relative imports like "from . import x")
    module_path = node.module or ""
    
    # Check if relative import
    is_relative = node.level > 0
    
    # If relative, prepend dots
    if is_relative:
        module_path = "." * node.level + module_path
    
    # Get imported names and aliases
    names = []
    aliases = {}
    for alias in node.names:
        names.append(alias.name)
        aliases[alias.name] = alias.asname
    
    return ImportStatement(
        line_number=line_num,
        col_offset=node.col_offset,
        original_text=original_text.strip(),
        module_path=module_path,
        is_relative=is_relative,
        import_type="from",
        names=names,
        aliases=aliases
    )


def update_import_path(
    import_stmt: ImportStatement,
    old_path: str,
    new_path: str
) -> ImportStatement:
    """
    Update import statement to use new module path.
    
    Args:
        import_stmt: ImportStatement to update
        old_path: Old module path to replace
        new_path: New module path to use
        
    Returns:
        New ImportStatement with updated module path
        
    Requirements: 1.3, 4.2, 4.3
    """
    logger.debug(
        f"Updating import path from '{old_path}' to '{new_path}' "
        f"in statement: {import_stmt.original_text}"
    )
    
    # Check if this import statement matches the old path
    if not _import_matches_path(import_stmt, old_path):
        logger.debug(f"Import does not match old path, skipping")
        return import_stmt
    
    # Update the module path
    updated_module_path = _replace_module_path(
        import_stmt.module_path, old_path, new_path
    )
    
    # Generate new import statement text
    new_text = _generate_import_text(
        import_stmt.import_type,
        updated_module_path,
        import_stmt.names,
        import_stmt.aliases
    )
    
    logger.info(f"Updated import: '{import_stmt.original_text}' -> '{new_text}'")
    
    # Create new ImportStatement with updated values
    return ImportStatement(
        line_number=import_stmt.line_number,
        col_offset=import_stmt.col_offset,
        original_text=new_text,
        module_path=updated_module_path,
        is_relative=import_stmt.is_relative,
        import_type=import_stmt.import_type,
        names=import_stmt.names,
        aliases=import_stmt.aliases
    )


def _import_matches_path(import_stmt: ImportStatement, path: str) -> bool:
    """Check if import statement matches the given path."""
    module = import_stmt.module_path.lstrip('.')
    
    # Exact match
    if module == path:
        return True
    
    # Check if path is a prefix (for submodule imports)
    if module.startswith(path + '.'):
        return True
    
    return False


def _replace_module_path(current_path: str, old_path: str, new_path: str) -> str:
    """Replace old path with new path in module path."""
    # Handle relative imports
    if current_path.startswith('.'):
        dots = len(current_path) - len(current_path.lstrip('.'))
        module = current_path.lstrip('.')
        
        if module == old_path:
            return '.' * dots + new_path
        elif module.startswith(old_path + '.'):
            return '.' * dots + new_path + module[len(old_path):]
        else:
            return current_path
    
    # Handle absolute imports
    if current_path == old_path:
        return new_path
    elif current_path.startswith(old_path + '.'):
        return new_path + current_path[len(old_path):]
    else:
        return current_path


def _generate_import_text(
    import_type: str,
    module_path: str,
    names: List[str],
    aliases: Dict[str, Optional[str]]
) -> str:
    """Generate import statement text from components."""
    if import_type == "import":
        # import module or import module as alias
        name = names[0]
        alias = aliases.get(name)
        if alias:
            return f"import {module_path} as {alias}"
        else:
            return f"import {module_path}"
    
    elif import_type == "from":
        # from module import name1, name2 as alias2, ...
        import_parts = []
        for name in names:
            alias = aliases.get(name)
            if alias:
                import_parts.append(f"{name} as {alias}")
            else:
                import_parts.append(name)
        
        imports_str = ", ".join(import_parts)
        return f"from {module_path} import {imports_str}"
    
    else:
        raise ValueError(f"Unknown import type: {import_type}")


def rewrite_file_imports(
    file: Path,
    updates: Dict[str, str]
) -> None:
    """
    Update all imports in a file based on path mappings.
    
    Args:
        file: Path to Python file to update
        updates: Dict mapping old module paths to new module paths
        
    Raises:
        FileNotFoundError: If file doesn't exist
        SyntaxError: If file contains invalid Python syntax
        
    Requirements: 1.3, 4.2, 4.3
    """
    file = Path(file).resolve()
    
    if not file.exists():
        raise FileNotFoundError(f"File does not exist: {file}")
    
    logger.info(f"Rewriting imports in {file}")
    logger.debug(f"Path mappings: {updates}")
    
    try:
        # Find all import statements
        imports = find_import_statements(file)
        
        if not imports:
            logger.debug(f"No imports found in {file}")
            return
        
        # Read file content
        with open(file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Track which lines have been updated
        updated_lines = {}
        
        # Update each import statement
        for import_stmt in imports:
            for old_path, new_path in updates.items():
                if _import_matches_path(import_stmt, old_path):
                    updated_stmt = update_import_path(import_stmt, old_path, new_path)
                    
                    # Store the updated line
                    line_idx = import_stmt.line_number - 1
                    if line_idx < len(lines):
                        # Preserve indentation
                        original_line = lines[line_idx]
                        indent = len(original_line) - len(original_line.lstrip())
                        updated_lines[line_idx] = ' ' * indent + updated_stmt.original_text + '\n'
                    
                    break  # Only apply first matching update
        
        # Apply updates to lines
        if updated_lines:
            for line_idx, new_line in updated_lines.items():
                lines[line_idx] = new_line
            
            # Write updated content back to file
            with open(file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            logger.info(f"Updated {len(updated_lines)} import statements in {file}")
        else:
            logger.debug(f"No imports needed updating in {file}")
            
    except Exception as e:
        logger.error(f"Error rewriting imports in {file}: {e}")
        raise
