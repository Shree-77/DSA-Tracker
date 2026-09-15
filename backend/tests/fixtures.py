"""Test fixtures: build in-memory .xlsx workbooks that mirror the real plan.

The generated 56-day / 8-week / 8-phase workbook matches the structure of
``DSA_Recursion_to_Trees_8_Week_Plan.xlsx`` (DSA Plan + Daily Tracker + Overview
sheets) so tests exercise the exact same import path used in production.
"""

from __future__ import annotations

import io

import pandas as pd

# 8 phases, one per week (7 days each = 56 days).
PHASES = [
    "Recursion",
    "Recursive Sorting",
    "Subsequences",
    "Backtracking",
    "Binary Trees",
    "Tree Recursion",
    "BFS",
    "BST",
]

# A representative focus/task per day (7 per phase).
FOCUS_BY_PHASE = {
    "Recursion": [
        ("Basics", "Print 1..N recursively", "Easy"),
        ("Basics", "Sum of first N numbers", "Easy"),
        ("Factorial", "Factorial recursively", "Easy"),
        ("Reverse", "Reverse an array", "Easy"),
        ("Palindrome", "Check palindrome", "Medium"),
        ("Fibonacci", "Nth Fibonacci", "Medium"),
        ("Power", "Fast power (x^n)", "Medium"),
    ],
    "Recursive Sorting": [
        ("Bubble Sort", "Recursive Bubble Sort", "Easy"),
        ("Selection Sort", "Recursive Selection Sort", "Easy"),
        ("Insertion Sort", "Recursive Insertion Sort", "Medium"),
        ("Merge Sort", "Merge Sort", "Medium"),
        ("Quick Sort", "Quick Sort", "Medium"),
        ("Count Inversions", "Count inversions", "Hard"),
        ("Review", "Sorting review problems", "Mixed"),
    ],
    "Subsequences": [
        ("Generate", "All subsequences", "Medium"),
        ("Sum", "Subsequences with sum K", "Medium"),
        ("Count", "Count subsequences", "Medium"),
        ("Print One", "Print any subsequence with sum K", "Medium"),
        ("Subsets", "Power set", "Medium"),
        ("Combination Sum", "Combination Sum", "Medium"),
        ("Review", "Subsequence review", "Mixed"),
    ],
    "Backtracking": [
        ("Permutations", "All permutations", "Medium"),
        ("N-Queens", "N-Queens", "Hard"),
        ("Sudoku", "Sudoku solver", "Hard"),
        ("Rat in Maze", "Rat in a maze", "Medium"),
        ("Word Search", "Word search", "Medium"),
        ("Palindrome Partition", "Palindrome partitioning", "Hard"),
        ("Review", "Backtracking review", "Mixed"),
    ],
    "Binary Trees": [
        ("Traversals", "Inorder/Preorder/Postorder", "Easy"),
        ("Level Order", "Level order traversal", "Medium"),
        ("Height", "Height of tree", "Easy"),
        ("Diameter", "Diameter of tree", "Medium"),
        ("Balanced", "Check balanced tree", "Medium"),
        ("Max Path Sum", "Max path sum", "Hard"),
        ("Review", "Tree review", "Mixed"),
    ],
    "Tree Recursion": [
        ("LCA", "Lowest common ancestor", "Medium"),
        ("Path", "Root to node path", "Medium"),
        ("Boundary", "Boundary traversal", "Hard"),
        ("Vertical", "Vertical order traversal", "Hard"),
        ("Views", "Top/Bottom view", "Medium"),
        ("Serialize", "Serialize/Deserialize", "Hard"),
        ("Review", "Tree recursion review", "Mixed"),
    ],
    "BFS": [
        ("Basics", "BFS traversal", "Medium"),
        ("Shortest Path", "Shortest path in grid", "Medium"),
        ("Rotten Oranges", "Rotten oranges", "Medium"),
        ("Flood Fill", "Flood fill", "Easy"),
        ("Word Ladder", "Word ladder", "Hard"),
        ("Multi-source", "Multi-source BFS", "Medium"),
        ("Review", "BFS review", "Mixed"),
    ],
    "BST": [
        ("Search", "Search in BST", "Easy"),
        ("Insert", "Insert into BST", "Medium"),
        ("Delete", "Delete node in BST", "Medium"),
        ("Validate", "Validate BST", "Medium"),
        ("Kth Smallest", "Kth smallest element", "Medium"),
        ("LCA in BST", "LCA in BST", "Easy"),
        ("Review", "BST review", "Mixed"),
    ],
}


def build_plan_rows() -> list[dict]:
    rows: list[dict] = []
    day = 1
    for week_index, phase in enumerate(PHASES, start=1):
        for focus, task, difficulty in FOCUS_BY_PHASE[phase]:
            rows.append(
                {
                    "Day": day,
                    "Week": week_index,
                    "Phase": phase,
                    "Focus": focus,
                    "Problems / Task": task,
                    "Difficulty": difficulty,
                    "Status": "NOT_STARTED",
                    "Completed Date": None,
                    "Notes": None,
                }
            )
            day += 1
    return rows


def build_valid_workbook(with_tracker: bool = True) -> bytes:
    """Return bytes of a valid 56-day workbook."""
    plan_df = pd.DataFrame(build_plan_rows())

    sheets: dict[str, pd.DataFrame] = {"DSA Plan": plan_df}

    if with_tracker:
        tracker_rows = [
            {
                "Day": 1,
                "Date": "2026-09-15",
                "Study Hours": 2.0,
                "Problems Attempted": 3,
                "Solved Alone": 2,
                "Needed Hint": 1,
                "Needed Solution": 0,
                "Confidence (1-5)": 4,
                "Reflection": "Good start",
            },
            {
                "Day": 2,
                "Date": "2026-09-16",
                "Study Hours": 1.5,
                "Problems Attempted": 2,
                "Solved Alone": 2,
                "Needed Hint": 0,
                "Needed Solution": 0,
                "Confidence (1-5)": 5,
                "Reflection": "Felt confident",
            },
        ]
        sheets["Daily Tracker"] = pd.DataFrame(tracker_rows)

    overview_rows = [
        {"Key": "Plan", "Value": "DSA Recursion → Trees"},
        {"Key": "Description", "Value": "8-week recursion to trees plan"},
    ]
    sheets["Overview"] = pd.DataFrame(overview_rows)

    return _to_xlsx_bytes(sheets)


def build_workbook_missing_columns() -> bytes:
    """Workbook whose plan sheet lacks the required Day column."""
    df = pd.DataFrame(
        [{"Week": 1, "Phase": "Recursion", "Problems / Task": "Print 1..N"}]
    )
    return _to_xlsx_bytes({"DSA Plan": df})


def build_workbook_invalid_row() -> bytes:
    """Workbook with a missing day number in one row (row 3 / Excel)."""
    rows = build_plan_rows()[:5]
    rows[1]["Day"] = None  # Excel row 3
    return _to_xlsx_bytes({"DSA Plan": pd.DataFrame(rows)})


def build_workbook_duplicate_days() -> bytes:
    rows = build_plan_rows()[:5]
    rows[2]["Day"] = rows[1]["Day"]  # duplicate
    return _to_xlsx_bytes({"DSA Plan": pd.DataFrame(rows)})


def build_workbook_invalid_difficulty() -> bytes:
    rows = build_plan_rows()[:3]
    rows[0]["Difficulty"] = "Impossible"
    return _to_xlsx_bytes({"DSA Plan": pd.DataFrame(rows)})


def _to_xlsx_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)
    return buffer.getvalue()
