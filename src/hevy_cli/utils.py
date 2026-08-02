"""Utility functions for Hevy CLI calculations."""

from __future__ import annotations

import re
from typing import Any

import structlog

logger = structlog.get_logger()

# Map rep ranges to (rest_seconds, rpe)
# Based on training principles: heavy strength needs more rest
REST_MAP: dict[str, tuple[int, float]] = {
    "3-5": (150, 8.5),  # Heavy strength
    "4-6": (150, 8.5),  # Heavy strength
    "5-8": (120, 8.0),  # Strength + hypertrophy
    "6-8": (120, 8.0),  # Strength + hypertrophy
    "6-10": (120, 8.0),  # Mixed
    "8-10": (120, 8.0),  # Hypertrophy
    "8-12": (90, 7.5),  # Hypertrophy
    "10-12": (90, 7.5),  # Hypertrophy + pump
    "12-15": (90, 7.5),  # Higher rep
    "15-20": (60, 7.0),  # Pump/endurance
}

# Default rest if no rep range match
DEFAULT_REST_SECONDS = 90
DEFAULT_RPE = 7.5

_COACH_RPE_RE = re.compile(
    r"(?<![\w])rpe\s*@\s*(?P<low>\d+(?:\.\d+)?)"
    r"(?:\s*[-\u2013\u2014]\s*(?P<high>\d+(?:\.\d+)?))?"
    r"(?=$|[\s,.;:!?|)\]}])",
    re.IGNORECASE,
)


def parse_rep_range(rep_range_str: str | None) -> tuple[int | None, int | None]:
    """Parse a rep range string like '8-12' or '3 x 8-12'.

    Returns (start, end) rep values or (None, None) if parsing fails.
    """
    if not rep_range_str:
        return None, None

    # Match patterns like "8-12", "3 x 8-12", "8-12(Sobrecarga)"
    match = re.search(r"(\d+)\s*-\s*(\d+)", rep_range_str)
    if match:
        return int(match.group(1)), int(match.group(2))

    return None, None


def calculate_rest_seconds(rep_range_str: str | None) -> int:
    """Calculate recommended rest_seconds based on rep range.

    Args:
        rep_range_str: Rep range string like "8-12" or "3 x 8-12(Sobrecarga)"

    Returns:
        Recommended rest seconds (default 90)
    """
    if not rep_range_str:
        return DEFAULT_REST_SECONDS

    start, end = parse_rep_range(rep_range_str)
    if start is None or end is None:
        return DEFAULT_REST_SECONDS

    # Prefer exact match first
    exact_key = f"{start}-{end}"
    if exact_key in REST_MAP:
        rest_seconds, rpe = REST_MAP[exact_key]
        logger.debug(
            "calculated_rest_seconds",
            rep_range=rep_range_str,
            matched_range=exact_key,
            rest_seconds=rest_seconds,
            rpe=rpe,
        )
        return rest_seconds

    # Fall back to closest lower range by start value
    for range_key in sorted(REST_MAP.keys(), key=lambda x: int(x.split("-")[0]), reverse=True):
        range_start, _ = map(int, range_key.split("-"))
        if start >= range_start:
            rest_seconds, rpe = REST_MAP[range_key]
            logger.debug(
                "calculated_rest_seconds",
                rep_range=rep_range_str,
                matched_range=range_key,
                rest_seconds=rest_seconds,
                rpe=rpe,
            )
            return rest_seconds

    return DEFAULT_REST_SECONDS


def get_rpe_for_range(rep_range_str: str | None) -> float:
    """Get recommended RPE for a rep range.

    Args:
        rep_range_str: Rep range string like "8-12"

    Returns:
        Recommended RPE value (default 7.5)
    """
    if not rep_range_str:
        return DEFAULT_RPE

    start, end = parse_rep_range(rep_range_str)
    if start is None or end is None:
        return DEFAULT_RPE

    # Prefer exact match first
    exact_key = f"{start}-{end}"
    if exact_key in REST_MAP:
        _, rpe = REST_MAP[exact_key]
        return rpe

    # Fall back to closest lower range
    for range_key in sorted(REST_MAP.keys(), key=lambda x: int(x.split("-")[0]), reverse=True):
        range_start, _ = map(int, range_key.split("-"))
        if start >= range_start:
            _, rpe = REST_MAP[range_key]
            return rpe

    return DEFAULT_RPE


