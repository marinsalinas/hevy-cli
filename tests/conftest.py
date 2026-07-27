"""Shared test fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

import pytest
import respx

from hevy_cli.client import HevyClient


@pytest.fixture
def api_key() -> str:
    return "test-api-key-12345"


@pytest.fixture
def base_url() -> str:
    return "https://api.hevy.com"


@pytest.fixture
def client(api_key: str, base_url: str) -> HevyClient:
    return HevyClient(api_key=api_key, base_url=base_url)


@pytest.fixture
def mock_api(base_url: str):
    """Context manager for mocking Hevy API calls with respx."""
    with respx.mock(base_url=base_url) as mock:
        yield mock


@pytest.fixture(autouse=True)
def isolated_config(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Path | None:
    """Redirect XDG config to tmp_path so tests never read the developer's real config.

    Opt out with @pytest.mark.no_isolated_config for tests that need to exercise
    the real config_path()/config_dir()/data_dir() resolvers; those tests should
    monkeypatch hevy_cli.config.platformdirs.user_config_dir themselves.
    """
    if request.node.get_closest_marker("no_isolated_config"):
        return None
    fake = tmp_path / "config.toml"
    monkeypatch.setattr("hevy_cli.config.config_path", lambda: fake)
    # Never read the developer's real operating-system credential store in tests.
    monkeypatch.setattr("hevy_cli.cli.get_api_key", lambda: None)
    return fake


# ── Sample response data ──────────────────────────────────────────────────────


@pytest.fixture
def sample_workout() -> dict:
    return {
        "id": "abc-123",
        "title": "Morning Workout 💪",
        "description": "Good session",
        "routine_id": None,
        "start_time": "2024-08-14T12:00:00Z",
        "end_time": "2024-08-14T13:00:00Z",
        "updated_at": "2024-08-14T13:00:00Z",
        "created_at": "2024-08-14T12:00:00Z",
        "exercises": [
            {
                "index": 0,
                "title": "Bench Press (Barbell)",
                "notes": "Felt good",
                "exercise_template_id": "D04AC939",
                "supersets_id": None,
                "sets": [
                    {
                        "index": 0,
                        "type": "normal",
                        "weight_kg": 100,
                        "reps": 10,
                        "distance_meters": None,
                        "duration_seconds": None,
                        "rpe": 8.5,
                        "custom_metric": None,
                    }
                ],
            }
        ],
    }


@pytest.fixture
def multi_workout_response(sample_workout: dict) -> dict:
    """Three workouts at different dates for date-range filter tests."""
    return {
        "page": 1,
        "page_count": 1,
        "workouts": [
            {**sample_workout, "id": "workout-aug-10", "start_time": "2024-08-10T12:00:00Z"},
            {**sample_workout, "id": "workout-aug-14", "start_time": "2024-08-14T12:00:00Z"},
            {**sample_workout, "id": "workout-aug-20", "start_time": "2024-08-20T12:00:00Z"},
        ],
    }


@pytest.fixture
def sample_routine() -> dict:
    return {
        "id": "routine-456",
        "title": "Upper Body 💪",
        "folder_id": None,
        "notes": "Focus on form",
        "updated_at": "2024-08-14T12:00:00Z",
        "created_at": "2024-08-14T12:00:00Z",
        "exercises": [],
    }


@pytest.fixture
def sample_folder() -> dict:
    return {
        "id": 42,
        "index": 0,
        "title": "Push Pull 🏋️‍♂️",
        "updated_at": "2024-08-14T12:00:00Z",
        "created_at": "2024-08-14T12:00:00Z",
    }


@pytest.fixture
def sample_exercise_template() -> dict:
    return {
        "id": "D04AC939",
        "title": "Bench Press (Barbell)",
        "type": "weight_reps",
        "primary_muscle_group": "chest",
        "secondary_muscle_groups": ["triceps", "shoulders"],
        "is_custom": False,
    }
