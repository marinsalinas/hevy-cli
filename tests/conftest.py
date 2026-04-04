"""Shared test fixtures."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

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
