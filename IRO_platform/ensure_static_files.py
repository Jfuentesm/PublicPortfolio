#!/usr/bin/env python
# ensure_static_files.py
import os
import shutil
import sys

def ensure_handsontable_manager_js():
    """
    Ensures that handsontable-manager.js is properly collected and accessible.
    """
    # Define paths
    project_root = os.path.dirname(os.path.abspath(__file__))
    source_file = os.path.join(project_root, 'static', 'js', 'handsontable-manager.js')
    static_root = os.path.join(project_root, 'core', 'static', 'js')
    target_file = os.path.join(static_root, 'handsontable-manager.js')
    
    # Ensure target directory exists
    os.makedirs(static_root, exist_ok=True)
    
    # Check if source file exists
    if not os.path.exists(source_file):
        print(f"Error: Source file {source_file} does not exist.")
        return False
    
    # Copy file
    try:
        shutil.copy2(source_file, target_file)
        print(f"Successfully copied {source_file} to {target_file}")
        return True
    except Exception as e:
        print(f"Error copying file: {str(e)}")
        return False

if __name__ == "__main__":
    success = ensure_handsontable_manager_js()
    sys.exit(0 if success else 1)