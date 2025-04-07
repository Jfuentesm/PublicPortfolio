# --- COMPLETE UPDATED SCRIPT ---

import sys
import os
from pathlib import Path
from datetime import datetime
import re # For parsing comma-separated list robustly

# --- Try importing PySide6 ---
try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtCore import Qt, Slot
    from PySide6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QTreeView, QLabel, QRadioButton, QGroupBox,
        QMessageBox, QFrame, QTextEdit, QLineEdit
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


# --- Reusable Core Logic (Updated Exclusions) ---

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

def get_potential_files_recursively(current_directory, original_root_dir, script_name):
    """
    Recursively get potential files relative to the original_root_dir,
    excluding specified types and patterns. Returns relative paths.
    """
    potential_files = []
    current_directory_path = Path(current_directory).resolve()

    # --- Root-level checks ---
    if current_directory_path == original_root_dir:
        compose_file = original_root_dir / 'compose.yaml'
        dockerfile = original_root_dir / 'Dockerfile'
        if compose_file.exists() and compose_file.is_file():
            potential_files.append(compose_file.relative_to(original_root_dir))
        if dockerfile.exists() and dockerfile.is_file():
            potential_files.append(dockerfile.relative_to(original_root_dir))

        docs_dir = original_root_dir / 'docs'
        if docs_dir.exists() and docs_dir.is_dir():
            for item in docs_dir.glob('*.md'):
                if item.is_file() and item.parent == docs_dir:
                    potential_files.append(item.resolve().relative_to(original_root_dir))

    # --- Recursive scan ---
    try:
        for item_entry in os.scandir(current_directory_path):
            item = Path(item_entry.path)
            item_abs_path = item.resolve()

            try:
                relative_path = item_abs_path.relative_to(original_root_dir)
                relative_path_str = relative_path.as_posix()
            except ValueError:
                # print(f"Warning: Item {item} is outside the project root {original_root_dir}. Skipping.")
                continue
            except Exception as e:
                print(f"Warning: Error during relative path calculation for {item}: {e}. Skipping.")
                continue

            # --- Exclusions ---
            if item.name == script_name: continue
            if item.name.startswith('.') and item.name != '.scripts': continue
            # Exclude common build/env dirs, archive dirs, and our own output files/dirs
            # *** ADDED OUTPUT_BASE_DIR_NAME to exclusions ***
            if item.name in ['.venv', 'venv', 'env', '__pycache__', 'node_modules', 'dist', 'build', OUTPUT_BASE_DIR_NAME] or \
               item.name.startswith('concatignore') or \
               item.name.startswith('archive') or \
               item.name.startswith('planning_and_focus_window') or \
               item.name.startswith('planning_request_') or \
               item.name.startswith('concat_'):
                continue
            # Exclude top-level 'docs' unless inside 'scripts'
            if item.is_dir() and item.name == 'docs' and 'scripts' not in relative_path_str.split('/'): continue

            # --- File processing ---
            if item.is_file():
                excluded_suffixes = [
                    '.log', '.xlsx', '.xls', '.csv', '.data', '.db', '.sqlite', '.sqlite3',
                    '.pkl', '.joblib', '.h5', '.hdf5',
                    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.ico',
                    '.pdf', '.doc', '.docx', '.ppt', '.pptx',
                    '.zip', '.gz', '.tar', '.rar',
                    '.exe', '.dll', '.so', '.o', '.a', '.lib',
                    '.pyc', '.pyd', '.pyo',
                    '.swp', '.swo', '.json'
                ]
                if item.suffix.lower() in excluded_suffixes: continue
                # Add relative path (relative to original root)
                if relative_path not in potential_files:
                    potential_files.append(relative_path)

            # --- Directory processing ---
            elif item.is_dir():
                # Recurse, passing original root dir
                potential_files.extend(get_potential_files_recursively(item_abs_path, original_root_dir, script_name))

    except FileNotFoundError: print(f"Warning: Directory not found during scan: {current_directory_path}. Skipping.")
    except PermissionError: print(f"Warning: Permission denied for directory: {current_directory_path}. Skipping.")
    except Exception as e: print(f"Error scanning directory {current_directory_path}: {e}")

    # Remove duplicates and sort
    return sorted(list(dict.fromkeys(potential_files)), key=lambda p: p.as_posix())


