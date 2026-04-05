"""Tests for HevyClient."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import respx
from httpx import Response

from hevy_cli.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)

if TYPE_CHECKING:
    from hevy_cli.client import HevyClient


class TestListWorkouts:
    @respx.mock
    def test_list_workouts_success(self, client: HevyClient, sample_workout: dict) -> None:
        respx.get("/v1/workouts").mock(
            return_value=Response(
                200,
                json={"page": 1, "page_count": 1, "workouts": [sample_workout]},
            )
        )
        result = client.list_workouts(page=1, page_size=5)
        assert len(result.workouts) == 1
        assert result.workouts[0].title == "Morning Workout 💪"
        assert result.page == 1

    @respx.mock
    def test_list_workouts_pagination(self, client: HevyClient, sample_workout: dict) -> None:
        respx.get("/v1/workouts").mock(
            return_value=Response(
                200,
                json={"page": 2, "page_count": 5, "workouts": [sample_workout]},
            )
        )
        result = client.list_workouts(page=2, page_size=5)
        assert result.page == 2
        assert result.page_count == 5


class TestGetWorkout:
    @respx.mock
    def test_get_workout_success(self, client: HevyClient, sample_workout: dict) -> None:
        respx.get("/v1/workouts/abc-123").mock(return_value=Response(200, json=sample_workout))
        result = client.get_workout("abc-123")
        assert result.id == "abc-123"
        assert len(result.exercises) == 1
        assert result.exercises[0].sets[0].weight_kg == 100

    @respx.mock
    def test_get_workout_not_found(self, client: HevyClient) -> None:
        respx.get("/v1/workouts/nonexistent").mock(return_value=Response(404))
        with pytest.raises(NotFoundError):
            client.get_workout("nonexistent")


class TestWorkoutCount:
    @respx.mock
    def test_count_workouts(self, client: HevyClient) -> None:
        respx.get("/v1/workouts/count").mock(return_value=Response(200, json={"workout_count": 42}))
        assert client.count_workouts() == 42


class TestErrorHandling:
    @respx.mock
    def test_authentication_error(self, client: HevyClient) -> None:
        respx.get("/v1/workouts").mock(
            return_value=Response(401, json={"error": "Invalid API key"})
        )
        with pytest.raises(AuthenticationError):
            client.list_workouts()

    @respx.mock
    def test_validation_error(self, client: HevyClient) -> None:
        respx.post("/v1/workouts").mock(
            return_value=Response(400, json={"error": "Invalid request body"})
        )
        with pytest.raises(ValidationError):
            from hevy_cli.models import WorkoutInput

            client.create_workout(
                WorkoutInput(
                    title="Test",
                    start_time="2024-01-01T00:00:00Z",
                    end_time="2024-01-01T01:00:00Z",
                )
            )

    @respx.mock
    def test_rate_limit_error(self, client: HevyClient) -> None:
        respx.get("/v1/workouts").mock(return_value=Response(429, headers={"Retry-After": "30"}))
        with pytest.raises(RateLimitError) as exc_info:
            client.list_workouts()
        assert exc_info.value.retry_after == 30


class TestExerciseTemplates:
    @respx.mock
    def test_list_exercises(self, client: HevyClient, sample_exercise_template: dict) -> None:
        respx.get("/v1/exercise_templates").mock(
            return_value=Response(
                200,
                json={
                    "page": 1,
                    "page_count": 1,
                    "exercise_templates": [sample_exercise_template],
                },
            )
        )
        result = client.list_exercises(page=1, page_size=5)
        assert len(result.exercise_templates) == 1
        assert result.exercise_templates[0].title == "Bench Press (Barbell)"

    @respx.mock
    def test_get_exercise(self, client: HevyClient, sample_exercise_template: dict) -> None:
        respx.get("/v1/exercise_templates/D04AC939").mock(
            return_value=Response(200, json=sample_exercise_template)
        )
        result = client.get_exercise("D04AC939")
        assert result.id == "D04AC939"
        assert result.primary_muscle_group.value == "chest"


class TestRoutines:
    @respx.mock
    def test_list_routines(self, client: HevyClient, sample_routine: dict) -> None:
        respx.get("/v1/routines").mock(
            return_value=Response(
                200,
                json={"page": 1, "page_count": 1, "routines": [sample_routine]},
            )
        )
        result = client.list_routines()
        assert len(result.routines) == 1
        assert result.routines[0].title == "Upper Body 💪"

    @respx.mock
    def test_update_routine(self, client: HevyClient, sample_routine: dict) -> None:
        """API returns {"routine": [{ ... }]} — verify we unwrap correctly."""
        from hevy_cli.models import RoutineUpdateInput

        updated = {**sample_routine, "title": "Renamed Routine"}
        respx.put("/v1/routines/routine-456").mock(
            return_value=Response(200, json={"routine": [updated]})
        )
        result = client.update_routine(
            "routine-456",
            RoutineUpdateInput(title="Renamed Routine", exercises=[]),
        )
        assert result.title == "Renamed Routine"
        assert result.id == "routine-456"


class TestFolders:
    @respx.mock
    def test_list_folders(self, client: HevyClient, sample_folder: dict) -> None:
        respx.get("/v1/routine_folders").mock(
            return_value=Response(
                200,
                json={"page": 1, "page_count": 1, "routine_folders": [sample_folder]},
            )
        )
        result = client.list_folders()
        assert len(result.routine_folders) == 1
        assert result.routine_folders[0].title == "Push Pull 🏋️‍♂️"

    @respx.mock
    def test_create_folder(self, client: HevyClient, sample_folder: dict) -> None:
        respx.post("/v1/routine_folders").mock(return_value=Response(201, json=sample_folder))
        result = client.create_folder("Push Pull 🏋️‍♂️")
        assert result.title == "Push Pull 🏋️‍♂️"
        assert result.id == 42
