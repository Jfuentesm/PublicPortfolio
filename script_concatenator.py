"""Generate a single file containing the concatenated files from backlog_generation folder."""

import os
from pathlib import Path
from datetime import datetime

def read_file_content(file_path):
    """Read and return the content of a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading {file_path}: {str(e)}"

def main():
    # Define paths
    root_dir = Path(__file__).parent
    backlog_generation_dir = root_dir / "backlog_generation"

    # Gather all files in backlog_generation folder
    files_to_include = sorted(backlog_generation_dir.iterdir())

    # Create a timestamp string in the format YYYYMMDD_HHMMSS
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Construct the output file name (foldersincluded_datetimestamp.py)
    output_file_name = f"{backlog_generation_dir.name}_{timestamp_str}.py"
    output_file = root_dir / output_file_name

    with open(output_file, 'w', encoding='utf-8') as f:
        # Write file tree section
        f.write("'''\nIncluded Files:\n")
        for file_path in files_to_include:
            rel_path = file_path.relative_to(root_dir)
            f.write(f"- {rel_path}\n")
        f.write("\n'''\n\n")

        # Write concatenated source code section
        f.write("# Concatenated Source Code\n\n")

        # Process files
        for file_path in files_to_include:
            rel_path = file_path.relative_to(root_dir)

            # Write file header
            f.write(f"<file path='{rel_path}'>\n")

            # Write file content
            content = read_file_content(file_path)
            f.write(content)

            # Write file footer
            f.write("\n</file>\n\n")

        # Add error and output instruction template
        f.write('"""\n')
        f.write('<goal>\n\n\n')
        f.write('</goal>\n\n\n')
        f.write('<output instruction>\n')
        f.write('1) Explain \n')
        f.write('2) Give me the COMPLETE UPDATED VERSION of each script that needs to be updated\n')
        f.write('</output instruction>\n')
        f.write('"""\n')

if __name__ == "__main__":
    main()