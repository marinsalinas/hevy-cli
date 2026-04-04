"""Pydantic models derived from the Hevy OpenAPI spec."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

# ── Enums ──────────────────────────────────────────────────────────────────────


class SetType(StrEnum):
    WARMUP = "warmup"
    NORMAL = "normal"
    FAILURE = "failure"
    DROPSET = "dropset"


class ExerciseType(StrEnum):
    WEIGHT_REPS = "weight_reps"
    REPS_ONLY = "reps_only"
    BODYWEIGHT_REPS = "bodyweight_reps"
    BODYWEIGHT_ASSISTED_REPS = "bodyweight_assisted_reps"
    DURATION = "duration"
    WEIGHT_DURATION = "weight_duration"
    DISTANCE_DURATION = "distance_duration"
    SHORT_DISTANCE_WEIGHT = "short_distance_weight"


class MuscleGroup(StrEnum):
    ABDOMINALS = "abdominals"
    SHOULDERS = "shoulders"
    BICEPS = "biceps"
    TRICEPS = "triceps"
    FOREARMS = "forearms"
    QUADRICEPS = "quadriceps"
    HAMSTRINGS = "hamstrings"
    CALVES = "calves"
    GLUTES = "glutes"
    ABDUCTORS = "abductors"
    ADDUCTORS = "adductors"
    LATS = "lats"
    UPPER_BACK = "upper_back"
    TRAPS = "traps"
    LOWER_BACK = "lower_back"
    CHEST = "chest"
    CARDIO = "cardio"
    NECK = "neck"
    FULL_BODY = "full_body"
    OTHER = "other"


class EquipmentCategory(StrEnum):
    NONE = "none"
    BARBELL = "barbell"
    DUMBBELL = "dumbbell"
    KETTLEBELL = "kettlebell"
    MACHINE = "machine"
    PLATE = "plate"
    RESISTANCE_BAND = "resistance_band"
    SUSPENSION = "suspension"
    OTHER = "other"


# ── Response Models ────────────────────────────────────────────────────────────


class Set(BaseModel):
    """A single set within an exercise."""

    index: int
    type: SetType
    weight_kg: float | None = None
    reps: int | None = None
    distance_meters: float | None = None
    duration_seconds: int | None = None
    rpe: float | None = None
    custom_metric: float | None = None


class RoutineSet(BaseModel):
    """A set within a routine exercise (includes rep_range)."""

    index: int
    type: SetType
    weight_kg: float | None = None
    reps: int | None = None
    rep_range: RepRange | None = None
    distance_meters: float | None = None
    duration_seconds: int | None = None
    rpe: float | None = None
    custom_metric: float | None = None


class RepRange(BaseModel):
    """Rep range for routine sets."""

    start: int | None = None
    end: int | None = None


# Fix forward reference
RoutineSet.model_rebuild()


class Exercise(BaseModel):
    """An exercise within a workout."""

    index: int
    title: str
    notes: str | None = None
    exercise_template_id: str
    supersets_id: int | None = None
    sets: list[Set] = Field(default_factory=list)


class RoutineExercise(BaseModel):
    """An exercise within a routine."""

    index: int
    title: str
    notes: str | None = None
    exercise_template_id: str
    supersets_id: int | None = None
    rest_seconds: str | None = None
    sets: list[RoutineSet] = Field(default_factory=list)


class Workout(BaseModel):
    """A completed workout."""

    id: str
    title: str
    description: str | None = None
    routine_id: str | None = None
    start_time: str
    end_time: str
    updated_at: str
    created_at: str
    exercises: list[Exercise] = Field(default_factory=list)


class Routine(BaseModel):
    """A workout routine template."""

    id: str
    title: str
    folder_id: int | None = None
    notes: str | None = None
    updated_at: str
    created_at: str
    exercises: list[RoutineExercise] = Field(default_factory=list)


class RoutineFolder(BaseModel):
    """A folder for organizing routines."""

    id: int
    index: int
    title: str
    updated_at: str
    created_at: str


class ExerciseTemplate(BaseModel):
    """An exercise template (built-in or custom)."""

    id: str
    title: str
    type: ExerciseType
    primary_muscle_group: MuscleGroup
    secondary_muscle_groups: list[str] = Field(default_factory=list)
    is_custom: bool = False


class ExerciseHistoryEntry(BaseModel):
    """A single set from exercise history."""

    workout_id: str
    workout_title: str
    workout_start_time: str
    workout_end_time: str
    exercise_template_id: str
    weight_kg: float | None = None
    reps: int | None = None
    distance_meters: int | None = None
    duration_seconds: int | None = None
    rpe: float | None = None
    custom_metric: float | None = None
    set_type: str


# ── Request Models ─────────────────────────────────────────────────────────────


class SetInput(BaseModel):
    """Input for creating/updating a set."""

    type: SetType = SetType.NORMAL
    weight_kg: float | None = None
    reps: int | None = None
    distance_meters: int | None = None
    duration_seconds: int | None = None
    custom_metric: float | None = None
    rpe: float | None = None


class ExerciseInput(BaseModel):
    """Input for creating/updating an exercise in a workout."""

    exercise_template_id: str
    superset_id: int | None = None
    notes: str | None = None
    sets: list[SetInput] = Field(default_factory=list)


class WorkoutInput(BaseModel):
    """Input for creating/updating a workout."""

    title: str
    description: str | None = None
    start_time: str
    end_time: str
    is_private: bool = False
    exercises: list[ExerciseInput] = Field(default_factory=list)


class RoutineSetInput(BaseModel):
    """Input for creating/updating a routine set."""

    type: SetType = SetType.NORMAL
    weight_kg: float | None = None
    reps: int | None = None
    distance_meters: int | None = None
    duration_seconds: int | None = None
    custom_metric: float | None = None
    rep_range: RepRange | None = None


class RoutineExerciseInput(BaseModel):
    """Input for creating/updating an exercise in a routine."""

    exercise_template_id: str
    superset_id: int | None = None
    rest_seconds: int | None = None
    notes: str | None = None
    sets: list[RoutineSetInput] = Field(default_factory=list)


class RoutineInput(BaseModel):
    """Input for creating a routine."""

    title: str
    folder_id: int | None = None
    notes: str | None = None
    exercises: list[RoutineExerciseInput] = Field(default_factory=list)


class RoutineUpdateInput(BaseModel):
    """Input for updating a routine (no folder_id)."""

    title: str
    notes: str | None = None
    exercises: list[RoutineExerciseInput] = Field(default_factory=list)


class CustomExerciseInput(BaseModel):
    """Input for creating a custom exercise template."""

    title: str
    exercise_type: ExerciseType
    equipment_category: EquipmentCategory = EquipmentCategory.NONE
    muscle_group: MuscleGroup
    other_muscles: list[MuscleGroup] = Field(default_factory=list)


# ── Paginated Responses ───────────────────────────────────────────────────────


class PaginatedResponse(BaseModel):
    """Base for paginated API responses."""

    page: int
    page_count: int


class WorkoutList(PaginatedResponse):
    workouts: list[Workout] = Field(default_factory=list)


class RoutineList(PaginatedResponse):
    routines: list[Routine] = Field(default_factory=list)


class RoutineFolderList(PaginatedResponse):
    routine_folders: list[RoutineFolder] = Field(default_factory=list)


class ExerciseTemplateList(PaginatedResponse):
    exercise_templates: list[ExerciseTemplate] = Field(default_factory=list)


class WorkoutCount(BaseModel):
    workout_count: int
