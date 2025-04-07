# --- COMPLETE UPDATED SCRIPT ---

import sys
import os
from pathlib import Path
from datetime import datetime

# --- Try importing PySide6 ---
try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtCore import Qt, Slot # Qt for flags, Slot for explicit slot decoration
    from PySide6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QTreeView, QLabel, QRadioButton, QGroupBox,
        QMessageBox, QScrollArea, QFrame # Added QScrollArea, QFrame
    )
    from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon, QFont
except ImportError:
    print("Error: PySide6 is not installed.")
    print("Please install it using: pip install PySide6")
    sys.exit(1)

# --- Reusable Core Logic (Unchanged) ---

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
            if item.name in ['.venv', 'venv', 'env', '__pycache__', 'node_modules', 'dist', 'build'] or \
               item.name.startswith('concatignore') or \
               item.name.startswith('archive') or \
               item.name.startswith('planning_and_focus_window'): continue
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

class ScriptAggregatorApp(QWidget): # Inherit from QWidget
    def __init__(self, script_dir, script_name):
        super().__init__() # Call parent constructor
        self.script_dir = Path(script_dir).resolve()
        self.script_name = script_name
        # Get standard icons (works better across platforms than unicode chars sometimes)
        self.folder_icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DirIcon)
        self.file_icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileIcon)
        self.model = QStandardItemModel() # Model for the TreeView
        self.tree_view = QTreeView()
        self.status_label = QLabel("Ready. Scanning for files...")
        self.mode_buttons = {} # To store radio buttons {key: button_widget}

        self.initUI() # Setup the UI
        self.populate_file_tree() # Fill the tree model
        file_count = self.count_files_in_model()
        self.status_label.setText(f"Ready. Found {file_count} potential files.")


    def initUI(self):
        self.setWindowTitle("Script Aggregator")
        self.setGeometry(200, 200, 850, 700) # x, y, width, height

        # --- Main Layout (Horizontal Split for Tree and Controls) ---
        main_h_layout = QHBoxLayout()

        # --- Left Side: File Tree ---
        left_v_layout = QVBoxLayout()
        header_label = QLabel("Select files to include:")
        font = header_label.font()
        font.setBold(True)
        header_label.setFont(font)

        self.tree_view.setModel(self.model)
        self.tree_view.setHeaderHidden(True) # Don't show column headers
        self.tree_view.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)

        left_v_layout.addWidget(header_label)
        left_v_layout.addWidget(self.tree_view)

        # --- Right Side: Controls ---
        right_v_layout = QVBoxLayout()
        right_v_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Align controls to top

        # Select Buttons
        select_buttons_layout = QHBoxLayout()
        select_all_button = QPushButton("Select All")
        select_none_button = QPushButton("Select None")
        select_all_button.clicked.connect(self.select_all)
        select_none_button.clicked.connect(self.select_none)
        select_buttons_layout.addWidget(select_all_button)
        select_buttons_layout.addWidget(select_none_button)
        right_v_layout.addLayout(select_buttons_layout)

        # Mode Selection GroupBox
        mode_groupbox = QGroupBox("Select Mode:")
        mode_layout = QVBoxLayout()
        first_mode_key = list(MODES.keys())[0]
        for key, mode_info in MODES.items():
            rb = QRadioButton(mode_info["name"])
            self.mode_buttons[key] = rb
            if key == first_mode_key:
                rb.setChecked(True)
            mode_layout.addWidget(rb)
        mode_groupbox.setLayout(mode_layout)
        right_v_layout.addWidget(mode_groupbox)

        right_v_layout.addStretch(1) # Add spacer to keep controls pushed up

        # --- Assemble Main Horizontal Layout ---
        left_widget = QWidget()
        left_widget.setLayout(left_v_layout)
        right_widget = QWidget()
        right_widget.setLayout(right_v_layout)

        main_h_layout.addWidget(left_widget, 3) # Tree area takes more space
        main_h_layout.addWidget(right_widget, 1) # Controls area takes less space

        # --- Bottom Area (Generate Button and Status Bar) ---
        # This layout will be placed *below* the main_h_layout
        bottom_v_layout = QVBoxLayout()

        # ****** THE CRITICAL EXECUTE BUTTON ******
        self.generate_button = QPushButton("Generate Concatenated File") # Store as instance variable if needed later
        self.generate_button.clicked.connect(self.generate_file)
        bottom_v_layout.addWidget(self.generate_button) # Add button to the bottom layout
        # *****************************************

        # Status Bar
        self.status_label.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        self.status_label.setLineWidth(1)
        bottom_v_layout.addWidget(self.status_label) # Add status bar below the button


        # --- Overall Layout (Vertical: Top Area + Bottom Area) ---
        # This is the main layout for the entire window (self)
        overall_layout = QVBoxLayout(self) # Set this as the layout for the main widget
        overall_layout.addLayout(main_h_layout) # Add the top part (tree + controls)
        overall_layout.addLayout(bottom_v_layout) # Add the bottom part (button + status)

        # self.setLayout(overall_layout) # No longer needed - passed 'self' to QVBoxLayout constructor


    def populate_file_tree(self):
        self.model.clear()
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
                    folder_item = QStandardItem(part)
                    folder_item.setIcon(self.folder_icon)
                    folder_item.setEditable(False)
                    parent_item.appendRow(folder_item)
                    folder_items[current_path_part_str] = folder_item
                    parent_item = folder_item
                else:
                    parent_item = folder_items[current_path_part_str]

            # Insert the file item
            file_name = rel_path.name
            file_item = QStandardItem(file_name)
            file_item.setIcon(self.file_icon)
            file_item.setCheckable(True)
            file_item.setCheckState(Qt.CheckState.Checked) # Default checked
            file_item.setEditable(False)
            file_item.setData(rel_path, PathRole) # Store the relative Path object
            parent_item.appendRow(file_item)


    def iterate_model_items(self, parent_item=None):
        """Generator to recursively yield all items in the model."""
        if parent_item is None:
            parent_item = self.model.invisibleRootItem()

        for row in range(parent_item.rowCount()):
            item = parent_item.child(row, 0)
            if item:
                yield item
                if item.hasChildren():
                    yield from self.iterate_model_items(item)


    def count_files_in_model(self):
        """Counts items in the model that represent files (have PathRole data)."""
        count = 0
        for item in self.iterate_model_items():
            # Check if it's a file item by seeing if it has path data stored
            if item.data(PathRole) is not None:
                count += 1
        return count

    @Slot()
    def select_all(self):
        """Checks all file items in the tree."""
        for item in self.iterate_model_items():
            if item.isCheckable(): # Check only items that are meant to be checkable (files)
                item.setCheckState(Qt.CheckState.Checked)
        self.status_label.setText("All files selected.")

    @Slot()
    def select_none(self):
        """Unchecks all file items in the tree."""
        for item in self.iterate_model_items():
            if item.isCheckable():
                item.setCheckState(Qt.CheckState.Unchecked)
        self.status_label.setText("All files deselected.")

    @Slot()
    def generate_file(self):
        """Gathers checked files and generates the output."""
        selected_relative_paths = []
        for item in self.iterate_model_items():
            # Ensure item is checkable and checked, and retrieve path data
            if item.isCheckable() and item.checkState() == Qt.CheckState.Checked:
                rel_path = item.data(PathRole)
                if rel_path: # Ensure path data exists
                    selected_relative_paths.append(rel_path)

        if not selected_relative_paths:
            QMessageBox.warning(self, "No Files Selected", "Please select at least one file to include.")
            return

        # Find selected mode
        selected_mode_key = None
        for key, button in self.mode_buttons.items():
            if button.isChecked():
                selected_mode_key = key
                break

        if not selected_mode_key:
             QMessageBox.critical(self, "Error", "No mode selected.")
             return

        selected_mode = MODES[selected_mode_key]

        # --- Prepare Output ---
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file_name = f"concatignore_{self.script_dir.name}_{selected_mode_key}_{timestamp_str}.txt"
        output_file = self.script_dir / output_file_name

        self.status_label.setText(f"Generating {output_file_name}...")
        QApplication.processEvents() # Update UI to show status message

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                # Preamble
                f.write('<issue to address>\n')
                f.write(selected_mode["issue_placeholder"])
                f.write('</issue to address>\n\n\n')
                f.write('<output instruction>\n')
                f.write(selected_mode["output_instruction"])
                f.write('\n</output instruction>\n\n\n')

                # File Tree
                f.write("<Tree of Included Files>\n")
                sorted_rel_paths = sorted(selected_relative_paths, key=lambda p: p.as_posix())
                for rel_path in sorted_rel_paths:
                    f.write(f"- {rel_path.as_posix()}\n")
                f.write("</Tree of Included Files>\n\n\n")

                # Concatenated Code
                f.write("<Concatenated Source Code>\n\n")
                for rel_path in sorted_rel_paths:
                    abs_path = self.script_dir / rel_path
                    rel_path_str = rel_path.as_posix()
                    f.write(f"<file path='{rel_path_str}'>\n")
                    content = read_file_content(abs_path)
                    f.write(content)
                    f.write("\n</file>\n\n")
                f.write("</Concatenated Source Code>")

            self.status_label.setText(f"Successfully generated: {output_file_name}")
            QMessageBox.information(self, "Success", f"Concatenated file created:\n{output_file}")

        except Exception as e:
            self.status_label.setText(f"Error generating file: {e}")
            QMessageBox.critical(self, "Error", f"Could not generate the file.\nError: {e}")
            print(f"Error details during generation: {e}")


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