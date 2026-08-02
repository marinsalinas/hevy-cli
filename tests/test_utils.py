"""Tests for utility functions."""

from __future__ import annotations

import pytest

from hevy_cli.utils import (
    build_set_with_weight,
    calculate_dropset_weight,
    calculate_rest_seconds,
    calculate_warmup_weight,
    enhance_coach_notes,
    extract_rep_range_from_notes,
    extract_rpe_from_notes,
    get_rpe_for_range,
    parse_rep_range,
    round_to_nearest_2_5,
    sanitize_routine_for_update,
    validate_set_type,
)

COACH_NOTES = [
    "5-8(Sobrecarga)\n\nRpe@6-7",
    "10-12(Sobrecarga)\n\nRpe@7-8",
    "15-30 seg x lado\n\nRpe@5-6",
    "12-20(Sobrecarga)\n\nRpe@8-9",
    "3 x 3 (1 semana)\n3 x 4(2 semana)\n3 x 5 (3 semana)\n3 x 6(4 semana)\n\nRpe@7-9",
    "8-12(Sobrecarga + Fase excéntrica)\n\nRpe@6-8",
    "12-20(Sobrecarga) x lado*\n\nRpe@5-6\n\nDato: 2 series en parte anterior y 2 series en parte posterior *",
]


class TestParseRepRange:
    def test_parse_standard_range(self) -> None:
        assert parse_rep_range("8-12") == (8, 12)

    def test_parse_with_sets(self) -> None:
        assert parse_rep_range("3 x 8-12") == (8, 12)

    def test_parse_with_parentheses(self) -> None:
        assert parse_rep_range("8-12(Sobrecarga progresiva)") == (8, 12)

    def test_parse_with_whitespace(self) -> None:
        assert parse_rep_range("8 - 12") == (8, 12)

    def test_parse_none(self) -> None:
        assert parse_rep_range(None) == (None, None)

    def test_parse_no_match(self) -> None:
        assert parse_rep_range("No rep range here") == (None, None)


class TestCalculateRestSeconds:
    def test_heavy_strength_range(self) -> None:
        assert calculate_rest_seconds("3-5") == 150
        assert calculate_rest_seconds("4-6") == 150

    def test_strength_hypertrophy_range(self) -> None:
        assert calculate_rest_seconds("6-8") == 120
        assert calculate_rest_seconds("5-8") == 120

    def test_hypertrophy_range(self) -> None:
        assert calculate_rest_seconds("8-12") == 90
        assert calculate_rest_seconds("10-12") == 90

    def test_endurance_range(self) -> None:
        assert calculate_rest_seconds("15-20") == 60

    def test_default_for_unknown(self) -> None:
        assert calculate_rest_seconds(None) == 90
        assert calculate_rest_seconds("no range") == 90

    def test_default_when_range_is_below_map(self) -> None:
        assert calculate_rest_seconds("1-2") == 90


class TestGetRpeForRange:
    def test_heavy_strength_rpe(self) -> None:
        assert get_rpe_for_range("3-5") == 8.5

    def test_hypertrophy_rpe(self) -> None:
        assert get_rpe_for_range("8-12") == 7.5

    def test_endurance_rpe(self) -> None:
        assert get_rpe_for_range("15-20") == 7.0

    def test_default_rpe(self) -> None:
        assert get_rpe_for_range(None) == 7.5

    def test_unparseable_input_uses_default(self) -> None:
        assert get_rpe_for_range("not a range") == 7.5

    def test_closest_lower_range_fallback(self) -> None:
        assert get_rpe_for_range("7-9") == 8.0

    def test_range_below_map_uses_default(self) -> None:
        assert get_rpe_for_range("1-2") == 7.5


class TestRoundToNearest25:
    def test_round_down(self) -> None:
        assert round_to_nearest_2_5(67.3) == 67.5
        assert round_to_nearest_2_5(66.2) == 65.0

    def test_round_up(self) -> None:
        assert round_to_nearest_2_5(66.3) == 67.5
        assert round_to_nearest_2_5(68.8) == 70.0

    def test_exact_multiple(self) -> None:
        assert round_to_nearest_2_5(67.5) == 67.5
        assert round_to_nearest_2_5(70.0) == 70.0


