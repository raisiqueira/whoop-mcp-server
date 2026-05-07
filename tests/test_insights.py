from whoop_mcp.insights import build_health_overview


def test_build_health_overview_computes_trends() -> None:
    overview = build_health_overview(
        days=7,
        profile={"first_name": "Rai"},
        body_measurement={"weight_kilogram": 80.0},
        cycles=[
            {"score_state": "SCORED", "score": {"strain": 10.0}},
            {"score_state": "SCORED", "score": {"strain": 14.0}},
        ],
        recoveries=[
            {
                "score_state": "SCORED",
                "score": {
                    "recovery_score": 80,
                    "resting_heart_rate": 48,
                    "hrv_rmssd_milli": 72,
                },
            },
            {
                "score_state": "SCORED",
                "score": {
                    "recovery_score": 60,
                    "resting_heart_rate": 50,
                    "hrv_rmssd_milli": 68,
                },
            },
        ],
        sleeps=[
            {
                "score_state": "SCORED",
                "score": {
                    "sleep_performance_percentage": 95,
                    "sleep_efficiency_percentage": 91,
                },
            },
            {
                "score_state": "SCORED",
                "score": {
                    "sleep_performance_percentage": 85,
                    "sleep_efficiency_percentage": 89,
                },
            },
        ],
        workouts=[
            {"score_state": "SCORED", "score": {"strain": 12.0}},
            {"score_state": "SCORED", "score": {"strain": 16.0}},
        ],
    )

    assert overview["trends"]["avg_recovery_score"] == 70.0
    assert overview["trends"]["avg_resting_heart_rate"] == 49.0
    assert overview["trends"]["avg_hrv_rmssd_milli"] == 70.0
    assert overview["trends"]["avg_day_strain"] == 12.0
    assert overview["trends"]["avg_sleep_performance"] == 90.0
    assert overview["trends"]["avg_sleep_efficiency"] == 90.0
    assert overview["trends"]["avg_workout_strain"] == 14.0
    assert overview["trends"]["workout_count"] == 2
    assert overview["notes"][0] == "Latest recovery is in WHOOP's green range."
