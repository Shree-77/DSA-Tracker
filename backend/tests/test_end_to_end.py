"""Full end-to-end flow matching the product's 'What I Expect You To Build'.

Import the sample plan -> see 56 days -> open today -> mark in progress ->
record stats -> mark done -> verify progress/streak/dashboard update.
"""

from __future__ import annotations

from tests import fixtures

START = "2026-09-15"


def _import(client) -> int:
    resp = client.post(
        "/api/plans/import",
        data={"start_date": START},
        files={"file": ("plan.xlsx", fixtures.build_valid_workbook(), "application/octet-stream")},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["plan"]["id"]


def test_complete_user_flow(client):
    plan_id = _import(client)

    # 1. See all 56 days.
    days = client.get(f"/api/plans/{plan_id}/days").json()
    assert len(days) == 56

    # 2. Correct phases / tasks / difficulty for Day 8.
    day8 = client.get(f"/api/plans/{plan_id}/days/8").json()
    assert day8["phase"] == "Recursive Sorting"
    assert day8["focus"] == "Bubble Sort"
    assert day8["task"] == "Recursive Bubble Sort"
    assert day8["difficulty"] == "Easy"
    assert day8["scheduled_date"] == "2026-09-22"

    # 3. Open today (Day 8) via override.
    today = client.get(f"/api/plans/{plan_id}/today", params={"today": "2026-09-22"}).json()
    assert today["state"] == "active"
    assert today["day"]["day_number"] == 8

    # 4. Mark In Progress.
    r = client.patch(f"/api/plans/{plan_id}/days/8", json={"status": "IN_PROGRESS"})
    assert r.json()["status"] == "IN_PROGRESS"

    # 5. Record study statistics.
    study_day_id = day8["id"]
    client.put(
        f"/api/study-days/{study_day_id}/tracker",
        json={
            "study_hours": 2.0,
            "problems_attempted": 3,
            "solved_alone": 2,
            "needed_hint": 1,
            "needed_solution": 0,
            "confidence": 4,
            "reflection": "Recursive bubble sort clicked",
        },
    )

    # 6. Mark Done (complete days 1..8 so streak has meaning).
    for n in range(1, 9):
        client.patch(f"/api/plans/{plan_id}/days/{n}", json={"status": "DONE"})

    # 7. Progress reflects completion + streak + stats.
    progress = client.get(
        f"/api/plans/{plan_id}/progress", params={"today": "2026-09-22"}
    ).json()
    assert progress["completed_days"] == 8
    assert progress["remaining_days"] == 48
    assert progress["completion_percentage"] == round(8 / 56 * 100, 2)
    assert progress["current_streak"] == 8
    assert progress["longest_streak"] == 8
    # Sample workbook's Daily Tracker sheet imports days 1 (2.0h) & 2 (1.5h);
    # plus our PUT of 2.0h on day 8 -> 5.5h total. Confirms tracker import
    # and API-recorded stats aggregate together.
    assert progress["total_study_hours"] == 5.5
    assert progress["problems_attempted"] == 3 + 3 + 2  # day8 + imported days 1,2
    assert progress["solved_alone"] == 2 + 2 + 2
    assert progress["average_confidence"] == round((4 + 4 + 5) / 3, 2)

    # 8. Weekly progress: week 1 fully done, week 2 has 1 (day 8).
    week1 = next(w for w in progress["weekly"] if w["week_number"] == 1)
    week2 = next(w for w in progress["weekly"] if w["week_number"] == 2)
    assert week1["completed"] == 7
    assert week2["completed"] == 1

    # 9. Dashboard 'today' completion count updated.
    today_after = client.get(
        f"/api/plans/{plan_id}/today", params={"today": "2026-09-22"}
    ).json()
    assert today_after["completed_days"] == 8
    assert today_after["day"]["status"] == "DONE"