# --- Mode Definitions (Unchanged) ---
MODES = {
    "debug": {
        "name": "Debug Mode",
        "issue_placeholder": "<Describe the bug or unexpected behavior observed>\n\n\n",
        "output_instruction": (
            "1) Reflect on 5-7 different possible sources of the problem based on the code provided.\n"
            "2) Distill those down to the most likely root cause.\n"
            "3) Provide the COMPLETE UPDATED VERSION of *only* the files that need changes to fix the likely root cause.\n"
            "4) Add logging or print statements within the changed code to help verify the fix and understand the flow.\n"
            "5) Explain the reasoning behind the fix and the added logging.\n"
        )
    },
    "add_feature": {
        "name": "Add New Feature",
        "issue_placeholder": "<Describe the new feature or enhancement required>\n\n\n",
        "output_instruction": (
            "1) Understand the new feature request based on the description and existing code.\n"
            "2) Identify which files need to be created or modified.\n"
            "3) Provide the COMPLETE code for any NEW files needed.\n"
            "4) Provide the COMPLETE UPDATED VERSION of any EXISTING files that need changes.\n"
            "5) Explain how the new code implements the feature and integrates with the existing structure.\n"
        )
    },
    "explain": {
        "name": "Explain / Brainstorm",
        "issue_placeholder": "<Ask a question about the code, request an explanation, or describe a concept to brainstorm>\n\n\n",
        "output_instruction": (
            "1) Carefully read the question or brainstorming topic.\n"
            "2) Analyze the provided code in the context of the request.\n"
            "3) Provide a clear explanation, answer the question, or offer brainstorming ideas/approaches.\n"
            "4) If suggesting code changes or approaches, illustrate with concise examples where appropriate (no need for full file rewrites unless specifically asked).\n"
            "5) Structure the response logically for easy understanding.\n"
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
        self.model = QStandardItemModel()
        self.tree_view = QTreeView()
        self.status_label = QLabel("Ready. Scanning for files...")
        self.mode_buttons = {}
        self.goal_input = QTextEdit()
        self.suggestion_input = QLineEdit()
        self.item_path_map = {} # Map path string -> QStandardItem

        # --- Define output directories relative to script_dir ---
        self.output_base_dir = self.script_dir / OUTPUT_BASE_DIR_NAME
        self.planning_output_dir = self.output_base_dir / PLANNING_SUBDIR_NAME
        self.action_output_dir = self.output_base_dir / ACTION_SUBDIR_NAME

        self.initUI()
        self.populate_file_tree()
        file_count = self.count_files_in_model()
        self.status_label.setText(f"Ready. Found {file_count} potential files.")


    def initUI(self):
        self.setWindowTitle("Script Aggregator (Two-Step)")
        self.setGeometry(150, 150, 950, 750)

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
        step0_groupbox = QGroupBox("Step 0: Generate Planning Request (includes all code)")
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
        select_all_button = QPushButton("Select All Files")
        select_none_button = QPushButton("Deselect All Files")
        select_all_button.clicked.connect(self.select_all)
        select_none_button.clicked.connect(self.select_none)
        select_buttons_layout.addWidget(select_all_button)
        select_buttons_layout.addWidget(select_none_button)
        select_layout.addLayout(select_buttons_layout)
        select_groupbox.setLayout(select_layout)
        right_v_layout.addWidget(select_groupbox)

        # Step 1b Mode
        mode_groupbox = QGroupBox("Step 1b: Select Final Action Mode")
        mode_layout = QVBoxLayout()
        first_mode_key = list(MODES.keys())[0]
        for key, mode_info in MODES.items():
            rb = QRadioButton(mode_info["name"])
            self.mode_buttons[key] = rb
            if key == first_mode_key: rb.setChecked(True)
            mode_layout.addWidget(rb)
        mode_groupbox.setLayout(mode_layout)
        right_v_layout.addWidget(mode_groupbox)

        right_v_layout.addStretch(1) # Spacer

        # Assemble Main Horizontal Layout
        left_widget = QWidget(); left_widget.setLayout(left_v_layout)
        right_widget = QWidget(); right_widget.setLayout(right_v_layout)
        main_h_layout.addWidget(left_widget, 3)
        main_h_layout.addWidget(right_widget, 2)

        # --- Bottom Area ---
        bottom_v_layout = QVBoxLayout()
        self.generate_button = QPushButton("Execute Step 1b: Generate Concatenated File for LLM Action")
        self.generate_button.clicked.connect(self.generate_final_output_file)
        bottom_v_layout.addWidget(self.generate_button)
        self.status_label.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        self.status_label.setLineWidth(1)
        bottom_v_layout.addWidget(self.status_label)

        # --- Overall Layout ---
        overall_layout = QVBoxLayout(self)
        overall_layout.addLayout(main_h_layout)
        overall_layout.addLayout(bottom_v_layout)


    def populate_file_tree(self):
        self.model.clear()
        self.item_path_map.clear()
        invisible_root = self.model.invisibleRootItem()
        folder_items = {'': invisible_root}

        potential_files = get_potential_files_recursively(self.script_dir, self.script_dir, self.script_name)

        for rel_path in potential_files:
            if not isinstance(rel_path, Path): continue

            parent_item = invisible_root
            current_path_part_cumulative = Path()

            # Create folder items
            for part in rel_path.parts[:-1]:
                current_path_part_cumulative = current_path_part_cumulative / part
                current_path_part_str = current_path_part_cumulative.as_posix()
                if current_path_part_str not in folder_items:
                    folder_item = QStandardItem(part); folder_item.setIcon(self.folder_icon); folder_item.setEditable(False)
                    parent_item.appendRow(folder_item)
                    folder_items[current_path_part_str] = folder_item
                    parent_item = folder_item
                else:
                    parent_item = folder_items[current_path_part_str]

            # Insert file item
            file_name = rel_path.name
            file_item = QStandardItem(file_name); file_item.setIcon(self.file_icon)
            file_item.setCheckable(True); file_item.setCheckState(Qt.CheckState.Checked)
            file_item.setEditable(False); file_item.setData(rel_path, PathRole)
            parent_item.appendRow(file_item)
            self.item_path_map[rel_path.as_posix()] = file_item


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
        """Checks all file items using the map."""
        for item in self.item_path_map.values():
            if item.isCheckable(): item.setCheckState(Qt.CheckState.Checked)
        self.status_label.setText("All files selected (for Step 1b).")

    @Slot()
    def select_none(self):
        """Unchecks all file items using the map."""
        for item in self.item_path_map.values():
            if item.isCheckable(): item.setCheckState(Qt.CheckState.Unchecked)
        self.status_label.setText("All files deselected (for Step 1b).")

    @Slot()
    def generate_planning_request(self):
        """Generates the Step 0 request file including goal and ALL project code."""
        goal = self.goal_input.toPlainText().strip()
        if not goal:
            QMessageBox.warning(self, "Input Missing", "Please describe your goal for Step 0.")
            return

        self.status_label.setText("Gathering all project files for planning request...")
        QApplication.processEvents()

        all_potential_files = get_potential_files_recursively(self.script_dir, self.script_dir, self.script_name)

        if not all_potential_files:
             QMessageBox.warning(self, "No Files Found", "No source files found in the project directory to include in the planning request.")
             self.status_label.setText("Ready.")
             return

        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        # *** Use new output directory ***
        output_dir = self.planning_output_dir
        output_filename = f"planning_request_{timestamp_str}.txt"
        output_file = output_dir / output_filename

        self.status_label.setText(f"Generating {output_filename} in {output_dir.relative_to(self.script_dir)}...")
        QApplication.processEvents()

        try:
            # *** Create directory if it doesn't exist ***
            output_dir.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                # --- Part 1: Goal Description ---
                f.write("--- Goal Description ---\n\n")
                f.write(goal)
                f.write("\n\n")

                # --- Part 2: Instructions for LLM ---
                f.write("--- Instructions for LLM ---\n\n")
                f.write("Based on the goal described above and the complete project source code provided below, please identify the files that would likely need to be:\n")
                f.write("a) Modified to implement the goal.\n")
                f.write("b) Provided as essential context for understanding the relevant parts of the codebase.\n\n")
                f.write("Please list the relevant file paths **relative to the project root**.\n\n")
                f.write("**Output Format:** Provide the list as a single line of comma-separated file paths. Use forward slashes `/` as path separators.\n\n")
                f.write("Example Output:\nsrc/core/feature.py, src/utils/helpers.py, tests/test_feature.py, config/settings.yaml\n\n")
                f.write("--- End Instructions ---\n\n")

                # --- Part 3: Project File Tree ---
                f.write("<Project File Tree>\n")
                sorted_all_files = sorted(all_potential_files, key=lambda p: p.as_posix())
                for rel_path in sorted_all_files:
                    f.write(f"- {rel_path.as_posix()}\n")
                f.write("</Project File Tree>\n\n\n")

                # --- Part 4: Concatenated Project Source Code ---
                f.write("<Project Source Code>\n\n")
                for rel_path in sorted_all_files:
                    abs_path = self.script_dir / rel_path
                    rel_path_str = rel_path.as_posix()
                    f.write(f"<file path='{rel_path_str}'>\n")
                    content = read_file_content(abs_path)
                    f.write(content)
                    f.write("\n</file>\n\n")
                f.write("</Project Source Code>\n\n")

                # --- Part 5: Placeholder for LLM Output ---
                f.write("--- Identified Files (Provide comma-separated list below) ---\n\n\n")


            # *** Update message with new path ***
            relative_output_path = output_file.relative_to(self.script_dir)
            self.status_label.setText(f"Planning request file generated: {relative_output_path}")
            QMessageBox.information(self, "Step 0 Success",
                                    f"Planning request file (including all code) created:\n{relative_output_path}\n\n"
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

        suggested_paths_raw = [p.strip() for p in suggestions_text.split(',') if p.strip()]
        suggested_paths_normalized = set()
        for p_raw in suggested_paths_raw:
            p_norm = p_raw.replace("\\", "/").strip('/')
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
            else:
                not_found.append(norm_path)

        status_msg = f"Applied suggestions: {found_count} files selected for Step 1b."
        if not_found:
            status_msg += f" ({len(not_found)} suggested files not found: {', '.join(not_found[:3])}{'...' if len(not_found) > 3 else ''})"
            print(f"Warning: Suggested files not found: {', '.join(not_found)}")
            QMessageBox.warning(self, "Partial Match",
                                f"Applied suggestions, but some files suggested by the LLM were not found in the current project structure:\n\n"
                                f"- {chr(10).join(not_found)}\n\n"
                                f"Please verify the selection in the tree for Step 1b.")
        self.status_label.setText(status_msg)


    @Slot()
    def generate_final_output_file(self):
        """Gathers currently checked files and generates the final output for LLM action."""
        selected_relative_paths = []
        for item in self.item_path_map.values():
            if item.isCheckable() and item.checkState() == Qt.CheckState.Checked:
                rel_path = item.data(PathRole)
                if rel_path: selected_relative_paths.append(rel_path)

        if not selected_relative_paths:
            QMessageBox.warning(self, "No Files Selected", "Please select at least one file (either manually or by applying suggestions) before executing Step 1b.")
            return

        selected_mode_key = None
        for key, button in self.mode_buttons.items():
            if button.isChecked(): selected_mode_key = key; break
        if not selected_mode_key:
             QMessageBox.critical(self, "Error", "No final action mode (Step 1b) selected.")
             return
        selected_mode = MODES[selected_mode_key]

        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        # *** Use new output directory ***
        output_dir = self.action_output_dir
        # Use project folder name in filename for context if multiple projects use this tool
        project_folder_name = self.script_dir.name
        output_filename = f"action_{project_folder_name}_{selected_mode_key}_{timestamp_str}.txt"
        output_file = output_dir / output_filename

        self.status_label.setText(f"Generating final action file: {output_filename} in {output_dir.relative_to(self.script_dir)}...")
        QApplication.processEvents()

        try:
            # *** Create directory if it doesn't exist ***
            output_dir.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                # Preamble based on final action mode
                f.write('<issue to address>\n')
                f.write(selected_mode["issue_placeholder"])
                f.write('</issue to address>\n\n\n')
                f.write('<output instruction>\n')
                f.write(selected_mode["output_instruction"])
                f.write('\n</output instruction>\n\n\n')

                # File Tree (of selected files for this step)
                f.write("<Tree of Included Files>\n")
                sorted_rel_paths = sorted(selected_relative_paths, key=lambda p: p.as_posix())
                for rel_path in sorted_rel_paths:
                    f.write(f"- {rel_path.as_posix()}\n")
                f.write("</Tree of Included Files>\n\n\n")

                # Concatenated Code (of selected files for this step)
                f.write("<Concatenated Source Code>\n\n")
                for rel_path in sorted_rel_paths:
                    abs_path = self.script_dir / rel_path
                    rel_path_str = rel_path.as_posix()
                    f.write(f"<file path='{rel_path_str}'>\n")
                    content = read_file_content(abs_path)
                    f.write(content)
                    f.write("\n</file>\n\n")
                f.write("</Concatenated Source Code>")

            # *** Update message with new path ***
            relative_output_path = output_file.relative_to(self.script_dir)
            self.status_label.setText(f"Successfully generated final action file: {relative_output_path}")
            QMessageBox.information(self, "Step 1b Success", f"Final concatenated file for LLM action created:\n{relative_output_path}")

        except Exception as e:
            self.status_label.setText(f"Error generating final action file: {e}")
            QMessageBox.critical(self, "Step 1b Error", f"Could not generate the final action file.\nError: {e}")
            print(f"Error details during final generation: {e}")


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