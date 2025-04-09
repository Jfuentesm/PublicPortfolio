# --- COMPLETE UPDATED SCRIPT ---

import sys
import os
from pathlib import Path
from datetime import datetime
import re # For parsing comma-separated list robustly AND file blocks

# --- Try importing PySide6 ---
try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtCore import Qt, Slot
    from PySide6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QTreeView, QLabel, QRadioButton, QGroupBox,
        QMessageBox, QFrame, QTextEdit, QLineEdit, QCheckBox
    )
    from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon, QFont
except ImportError:
    print("Error: PySide6 is not installed.")
    print("Please install it using: pip install PySide6")
    sys.exit(1)

# --- Constants for Output Directories ---
OUTPUT_BASE_DIR_NAME = "dev_prompts"
PLANNING_SUBDIR_NAME = "1a_planning_prompts"
ACTION_SUBDIR_NAME = "1b_dev_prompts"

# --- Constants for File Parsing ---
# Regex to find <file path='...'>...</file> blocks, capturing path and content
# Handles single/double quotes, whitespace, and multi-line content
FILE_BLOCK_REGEX = re.compile(
    r"<file\s+path=['\"](.*?)['\"]\s*>(.*?)</file>",
    re.DOTALL | re.IGNORECASE # DOTALL makes . match newlines, IGNORECASE for <file> tag
)


# --- Reusable Core Logic ---