def round_to_nearest_2_5(weight_kg: float) -> float:
    """Round weight to nearest 2.5kg increment (standard plate math).

    Args:
        weight_kg: Weight in kilograms

    Returns:
        Weight rounded to nearest 2.5kg
    """
    return round(weight_kg / 2.5) * 2.5


def calculate_warmup_weight(working_weight_kg: float, percentage: float = 0.5) -> float:
    """Calculate warmup weight as percentage of working weight.

    Default is 50% of working weight, rounded to 2.5kg increments.

    Args:
        working_weight_kg: The working set weight in kg
        percentage: Percentage to use (default 0.5 = 50%)

    Returns:
        Warmup weight rounded to 2.5kg
    """
    warmup = working_weight_kg * percentage
    rounded = round_to_nearest_2_5(warmup)
    logger.debug(
        "calculated_warmup_weight",
        working_weight=working_weight_kg,
        percentage=percentage,
        warmup_weight=rounded,
    )
    return rounded


def calculate_dropset_weight(working_weight_kg: float, percentage: float = 0.7) -> float:
    """Calculate dropset weight as percentage of working weight.

    Default is 70% of working weight, rounded to 2.5kg increments.

    Args:
        working_weight_kg: The working set weight in kg
        percentage: Percentage to use (default 0.7 = 70%)

    Returns:
        Dropset weight rounded to 2.5kg
    """
    dropset = working_weight_kg * percentage
    rounded = round_to_nearest_2_5(dropset)
    logger.debug(
        "calculated_dropset_weight",
        working_weight=working_weight_kg,
        percentage=percentage,
        dropset_weight=rounded,
    )
    return rounded


def extract_rep_range_from_notes(notes: str | None) -> str | None:
    """Extract rep range from coach notes.

    Looks for patterns like:
    - "3 x 8-12"
    - "8-12(Sobrecarga progresiva)"
    - "3 x 3-5\\n1 x 8-10"

    Args:
        notes: Coach notes string

    Returns:
        Rep range string like "8-12" or None
    """
    if not notes:
        return None

    # RPE ranges describe intensity, not repetitions.
    clean_notes = _COACH_RPE_RE.sub(" ", notes).replace("\\n", " ").replace("\n", " ")

    # Try to find rep range patterns
    # Priority: look for patterns with x (sets x reps)
    match = re.search(r"\d+\s*x\s*(\d+\s*-\s*\d+)", clean_notes)
    if match:
        return match.group(1)

    # Look for standalone rep ranges
    match = re.search(r"(\d+\s*-\s*\d+)", clean_notes)
    if match:
        return match.group(1)

    return None


def extract_rpe_from_notes(notes: str | None) -> float | None:
    """Extract a coach-declared ``RPE@N`` or ``RPE@N-M`` value.

    For a range, the upper end is returned because it represents the hardest
    effort permitted by the coach. Values outside the RPE scale are ignored.
    """
    if not notes:
        return None

    match = _COACH_RPE_RE.search(notes)
    if not match:
        return None

    low = float(match.group("low"))
    high = float(match.group("high") or match.group("low"))
    if not 0 <= low <= high <= 10:
        return None
    return high


