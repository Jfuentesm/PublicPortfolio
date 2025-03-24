"""
Generate a single file containing the concatenated files from backlog_generation folder,
**excluding** any files not needed for the ESG/Sustainability Analyst persona UI development.
"""

import os
from pathlib import Path
from datetime import datetime

# 1. Create a comprehensive set of relative paths (as strings) to exclude, exactly matching
#    the files and folders you specified.
EXCLUDED_RELATIVE_PATHS = {
    # 1. Docker and Environment Files
    "Dockerfile",
    "docker-compose.yaml",
    "run_local.sh",
    "ensure_static_files.py",
    "requirements.txt",

    # 2. Migrations
    "apps/assessments/migrations/0001_initial.py",
    "apps/assessments/migrations/0002_assessment_tenant.py",
    "apps/assessments/migrations/0003_alter_assessment_tenant.py",
    "apps/assessments/migrations/__init__.py",
    "tenants/migrations/0001_initial.py",
    "tenants/migrations/__init__.py",

    # 3. Management Commands and SQL Setup
    "scripts/01-init-schemas.sql",
    "tenants/management/commands/__init__.py",
    "tenants/management/commands/init_sample_data.py",
    "tenants/management/commands/init_tenant.py",

    # 4. Celery Task / Asynchronous Logic
    "apps/assessments/tasks.py",
    "core/celery.py",

    # 5. WSGI, Core Startup, and Environment Config
    "core/wsgi.py",
    "core/settings/__init__.py",
    "core/settings/base.py",
    "core/settings/local.py",
    "core/settings/production.py",
    "manage.py",

    # 6. Middleware
    "core/middleware/__init__.py",
    "core/middleware/context_middleware.py",
    "core/middleware/logging_middleware.py",

    # 7. Database & Admin Config
    "apps/assessments/admin.py",
    "tenants/admin.py",
    "apps/assessments/api/serializers.py",
    "apps/assessments/api/urls.py",
    "apps/assessments/api/views.py",
    "tenants/api/serializers.py",
    "tenants/api/urls.py",
    "tenants/api/views.py",
    "apps/assessments/templatetags/__init__.py",
    "apps/assessments/templatetags/assessment_filters.py",
    "tenants/apps.py",
    "tenants/views.py",
    "tenants/urls.py",

    # 8. Miscellaneous Items Not Directly Involved in UI
    "core/__init__.py",
    "apps/assessments/__init__.py",
    # Dockerfile is listed again in the instructions but it's already included above.
}


def read_file_content(file_path):
    """Read and return the content of a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading {file_path}: {str(e)}"


def get_files_recursively(directory, root_dir):
    """
    Recursively collect all valid files in 'directory',
    skipping those listed in EXCLUDED_RELATIVE_PATHS or
    matching certain existing ignore rules.
    """
    files = []

    # Check if compose.yaml or Dockerfile are in the top level
    compose_file = directory / 'compose.yaml'
    dockerfile = directory / 'Dockerfile'
    if compose_file.exists():
        rel_path_compose = compose_file.relative_to(root_dir).as_posix()
        if rel_path_compose not in EXCLUDED_RELATIVE_PATHS:
            files.append(compose_file)
    if dockerfile.exists():
        rel_path_docker = dockerfile.relative_to(root_dir).as_posix()
        if rel_path_docker not in EXCLUDED_RELATIVE_PATHS:
            files.append(dockerfile)

    # Specifically handle /docs folder for .md files
    docs_dir = directory / 'docs'
    if docs_dir.exists() and docs_dir.is_dir():
        for item in docs_dir.glob('*.md'):
            if item.is_file() and item.parent == docs_dir:
                rel_path = item.relative_to(root_dir).as_posix()
                if rel_path not in EXCLUDED_RELATIVE_PATHS:
                    files.append(item)

    # Explore directory items
    for item in sorted(directory.iterdir()):
        # Skip these patterns right away
        if (
            item.name == '.venv' or
            (item.name.startswith('.') and item.name != '.scripts') or
            item.name.startswith('concatignore') or
            item.name.startswith('archive') or
            # Skip entire docs subfolders (but we've included top-level .md files)
            (item.name.startswith('docs') and 'scripts' not in str(item) and item.is_dir()) or
            item.name.startswith('planning_and_focus_window')
        ):
            continue

        rel_path = item.relative_to(root_dir).as_posix()

        # Check if this file or folder is in the exclusion list
        # or if the path resides in a subdirectory we want to skip (e.g. migrations).
        if rel_path in EXCLUDED_RELATIVE_PATHS:
            continue

        # If it's a directory, recurse into it
        if item.is_dir():
            files.extend(get_files_recursively(item, root_dir))
        else:
            # We'll accept only certain file types, or Dockerfile. Then check exclusion.
            if item.suffix in ['.py', '.txt', '.md', '.html', '.json', '.js', '.vue', '.sh', '.yaml', '.yml', '.sql'] or item.name == 'Dockerfile':
                # Last check: exclude if path is matched
                if rel_path not in EXCLUDED_RELATIVE_PATHS:
                    files.append(item)

    return files


def main():
    # Define paths
    root_dir = Path(__file__).parent
    backlog_generation_dir = root_dir  # Using the current directory as the root

    # Gather files recursively, excluding the items as specified
    files_to_include = get_files_recursively(backlog_generation_dir, root_dir)

    # Create a timestamp string in the format YYYYMMDD_HHMMSS
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Construct the output file name (foldername_datetimestamp.py)
    output_file_name = f"concatignore_withdocs_{backlog_generation_dir.name}_{timestamp_str}.py"
    output_file = root_dir / output_file_name

    with open(output_file, 'w', encoding='utf-8') as f:
        # Add goal and output instruction template
        f.write('<goal>\n\n\n')
        f.write('</goal>\n\n\n')
        f.write('<output instruction>\n')
        f.write('1) Explain if this is already complete, or what is missing\n')
        f.write('2) Give me the COMPLETE UPDATED VERSION of each script that needs to be updated or created\n')
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