def read_file_content(file_path):
    """Read and return the content of a file, handling potential encoding issues."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                print(f"Warning: Read {file_path} with latin-1 encoding.")
                return f.read()
        except Exception as e:
            print(f"Error reading {file_path} (tried utf-8, latin-1): {str(e)}")
            return f"--- ERROR READING FILE (tried utf-8, latin-1) ---\nPath: {file_path}\nError: {str(e)}\n--- END ERROR ---"
    except FileNotFoundError:
        print(f"Error: File not found during read: {file_path}")
        return f"--- ERROR: FILE NOT FOUND ---\nPath: {file_path}\n--- END ERROR ---"
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return f"--- ERROR READING FILE ---\nPath: {file_path}\nError: {str(e)}\n--- END ERROR ---"

def get_potential_files_recursively(current_directory, original_root_dir, script_name, include_logs=False):
    """
    Recursively get potential files relative to the original_root_dir,
    excluding specified types and patterns. Returns relative paths.

    Args:
        current_directory (Path or str): The directory to start scanning from.
        original_root_dir (Path): The root directory of the project.
        script_name (str): The name of the script file itself, to exclude it.
        include_logs (bool): If True, .log files will be included in the scan.
                             Defaults to False.
    """
    potential_files = []
    current_directory_path = Path(current_directory).resolve()
    original_root_dir_resolved = original_root_dir.resolve() # Ensure root is resolved

    # --- Root-level checks ---
    if current_directory_path == original_root_dir_resolved:
        compose_file = original_root_dir_resolved / 'compose.yaml'
        dockerfile = original_root_dir_resolved / 'Dockerfile'
        if compose_file.exists() and compose_file.is_file():
            potential_files.append(compose_file.relative_to(original_root_dir_resolved))
        if dockerfile.exists() and dockerfile.is_file():
            potential_files.append(dockerfile.relative_to(original_root_dir_resolved))

        docs_dir = original_root_dir_resolved / 'docs'
        if docs_dir.exists() and docs_dir.is_dir():
            for item in docs_dir.glob('*.md'):
                if item.is_file() and item.parent == docs_dir:
                    potential_files.append(item.resolve().relative_to(original_root_dir_resolved))

    # --- Recursive scan ---
    try:
        for item_entry in os.scandir(current_directory_path):
            item = Path(item_entry.path)
            item_abs_path = item.resolve()

            try:
                # Ensure the item is actually within the project root before proceeding
                if not item_abs_path.is_relative_to(original_root_dir_resolved):
                     # print(f"Debug: Item {item_abs_path} is outside project root {original_root_dir_resolved}. Skipping.")
                     continue
                relative_path = item_abs_path.relative_to(original_root_dir_resolved)
                relative_path_str = relative_path.as_posix()
            except ValueError:
                # This might happen if symlinks point outside, is_relative_to should catch most cases
                print(f"Warning: Could not get relative path for {item_abs_path} against {original_root_dir_resolved}. Skipping.")
                continue
            except Exception as e:
                print(f"Warning: Error during relative path calculation for {item}: {e}. Skipping.")
                continue

            # --- Exclusions ---
            if item.name == script_name: continue
            if item.name.startswith('.') and item.name != '.scripts': continue
            # Exclude common build/env dirs, archive dirs, and our own output files/dirs
            if item.name in ['.venv', 'venv', 'env', '__pycache__', 'node_modules', 'dist', 'build', OUTPUT_BASE_DIR_NAME] or \
               item.name.startswith('concatignore') or \
               item.name.startswith('archive') or \
               item.name.startswith('planning_and_focus_window') or \
               item.name.startswith('planning_request_') or \
               item.name.startswith('concat_') or \
               item.name == '.git': # Explicitly exclude .git
                continue
            # Exclude top-level 'docs' unless inside 'scripts'
            if item.is_dir() and item.name == 'docs' and 'scripts' not in relative_path_str.split('/'): continue

            # --- File processing ---
            if item.is_file():
                excluded_suffixes = [
                    # '.log', # Handled by include_logs flag
                    '.xlsx', '.xls', '.csv', '.data', '.db', '.sqlite', '.sqlite3',
                    '.pkl', '.joblib', '.h5', '.hdf5',
                    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.ico',
                    '.pdf', '.doc', '.docx', '.ppt', '.pptx',
                    '.zip', '.gz', '.tar', '.rar',
                    '.exe', '.dll', '.so', '.o', '.a', '.lib',
                    '.pyc', '.pyd', '.pyo',
                    '.swp', '.swo', '.json'
                ]
                # Conditionally exclude .log files
                if item.suffix.lower() == '.log' and not include_logs:
                    continue
                if item.suffix.lower() in excluded_suffixes:
                    continue

                # Add relative path (relative to original root)
                if relative_path not in potential_files:
                    potential_files.append(relative_path)

            # --- Directory processing ---
            elif item.is_dir():
                # Recurse, passing original root dir and include_logs flag
                potential_files.extend(get_potential_files_recursively(item_abs_path, original_root_dir_resolved, script_name, include_logs))

    except FileNotFoundError: print(f"Warning: Directory not found during scan: {current_directory_path}. Skipping.")
    except PermissionError: print(f"Warning: Permission denied for directory: {current_directory_path}. Skipping.")
    except Exception as e: print(f"Error scanning directory {current_directory_path}: {e}")

    # Remove duplicates and sort
    return sorted(list(dict.fromkeys(potential_files)), key=lambda p: p.as_posix())


# --- Mode Definitions (Unchanged) ---
MODES = {
    "debug": {
        "name": "Debug Mode",
        "issue_placeholder": "<Describe the bug or unexpected behavior observed>\n\n\n", # Kept for planning, action uses goal_input
        "output_instruction": (
            "1) Reflect on 5-7 different possible sources of the problem based on the code provided and the goal/issue description.\n"
            "2) Distill those down to the most likely root cause.\n"
            "3) Provide the COMPLETE UPDATED VERSION of *only* the files that need changes to fix the likely root cause.\n"
            "   Use the format: <file path='relative/path/to/file.ext'>\n[COMPLETE FILE CONTENT]\n</file>\n"
        )
    },
    "add_feature": {
        "name": "Add New Feature",
        "issue_placeholder": "<Describe the new feature or enhancement required>\n\n\n", # Kept for planning, action uses goal_input
        "output_instruction": (
            "1) Explain if this is already complete, or what is missing\n"
            "2) Provide the COMPLETE code for any NEW files needed.\n"
            "3) Provide the COMPLETE UPDATED VERSION of any EXISTING files that need changes.\n"
            "   Use the format: <file path='relative/path/to/file.ext'>\n[COMPLETE FILE CONTENT]\n</file>\n for both new and updated files."
        )
    },
    "explain": {
        "name": "Explain / Brainstorm",
        "issue_placeholder": "<Ask a question about the code, request an explanation, or describe a concept to brainstorm>\n\n\n", # Kept for planning, action uses goal_input
        "output_instruction": (
            "Provide a clear explanation, answer the question, or offer brainstorming ideas/approaches.\n"
            "If suggesting code changes or approaches, illustrate with concise examples where appropriate (no need for full file rewrites unless specifically asked).\n"
        )
    }
}

# --- Custom Role for Storing Path Data in Model ---
PathRole = Qt.UserRole + 1

# --- PySide6 GUI Application Class ---

class ScriptAggregatorApp(QWidget):
    def __init__(self, script_dir, script_name):
        super().__init__()
        self.script_dir = Path(script_dir).resolve() # Absolute path to the script's dir (project root)
        self.script_name = script_name
        self.folder_icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DirIcon)
        self.file_icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileIcon)
        self.log_icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileIcon) # Could customize later
        self.model = QStandardItemModel()
        self.tree_view = QTreeView()
        self.status_label = QLabel("Ready. Scanning for files...")
        self.mode_buttons = {}
        self.goal_input = QTextEdit() # User's main goal/task description
        self.suggestion_input = QLineEdit()
        self.include_logs_checkbox = QCheckBox("Include selected .log files in Step 1b output")
        self.llm_response_input = QTextEdit() # <-- NEW: Input for LLM response
        self.item_path_map = {} # Map path string -> QStandardItem

        # --- Define output directories relative to script_dir ---
        self.output_base_dir = self.script_dir / OUTPUT_BASE_DIR_NAME
        self.planning_output_dir = self.output_base_dir / PLANNING_SUBDIR_NAME
        self.action_output_dir = self.output_base_dir / ACTION_SUBDIR_NAME

        self.initUI()
        self.populate_file_tree() # Includes logs by default in the scan
        file_count = self.count_files_in_model()
        self.status_label.setText(f"Ready. Found {file_count} potential files (including .log).")


    def initUI(self):
        self.setWindowTitle("Script Aggregator & Applier") # Updated title
        self.setGeometry(150, 150, 1050, 850) # Increased size slightly

        main_h_layout = QHBoxLayout()
        left_v_layout = QVBoxLayout()
        right_v_layout = QVBoxLayout()
        right_v_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Left Side: File Tree ---
        tree_header_label = QLabel("Files in Project (Checkboxes for Step 1b):")
        font = tree_header_label.font(); font.setBold(True); tree_header_label.setFont(font)
        self.tree_view.setModel(self.model)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        left_v_layout.addWidget(tree_header_label)
        left_v_layout.addWidget(self.tree_view)

        # --- Right Side: Controls ---
        # Step 0
        step0_groupbox = QGroupBox("Step 0: Generate Planning Request (excludes .log files)")
        step0_layout = QVBoxLayout()
        step0_layout.addWidget(QLabel("Describe your overall goal or task:"))
        self.goal_input.setPlaceholderText("e.g., Refactor the database connection logic to use a connection pool, Add user authentication using JWT...")
        self.goal_input.setMinimumHeight(60)
        step0_layout.addWidget(self.goal_input)
        generate_planning_button = QPushButton("Generate Planning Request File")
        generate_planning_button.clicked.connect(self.generate_planning_request)
        step0_layout.addWidget(generate_planning_button)
        step0_groupbox.setLayout(step0_layout)
        right_v_layout.addWidget(step0_groupbox)

        # Step 1a
        step1a_groupbox = QGroupBox("Step 1a: Apply LLM File Suggestions")
        step1a_layout = QVBoxLayout()
        step1a_layout.addWidget(QLabel("Paste comma-separated file list from LLM:"))
        self.suggestion_input.setPlaceholderText("e.g., src/db.py, src/auth/jwt.py, tests/test_auth.py")
        step1a_layout.addWidget(self.suggestion_input)
        apply_suggestion_button = QPushButton("Apply Suggested Files to Selection Below")
        apply_suggestion_button.clicked.connect(self.apply_suggested_files)
        step1a_layout.addWidget(apply_suggestion_button)
        step1a_groupbox.setLayout(step1a_layout)
        right_v_layout.addWidget(step1a_groupbox)

        # Manual Selection
        select_groupbox = QGroupBox("Manual File Selection (for Step 1b)")
        select_layout = QVBoxLayout()
        select_buttons_layout = QHBoxLayout()
        select_all_button = QPushButton("Select All Visible Files")
        select_none_button = QPushButton("Deselect All Visible Files")
        select_all_button.clicked.connect(self.select_all)
        select_none_button.clicked.connect(self.select_none)
        select_buttons_layout.addWidget(select_all_button)
        select_buttons_layout.addWidget(select_none_button)
        select_layout.addLayout(select_buttons_layout)
        select_groupbox.setLayout(select_layout)
        right_v_layout.addWidget(select_groupbox)

        # Step 1b Mode
        mode_groupbox = QGroupBox("Step 1b: Select Action Mode & Generate Action Prompt") # Updated title
        mode_layout = QVBoxLayout()
        first_mode_key = list(MODES.keys())[0]
        for key, mode_info in MODES.items():
            rb = QRadioButton(mode_info["name"])
            self.mode_buttons[key] = rb
            if key == first_mode_key: rb.setChecked(True)
            mode_layout.addWidget(rb)
        mode_layout.addWidget(self.include_logs_checkbox)
        self.include_logs_checkbox.setChecked(False)
        self.generate_button = QPushButton("Execute Step 1b: Generate Concatenated File for LLM Action") # Moved button here
        self.generate_button.clicked.connect(self.generate_final_output_file)
        mode_layout.addWidget(self.generate_button) # Add button to this group
        mode_groupbox.setLayout(mode_layout)
        right_v_layout.addWidget(mode_groupbox)

        # --- NEW: Step 2 Apply Changes ---
        step2_groupbox = QGroupBox("Step 2: Apply LLM Changes")
        step2_layout = QVBoxLayout()
        step2_layout.addWidget(QLabel("Paste the LLM response containing <file> blocks below:"))
        self.llm_response_input.setPlaceholderText("<file path='relative/path/to/file.ext'>\n[COMPLETE FILE CONTENT]\n</file>\n...")
        self.llm_response_input.setMinimumHeight(150) # Make it reasonably tall
        self.llm_response_input.setAcceptRichText(False) # Ensure plain text
        step2_layout.addWidget(self.llm_response_input)
        self.apply_changes_button = QPushButton("Parse and Apply Changes to Project Files")
        self.apply_changes_button.clicked.connect(self.apply_llm_changes) # Connect to new slot
        step2_layout.addWidget(self.apply_changes_button)
        step2_groupbox.setLayout(step2_layout)
        right_v_layout.addWidget(step2_groupbox)
        # --- END NEW STEP 2 ---

        right_v_layout.addStretch(1) # Spacer

        # Assemble Main Horizontal Layout
        left_widget = QWidget(); left_widget.setLayout(left_v_layout)
        right_widget = QWidget(); right_widget.setLayout(right_v_layout)
        main_h_layout.addWidget(left_widget, 3) # Give tree more space
        main_h_layout.addWidget(right_widget, 4) # Give controls more space

        # --- Bottom Area ---
        bottom_v_layout = QVBoxLayout()
        # self.generate_button = QPushButton("Execute Step 1b: Generate Concatenated File for LLM Action") # Button moved up
        # self.generate_button.clicked.connect(self.generate_final_output_file)
        # bottom_v_layout.addWidget(self.generate_button) # Button moved up
        self.status_label.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        self.status_label.setLineWidth(1)
        bottom_v_layout.addWidget(self.status_label)

        # --- Overall Layout ---
        overall_layout = QVBoxLayout(self)
        overall_layout.addLayout(main_h_layout)
        overall_layout.addLayout(bottom_v_layout)


    def populate_file_tree(self):
        """Populates the tree view, including .log files."""
        self.model.clear()
        self.item_path_map.clear()
        invisible_root = self.model.invisibleRootItem()
        folder_items = {'': invisible_root} # Maps relative folder path str to QStandardItem

        # Call with include_logs=True so they appear in the tree for selection
        potential_files = get_potential_files_recursively(
            self.script_dir,
            self.script_dir,
            self.script_name,
            include_logs=True
        )

        for rel_path in potential_files:
            if not isinstance(rel_path, Path): continue

            parent_item = invisible_root
            current_path_part_cumulative = Path()

            # Create folder items as needed
            for part in rel_path.parts[:-1]:
                current_path_part_cumulative = current_path_part_cumulative / part
                current_path_part_str = current_path_part_cumulative.as_posix()
                if current_path_part_str not in folder_items:
                    folder_item = QStandardItem(part)
                    folder_item.setIcon(self.folder_icon)
                    folder_item.setEditable(False)
                    folder_item.setCheckable(False) # Folders are not checkable
                    parent_item.appendRow(folder_item)
                    folder_items[current_path_part_str] = folder_item
                    parent_item = folder_item
                else:
                    parent_item = folder_items[current_path_part_str]

            # Insert file item
            file_name = rel_path.name
            file_item = QStandardItem(file_name)
            # Set icon based on suffix
            if rel_path.suffix.lower() == '.log':
                file_item.setIcon(self.log_icon)
            else:
                file_item.setIcon(self.file_icon)

            file_item.setCheckable(True)
            file_item.setCheckState(Qt.CheckState.Checked) # Default to checked
            file_item.setEditable(False)
            file_item.setData(rel_path, PathRole) # Store the Path object
            parent_item.appendRow(file_item)
            self.item_path_map[rel_path.as_posix()] = file_item # Add to map for easy lookup

        self.tree_view.expandToDepth(0) # Expand top-level items


    def iterate_model_items(self, parent_item=None):
        """Generator to recursively yield all items in the model."""
        if parent_item is None: parent_item = self.model.invisibleRootItem()
        for row in range(parent_item.rowCount()):
            item = parent_item.child(row, 0)
            if item:
                yield item
                if item.hasChildren(): yield from self.iterate_model_items(item)

    def count_files_in_model(self):
        """Counts file items using the item_path_map."""
        return len(self.item_path_map)

    @Slot()
    def select_all(self):
        """Checks all file items (leaves) in the tree view."""
        for item in self.item_path_map.values():
            if item.isCheckable(): # Only check files, not folders
                item.setCheckState(Qt.CheckState.Checked)
        self.status_label.setText("All visible files selected (for Step 1b).")

    @Slot()
    def select_none(self):
        """Unchecks all file items (leaves) in the tree view."""
        for item in self.item_path_map.values():
             if item.isCheckable(): # Only uncheck files
                item.setCheckState(Qt.CheckState.Unchecked)
        self.status_label.setText("All visible files deselected (for Step 1b).")

    @Slot()
    def generate_planning_request(self):
        """Generates the Step 0 request file including goal and project code (EXCLUDING .log files)."""
        goal = self.goal_input.toPlainText().strip()
        if not goal:
            QMessageBox.warning(self, "Input Missing", "Please describe your overall goal for Step 0.")
            return

        self.status_label.setText("Gathering project files (excluding .log) for planning request...")
        QApplication.processEvents()

        # Call with include_logs=False for the planning step
        all_potential_files_no_logs = get_potential_files_recursively(
            self.script_dir,
            self.script_dir,
            self.script_name,
            include_logs=False # Explicitly exclude logs here
        )

        if not all_potential_files_no_logs:
             QMessageBox.warning(self, "No Files Found", "No source files (excluding .log) found in the project directory to include in the planning request.")
             self.status_label.setText("Ready.")
             return

        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = self.planning_output_dir
        output_filename = f"planning_request_{timestamp_str}.txt"
        output_file = output_dir / output_filename

        self.status_label.setText(f"Generating {output_filename} in {output_dir.relative_to(self.script_dir)}...")
        QApplication.processEvents()

        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                # Part 1: Goal
                f.write("--- Goal Description ---\n\n")
                f.write(goal)
                f.write("\n\n")

                # Part 2: Instructions
                f.write("--- Instructions for LLM ---\n\n")
                f.write("Based on the goal described above and the complete project source code provided below (excluding .log files), please identify the files that would likely need to be:\n")
                f.write("a) Modified to implement the goal.\n")
                f.write("b) Provided as essential context for understanding the relevant parts of the codebase.\n\n")
                f.write("Please list the relevant file paths **relative to the project root**.\n\n")
                f.write("**Output Format:** Provide the list as a single line of comma-separated file paths. Use forward slashes `/` as path separators.\n\n")
                f.write("Example Output:\nsrc/core/feature.py, src/utils/helpers.py, tests/test_feature.py, config/settings.yaml\n\n")
                f.write("--- End Instructions ---\n\n")

                # Part 3: File Tree
                f.write("<Project File Tree (excluding .log files)>\n")
                sorted_all_files = sorted(all_potential_files_no_logs, key=lambda p: p.as_posix())
                for rel_path in sorted_all_files:
                    f.write(f"- {rel_path.as_posix()}\n")
                f.write("</Project File Tree>\n\n\n")

                # Part 4: Source Code
                f.write("<Project Source Code (excluding .log files)>\n\n")
                for rel_path in sorted_all_files:
                    abs_path = self.script_dir / rel_path
                    rel_path_str = rel_path.as_posix()
                    f.write(f"<file path='{rel_path_str}'>\n")
                    content = read_file_content(abs_path)
                    f.write(content)
                    f.write("\n</file>\n\n")
                f.write("</Project Source Code>\n\n")

                # Part 5: Placeholder
                f.write("--- Identified Files (Provide comma-separated list below) ---\n\n\n")

            relative_output_path = output_file.relative_to(self.script_dir)
            self.status_label.setText(f"Planning request file generated: {relative_output_path}")
            QMessageBox.information(self, "Step 0 Success",
                                    f"Planning request file (excluding .log files) created:\n{relative_output_path}\n\n"
                                    "Please copy its content, paste it into your LLM, and paste the LLM's comma-separated file list output into the 'Step 1a' input box.")

        except Exception as e:
            self.status_label.setText(f"Error generating planning request file: {e}")
            QMessageBox.critical(self, "Step 0 Error", f"Could not generate the planning request file.\nError: {e}")
            print(f"Error details during planning generation: {e}")


    @Slot()
    def apply_suggested_files(self):
        """Parses the suggestion input and updates the tree view selection."""
        suggestions_text = self.suggestion_input.text().strip()
        if not suggestions_text:
            QMessageBox.warning(self, "Input Missing", "Please paste the comma-separated file list from the LLM into the 'Step 1a' input box.")
            return

        try:
            suggested_paths_raw = re.findall(r'[^,\s"]+|"[^"]*"', suggestions_text)
            suggested_paths_raw = [p.strip().strip('"') for p in suggested_paths_raw if p.strip()]
        except Exception as e:
            QMessageBox.warning(self, "Parsing Error", f"Could not parse the file list. Please ensure it's comma-separated.\nError: {e}")
            return

        suggested_paths_normalized = set()
        for p_raw in suggested_paths_raw:
            p_norm = p_raw.replace("\\", "/").strip('/')
            if p_norm:
                 suggested_paths_normalized.add(p_norm)

        if not suggested_paths_normalized:
             QMessageBox.warning(self, "Parsing Error", "Could not parse any valid file paths from the input.")
             return

        self.select_none() # Start by deselecting all for Step 1b

        found_count = 0
        not_found = []
        for norm_path in suggested_paths_normalized:
            item = self.item_path_map.get(norm_path)
            if item and item.isCheckable():
                item.setCheckState(Qt.CheckState.Checked)
                found_count += 1
                parent = item.parent()
                while parent:
                    self.tree_view.expand(self.model.indexFromItem(parent))
                    parent = parent.parent()
            else:
                not_found.append(norm_path)

        status_msg = f"Applied suggestions: {found_count} files selected for Step 1b."
        if not_found:
            status_msg += f" ({len(not_found)} suggested files not found/selectable: {', '.join(not_found[:3])}{'...' if len(not_found) > 3 else ''})"
            print(f"Warning: Suggested files not found/selectable: {', '.join(not_found)}")
            QMessageBox.warning(self, "Partial Match",
                                f"Applied suggestions, but some files suggested by the LLM were not found in the current project structure or are not selectable (e.g., folders):\n\n"
                                f"- {chr(10).join(not_found)}\n\n"
                                f"Please verify the selection in the tree for Step 1b. Note: .log files will only be included if manually checked AND the 'Include .log files' option is enabled below.")
        self.status_label.setText(status_msg)


    @Slot()
    def generate_final_output_file(self):
        """Gathers currently checked files and generates the final output for LLM action,
           optionally including .log files based on the checkbox."""
        goal_text = self.goal_input.toPlainText().strip()
        if not goal_text:
            QMessageBox.warning(self, "Input Missing", "Please ensure the overall goal/task is described in the 'Step 0' box before generating the final action file.")
            return

        include_logs_in_output = self.include_logs_checkbox.isChecked()

        selected_relative_paths = []
        for item in self.item_path_map.values():
            if item.isCheckable() and item.checkState() == Qt.CheckState.Checked:
                rel_path = item.data(PathRole)
                if rel_path:
                    if not include_logs_in_output and rel_path.suffix.lower() == '.log':
                        continue
                    selected_relative_paths.append(rel_path)

        if not selected_relative_paths:
            msg = "Please select at least one file (either manually or by applying suggestions) before executing Step 1b."
            if not include_logs_in_output:
                 msg += "\nNote: .log files are currently excluded based on the checkbox setting."
            QMessageBox.warning(self, "No Files Selected", msg)
            return

        selected_mode_key = None
        for key, button in self.mode_buttons.items():
            if button.isChecked(): selected_mode_key = key; break
        if not selected_mode_key:
             QMessageBox.critical(self, "Error", "No final action mode (Step 1b) selected.")
             return
        selected_mode = MODES[selected_mode_key]

        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = self.action_output_dir
        project_folder_name = self.script_dir.name
        log_status_tag = "_inclLogs" if include_logs_in_output else "_exclLogs"
        output_filename = f"action_{project_folder_name}_{selected_mode_key}{log_status_tag}_{timestamp_str}.txt"
        output_file = output_dir / output_filename

        status_prefix = "Including" if include_logs_in_output else "Excluding"
        self.status_label.setText(f"{status_prefix} .log files. Generating final action file: {output_filename} in {output_dir.relative_to(self.script_dir)}...")
        QApplication.processEvents()

        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                # Goal
                f.write('<goal or issue to address>\n')
                f.write(goal_text)
                f.write('\n</goal or issue to address>\n\n\n')

                # Instruction
                f.write('<output instruction>\n')
                f.write(selected_mode["output_instruction"])
                f.write('\n</output instruction>\n\n\n')

                # File Tree
                f.write("<Tree of Included Files>\n")
                sorted_rel_paths = sorted(selected_relative_paths, key=lambda p: p.as_posix())
                for rel_path in sorted_rel_paths:
                    f.write(f"- {rel_path.as_posix()}\n")
                if not include_logs_in_output:
                     f.write("\n(Note: .log files were excluded from this list based on user setting)\n")
                f.write("</Tree of Included Files>\n\n\n")

                # Code
                f.write("<Concatenated Source Code>\n\n")
                for rel_path in sorted_rel_paths:
                    abs_path = self.script_dir / rel_path
                    rel_path_str = rel_path.as_posix()
                    f.write(f"<file path='{rel_path_str}'>\n")
                    content = read_file_content(abs_path)
                    f.write(content)
                    f.write("\n</file>\n\n")
                f.write("</Concatenated Source Code>")

            relative_output_path = output_file.relative_to(self.script_dir)
            self.status_label.setText(f"Successfully generated final action file: {relative_output_path}")
            QMessageBox.information(self, "Step 1b Success",
                                    f"Final concatenated file for LLM action created:\n{relative_output_path}\n\n"
                                    "Copy the content, paste into the LLM, then paste the LLM's response into the 'Step 2' box below.")

        except Exception as e:
            self.status_label.setText(f"Error generating final action file: {e}")
            QMessageBox.critical(self, "Step 1b Error", f"Could not generate the final action file.\nError: {e}")
            print(f"Error details during final generation: {e}")

    # --- NEW SLOT ---
    @Slot()
    def apply_llm_changes(self):
        """Parses the LLM response from the Step 2 input and applies changes to project files."""
        llm_response = self.llm_response_input.toPlainText().strip()
        if not llm_response:
            QMessageBox.warning(self, "Input Missing", "Please paste the LLM response containing <file> blocks into the 'Step 2' input box.")
            return

        self.status_label.setText("Parsing LLM response for file blocks...")
        QApplication.processEvents()

        try:
            file_blocks = FILE_BLOCK_REGEX.findall(llm_response)
        except Exception as e:
            self.status_label.setText("Error parsing LLM response.")
            QMessageBox.critical(self, "Parsing Error", f"Could not parse the LLM response using regex.\nError: {e}")
            print(f"Regex parsing error: {e}")
            return

        if not file_blocks:
            self.status_label.setText("No file blocks found in the response.")
            QMessageBox.information(self, "No Changes Found", "Could not find any blocks matching the format `<file path='...'>...</file>` in the provided text.")
            return

        self.status_label.setText(f"Found {len(file_blocks)} potential file blocks. Validating paths...")
        QApplication.processEvents()

        valid_changes = []
        skipped_files = []
        project_root_resolved = self.script_dir.resolve()

        for path_str, content in file_blocks:
            # Normalize path separators and remove potential leading/trailing whitespace/slashes
            relative_path_str = path_str.strip().replace("\\", "/").strip('/')
            if not relative_path_str:
                 skipped_files.append(f"(Empty path provided in <file> tag)")
                 continue

            try:
                # Construct absolute path and resolve it (handles .. etc.)
                abs_path = (project_root_resolved / relative_path_str).resolve()

                # --- Security/Validation Checks ---
                # 1. Is it within the project directory?
                if not abs_path.is_relative_to(project_root_resolved):
                    skipped_files.append(f"{relative_path_str} (Path is outside project directory)")
                    print(f"Warning: Skipping file outside project root: {relative_path_str} -> {abs_path}")
                    continue

                # 2. Does the *directory* for the file exist? (We might be creating a new file)
                parent_dir = abs_path.parent
                if not parent_dir.exists():
                     skipped_files.append(f"{relative_path_str} (Parent directory does not exist: {parent_dir.relative_to(project_root_resolved)})")
                     print(f"Warning: Skipping file as parent directory does not exist: {parent_dir}")
                     continue
                if not parent_dir.is_dir():
                    skipped_files.append(f"{relative_path_str} (Parent path is not a directory: {parent_dir.relative_to(project_root_resolved)})")
                    print(f"Warning: Skipping file as parent path is not a directory: {parent_dir}")
                    continue

                # 3. Is the final path a directory itself? (Should be a file)
                if abs_path.is_dir():
                    skipped_files.append(f"{relative_path_str} (Path points to an existing directory, not a file)")
                    print(f"Warning: Skipping path as it points to a directory: {abs_path}")
                    continue

                # If all checks pass, add to valid changes
                # Store the resolved absolute path and the original content
                valid_changes.append({"abs_path": abs_path, "content": content, "rel_path_str": relative_path_str})
                print(f"Validated file for update/creation: {relative_path_str} -> {abs_path}")

            except Exception as e:
                # Catch potential errors during path manipulation/resolution
                skipped_files.append(f"{relative_path_str} (Error processing path: {e})")
                print(f"Error processing path {relative_path_str}: {e}")
                continue

        if not valid_changes:
            self.status_label.setText("No valid file paths found in response.")
            msg = "No valid file paths found within the project structure in the LLM response."
            if skipped_files:
                msg += "\n\nThe following paths were skipped:\n- " + "\n- ".join(skipped_files)
            QMessageBox.warning(self, "No Valid Changes", msg)
            return

        # --- Confirmation Dialog ---
        confirmation_message = f"Found {len(valid_changes)} valid file(s) to apply changes to:\n\n"
        for change in valid_changes:
            rel_path_display = change['rel_path_str']
            status = " (Will be created)" if not change['abs_path'].exists() else " (Will be overwritten)"
            confirmation_message += f"- {rel_path_display}{status}\n"

        confirmation_message += "\nThis action CANNOT be undone. Are you sure you want to proceed?"

        if skipped_files:
             confirmation_message += f"\n\nNote: {len(skipped_files)} path(s) mentioned in the response were skipped (invalid, outside project, etc.)."

        reply = QMessageBox.question(self, "Confirm Changes", confirmation_message,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.No:
            self.status_label.setText("Changes cancelled by user.")
            return

        # --- Apply Changes ---
        self.status_label.setText(f"Applying changes to {len(valid_changes)} file(s)...")
        QApplication.processEvents()

        success_count = 0
        failed_files = []

        for change in valid_changes:
            abs_path = change["abs_path"]
            content = change["content"]
            rel_path_str = change["rel_path_str"]
            try:
                # Ensure parent directory exists (redundant check, but safe)
                abs_path.parent.mkdir(parents=True, exist_ok=True)
                # Write the content (overwrites if exists, creates if not)
                with open(abs_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                success_count += 1
                print(f"Successfully wrote changes to: {rel_path_str}")
            except IOError as e:
                failed_files.append(f"{rel_path_str} (IOError: {e})")
                print(f"Error writing file {rel_path_str}: {e}")
            except Exception as e:
                failed_files.append(f"{rel_path_str} (Error: {e})")
                print(f"Unexpected error writing file {rel_path_str}: {e}")

        # --- Final Report ---
        final_message = f"Applied changes: {success_count} file(s) updated/created successfully."
        if failed_files:
            final_message += f"\n\nFailed to update {len(failed_files)} file(s):\n- " + "\n- ".join(failed_files)
            QMessageBox.warning(self, "Partial Success", final_message)
        else:
            QMessageBox.information(self, "Success", final_message)

        if skipped_files:
             final_message += f"\n({len(skipped_files)} skipped paths)"

        self.status_label.setText(final_message)

        # Optional: Refresh the file tree view?
        # self.populate_file_tree() # Might be slow for large projects


# --- Main Execution ---
if __name__ == "__main__":
    # Determine script directory and name
    if getattr(sys, 'frozen', False):
        application_path = Path(sys.executable).parent
        script_name = Path(sys.executable).name
    else:
        application_path = Path(__file__).parent
        script_name = Path(__file__).name

    script_dir_abs = application_path.resolve()

    # --- Qt Application Setup ---
    app = QApplication(sys.argv)
    window = ScriptAggregatorApp(script_dir=script_dir_abs, script_name=script_name)
    window.show()
    sys.exit(app.exec())