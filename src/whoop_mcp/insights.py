from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def _avg(values: Iterable[float]) -> float | None:
    items = list(values)
    if not items:
        return None
    return round(sum(items) / len(items), 2)


def _scored_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [record for record in records if record.get("score_state") == "SCORED"]


def build_health_overview(
    *,
    days: int,
    profile: dict[str, Any] | None,
    body_measurement: dict[str, Any] | None,
    cycles: list[dict[str, Any]],
    recoveries: list[dict[str, Any]],
    sleeps: list[dict[str, Any]],
    workouts: list[dict[str, Any]],
) -> dict[str, Any]:
    scored_cycles = _scored_records(cycles)
    scored_recoveries = _scored_records(recoveries)
    scored_sleeps = _scored_records(sleeps)
    scored_workouts = _scored_records(workouts)

    latest_recovery = (
        scored_recoveries[0] if scored_recoveries else (recoveries[0] if recoveries else None)
    )
    latest_sleep = scored_sleeps[0] if scored_sleeps else (sleeps[0] if sleeps else None)
    latest_cycle = scored_cycles[0] if scored_cycles else (cycles[0] if cycles else None)

    overview = {
        "window_days": days,
        "profile": profile,
        "body_measurement": body_measurement,
        "latest": {
            "cycle": latest_cycle,
            "recovery": latest_recovery,
            "sleep": latest_sleep,
            "workouts": workouts[:5],
        },
        "trends": {
            "avg_recovery_score": _avg(
                float(record["score"]["recovery_score"])
                for record in scored_recoveries
                if record.get("score")
            ),
            "avg_resting_heart_rate": _avg(
                float(record["score"]["resting_heart_rate"])
                for record in scored_recoveries
                if record.get("score")
            ),
            "avg_hrv_rmssd_milli": _avg(
                float(record["score"]["hrv_rmssd_milli"])
                for record in scored_recoveries
                if record.get("score")
            ),
            "avg_day_strain": _avg(
                float(record["score"]["strain"]) for record in scored_cycles if record.get("score")
            ),
            "avg_sleep_performance": _avg(
                float(record["score"]["sleep_performance_percentage"])
                for record in scored_sleeps
                if record.get("score")
            ),
            "avg_sleep_efficiency": _avg(
                float(record["score"]["sleep_efficiency_percentage"])
                for record in scored_sleeps
                if record.get("score")
            ),
            "avg_workout_strain": _avg(
                float(record["score"]["strain"])
                for record in scored_workouts
                if record.get("score")
            ),
            "workout_count": len(workouts),
        },
    }

    notes: list[str] = []
    if latest_recovery and latest_recovery.get("score"):
        recovery_score = latest_recovery["score"].get("recovery_score")
        if recovery_score is not None:
            if recovery_score >= 67:
                notes.append("Latest recovery is in WHOOP's green range.")
            elif recovery_score >= 34:
                notes.append("Latest recovery is in WHOOP's yellow range.")
            else:
                notes.append("Latest recovery is in WHOOP's red range.")

    if latest_sleep and latest_sleep.get("score"):
        sleep_performance = latest_sleep["score"].get("sleep_performance_percentage")
        if sleep_performance is not None:
            notes.append(f"Latest sleep performance was {sleep_performance} percent.")

    overview["notes"] = notes
    return overview
