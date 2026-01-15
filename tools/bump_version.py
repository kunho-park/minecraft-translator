import sys
import re
from pathlib import Path

def bump_version(new_version):
    # Remove 'v' prefix if present for file content
    clean_version = new_version.lstrip('v')
    
    files_to_update = [
        ("pyproject.toml", r'version = "(.*)"', f'version = "{clean_version}"'),
        ("gui/__init__.py", r'__version__ = "(.*)"', f'__version__ = "{clean_version}"'),
        ("src/__init__.py", r'__version__ = "(.*)"', f'__version__ = "{clean_version}"'),
    ]

    base_dir = Path(__file__).parent.parent

    for filename, pattern, replacement in files_to_update:
        file_path = base_dir / filename
        if not file_path.exists():
            print(f"Warning: {filename} not found.")
            continue

        content = file_path.read_text(encoding='utf-8')
        new_content = re.sub(pattern, replacement, content, count=1)
        
        if content != new_content:
            file_path.write_text(new_content, encoding='utf-8')
            print(f"Updated {filename} to version {clean_version}")
        else:
            print(f"No changes made to {filename} (maybe pattern didn't match or version already set)")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python bump_version.py <new_version>")
        sys.exit(1)
    
    bump_version(sys.argv[1])