def _has_equivalent_progression(notes: str, progression_rule: str) -> bool:
    """Return whether notes already contain the generated progression rule."""

    def normalize(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip().casefold()

    if normalize(progression_rule) in normalize(notes):
        return True

    requested_range = parse_rep_range(progression_rule)
    if requested_range == (None, None):
        return False
    for match in re.finditer(
        r"add\s+weight\s+when\s+hitting\s+(?:the\s+)?top\s+of\s+"
        r"\d+\s*-\s*\d+\s+rep\s+range",
        notes,
        re.IGNORECASE,
    ):
        if parse_rep_range(match.group()) == requested_range:
            return True
    return False


def enhance_coach_notes(
    original_notes: str | None,
    target_rpe: float | None = None,
    progression_rule: str | None = None,
) -> str:
    """Enhance coach notes by appending data (never replacing).

    Uses "|" separator to append new information to existing notes.
    Idempotent: skips values already present in the notes to avoid
    double-appending on re-runs.

    Args:
        original_notes: Original coach notes
        target_rpe: Target RPE value to add
        progression_rule: Progression rule to add

    Returns:
        Enhanced notes with appended information
    """
    if not original_notes:
        original_notes = ""

    notes_text = original_notes.strip()
    additions: list[str] = []

    if target_rpe is not None and extract_rpe_from_notes(notes_text) is None:
        rpe_str = f"Target RPE {target_rpe}"
        if rpe_str not in notes_text:
            additions.append(rpe_str)

    if progression_rule and not _has_equivalent_progression(notes_text, progression_rule):
        additions.append(progression_rule)

    if not additions:
        return original_notes

    # Join with " | " separator; skip empty original notes
    parts = [notes_text, *additions] if notes_text else additions

    enhanced = " | ".join(parts)
    logger.debug(
        "enhanced_coach_notes",
        original_length=len(original_notes),
        enhanced_length=len(enhanced),
    )
    return enhanced


def validate_set_type(set_type: str) -> str:
    """Validate and normalize set type.

    Valid types: warmup, normal, dropset, failure

    Args:
        set_type: Set type string to validate

    Returns:
        Normalized set type string

    Raises:
        ValueError: If set type is invalid
    """
    valid_types = {"warmup", "normal", "dropset", "failure"}
    normalized = set_type.lower().strip()

    if normalized not in valid_types:
        raise ValueError(f"Invalid set type '{set_type}'. Must be one of: {valid_types}")

    return normalized


def sanitize_routine_for_update(data: dict[str, Any]) -> dict[str, Any]:
    """Strip all read-only and forbidden fields from routine data for PUT.

    This is the canonical function for preparing routine data for the Hevy API
    update endpoint. It handles ALL known gotchas:
    - folder_id: Hevy rejects 400 if present in PUT
    - id, created_at, updated_at: read-only response fields
    - index: response-only ordering field on exercises and sets
    - title on exercises: read-only (derived from exercise_template_id)

    Returns a clean dict safe for RoutineUpdateInput validation.
    """
    routine_readonly = {"folder_id", "id", "created_at", "updated_at"}
    exercise_readonly = {"index", "title"}
    set_readonly = {"index", "rpe"}

    stripped_fields: list[str] = []
    for field in routine_readonly:
        if field in data:
            stripped_fields.append(field)
            del data[field]

    for ex in data.get("exercises", []):
        for field in exercise_readonly:
            ex.pop(field, None)
        for s in ex.get("sets", []):
            for field in set_readonly:
                s.pop(field, None)

    if stripped_fields:
        logger.info(
            "sanitized_routine_for_update",
            stripped_fields=stripped_fields,
            title=data.get("title"),
        )

    return data


def build_set_with_weight(
    set_type: str,
    weight_kg: float | None = None,
    reps: int | None = None,
    working_weight: float | None = None,
) -> dict[str, Any]:
    """Build a set dict with appropriate weight calculation.

    Args:
        set_type: Type of set (warmup, normal, dropset, failure)
        weight_kg: Explicit weight (optional)
        reps: Number of reps
        working_weight: Working weight for calculating warmup/dropset

    Returns:
        Set dictionary ready for API
    """
    set_type = validate_set_type(set_type)

    final_weight = weight_kg

    # Calculate weights based on set type if not explicitly provided
    if final_weight is None and working_weight is not None:
        if set_type == "warmup":
            final_weight = calculate_warmup_weight(working_weight)
        elif set_type == "dropset":
            final_weight = calculate_dropset_weight(working_weight)
        else:
            final_weight = working_weight

    return {
        "type": set_type,
        "weight_kg": final_weight,
        "reps": reps,
        "distance_meters": None,
        "duration_seconds": None,
        "custom_metric": None,
    }