class TestCalculateWarmupWeight:
    def test_default_50_percent(self) -> None:
        assert calculate_warmup_weight(100) == 50.0

    def test_custom_percentage(self) -> None:
        assert calculate_warmup_weight(100, percentage=0.6) == 60.0

    def test_rounding(self) -> None:
        # 67.5 * 0.5 = 33.75 -> rounds to 32.5 (or 35?)
        result = calculate_warmup_weight(67.5)
        assert result % 2.5 == 0  # Must be multiple of 2.5


class TestCalculateDropsetWeight:
    def test_default_70_percent(self) -> None:
        assert calculate_dropset_weight(100) == 70.0

    def test_custom_percentage(self) -> None:
        assert calculate_dropset_weight(100, percentage=0.75) == 75.0

    def test_rounding(self) -> None:
        result = calculate_dropset_weight(67.5)
        assert result % 2.5 == 0


class TestExtractRepRangeFromNotes:
    def test_empty_notes_have_no_range(self) -> None:
        assert extract_rep_range_from_notes(None) is None

    def test_extract_from_sets_x_reps(self) -> None:
        assert extract_rep_range_from_notes("3 x 8-12") == "8-12"

    def test_extract_from_complex_notes(self) -> None:
        notes = "3 x 8-12(Sobrecarga progresiva)"
        assert extract_rep_range_from_notes(notes) == "8-12"

    def test_extract_multiple_lines(self) -> None:
        notes = "3 x 3-5\\n1 x 8-10"
        assert extract_rep_range_from_notes(notes) == "3-5"

    def test_no_range_found(self) -> None:
        assert extract_rep_range_from_notes("No rep info here") is None

    def test_does_not_treat_rpe_range_as_rep_range(self) -> None:
        assert extract_rep_range_from_notes(COACH_NOTES[4]) == "3-3"

    def test_single_rep_wave_uses_minimum_reps(self) -> None:
        notes = "3 x 6 week four / 3 x 3 week one / 3 x 5 week three"
        assert extract_rep_range_from_notes(notes) == "3-3"
        assert calculate_rest_seconds(extract_rep_range_from_notes(notes)) == 150

    def test_sets_x_range_takes_priority_over_single_reps(self) -> None:
        assert extract_rep_range_from_notes("3 x 8-12 / 5 x 5") == "8-12"

    def test_duration_style_note_uses_same_last_resort_heuristic(self) -> None:
        rep_range = extract_rep_range_from_notes("2 x 20 seg")
        assert rep_range == "20-20"
        assert calculate_rest_seconds(rep_range) == 60


class TestExtractRpeFromNotes:
    @pytest.mark.parametrize(
        ("notes", "expected"),
        zip(COACH_NOTES, [7.0, 8.0, 6.0, 9.0, 9.0, 8.0, 6.0], strict=True),
    )
    def test_extracts_real_coach_notes(self, notes: str, expected: float) -> None:
        assert extract_rpe_from_notes(notes) == expected

    @pytest.mark.parametrize(
        ("notes", "expected"),
        [
            ("Rpe@6-7", 7.0),
            ('Rpe@6-7"', 7.0),
            ("Rpe@6-7🏋️", 7.0),
            ("Rpe@6-7\nNext instruction", 7.0),
            ("Rpe@6\u22127", 7.0),
            ("Rpe@6\u20107", 7.0),
            ("Rpe@6\u20137", 7.0),
            ("Rpe@6\u20147", 7.0),
            ("Rpe@10", 10.0),
            ("rpe@5.5", 5.5),
            ("RPE@7-9.", 9.0),
            ("RPE@7-9,", 9.0),
            ("RPE@7-9;", 9.0),
            ("RPE@7-9)", 9.0),
            ("Rpe@6 - 7", 7.0),
            ("Rpe@6-", 6.0),
        ],
    )
    def test_accepts_case_whitespace_and_punctuation(self, notes: str, expected: float) -> None:
        assert extract_rpe_from_notes(notes) == expected

    @pytest.mark.parametrize(
        "notes",
        [
            "carpe diem",
            "carpet work",
            "RPE target 7",
            "RPE@11",
            "rpe@6-7kg",
            "terapia (rpe no aplica)",
        ],
    )
    def test_rejects_unrelated_or_invalid_text(self, notes: str) -> None:
        assert extract_rpe_from_notes(notes) is None

    @pytest.mark.parametrize(
        "notes",
        [
            "RPE@7-9.",
            "RPE@7-9,",
            "RPE@7-9;",
            "RPE@7-9)",
        ],
    )
    def test_supported_terminators_prevent_generic_rpe(self, notes: str) -> None:
        assert "Target RPE" not in enhance_coach_notes(notes, target_rpe=8.0)


