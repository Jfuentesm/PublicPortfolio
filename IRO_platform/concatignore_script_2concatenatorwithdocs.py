"""Generate a structured context file for LLM code assistance with enhanced organization and XML tagging."""

import os
from pathlib import Path
from datetime import datetime
import json

def read_file_content(file_path):
    """Read and return the content of a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading {file_path}: {str(e)}"

def categorize_file(file_path):
    """Categorize files based on their location and type."""
    # Special handling for README files in root
    if file_path.name.lower() in ['readme.md', 'readme.txt'] and file_path.parent == file_path.parent.parent:
        return 'project_info'
    elif 'docs' in str(file_path):
        return 'documentation'
    elif file_path.suffix in ['.md', '.txt']:
        return 'documentation'
    elif file_path.suffix in ['.html']:
        return 'front-end'
    elif 'test' in str(file_path).lower():
        return 'tests'
    elif file_path.name in ['docker-compose.yaml','compose.yaml', 'Dockerfile']:
        return 'infrastructure'
    elif file_path.suffix in ['.py', '.js', '.vue']:
        return 'source_code'
    else:
        return 'other'

def get_files_recursively(directory, focus_files=None):
    """Recursively get all files in the directory with improved categorization"""
    files = []
    
    # Standard exclusions
    exclusions = {
        '.venv', 'concatignore', 'archive', 'planning_and_focus_window',
        '__pycache__', 'node_modules', '.git'
    }
    
    # First, check for README in root directory
    readme_files = ['README.md', 'README.txt', 'readme.md', 'readme.txt']
    for readme in readme_files:
        readme_path = directory / readme
        if readme_path.is_file():
            files.append((0, readme_path, 'project_info'))  # Highest priority for README
    
    # Then get all other files
    for item in sorted(directory.rglob('*')):
        # Skip excluded directories and files
        if any(excl in str(item) for excl in exclusions):
            continue
            
        if item.is_file():
            if (item.suffix in ['.py', '.txt', '.md', '.html', '.json', '.js', 
                              '.vue', '.sh', '.yaml', '.yml', '.sql'] or 
                item.name == 'Dockerfile'):
                
                # Skip README if already added
                if item in [f[1] for f in files]:
                    continue
                
                # Prioritize focus files if specified
                priority = 1
                if focus_files and any(focus in str(item) for focus in focus_files):
                    priority = 0
                    
                files.append((priority, item, categorize_file(item)))
    
    # Sort by priority and path
    return sorted(files)

def main():
    root_dir = Path(__file__).parent
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file_name = f"llm_context_{root_dir.name}_{timestamp_str}.md"
    
    # Allow specification of focus files
    focus_files = input("Enter comma-separated list of focus files (or press Enter to skip): ").split(',')
    focus_files = [f.strip() for f in focus_files if f.strip()]
    
    files_to_include = get_files_recursively(root_dir, focus_files)

    with open(output_file_name, 'w', encoding='utf-8') as f:
        # Write structured header
        f.write('# Project Context for LLM Analysis\n\n')
        
        # Task specification section
        f.write('''<task_specification>
    <goal>
    <!-- Insert your specific goal here -->
    </goal>
    
    <expected_output>
    # Overview and explanation
 
    # COMPLETE UPDATED Code
    <!-- Give me the COMPLETE UPDATED VERSION of each script that needs to be updated or created -->
    </expected_output>
    
    <focus_areas>
    <!-- List specific areas or files that need special attention -->
    </focus_areas>
</task_specification>\n\n''')

        # Project structure section
        f.write('## Project Structure\n\n')
        f.write('<project_structure>\n')
        
        # Organize files by category
        files_by_category = {}
        for _, file_path, category in files_to_include:
            if category not in files_by_category:
                files_by_category[category] = []
            files_by_category[category].append(file_path.relative_to(root_dir))

        # Ensure project_info (README) comes first if it exists
        if 'project_info' in files_by_category:
            f.write("\n### Project Information\n")
            for file in sorted(files_by_category['project_info']):
                f.write(f"- {file}\n")
            del files_by_category['project_info']

        # Write remaining categories
        for category, files in files_by_category.items():
            f.write(f"\n### {category.title()}\n")
            for file in sorted(files):
                f.write(f"- {file}\n")
        
        f.write('</project_structure>\n\n')

        # Source code section
        f.write('## Source Code\n\n')
        f.write('<source_code>\n')
        
        for _, file_path, category in files_to_include:
            rel_path = file_path.relative_to(root_dir)
            
            f.write(f'''<file>
    <path>{rel_path}</path>
    <category>{category}</category>
    <content>
```{file_path.suffix[1:] if file_path.suffix else ''}
{read_file_content(file_path)}
```
    </content>
</file>\n\n''')

        f.write('</source_code>\n')

if __name__ == "__main__":
    main()
