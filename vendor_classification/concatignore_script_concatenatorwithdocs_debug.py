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

def get_files_recursively(directory):
    """Recursively get all files in the directory"""
    files = []
    
    # Explicitly check for compose.yaml and Dockerfile
    compose_file = directory / 'compose.yaml'
    dockerfile = directory / 'Dockerfile'
    if compose_file.exists():
        files.append(compose_file)
    if dockerfile.exists():
        files.append(dockerfile)
    
    # First, add .md files directly in /docs folder
    docs_dir = directory / 'docs'
    if docs_dir.exists() and docs_dir.is_dir():
        for item in docs_dir.glob('*.md'):
            if item.is_file() and item.parent == docs_dir:  # Only include files directly in /docs
                files.append(item)
    
    for item in sorted(directory.iterdir()):
        # Modified exclusion rules
        if (item.name == '.venv' or 
            (item.name.startswith('.') and item.name != '.scripts') or
            item.name.startswith('concatignore') or 
            item.name.startswith('archive') or 
            (item.name.startswith('docs') and 'scripts' not in str(item) and item.is_dir()) or  # Modified to allow .md files in root /docs
            item.name.startswith('planning_and_focus_window')):
            continue
        
        if item.is_file():
            # Added Dockerfile to the list of valid extensions
            if item.suffix in ['.py', '.txt', '.md', '.html', '.json', '.js', '.vue', '.sh', '.yaml', '.yml', '.sql','.web','.worker'] or item.name == 'Dockerfile':
                files.append(item)
        elif item.is_dir():
            files.extend(get_files_recursively(item))
    return files

def main():
    # Define paths
    root_dir = Path(__file__).parent
    backlog_generation_dir = root_dir  # assuming backlog_generation is the current root dir

    # Gather all files recursively, excluding the items as specified
    files_to_include = get_files_recursively(backlog_generation_dir)

    # Create a timestamp string in the format YYYYMMDD_HHMMSS
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Construct the output file name (foldername_datetimestamp.py)
    output_file_name = f"concatignore_withdocs_{backlog_generation_dir.name}_{timestamp_str}.py"
    output_file = root_dir / output_file_name

    with open(output_file, 'w', encoding='utf-8') as f:
        # Add goal and output instruction template
        f.write('<issue to solve>\n\n\n')
        f.write('</issue to solve>\n\n\n')
        f.write('<output instruction>\n')
        f.write('1) Reflect on 5-7 different possible sources of the problem, distill those down to the most likely root cause \n')
        f.write('2) Give me the COMPLETE UPDATED VERSION of each script that needs to be updated to adrees the more likely root cause and add logging to confirm the hypothesis\n')
        f.write('</output instruction>\n\n')
        f.write('\n')

        # Write file tree section
        f.write("\n <Tree of Included Files>\n")
        for file_path in files_to_include:
            rel_path = file_path.relative_to(root_dir)
            f.write(f"- {rel_path}\n")
        f.write("\n\n\n")
        f.write("\n <Tree of Included Files>\n")

        # Write concatenated source code section
        f.write("\n\n<Concatenated Source Code>\n\n")

        # Process files
        for file_path in files_to_include:
            rel_path = file_path.relative_to(root_dir)

            # Skip the output file itself if it exists
            if file_path.name == output_file_name:
                continue

            # Write file header
            f.write(f"<file path='{rel_path}'>\n")

            # Write file content
            content = read_file_content(file_path)
            f.write(content)

            # Write file footer
            f.write("\n</file>\n\n")

        f.write("</Concatenated Source Code>")

if __name__ == "__main__":
    main()