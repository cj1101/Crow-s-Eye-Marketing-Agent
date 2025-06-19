#!/usr/bin/env python3
"""
Fix null bytes in Python files that prevent deployment.
"""
import os
import glob

def fix_null_bytes_in_file(filepath):
    """Remove null bytes from a file."""
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        
        if b'\x00' in content:
            print(f"Found null bytes in: {filepath}")
            clean_content = content.replace(b'\x00', b'')
            with open(filepath, 'wb') as f:
                f.write(clean_content)
            print(f"Cleaned: {filepath}")
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Find and fix null bytes in all Python files."""
    python_files = []
    
    # Find all Python files in crow_eye_api
    for root, dirs, files in os.walk('crow_eye_api'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"Checking {len(python_files)} Python files...")
    
    fixed_count = 0
    for py_file in python_files:
        if fix_null_bytes_in_file(py_file):
            fixed_count += 1
    
    print(f"Fixed {fixed_count} files with null bytes.")
    
    if fixed_count > 0:
        print("Files have been cleaned. Ready to redeploy!")
    else:
        print("No null bytes found in Python files.")

if __name__ == "__main__":
    main() 