import json
import sys
from pathlib import Path

def check_notebook_execution(file_path: str) -> None:
    """
    Checks if a Jupyter Notebook file (.ipynb) had all its code cells
    executed in sequential order. Output is formatted as Markdown.

    Args:
        file_path: The path to the .ipynb file.
    """
    notebook_path = Path(file_path)

    if not notebook_path.exists():
        print(f"### ❌ Error\n\n> **File not found:** `{notebook_path}`")
        return

    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"### ❌ Error\n\n> Could not parse JSON from `{notebook_path}`. The file may be corrupted.")
        return
    except Exception as e:
        print(f"### ❌ An unexpected error occurred\n\n> {e}")
        return

    expected_count = 1
    code_cells = [cell for cell in data['cells'] if cell['cell_type'] == 'code']
    
    if not code_cells:
        print(f"### ✅ Notebook Contains No Code\n\n> The notebook `{notebook_path.name}` has no code cells to check.")
        return

    for i, cell in enumerate(code_cells):
        cell_number = i + 1
        execution_count = cell.get('execution_count')

        if execution_count is None:
            print(f"### ⚠️ Warning: Cell Not Run\n\n> Code cell **{cell_number}** in `{notebook_path.name}` was not executed.")
            return

        if execution_count != expected_count:
            print(f"### ❌ Out of Order Execution\n\n> Mismatch found in `{notebook_path.name}` at code cell **{cell_number}**.")
            print(f"> - **Expected execution count:** `{expected_count}`")
            print(f"> - **Found execution count:** `{execution_count}`")
            return
        
        expected_count += 1
    
    print(f"### ✅ Success!\n\n> All **{len(code_cells)}** code cells in `{notebook_path.name}` were run in sequential order.")


if __name__ == '__main__':
    # Check if a file path was provided as a command-line argument
    if len(sys.argv) < 2:
        script_name = Path(sys.argv[0]).name
        print(f"### ⚠️ Usage\n\n> Please provide the path to the notebook file as an argument.\n>\n> `python {script_name} YourNotebook.ipynb`")
        sys.exit(1)

    # The first argument is the notebook file path
    notebook_to_check = sys.argv[1]
    check_notebook_execution(notebook_to_check)