class TestEnhanceCoachNotes:
    def test_append_rpe(self) -> None:
        result = enhance_coach_notes("3 x 8-12", target_rpe=7.5)
        assert "3 x 8-12" in result
        assert "Target RPE 7.5" in result
        assert " | " in result

    def test_append_progression_rule(self) -> None:
        result = enhance_coach_notes(
            "3 x 8-12",
            progression_rule="Add weight when hitting 12 reps",
        )
        assert "Add weight when hitting 12 reps" in result

    def test_append_both(self) -> None:
        result = enhance_coach_notes(
            "3 x 8-12",
            target_rpe=7.5,
            progression_rule="Progress when ready",
        )
        assert "Target RPE 7.5" in result
        assert "Progress when ready" in result

    def test_no_original_notes(self) -> None:
        result = enhance_coach_notes(None, target_rpe=8.0)
        assert result == "Target RPE 8.0"

    def test_no_additions(self) -> None:
        assert enhance_coach_notes("Original notes") == "Original notes"

    def test_idempotent_rpe(self) -> None:
        """Re-enhancing with same RPE should not double-append."""
        first = enhance_coach_notes("3 x 8-12", target_rpe=7.5)
        second = enhance_coach_notes(first, target_rpe=7.5)
        assert second.count("Target RPE 7.5") == 1

    def test_idempotent_progression(self) -> None:
        """Re-enhancing with same progression rule should not double-append."""
        rule = "Add weight when hitting top of 8-12 rep range"
        first = enhance_coach_notes("3 x 8-12", target_rpe=7.5, progression_rule=rule)
        second = enhance_coach_notes(first, target_rpe=7.5, progression_rule=rule)
        assert second.count(rule) == 1
        assert second.count("Target RPE 7.5") == 1

    @pytest.mark.parametrize("notes", COACH_NOTES)
    def test_honors_coach_rpe_and_is_idempotent(self, notes: str) -> None:
        rep_range = extract_rep_range_from_notes(notes)
        rule = f"Add weight when hitting top of {rep_range} rep range" if rep_range else None
        first = enhance_coach_notes(notes, target_rpe=9.5, progression_rule=rule)
        second = enhance_coach_notes(first, target_rpe=9.5, progression_rule=rule)
        assert "Target RPE" not in first
        assert second == first

    def test_equivalent_progression_is_not_duplicated(self) -> None:
        notes = "8-12 reps | ADD weight when hitting the top of 8 - 12 rep range."
        rule = "Add weight when hitting top of 8-12 rep range"
        assert enhance_coach_notes(notes, progression_rule=rule) == notes

    def test_different_progression_range_does_not_suppress_new_rule(self) -> None:
        notes = "Add weight when hitting top of 10-12 rep range"
        rule = "Add weight when hitting top of 8-12 rep range"
        enhanced = enhance_coach_notes(notes, progression_rule=rule)
        assert notes in enhanced
        assert rule in enhanced


class TestBuildSetWithWeight:
    def test_derives_warmup_weight(self) -> None:
        result = build_set_with_weight("warmup", reps=8, working_weight=100)
        assert result["weight_kg"] == 50.0
        assert result["reps"] == 8

    def test_derives_dropset_weight(self) -> None:
        result = build_set_with_weight("dropset", reps=10, working_weight=100)
        assert result["weight_kg"] == 70.0
        assert result["type"] == "dropset"

    def test_plain_set_uses_working_weight(self) -> None:
        result = build_set_with_weight("normal", working_weight=100)
        assert result["weight_kg"] == 100

    def test_explicit_weight_is_preserved(self) -> None:
        result = build_set_with_weight("warmup", weight_kg=30, working_weight=100)
        assert result["weight_kg"] == 30


class TestValidateSetType:
    def test_valid_types(self) -> None:
        assert validate_set_type("warmup") == "warmup"
        assert validate_set_type("normal") == "normal"
        assert validate_set_type("dropset") == "dropset"
        assert validate_set_type("failure") == "failure"

    def test_case_insensitive(self) -> None:
        assert validate_set_type("WARMUP") == "warmup"
        assert validate_set_type("Warmup") == "warmup"

    def test_whitespace_trim(self) -> None:
        assert validate_set_type("  warmup  ") == "warmup"

    def test_invalid_type_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid set type"):
            validate_set_type("invalid")

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid set type"):
            validate_set_type("")


