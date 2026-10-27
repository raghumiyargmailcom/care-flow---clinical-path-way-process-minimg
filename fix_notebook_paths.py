# -*- coding: utf-8 -*-
"""
fix_notebook_paths.py
---------------------
Fixes hardcoded absolute paths in CareFlow Jupyter notebooks so they work
on any machine.  Run from anywhere inside the repo:

    python fix_notebook_paths.py

Changes made
------------
01_data_cleaning.ipynb
  1. Adds a Path-setup cell at position 0 that defines PROJECT_ROOT,
     DATA_FILE, and CLEANED_DATA dynamically.
  2. Replaces the hardcoded pd.read_csv(r"C:\\Users\\Hp\\...") call
     with  pd.read_csv(DATA_FILE).
  3. Replaces  df.to_csv('cleaned_data', index=False)
     with  df.to_csv(CLEANED_DATA, index=False).

pm4py_work.ipynb
  1. Adds the same Path-setup cell at position 0.
  2. Replaces  df = pd.read_csv("cleaned_data")
     with  df = pd.read_csv(CLEANED_DATA).

filter.ipynb
  1. Adds the same Path-setup cell at position 0.
  2. Replaces  df = pd.read_csv("cleaned_data")
     with  df = pd.read_csv(CLEANED_DATA).
"""

import json
import copy
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).resolve().parent
NOTEBOOK_DIR = REPO_ROOT / "notebook"

CLEANING_NB  = NOTEBOOK_DIR / "01_data_cleaning.ipynb"
PM4PY_NB     = NOTEBOOK_DIR / "pm4py_work.ipynb"
FILTER_NB    = NOTEBOOK_DIR / "filter.ipynb"

# ── Path-setup cell (injected as the very first code cell) ────────────────────
PATH_SETUP_CELL = {
    "cell_type": "code",
    "execution_count": None,
    "id": "careflow-path-setup",
    "metadata": {},
    "outputs": [],
    "source": [
        "# ── CareFlow: portable path setup ──────────────────────────────────────\n",
        "# This cell resolves paths relative to the repo root so the notebook\n",
        "# works on any machine regardless of where the repo is cloned.\n",
        "from pathlib import Path\n",
        "\n",
        "# The notebook lives in  <repo>/notebook/\n",
        "NOTEBOOK_DIR  = Path().resolve()          # directory Jupyter was launched from\n",
        "PROJECT_ROOT  = NOTEBOOK_DIR.parent       # one level up → repo root\n",
        "DATA_FILE     = PROJECT_ROOT / 'data4' / 'hospital_process_mining_event_log-1.csv'\n",
        "CLEANED_DATA  = NOTEBOOK_DIR / 'cleaned_data.csv'\n",
        "\n",
        "print('Project root :', PROJECT_ROOT)\n",
        "print('Raw data     :', DATA_FILE)\n",
        "print('Cleaned data :', CLEANED_DATA)\n"
    ]
}

# ── Helper ────────────────────────────────────────────────────────────────────

def load_nb(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_nb(nb: dict, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    print(f"  [OK] Saved: {path.name}")

def prepend_setup_cell(nb: dict) -> dict:
    """Insert PATH_SETUP_CELL as the first cell if not already present."""
    nb = copy.deepcopy(nb)
    if nb["cells"] and nb["cells"][0].get("id") == "careflow-path-setup":
        print("    (setup cell already present — skipping insert)")
        return nb
    nb["cells"].insert(0, copy.deepcopy(PATH_SETUP_CELL))
    return nb

def replace_in_source(cell: dict, old: str, new: str) -> bool:
    """Replace `old` with `new` in every line of cell['source']. Returns True if changed."""
    changed = False
    new_source = []
    for line in cell.get("source", []):
        if old in line:
            line = line.replace(old, new)
            changed = True
        new_source.append(line)
    cell["source"] = new_source
    return changed

# ── Fix 01_data_cleaning.ipynb ────────────────────────────────────────────────

def fix_cleaning_notebook():
    print("Fixing 01_data_cleaning.ipynb …")
    nb = load_nb(CLEANING_NB)
    nb = prepend_setup_cell(nb)

    OLD_READ  = r'df = pd.read_csv(r"C:\Users\Hp\Desktop\process mining\care-flow---clinical-path-way-process-minimg\data4\hospital_process_mining_event_log-1.csv")'
    NEW_READ  = "df = pd.read_csv(DATA_FILE)"
    OLD_SAVE  = "df.to_csv('cleaned_data', index=False)"
    NEW_SAVE  = "df.to_csv(CLEANED_DATA, index=False)"

    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        if replace_in_source(cell, OLD_READ, NEW_READ):
            print("    [OK] Fixed: read_csv path")
        if replace_in_source(cell, OLD_SAVE, NEW_SAVE):
            print("    [OK] Fixed: to_csv path")

    save_nb(nb, CLEANING_NB)

# ── Fix pm4py_work.ipynb ──────────────────────────────────────────────────────

def fix_pm4py_notebook():
    print("Fixing pm4py_work.ipynb …")
    nb = load_nb(PM4PY_NB)
    nb = prepend_setup_cell(nb)

    OLD_READ = 'df = pd.read_csv("cleaned_data")'
    NEW_READ = "df = pd.read_csv(CLEANED_DATA)"

    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        if replace_in_source(cell, OLD_READ, NEW_READ):
            print("    [OK] Fixed: read_csv path")

    save_nb(nb, PM4PY_NB)

# ── Fix filter.ipynb ──────────────────────────────────────────────────────────

def fix_filter_notebook():
    print("Fixing filter.ipynb …")
    nb = load_nb(FILTER_NB)
    nb = prepend_setup_cell(nb)

    OLD_READ = 'df = pd.read_csv("cleaned_data")'
    NEW_READ = "df = pd.read_csv(CLEANED_DATA)"

    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        if replace_in_source(cell, OLD_READ, NEW_READ):
            print("    [OK] Fixed: read_csv path")

    save_nb(nb, FILTER_NB)

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    fix_cleaning_notebook()
    fix_pm4py_notebook()
    fix_filter_notebook()
    print("\nAll notebooks patched successfully.")
    print("IMPORTANT: Open Jupyter from inside the  notebook/  directory")
    print("so that Path().resolve() points to the correct location.")
