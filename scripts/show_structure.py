"""
Display the current project structure.
"""
import os
from pathlib import Path


def print_tree(directory, prefix="", ignore_dirs={".git", ".venv", "__pycache__", "cache"}):
    """Recursively print directory tree."""
    directory = Path(directory)
    contents = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name))
    
    for i, path in enumerate(contents):
        is_last = i == len(contents) - 1
        current_prefix = "└── " if is_last else "├── "
        
        # Skip ignored directories
        if path.is_dir() and path.name in ignore_dirs:
            continue
        
        print(f"{prefix}{current_prefix}{path.name}{'/' if path.is_dir() else ''}")
        
        if path.is_dir():
            extension = "    " if is_last else "│   "
            print_tree(path, prefix + extension, ignore_dirs)


if __name__ == "__main__":
    print("\nProject Structure:")
    print("==================")
    print("acs_llm_agent/")
    print_tree(".", ignore_dirs={".git", ".venv", "__pycache__", "cache", ".pytest_cache"})