class TestSanitizeRoutineForUpdate:
    """Tests for sanitize_routine_for_update — the centralized payload cleaner."""

    def test_strips_folder_id(self) -> None:
        """folder_id must NEVER reach Hevy PUT endpoint (returns 400)."""
        data = {"title": "Test", "folder_id": 42, "exercises": []}
        result = sanitize_routine_for_update(data)
        assert "folder_id" not in result

    def test_strips_all_readonly_fields(self) -> None:
        """All read-only response fields must be stripped."""
        data = {
            "id": "routine-123",
            "title": "Test",
            "folder_id": 42,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "notes": None,
            "exercises": [],
        }
        result = sanitize_routine_for_update(data)
        assert "id" not in result
        assert "folder_id" not in result
        assert "created_at" not in result
        assert "updated_at" not in result
        assert result["title"] == "Test"

    def test_strips_exercise_readonly_fields(self) -> None:
        """Exercise index and title (read-only) should be stripped."""
        data = {
            "title": "Test",
            "exercises": [
                {
                    "index": 0,
                    "title": "Bench Press",
                    "exercise_template_id": "D04AC939",
                    "sets": [{"index": 0, "type": "normal", "weight_kg": 80, "reps": 10}],
                }
            ],
        }
        result = sanitize_routine_for_update(data)
        ex = result["exercises"][0]
        assert "index" not in ex
        assert "title" not in ex
        assert ex["exercise_template_id"] == "D04AC939"
        assert "index" not in ex["sets"][0]

    def test_preserves_set_types(self) -> None:
        """All 4 set types must survive sanitization."""
        data = {
            "title": "Test",
            "exercises": [
                {
                    "exercise_template_id": "D04AC939",
                    "sets": [
                        {"type": "warmup", "weight_kg": 40, "reps": 8},
                        {"type": "normal", "weight_kg": 80, "reps": 5},
                        {"type": "dropset", "weight_kg": 55, "reps": 8},
                        {"type": "failure", "weight_kg": 60, "reps": None},
                    ],
                }
            ],
        }
        result = sanitize_routine_for_update(data)
        types = [s["type"] for s in result["exercises"][0]["sets"]]
        assert types == ["warmup", "normal", "dropset", "failure"]

    def test_no_fields_to_strip(self) -> None:
        """Clean data should pass through unchanged."""
        data = {
            "title": "Clean",
            "notes": None,
            "exercises": [
                {
                    "exercise_template_id": "D04AC939",
                    "superset_id": None,
                    "rest_seconds": 90,
                    "notes": "3 x 8-12",
                    "sets": [{"type": "normal", "weight_kg": 80, "reps": 10}],
                }
            ],
        }
        result = sanitize_routine_for_update(data)
        assert result["title"] == "Clean"
        assert len(result["exercises"]) == 1

    def test_handles_get_response_directly(self) -> None:
        """Full GET response format should be safely sanitized for PUT."""
        data = {
            "id": "routine-456",
            "title": "Upper Body",
            "folder_id": 42,
            "notes": "Coach notes",
            "updated_at": "2024-08-14T12:00:00Z",
            "created_at": "2024-08-14T12:00:00Z",
            "exercises": [
                {
                    "index": 0,
                    "title": "Bench Press",
                    "exercise_template_id": "D04AC939",
                    "supersets_id": 1,
                    "rest_seconds": 90,
                    "notes": "3 x 8-12",
                    "sets": [
                        {
                            "index": 0,
                            "type": "warmup",
                            "weight_kg": 40,
                            "reps": 8,
                            "rpe": 5.0,
                        },
                        {
                            "index": 1,
                            "type": "normal",
                            "weight_kg": 80,
                            "reps": 10,
                            "rpe": 8.5,
                        },
                    ],
                }
            ],
        }
        result = sanitize_routine_for_update(data)
        # All top-level readonly fields gone
        for field in ("id", "folder_id", "created_at", "updated_at"):
            assert field not in result
        # Nested readonly fields gone
        ex = result["exercises"][0]
        assert "index" not in ex
        for s in ex["sets"]:
            assert "index" not in s
            assert "rpe" not in s
        # Data preserved
        assert result["title"] == "Upper Body"
        assert ex["exercise_template_id"] == "D04AC939"
        assert ex["sets"][0]["type"] == "warmup"
        assert ex["sets"][1]["weight_kg"] == 80
