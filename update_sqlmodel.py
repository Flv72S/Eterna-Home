#!/usr/bin/env python3
"""
Script to update SQLModel session.query() calls to session.exec() with select()
"""

import os
import re
from pathlib import Path

def update_file(file_path):
    """Update a single file to use session.exec() instead of session.query()"""
    print(f"Processing: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Add select import if not present
    if 'from sqlmodel import' in content and 'select' not in content:
        content = re.sub(
            r'from sqlmodel import ([^,\n]+)',
            r'from sqlmodel import \1, select',
            content
        )
    
    # Update session.query() calls to session.exec(select())
    # Pattern 1: session.exec(select(Model).where(...))
    content = re.sub(
        r'session\.query\(([^)]+)\)\.filter\(([^)]+)\)',
        r'session.exec(select(\1).where(\2))',
        content
    )
    
    # Pattern 2: session.exec(select(Model).where(...)).all()
    content = re.sub(
        r'session\.query\(([^)]+)\)\.filter\(([^)]+)\)\.all\(\)',
        r'session.exec(select(\1).where(\2)).all()',
        content
    )
    
    # Pattern 3: session.exec(select(Model).where(...)).first()
    content = re.sub(
        r'session\.query\(([^)]+)\)\.filter\(([^)]+)\)\.first\(\)',
        r'session.exec(select(\1).where(\2)).first()',
        content
    )
    
    # Pattern 4: session.exec(select(Model).join(...).where(...))
    content = re.sub(
        r'session\.query\(([^)]+)\)\.join\(([^)]+)\)\.filter\(([^)]+)\)',
        r'session.exec(select(\1).join(\2).where(\3))',
        content
    )
    
    # Pattern 5: session.exec(select(Model).join(...).where(...)).all()
    content = re.sub(
        r'session\.query\(([^)]+)\)\.join\(([^)]+)\)\.filter\(([^)]+)\)\.all\(\)',
        r'session.exec(select(\1).join(\2).where(\3)).all()',
        content
    )
    
    # Pattern 6: session.exec(select(Model).join(...).where(...)).first()
    content = re.sub(
        r'session\.query\(([^)]+)\)\.join\(([^)]+)\)\.filter\(([^)]+)\)\.first\(\)',
        r'session.exec(select(\1).join(\2).where(\3)).first()',
        content
    )
    
    # Pattern 7: session.exec(select(Model).where(...)).delete()
    content = re.sub(
        r'session\.query\(([^)]+)\)\.filter\(([^)]+)\)\.delete\(\)',
        r'session.exec(select(\1).where(\2)).delete()',
        content
    )
    
    # Pattern 8: session.exec(select(Model).where(...)).statement
    content = re.sub(
        r'session\.query\(([^)]+)\)\.filter\(([^)]+)\)\.statement',
        r'select(\1).where(\2)',
        content
    )
    
    # If content changed, write it back
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Updated: {file_path}")
        return True
    else:
        print(f"  No changes needed: {file_path}")
        return False

def main():
    """Main function to process all Python files"""
    # Get the project root directory
    project_root = Path(__file__).parent
    
    # Files to process (excluding venv and other directories)
    files_to_process = []
    
    for root, dirs, files in os.walk(project_root):
        # Skip venv and other directories
        dirs[:] = [d for d in dirs if d not in ['venv311', '__pycache__', '.git', 'node_modules']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                files_to_process.append(file_path)
    
    print(f"Found {len(files_to_process)} Python files to process")
    
    updated_count = 0
    for file_path in files_to_process:
        if update_file(file_path):
            updated_count += 1
    
    print(f"\nUpdated {updated_count} files")

if __name__ == "__main__":
    main() 