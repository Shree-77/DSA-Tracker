"""Generate the sample DSA plan workbook used for demos and testing.

Produces ``DSA_Recursion_to_Trees_8_Week_Plan.xlsx`` with three sheets:
  * DSA Plan     (56 days, 8 weeks, 8 phases)
  * Daily Tracker (a couple of example rows)
  * Overview      (plan metadata)

Run:
    python scripts/generate_sample_plan.py [output_path]
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running from the backend/ directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from tests.fixtures import build_plan_rows  # noqa: E402


def main(output: str) -> None:
    plan_df = pd.DataFrame(build_plan_rows())

    tracker_df = pd.DataFrame(
        [
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
    )

    overview_df = pd.DataFrame(
        [
            {"Key": "Plan", "Value": "DSA Recursion → Trees"},
            {"Key": "Description", "Value": "8-week / 56-day plan: Recursion → BST"},
            {"Key": "Total Days", "Value": 56},
            {"Key": "Total Weeks", "Value": 8},
        ]
    )

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        plan_df.to_excel(writer, sheet_name="DSA Plan", index=False)
        tracker_df.to_excel(writer, sheet_name="Daily Tracker", index=False)
        overview_df.to_excel(writer, sheet_name="Overview", index=False)

    print(f"Wrote {output} ({len(plan_df)} days)")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "DSA_Recursion_to_Trees_8_Week_Plan.xlsx"
    main(out)
