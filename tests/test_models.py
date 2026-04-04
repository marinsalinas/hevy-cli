"""Tests for Pydantic models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from hevy_cli.models import (
    ExerciseTemplate,
    ExerciseType,
    MuscleGroup,
    Set,
    SetType,
    Workout,
    WorkoutInput,
)


class TestSetModel:
    def test_basic_set(self) -> None:
        s = Set(index=0, type=SetType.NORMAL, weight_kg=100, reps=10)
        assert s.weight_kg == 100
        assert s.reps == 10
        assert s.type == SetType.NORMAL

    def test_set_with_nulls(self) -> None:
        s = Set(index=0, type=SetType.WARMUP)
        assert s.weight_kg is None
        assert s.reps is None
        assert s.rpe is None


class TestWorkoutModel:
    def test_parse_workout(self, sample_workout: dict) -> None:
        w = Workout.model_validate(sample_workout)
        assert w.id == "abc-123"
        assert len(w.exercises) == 1
        assert w.exercises[0].sets[0].weight_kg == 100


class TestWorkoutInput:
    def test_create_input(self) -> None:
        w = WorkoutInput(
            title="Test",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-01-01T01:00:00Z",
        )
        assert w.title == "Test"
        assert w.exercises == []

    def test_dump_excludes_none(self) -> None:
        w = WorkoutInput(
            title="Test",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-01-01T01:00:00Z",
        )
        d = w.model_dump(exclude_none=True)
        assert "description" not in d


class TestExerciseTemplate:
    def test_parse_template(self) -> None:
        t = ExerciseTemplate(
            id="D04AC939",
            title="Bench Press (Barbell)",
            type=ExerciseType.WEIGHT_REPS,
            primary_muscle_group=MuscleGroup.CHEST,
            secondary_muscle_groups=["triceps"],
            is_custom=False,
        )
        assert t.primary_muscle_group == MuscleGroup.CHEST
        assert t.type == ExerciseType.WEIGHT_REPS
