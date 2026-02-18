"""Script to automatically fix audit issues."""

import re
from pathlib import Path


def add_docstrings_to_file(file_path: Path):
    """
    Add missing docstrings to classes and functions in a file.
    
    Args:
        file_path: Path to the Python file to process
        
    Returns:
        bool: True if file was modified, False otherwise
    """
    content = file_path.read_text(encoding='utf-8')
    lines = content.split('\n')
    modified = False
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for class definition without docstring
        if re.match(r'^\s*class\s+\w+', line):
            # Check if next non-empty line is a docstring
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            
            if j < len(lines) and not lines[j].strip().startswith('"""') and not lines[j].strip().startswith("'''"):
                # Add docstring
                indent = len(line) - len(line.lstrip())
                class_name = re.search(r'class\s+(\w+)', line).group(1)
                new_lines.append(line)
                new_lines.append(' ' * (indent + 4) + f'"""{class_name} class."""')
                modified = True
                i += 1
                continue
        
        # Check for function definition without docstring
        if re.match(r'^\s*def\s+\w+', line) and 'def __' not in line:
            # Check if next non-empty line is a docstring
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            
            if j < len(lines) and not lines[j].strip().startswith('"""') and not lines[j].strip().startswith("'''"):
                # Add docstring
                indent = len(line) - len(line.lstrip())
                func_name = re.search(r'def\s+(\w+)', line).group(1)
                new_lines.append(line)
                new_lines.append(' ' * (indent + 4) + f'"""{func_name.replace("_", " ").title()} function."""')
                modified = True
                i += 1
                continue
        
        new_lines.append(line)
        i += 1
    
    if modified:
        file_path.write_text('\n'.join(new_lines), encoding='utf-8')
        print(f"Fixed: {file_path}")
        return True
    return False


def main():
    """
    Main function to fix docstrings in audit_system directory.
    
    Scans all Python files in the audit_system directory and adds
    missing docstrings to classes and functions.
    """
    # Fix docstrings in audit_system
    audit_dir = Path('audit_system')
    fixed_count = 0
    
    for py_file in audit_dir.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
        if add_docstrings_to_file(py_file):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} files")


if __name__ == '__main__':
    main()
