"""Generate a single file containing the concatenated files from the current directory."""

import os
from pathlib import Path
from datetime import datetime

def read_file_content(file_path):
    """Read and return the content of a file."""
    try:
        # Try reading with utf-8 first
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # If utf-8 fails, try with 'latin-1' or another common encoding
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                print(f"Warning: Read {file_path} with latin-1 encoding.")
                return f.read()
        except Exception as e:
            return f"Error reading {file_path} (tried utf-8, latin-1): {str(e)}"
    except Exception as e:
        return f"Error reading {file_path}: {str(e)}"


def get_files_recursively(directory):
    """Recursively get all files in the directory, excluding specified types and patterns."""
    files = []
    current_script_name = Path(__file__).name # Get the name of the script itself

    # Explicitly check for compose.yaml and Dockerfile at the current level
    compose_file = directory / 'compose.yaml'
    dockerfile = directory / 'Dockerfile'
    if compose_file.exists() and compose_file.is_file(): # Ensure it's a file
        files.append(compose_file)
    if dockerfile.exists() and dockerfile.is_file(): # Ensure it's a file
        files.append(dockerfile)

    # First, add .md files directly in /docs folder if it exists
    docs_dir = directory / 'docs'
    if docs_dir.exists() and docs_dir.is_dir():
        for item in docs_dir.glob('*.md'):
            # Only include .md files directly in /docs, not subdirectories
            if item.is_file() and item.parent == docs_dir:
                files.append(item)

    for item in sorted(directory.iterdir()):
        # --- Basic Exclusions ---
        # Skip the script file itself
        if item.name == current_script_name:
            continue
        # Skip hidden directories/files (except .scripts)
        if item.name.startswith('.') and item.name != '.scripts':
            continue
        # Skip specific directories/prefixes commonly used for build artifacts, envs, etc.
        if item.name in ['.venv', 'venv', 'env', '__pycache__', 'node_modules', 'dist', 'build'] or \
           item.name.startswith('concatignore') or \
           item.name.startswith('archive') or \
           item.name.startswith('planning_and_focus_window'):
            continue

        # Skip 'docs' directory itself (we handled top-level .md files above)
        # unless 'scripts' is part of its path (allows docs within script folders)
        # Use resolve() to get absolute path for robust comparison
        try:
            # Get the absolute path of the item
            item_abs_path = item.resolve()
            # Get the absolute path of the script's parent directory
            script_parent_abs_path = Path(__file__).parent.resolve()
            # Get the relative path
            relative_path_str = str(item_abs_path.relative_to(script_parent_abs_path))

            if item.is_dir() and item.name == 'docs' and 'scripts' not in relative_path_str.split(os.sep):
                 continue
        except ValueError:
             # This can happen if item is not within the script's parent directory structure,
             # though unlikely with iterdir(). Handle defensively.
             print(f"Warning: Could not determine relative path for {item}. Skipping related 'docs' check.")
             continue
        except Exception as e:
             print(f"Warning: Error during relative path calculation for {item}: {e}. Skipping related 'docs' check.")
             continue


        # --- File Processing ---
        if item.is_file():
            # --- File Exclusion Rules ---
            # Exclude common binary/temporary/log/data file types
            excluded_suffixes = [
                '.log', '.xlsx', '.xls', '.csv', '.data', '.db', '.sqlite', '.sqlite3',
                '.pkl', '.joblib', '.h5', '.hdf5',
                '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.ico',
                '.pdf', '.doc', '.docx', '.ppt', '.pptx',
                '.zip', '.gz', '.tar', '.rar',
                '.exe', '.dll', '.so', '.o', '.a', '.lib',
                '.pyc', '.pyd', '.pyo',
                '.swp', '.swo' # Vim swap files
                ]
            if item.suffix.lower() in excluded_suffixes:
                continue

            # --- File Inclusion Rules ---
            # Include specific text-based file types or names explicitly
            # (No need for explicit allowed_suffixes if we exclude binaries/data)
            # Just ensure it hasn't been added already
            if item not in files:
                files.append(item)

        # --- Recursive Directory Processing ---
        elif item.is_dir():
            # Recursively process allowed subdirectories
            files.extend(get_files_recursively(item))

    # Remove potential duplicates introduced by explicit checks and recursive calls
    # Using dict.fromkeys preserves order (Python 3.7+) and removes duplicates
    return list(dict.fromkeys(files))


def main():
    # Define paths
    root_dir = Path(__file__).parent
    # Assuming the script is run from the directory it needs to process

    # Gather all files recursively, applying exclusion rules
    files_to_include = get_files_recursively(root_dir) # Process from root_dir

    # Create a timestamp string in the format YYYYMMDD_HHMMSS
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Construct the output file name (concatignore_foldername_datetimestamp.txt)
    # Using root_dir.name ensures it uses the parent folder's name where the script resides
    # Changed extension to .txt to avoid potential syntax issues if pasted into code context
    output_file_name = f"concatignore_withdocs_{root_dir.name}_{timestamp_str}.txt"
    output_file = root_dir / output_file_name

    # Ensure the script doesn't include its *own output file* if run multiple times quickly
    # (This check is also handled by the concatignore prefix, but explicit is safer)
    # Note: files_to_include should already exclude the script itself via get_files_recursively
    files_to_include = [f for f in files_to_include if f.resolve() != output_file.resolve()]


    with open(output_file, 'w', encoding='utf-8') as f:
        # Add goal and output instruction template
        f.write('<goal>\n\n\n')
        f.write('</goal>\n\n\n')
        f.write('<output instruction>\n')
        f.write('1) Reflect on 5-7 different possible sources of the problem, distill those down to the most likely root cause \n')
        f.write('2) Give me the COMPLETE UPDATED VERSION of each script that needs to be updated to adrees the more likely root cause and add logging to confirm the hypothesis\n')
        f.write('</output instruction>\n\n')
        f.write('\n')

        # --- Write file tree section ---
        f.write("<Tree of Included Files>\n")
        # Use root_dir for relative paths to ensure consistency
        # Sort alphabetically for predictable order
        relative_paths = sorted([file_path.relative_to(root_dir) for file_path in files_to_include])

        for rel_path in relative_paths:
            # FIX: Use pathlib's as_posix() method to ensure forward slashes, avoiding backslash issues in f-strings
            posix_path_str = rel_path.as_posix()
            f.write(f"- {posix_path_str}\n")
        f.write("</Tree of Included Files>\n\n\n")


        # --- Write concatenated source code section ---
        f.write("<Concatenated Source Code>\n\n")

        # Process files (use the sorted list of relative paths for consistent order)
        for rel_path in relative_paths:
            file_path = root_dir / rel_path

            # FIX: Use pathlib's as_posix() method here as well for consistency
            posix_path_str = rel_path.as_posix()
            # Write file header using normalized relative path
            f.write(f"<file path='{posix_path_str}'>\n")

            # Write file content
            content = read_file_content(file_path)
            f.write(content)

            # Write file footer
            f.write("\n</file>\n\n")

        f.write("</Concatenated Source Code>")

    print(f"Concatenated file created: {output_file}")

if __name__ == "__main__":
    main()