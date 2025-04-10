# --- COMPLETE UPDATED SCRIPT ---

import sys
import os
from pathlib import Path
from datetime import datetime
import re # For parsing comma-separated list robustly AND file blocks
import shutil # For file copying
import tempfile # For temporary directory
import traceback # For detailed error printing

# --- Try importing PySide6 ---
try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtCore import Qt, Slot
    from PySide6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QTreeView, QLabel, QRadioButton, QGroupBox,
        QMessageBox, QFrame, QTextEdit, QLineEdit, QCheckBox,
        QScrollArea # <-- Import QScrollArea
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
# Regex to find <file path='...'>...</file> blocks.
# Handles potential code fences (```) within the content block because:
# - `.*?` is non-greedy, matching up to the *first* `</file>`.
# - `re.DOTALL` makes `.` match newline characters.
# - `re.IGNORECASE` allows `<file>` or `<FILE>`.
FILE_BLOCK_REGEX = re.compile(
    r"<file\s+path=['\"](.*?)['\"]\s*>(.*?)</file>",
    re.DOTALL | re.IGNORECASE
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
        # This is now expected when reading a backup of a newly created file during undo test
        # print(f"Info: File not found during read (might be expected): {file_path}")
        return None # Return None to indicate it didn't exist or couldn't be read
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return f"--- ERROR READING FILE ---\nPath: {file_path}\nError: {str(e)}\n--- END ERROR ---"

def get_potential_files_recursively(current_directory, original_root_dir, script_name, include_logs=False):
    """
    Recursively get potential files relative to the original_root_dir,
    excluding specified types and patterns. Returns relative paths.
    """
    potential_files = []
    current_directory_path = Path(current_directory).resolve()
    original_root_dir_resolved = original_root_dir.resolve()

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
            # Handle potential symlinks carefully - resolve first
            try:
                item_abs_path = item.resolve()
            except OSError as e:
                print(f"Warning: Could not resolve path {item}, possibly broken symlink: {e}. Skipping.")
                continue

            try:
                # Ensure the item is actually within the project root before proceeding
                if not item_abs_path.is_relative_to(original_root_dir_resolved):
                     continue
                relative_path = item_abs_path.relative_to(original_root_dir_resolved)
                relative_path_str = relative_path.as_posix()
            except ValueError:
                print(f"Warning: Could not get relative path for {item_abs_path} against {original_root_dir_resolved}. Skipping.")
                continue
            except Exception as e:
                print(f"Warning: Error during relative path calculation for {item}: {e}. Skipping.")
                continue

            # --- Exclusions ---
            if item.name == script_name: continue
            if item.name.startswith('.') and item.name != '.scripts': continue
            if item.name in ['.venv', 'venv', 'env', '__pycache__', 'node_modules', 'dist', 'build', OUTPUT_BASE_DIR_NAME, '.git'] or \
               item.name.startswith('concatignore') or \
               item.name.startswith('archive') or \
               item.name.startswith('planning_and_focus_window') or \
               item.name.startswith('planning_request_') or \
               item.name.startswith('concat_'):
                continue
            if item.is_dir() and item.name == 'docs' and 'scripts' not in relative_path_str.split('/'): continue

            # --- File processing ---
            if item.is_file():
                excluded_suffixes = [
                    '.xlsx', '.xls', '.csv', '.data', '.db', '.sqlite', '.sqlite3',
                    '.pkl', '.joblib', '.h5', '.hdf5',
                    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.ico',
                    '.pdf', '.doc', '.docx', '.ppt', '.pptx',
                    '.zip', '.gz', '.tar', '.rar',
                    '.exe', '.dll', '.so', '.o', '.a', '.lib',
                    '.pyc', '.pyd', '.pyo',
                    '.swp', '.swo', '.json'
                ]
                # Use Path.suffix for reliable extension checking
                file_suffix = item.suffix.lower()
                if file_suffix == '.log' and not include_logs:
                    continue
                if file_suffix in excluded_suffixes:
                    continue
                if relative_path not in potential_files:
                    potential_files.append(relative_path)

            # --- Directory processing ---
            elif item.is_dir():
                potential_files.extend(get_potential_files_recursively(item_abs_path, original_root_dir_resolved, script_name, include_logs))

    except FileNotFoundError: print(f"Warning: Directory not found during scan: {current_directory_path}. Skipping.")
    except PermissionError: print(f"Warning: Permission denied for directory: {current_directory_path}. Skipping.")
    except Exception as e: print(f"Error scanning directory {current_directory_path}: {e}")

    return sorted(list(dict.fromkeys(potential_files)), key=lambda p: p.as_posix())


# --- Mode Definitions (Unchanged) ---
MODES = {
    "debug": {
        "name": "Debug Mode",
        "issue_placeholder": "<Describe the bug or unexpected behavior observed>\n\n\n",
        "output_instruction": (
            "1) Reflect on 5-7 different possible sources of the problem based on the code provided and the goal/issue description.\n"
            "2) Distill those down to the most likely root cause.\n"
            "3) Provide the COMPLETE UPDATED VERSION of *only* the files that need changes to fix the likely root cause.\n"
            "   Use the format: <file path='relative/path/to/file.ext'>\n[COMPLETE FILE CONTENT]\n</file>\n"
        )
    },
    "add_feature": {
        "name": "Add New Feature",
        "issue_placeholder": "<Describe the new feature or enhancement required>\n\n\n",
        "output_instruction": (
            "1) Explain if this is already complete, or what is missing\n"
            "2) Provide the COMPLETE code for any NEW files needed.\n"
            "3) Provide the COMPLETE UPDATED VERSION of any EXISTING files that need changes.\n"
            "   Use the format: <file path='relative/path/to/file.ext'>\n[COMPLETE FILE CONTENT]\n</file>\n for both new and updated files."
        )
    },
    "explain": {
        "name": "Explain / Brainstorm",
        "issue_placeholder": "<Ask a question about the code, request an explanation, or describe a concept to brainstorm>\n\n\n",
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
        self.script_dir = Path(script_dir).resolve()
        self.script_name = script_name
        self.folder_icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DirIcon)
        self.file_icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileIcon)
        self.log_icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileIcon) # Using file icon for logs too
        self.model = QStandardItemModel()
        self.tree_view = QTreeView()
        self.status_label = QLabel("Ready. Scanning for files...")
        self.mode_buttons = {}
        self.goal_input = QTextEdit()
        self.suggestion_input = QLineEdit()
        self.include_logs_checkbox = QCheckBox("Include selected .log files in Step 1b output")
        self.llm_response_input = QTextEdit()
        self.item_path_map = {}

        # --- Undo State ---
        self.last_applied_changes = [] # List to store info about the last applied changes
        self.temp_backup_dir = None # Path to the temporary backup directory for the last apply

        # --- Define output directories relative to script_dir ---
        self.output_base_dir = self.script_dir / OUTPUT_BASE_DIR_NAME
        self.planning_output_dir = self.output_base_dir / PLANNING_SUBDIR_NAME
        self.action_output_dir = self.output_base_dir / ACTION_SUBDIR_NAME

        self.initUI()
        self.populate_file_tree()
        file_count = self.count_files_in_model()
        self.status_label.setText(f"Ready. Found {file_count} potential files (including .log).")


    def initUI(self):
        self.setWindowTitle("Script Aggregator & Applier (with Undo)")
        self.setGeometry(150, 150, 1050, 800) # Adjusted initial height slightly

        # --- Main Horizontal Layout (will go inside scroll area) ---
        main_h_layout = QHBoxLayout()
        left_v_layout = QVBoxLayout()
        right_v_layout = QVBoxLayout()
        right_v_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Keep controls aligned top

        # --- Left Side: File Tree ---
        tree_header_label = QLabel("Files in Project (Checkboxes for Step 1b):")
        font = tree_header_label.font(); font.setBold(True); tree_header_label.setFont(font)
        self.tree_view.setModel(self.model)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        # Set minimum height for tree view to prevent it collapsing too much
        self.tree_view.setMinimumHeight(400)
        left_v_layout.addWidget(tree_header_label)
        left_v_layout.addWidget(self.tree_view)
        left_v_layout.addStretch(1) # Add stretch to push tree up if space allows

        # --- Right Side: Controls ---
        # Step 0
        step0_groupbox = QGroupBox("Step 0: Generate Planning Request (excludes .log files)")
        step0_layout = QVBoxLayout()
        step0_layout.addWidget(QLabel("Describe your overall goal or task:"))
        self.goal_input.setPlaceholderText("e.g., Refactor the database connection logic...")
        self.goal_input.setMinimumHeight(60)
        self.goal_input.setMaximumHeight(150) # Limit max height
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
        self.suggestion_input.setPlaceholderText("e.g., src/db.py, src/auth/jwt.py,...")
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
        mode_groupbox = QGroupBox("Step 1b: Select Action Mode & Generate Action Prompt")
        mode_layout = QVBoxLayout()
        first_mode_key = list(MODES.keys())[0]
        for key, mode_info in MODES.items():
            rb = QRadioButton(mode_info["name"])
            self.mode_buttons[key] = rb
            if key == first_mode_key: rb.setChecked(True)
            mode_layout.addWidget(rb)
        mode_layout.addWidget(self.include_logs_checkbox)
        self.include_logs_checkbox.setChecked(False)
        self.generate_button = QPushButton("Execute Step 1b: Generate Concatenated File for LLM Action")
        self.generate_button.clicked.connect(self.generate_final_output_file)
        mode_layout.addWidget(self.generate_button)
        mode_groupbox.setLayout(mode_layout)
        right_v_layout.addWidget(mode_groupbox)

        # Step 2 Apply Changes
        step2_groupbox = QGroupBox("Step 2: Apply LLM Changes")
        step2_layout = QVBoxLayout()
        step2_layout.addWidget(QLabel("Paste the LLM response containing <file> blocks below:"))
        self.llm_response_input.setPlaceholderText("<file path='relative/path/to/file.ext'>\n[COMPLETE FILE CONTENT]\n</file>\n...")
        self.llm_response_input.setMinimumHeight(150)
        self.llm_response_input.setMaximumHeight(300) # Limit max height
        self.llm_response_input.setAcceptRichText(False)
        step2_layout.addWidget(self.llm_response_input)
        apply_undo_layout = QHBoxLayout()
        self.apply_changes_button = QPushButton("Parse and Apply Changes to Project Files")
        self.apply_changes_button.clicked.connect(self.apply_llm_changes)
        self.undo_button = QPushButton("Undo Last Apply")
        self.undo_button.clicked.connect(self.undo_last_apply)
        self.undo_button.setEnabled(False)
        apply_undo_layout.addWidget(self.apply_changes_button, 2)
        apply_undo_layout.addWidget(self.undo_button, 1)
        step2_layout.addLayout(apply_undo_layout)
        step2_groupbox.setLayout(step2_layout)
        right_v_layout.addWidget(step2_groupbox)

        # Add stretch to the bottom of the right layout if needed,
        # but AlignTop should handle most cases.
        # right_v_layout.addStretch(1)

        # Assemble Main Horizontal Layout
        left_widget = QWidget(); left_widget.setLayout(left_v_layout)
        right_widget = QWidget(); right_widget.setLayout(right_v_layout)
        main_h_layout.addWidget(left_widget, 3) # Ratio 3 for left
        main_h_layout.addWidget(right_widget, 4) # Ratio 4 for right

        # --- Create a container widget for the main horizontal layout ---
        main_content_widget = QWidget()
        main_content_widget.setLayout(main_h_layout)

        # --- Create Scroll Area and add the main content widget to it ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True) # Crucial for layout to expand
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded) # Also allow horizontal if needed
        scroll_area.setWidget(main_content_widget)

        # --- Bottom Area (Status Bar) ---
        bottom_v_layout = QVBoxLayout()
        self.status_label.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        self.status_label.setLineWidth(1)
        # Ensure status label doesn't stretch vertically
        bottom_v_layout.addWidget(self.status_label)
        bottom_v_layout.addStretch(0) # Prevent stretch

        # --- Overall Layout ---
        overall_layout = QVBoxLayout(self) # Set layout ON the main window (self)
        # Add the scroll area (containing the main content)
        overall_layout.addWidget(scroll_area, 1) # Give scroll area stretch factor 1
        # Add the status bar layout (fixed height)
        overall_layout.addLayout(bottom_v_layout, 0) # Give status bar stretch factor 0

    def populate_file_tree(self):
        """Populates the tree view, including .log files."""
        self.model.clear()
        self.item_path_map.clear()
        invisible_root = self.model.invisibleRootItem()
        folder_items = {'': invisible_root}

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

            for part in rel_path.parts[:-1]:
                current_path_part_cumulative = current_path_part_cumulative / part
                current_path_part_str = current_path_part_cumulative.as_posix()
                if current_path_part_str not in folder_items:
                    folder_item = QStandardItem(part)
                    folder_item.setIcon(self.folder_icon)
                    folder_item.setEditable(False)
                    folder_item.setCheckable(False) # Folders not checkable
                    parent_item.appendRow(folder_item)
                    folder_items[current_path_part_str] = folder_item
                    parent_item = folder_item
                else:
                    parent_item = folder_items[current_path_part_str]

            file_name = rel_path.name
            file_item = QStandardItem(file_name)
            # Use Path.suffix for reliable extension checking
            if rel_path.suffix.lower() == '.log':
                file_item.setIcon(self.log_icon)
            else:
                file_item.setIcon(self.file_icon)

            file_item.setCheckable(True)
            file_item.setCheckState(Qt.CheckState.Checked) # Default to checked
            file_item.setEditable(False)
            file_item.setData(rel_path, PathRole)
            parent_item.appendRow(file_item)
            self.item_path_map[rel_path.as_posix()] = file_item

        self.tree_view.expandToDepth(0)

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
            if item.isCheckable():
                item.setCheckState(Qt.CheckState.Checked)
        self.status_label.setText("All visible files selected (for Step 1b).")

    @Slot()
    def select_none(self):
        """Unchecks all file items (leaves) in the tree view."""
        for item in self.item_path_map.values():
             if item.isCheckable():
                item.setCheckState(Qt.CheckState.Unchecked)
        self.status_label.setText("All visible files deselected (for Step 1b).")

    @Slot()
    def generate_planning_request(self):
        """Generates the Step 0 request file (excluding .log files)."""
        goal = self.goal_input.toPlainText().strip()
        if not goal:
            QMessageBox.warning(self, "Input Missing", "Please describe your overall goal for Step 0.")
            return

        self.status_label.setText("Gathering project files (excluding .log) for planning request...")
        QApplication.processEvents()

        all_potential_files_no_logs = get_potential_files_recursively(
            self.script_dir, self.script_dir, self.script_name, include_logs=False
        )

        if not all_potential_files_no_logs:
             QMessageBox.warning(self, "No Files Found", "No source files (excluding .log) found for planning request.")
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
                # --- Content for Planning Request ---
                f.write("--- Goal Description ---\n\n")
                f.write(goal + "\n\n")
                f.write("--- Instructions for LLM ---\n\n")
                f.write("Based on the goal described above and the provided project context (file tree and source code below), identify the key files that likely need to be created, modified, or consulted to achieve the goal.\n\n")
                f.write("Please provide the list of relevant file paths as a single line, comma-separated string. Include only relative paths from the project root.\n\n")
                f.write("Example Output:\n")
                f.write("src/core/feature.py, src/utils/helpers.py, tests/test_feature.py, README.md\n\n")
                f.write("--- End Instructions ---\n\n")

                f.write("<Project File Tree (excluding .log files)>\n")
                sorted_all_files = sorted(all_potential_files_no_logs, key=lambda p: p.as_posix())
                for rel_path in sorted_all_files:
                    f.write(f"- {rel_path.as_posix()}\n")
                f.write("</Project File Tree>\n\n\n")

                f.write("<Project Source Code (excluding .log files)>\n\n")
                for rel_path in sorted_all_files:
                    abs_path = self.script_dir / rel_path
                    rel_path_str = rel_path.as_posix()
                    f.write(f"<file path='{rel_path_str}'>\n")
                    content = read_file_content(abs_path)
                    if content is not None:
                        f.write(content) # Check if read was successful
                    else:
                        f.write(f"--- Error reading file: {rel_path_str} ---")
                    f.write("\n</file>\n\n")
                f.write("</Project Source Code>\n\n")

                f.write("--- Identified Files (Provide comma-separated list below) ---\n\n\n")

            relative_output_path = output_file.relative_to(self.script_dir)
            self.status_label.setText(f"Planning request file generated: {relative_output_path}")
            QMessageBox.information(self, "Step 0 Success", f"Planning request file created:\n{relative_output_path}\n\nPaste this entire file content into the LLM to get the list of files for Step 1a.")

        except Exception as e:
            self.status_label.setText(f"Error generating planning request file: {e}")
            QMessageBox.critical(self, "Step 0 Error", f"Could not generate planning request file.\nError: {e}")
            print(f"Error details during planning generation:")
            traceback.print_exc()


    @Slot()
    def apply_suggested_files(self):
        """Parses the suggestion input and updates the tree view selection."""
        suggestions_text = self.suggestion_input.text().strip()
        if not suggestions_text:
            QMessageBox.warning(self, "Input Missing", "Please paste the comma-separated file list from the LLM.")
            return

        # Robust parsing of comma-separated list, handling quotes and whitespace
        try:
            # Find non-comma/whitespace sequences or quoted sequences
            suggested_paths_raw = re.findall(r'[^,\s"]+|"[^"]*"', suggestions_text)
            # Strip whitespace and quotes from each found part
            suggested_paths_raw = [p.strip().strip('"').strip() for p in suggested_paths_raw if p.strip()]
        except Exception as e:
            QMessageBox.warning(self, "Parsing Error", f"Could not parse file list.\nError: {e}")
            return

        # Normalize paths (use forward slashes, remove leading/trailing slashes)
        suggested_paths_normalized = set()
        for p_raw in suggested_paths_raw:
            p_norm = p_raw.replace("\\", "/").strip('/')
            if p_norm: # Ensure it's not empty after normalization
                suggested_paths_normalized.add(p_norm)

        if not suggested_paths_normalized:
             QMessageBox.warning(self, "Parsing Error", "Could not parse valid file paths from the input.")
             return

        self.select_none() # Start by deselecting all
        found_count = 0
        not_found = []

        # Apply suggestions to the tree view
        for norm_path in suggested_paths_normalized:
            item = self.item_path_map.get(norm_path)
            if item and item.isCheckable():
                item.setCheckState(Qt.CheckState.Checked)
                found_count += 1
                # Expand parent nodes to make the selected item visible
                parent = item.parent()
                while parent and parent != self.model.invisibleRootItem():
                    self.tree_view.expand(self.model.indexFromItem(parent))
                    parent = parent.parent()
            else:
                not_found.append(norm_path)

        # Report results
        status_msg = f"Applied suggestions: {found_count} files selected."
        if not_found:
            status_msg += f" ({len(not_found)} not found/selectable: {', '.join(not_found[:3])}{'...' if len(not_found) > 3 else ''})"
            print(f"Warning: Suggested files not found/selectable: {', '.join(not_found)}")
            QMessageBox.warning(self, "Partial Match", f"Applied suggestions, but some files were not found or are not selectable (e.g., directories):\n\n- {chr(10).join(not_found)}\n\nCheck the selection in the tree view.")
        elif found_count > 0:
             QMessageBox.information(self, "Suggestions Applied", f"Successfully selected {found_count} file(s) based on the provided list.")
        else:
             QMessageBox.warning(self, "No Matches", "None of the suggested files were found or selectable in the project tree.")

        self.status_label.setText(status_msg)


    @Slot()
    def generate_final_output_file(self):
        """Generates the final output file for LLM action."""
        goal_text = self.goal_input.toPlainText().strip()
        if not goal_text:
            QMessageBox.warning(self, "Input Missing", "Please ensure the overall goal is described in Step 0.")
            return

        include_logs_in_output = self.include_logs_checkbox.isChecked()
        selected_relative_paths = []
        # Iterate through the map which only contains file items
        for item in self.item_path_map.values():
            if item.isCheckable() and item.checkState() == Qt.CheckState.Checked:
                rel_path = item.data(PathRole)
                if rel_path and isinstance(rel_path, Path): # Ensure it's a Path object
                    # Skip .log files if checkbox is unchecked
                    if not include_logs_in_output and rel_path.suffix.lower() == '.log':
                        continue
                    selected_relative_paths.append(rel_path)
                elif rel_path:
                    print(f"Warning: Item data is not a Path object for item '{item.text()}'") # Debugging
                # else: # No PathRole data - should not happen for items in map
                #    print(f"Warning: Item '{item.text()}' has no PathRole data.")

        if not selected_relative_paths:
            msg = "Please select at least one file in the tree view before executing Step 1b."
            if not include_logs_in_output:
                msg += "\nNote: .log files are currently excluded based on the checkbox setting. Ensure other files are selected."
            QMessageBox.warning(self, "No Files Selected", msg)
            return

        selected_mode_key = None
        for key, button in self.mode_buttons.items():
            if button.isChecked():
                selected_mode_key = key
                break
        if not selected_mode_key:
             # Should not happen if one is checked by default, but good practice
             QMessageBox.critical(self, "Error", "No action mode (Step 1b) selected.")
             return
        selected_mode = MODES[selected_mode_key]

        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = self.action_output_dir
        project_folder_name = self.script_dir.name # Get project folder name
        log_status_tag = "_inclLogs" if include_logs_in_output else "_exclLogs"
        # Construct filename: action_PROJECTNAME_MODE_LOGSTATUS_TIMESTAMP.txt
        output_filename = f"action_{project_folder_name}_{selected_mode_key}{log_status_tag}_{timestamp_str}.txt"
        output_file = output_dir / output_filename

        status_prefix = "Including" if include_logs_in_output else "Excluding"
        self.status_label.setText(f"{status_prefix} .log files. Generating action file: {output_filename}...")
        QApplication.processEvents() # Update UI

        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                # --- Content for Action Prompt ---
                f.write('<goal or issue to address>\n')
                f.write(goal_text + '\n')
                f.write('</goal or issue to address>\n\n\n')

                f.write('<output instruction>\n')
                f.write(selected_mode["output_instruction"] + '\n')
                f.write('</output instruction>\n\n\n')

                f.write("<Tree of Included Files>\n")
                sorted_rel_paths = sorted(selected_relative_paths, key=lambda p: p.as_posix())
                for rel_path in sorted_rel_paths:
                    f.write(f"- {rel_path.as_posix()}\n")

                # Check if any log files EXIST in the project (using the map values)
                # and if they were excluded by the checkbox setting.
                log_files_exist_in_project = any(
                    item.data(PathRole).suffix.lower() == '.log'
                    for item in self.item_path_map.values()
                    if item.data(PathRole) and isinstance(item.data(PathRole), Path) # Check data exists and is Path
                )

                if not include_logs_in_output and log_files_exist_in_project:
                     # Add note only if logs exist in the project but were excluded by the checkbox
                     f.write("\n(Note: .log files were present but excluded from this context based on selection.)\n")

                f.write("</Tree of Included Files>\n\n\n")

                f.write("<Concatenated Source Code>\n\n")
                for rel_path in sorted_rel_paths:
                    abs_path = self.script_dir / rel_path
                    rel_path_str = rel_path.as_posix()
                    f.write(f"<file path='{rel_path_str}'>\n")
                    content = read_file_content(abs_path)
                    if content is not None:
                        f.write(content)
                    else:
                         f.write(f"--- Error reading file: {rel_path_str} ---")
                    f.write("\n</file>\n\n") # Add a newline before closing tag for clarity
                f.write("</Concatenated Source Code>")

            relative_output_path = output_file.relative_to(self.script_dir)
            self.status_label.setText(f"Successfully generated action file: {relative_output_path}")
            QMessageBox.information(self, "Step 1b Success", f"Action file created:\n{relative_output_path}\n\nPaste this entire file content into the LLM, then paste the LLM's response into the Step 2 input box below.")

        except Exception as e:
            self.status_label.setText(f"Error generating action file: {e}")
            QMessageBox.critical(self, "Step 1b Error", f"Could not generate action file.\nError: {e}")
            # Print detailed error including traceback for debugging
            print(f"Error details during final generation:")
            traceback.print_exc()


    @Slot()
    def apply_llm_changes(self):
        """Parses LLM response, creates backups, applies changes, and enables Undo."""
        llm_response = self.llm_response_input.toPlainText().strip()
        if not llm_response:
            QMessageBox.warning(self, "Input Missing", "Please paste the LLM response into the 'Step 2' input box.")
            return

        # --- Clear previous undo state ---
        self._cleanup_backup_dir() # Remove any old temp dir first
        self.last_applied_changes = []
        self.undo_button.setEnabled(False)

        self.status_label.setText("Parsing LLM response...")
        QApplication.processEvents()

        try:
            # Use the pre-compiled regex to find all file blocks
            file_blocks = FILE_BLOCK_REGEX.findall(llm_response)
        except Exception as e:
            # Regex errors are unlikely but possible with complex patterns
            self.status_label.setText("Error parsing LLM response.")
            QMessageBox.critical(self, "Parsing Error", f"Could not parse response using regex.\nError: {e}")
            return

        if not file_blocks:
            self.status_label.setText("No file blocks found.")
            QMessageBox.information(self, "No Changes Found", "No `<file path='...'>...</file>` blocks found in the Step 2 input.")
            return

        self.status_label.setText(f"Found {len(file_blocks)} file blocks. Validating paths...")
        QApplication.processEvents()

        valid_changes_to_confirm = []
        skipped_files = []
        project_root_resolved = self.script_dir.resolve()

        for path_str, content in file_blocks:
            # Normalize path extracted from regex group 1
            relative_path_str = path_str.strip().replace("\\", "/").strip('/')
            if not relative_path_str:
                 skipped_files.append("(Empty path provided in <file> tag)")
                 continue

            try:
                # Resolve the absolute path safely
                abs_path = (project_root_resolved / relative_path_str).resolve()

                # --- Security/Validation Checks ---
                # 1. Ensure path stays within the project directory
                if not abs_path.is_relative_to(project_root_resolved):
                    skipped_files.append(f"{relative_path_str} (Path is outside project directory)")
                    print(f"Security Warning: Skipping path outside project root: {abs_path}")
                    continue

                # 2. Check if parent directory exists and is actually a directory
                parent_dir = abs_path.parent
                # Allow creation of parent dirs later, but check if *existing* parent is a file
                if parent_dir.exists() and not parent_dir.is_dir():
                     skipped_files.append(f"{relative_path_str} (Parent path exists but is a file)")
                     print(f"Error: Cannot write file {relative_path_str}, parent path {parent_dir} is a file.")
                     continue

                # 3. Check if the target path itself is an existing directory
                if abs_path.is_dir():
                    skipped_files.append(f"{relative_path_str} (Path points to an existing directory)")
                    print(f"Error: Cannot overwrite directory with file: {relative_path_str}")
                    continue

                # If all checks pass, add to list for confirmation
                # Content comes directly from regex group 2
                valid_changes_to_confirm.append({
                    "abs_path": abs_path,
                    "content": content, # Use content directly as captured by regex
                    "rel_path_str": relative_path_str
                })

            except Exception as e:
                # Catch potential errors during path resolution or checks
                skipped_files.append(f"{relative_path_str} (Validation Error: {e})")
                print(f"Error validating path {relative_path_str}: {e}")
                continue

        if not valid_changes_to_confirm:
            self.status_label.setText("No valid file paths found after validation.")
            msg = "No valid file changes found in the response after validation."
            if skipped_files:
                msg += "\n\nSkipped paths:\n- " + "\n- ".join(skipped_files)
            QMessageBox.warning(self, "No Valid Changes", msg)
            return

        # --- Confirmation Dialog ---
        confirmation_message = f"Found {len(valid_changes_to_confirm)} valid file change(s) to apply:\n\n"
        for change in valid_changes_to_confirm:
            rel_path_display = change['rel_path_str']
            status = " (Will be created)" if not change['abs_path'].exists() else " (Will be overwritten)"
            confirmation_message += f"- {rel_path_display}{status}\n"

        confirmation_message += "\nBackups will be created in a temporary directory for overwritten files.\n\nProceed with applying these changes?"

        if skipped_files:
             # Show skipped files in a scrollable text box within the message box if there are many
             if len(skipped_files) > 5:
                  detailed_skipped = "\n\nSkipped paths:\n" + "\n".join(f"- {s}" for s in skipped_files)
                  msg_box = QMessageBox(self)
                  msg_box.setIcon(QMessageBox.Icon.Question)
                  msg_box.setWindowTitle("Confirm Changes")
                  msg_box.setText(confirmation_message + f"\n\nNote: {len(skipped_files)} path(s) were skipped (see details).")
                  msg_box.setDetailedText(detailed_skipped)
                  msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                  msg_box.setDefaultButton(QMessageBox.StandardButton.No)
                  reply = msg_box.exec()
             else:
                  confirmation_message += f"\n\nNote: {len(skipped_files)} path(s) skipped:\n- " + "\n- ".join(skipped_files)
                  reply = QMessageBox.question(self, "Confirm Changes", confirmation_message,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        else:
             reply = QMessageBox.question(self, "Confirm Changes", confirmation_message,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)


        if reply != QMessageBox.StandardButton.Yes: # Check for explicit Yes
            self.status_label.setText("Changes cancelled by user.")
            return

        # --- Create Backup Directory ---
        try:
            # Create a unique temporary directory for this operation's backups
            self.temp_backup_dir = Path(tempfile.mkdtemp(prefix="script_aggregator_undo_"))
            print(f"Created temporary backup directory: {self.temp_backup_dir}")
        except Exception as e:
            self.status_label.setText("Error creating backup directory.")
            QMessageBox.critical(self, "Backup Error", f"Could not create temporary backup directory.\nError: {e}")
            self.temp_backup_dir = None # Ensure it's None if creation failed
            return

        # --- Apply Changes & Create Backups ---
        self.status_label.setText(f"Applying changes to {len(valid_changes_to_confirm)} file(s)...")
        QApplication.processEvents()

        success_count = 0
        failed_files = []
        self.last_applied_changes = [] # Reset just before applying

        for change in valid_changes_to_confirm:
            abs_path = change["abs_path"]
            content = change["content"] # Use the raw captured content
            rel_path_str = change["rel_path_str"]
            backup_path = None
            was_created = False

            try:
                # --- Backup Logic ---
                if abs_path.exists():
                    # File exists, create backup before overwriting
                    # Sanitize rel_path_str for use in filename (replace slashes)
                    safe_filename_part = rel_path_str.replace('/', '_').replace('\\', '_')
                    backup_filename = f"{safe_filename_part}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.bak"
                    backup_path = self.temp_backup_dir / backup_filename
                    shutil.copy2(abs_path, backup_path) # copy2 preserves metadata
                    print(f"Backed up '{rel_path_str}' to '{backup_path.name}' in temp dir")
                    was_created = False
                else:
                    # File doesn't exist, will be created
                    was_created = True
                    backup_path = None # No backup needed for created files

                # --- Write File ---
                # Ensure parent directory exists before writing
                abs_path.parent.mkdir(parents=True, exist_ok=True)
                with open(abs_path, 'w', encoding='utf-8') as f:
                    # Write the content exactly as captured by the regex
                    # This includes any leading/trailing whitespace or code fences (```)
                    # that were between the <file> tags in the LLM response.
                    f.write(content)

                # --- Record Change for Undo ---
                self.last_applied_changes.append({
                    "original_path": abs_path,
                    "backup_path": backup_path, # Will be None if created
                    "was_created": was_created
                })
                success_count += 1
                action = "Created" if was_created else "Overwritten"
                print(f"Successfully {action}: {rel_path_str}")

            except (IOError, OSError, shutil.Error) as e:
                failed_files.append(f"{rel_path_str} (Write/Backup Error: {e})")
                print(f"Error processing file {rel_path_str}: {e}")
                # Attempt to rollback this specific file if backup exists? (Could get complex, skip for now)
            except Exception as e:
                # Catch any other unexpected errors during file processing
                failed_files.append(f"{rel_path_str} (Unexpected Error: {e})")
                print(f"Unexpected error processing file {rel_path_str}: {e}")

        # --- Final Report ---
        final_message = f"Apply complete. {success_count} file(s) updated/created."
        if failed_files:
            final_message += f"\nFailed to apply changes to {len(failed_files)} file(s):\n- " + "\n- ".join(failed_files)
            QMessageBox.warning(self, "Apply Partially Failed", final_message)
        elif success_count > 0: # Only show success message if something actually happened
             QMessageBox.information(self, "Apply Successful", final_message + "\nUndo is now available.")
        elif not failed_files and success_count == 0: # Should not happen if confirmation passed, but handle defensively
             final_message = "No changes were applied (though some were expected)."
             QMessageBox.information(self, "No Changes Applied", final_message)


        if skipped_files and success_count == 0 and not failed_files:
             # If only skipped files occurred, mention that specifically
             final_message = f"No changes applied. {len(skipped_files)} path(s) were skipped during validation."
        elif skipped_files:
             # Append skipped info if other actions occurred
             final_message += f"\n({len(skipped_files)} initial path(s) skipped during validation)"

        self.status_label.setText(final_message)

        # --- Enable Undo Button if successful changes were made and recorded ---
        if self.last_applied_changes: # Check if any changes were successfully recorded for undo
            self.undo_button.setEnabled(True)
        else:
            # If all failed or were skipped, cleanup the (likely empty) backup dir
             self._cleanup_backup_dir()
             self.undo_button.setEnabled(False)


    # --- NEW SLOT ---
    @Slot()
    def undo_last_apply(self):
        """Reverts the last set of applied changes using backups."""
        if not self.last_applied_changes:
            QMessageBox.information(self, "Undo", "No changes have been applied since the last undo or startup.")
            self.undo_button.setEnabled(False) # Ensure button is disabled
            return
        if not self.temp_backup_dir or not self.temp_backup_dir.exists():
             # Check if dir exists as well, might have been cleaned up prematurely
             QMessageBox.warning(self, "Undo Error", "Cannot undo: Backup directory information is missing or directory was removed.")
             self.last_applied_changes = [] # Clear state if backup is gone
             self.undo_button.setEnabled(False) # Disable button if state is inconsistent
             return

        reply = QMessageBox.question(self, "Confirm Undo",
                                     f"This will revert the last {len(self.last_applied_changes)} file change(s) applied in Step 2.\n\nProceed with Undo?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.No:
            return

        self.status_label.setText("Undoing changes...")
        QApplication.processEvents()

        undo_success_count = 0
        undo_failed_files = []

        # Iterate through the recorded changes (order might matter if dirs were involved, but likely ok here)
        for change_info in self.last_applied_changes:
            original_path = change_info["original_path"]
            backup_path = change_info["backup_path"]
            was_created = change_info["was_created"]
            rel_path_str = "UnknownPath" # Default
            try:
                 # Get relative path for messages, handle potential error if outside script_dir (shouldn't happen with validation)
                 rel_path_str = original_path.relative_to(self.script_dir).as_posix()
            except ValueError:
                 rel_path_str = str(original_path) # Fallback to absolute path string

            try:
                if was_created:
                    # If the file was newly created by 'apply', delete it
                    if original_path.exists() and original_path.is_file(): # Check it's a file before unlinking
                        original_path.unlink() # Delete the file
                        print(f"Undo: Deleted newly created file '{rel_path_str}'")
                        undo_success_count += 1
                    elif not original_path.exists():
                        # File already deleted? Count as success for undo.
                        print(f"Undo: Newly created file '{rel_path_str}' was already deleted.")
                        undo_success_count += 1
                    else:
                         # Path exists but is not a file (e.g., a directory was created somehow?) - report error
                         undo_failed_files.append(f"{rel_path_str} (Cannot delete, path is not a file)")
                         print(f"Error: Cannot undo creation of '{rel_path_str}', path exists but is not a file.")

                else:
                    # If the file was overwritten, restore from backup
                    if backup_path and backup_path.exists() and backup_path.is_file():
                        # Ensure parent dir exists before restoring (it should, but safety check)
                        original_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(backup_path, original_path) # Restore content and metadata
                        print(f"Undo: Restored '{rel_path_str}' from backup '{backup_path.name}'.")
                        undo_success_count += 1
                    elif backup_path and not backup_path.exists():
                        # Backup missing! Cannot restore.
                        undo_failed_files.append(f"{rel_path_str} (Backup file missing: {backup_path.name})")
                        print(f"Error: Cannot undo '{rel_path_str}', backup file missing: {backup_path}")
                    elif backup_path and not backup_path.is_file():
                         # Backup path exists but isn't a file
                         undo_failed_files.append(f"{rel_path_str} (Backup path is not a file: {backup_path.name})")
                         print(f"Error: Cannot undo '{rel_path_str}', backup path is not a file: {backup_path}")
                    elif not backup_path:
                        # Should not happen if was_created is False, but handle defensively
                         undo_failed_files.append(f"{rel_path_str} (Invalid state: Overwritten but no backup path recorded)")
                         print(f"Error: Cannot undo '{rel_path_str}', invalid state (no backup path).")

            except (IOError, OSError, shutil.Error) as e:
                 undo_failed_files.append(f"{rel_path_str} (Undo Error: {e})")
                 print(f"Error undoing change for {rel_path_str}: {e}")
            except Exception as e:
                 # Catch any other unexpected errors during undo
                 undo_failed_files.append(f"{rel_path_str} (Unexpected Undo Error: {e})")
                 print(f"Unexpected error undoing change for {rel_path_str}: {e}")

        # --- Report Undo Status ---
        final_message = f"Undo complete: {undo_success_count} change(s) reverted."
        if undo_failed_files:
            final_message += f"\nFailed to undo {len(undo_failed_files)} change(s):\n- " + "\n- ".join(undo_failed_files)
            QMessageBox.warning(self, "Undo Partially Failed", final_message + "\nManual check recommended.")
        elif undo_success_count > 0: # Only show success if something was reverted
            QMessageBox.information(self, "Undo Successful", final_message)
        else: # No successes and no failures (e.g., files were already deleted)
             QMessageBox.information(self, "Undo Complete", "Undo process finished. No files needed reverting (e.g., they were already in the target state).")


        self.status_label.setText(final_message)

        # --- Cleanup and Reset State ---
        self._cleanup_backup_dir() # Remove the temp backup dir
        self.last_applied_changes = [] # Clear the list of changes
        self.undo_button.setEnabled(False) # Disable undo button

        # Optional: Refresh tree view after undo? Might be useful if files were created/deleted.
        # print("Refreshing file tree after undo...")
        # self.populate_file_tree()
        # file_count = self.count_files_in_model()
        # self.status_label.setText(f"{final_message} | Found {file_count} files.")


    # --- Helper for cleaning up backup dir ---
    def _cleanup_backup_dir(self):
        """Safely removes the temporary backup directory if it exists."""
        if self.temp_backup_dir and self.temp_backup_dir.exists():
            try:
                shutil.rmtree(self.temp_backup_dir)
                print(f"Removed temporary backup directory: {self.temp_backup_dir}")
            except (IOError, OSError) as e:
                print(f"Warning: Could not remove temporary backup directory: {self.temp_backup_dir}\nError: {e}")
                # Optionally inform user if cleanup fails non-critically
                # QMessageBox.warning(self, "Cleanup Warning", f"Could not automatically remove the temporary backup directory:\n{self.temp_backup_dir}\nYou may need to remove it manually.\nError: {e}")
            finally:
                 self.temp_backup_dir = None # Reset path regardless of success

    # --- Ensure cleanup on exit ---
    def closeEvent(self, event):
        """Ensure temporary directory is cleaned up when the application closes."""
        print("Close event triggered, cleaning up backup directory...")
        self._cleanup_backup_dir()
        event.accept() # Proceed with closing the window


# --- Main Execution ---
if __name__ == "__main__":
    # Determine the directory where the script is running
    if getattr(sys, 'frozen', False):
        # If running as a bundled executable (e.g., PyInstaller)
        application_path = Path(sys.executable).parent
        script_name = Path(sys.executable).name
    else:
        # If running as a normal Python script
        application_path = Path(__file__).parent
        script_name = Path(__file__).name

    script_dir_abs = application_path.resolve()
    print(f"Running script '{script_name}' from directory: {script_dir_abs}")

    # Set up the Qt Application
    app = QApplication(sys.argv)
    # Apply a style if desired (optional)
    # app.setStyle('Fusion')

    # Create and show the main window
    window = ScriptAggregatorApp(script_dir=script_dir_abs, script_name=script_name)
    window.show()

    # Start the Qt event loop
    sys.exit(app.exec())
