"""HTTP client wrapper for the Hevy API."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .exceptions import (
    AuthenticationError,
    HevyError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from .models import (
    CustomExerciseInput,
    ExerciseHistoryEntry,
    ExerciseTemplate,
    ExerciseTemplateList,
    Routine,
    RoutineFolder,
    RoutineFolderList,
    RoutineInput,
    RoutineList,
    RoutineUpdateInput,
    Workout,
    WorkoutCount,
    WorkoutInput,
    WorkoutList,
)

if TYPE_CHECKING:
    from collections.abc import Generator

logger = structlog.get_logger()


class HevyClient:
    """Synchronous HTTP client for the Hevy v1 API."""

    # Fields that Hevy API rejects in PUT payloads (returns 400)
    FORBIDDEN_UPDATE_FIELDS = frozenset({"folder_id", "id", "created_at", "updated_at"})

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.hevy.com",
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"api-key": api_key, "Content-Type": "application/json"},
            timeout=timeout,
        )

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> HevyClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # ── Request helpers ────────────────────────────────────────────────────

    def _handle_response(self, response: httpx.Response) -> Any:
        """Map HTTP status codes to typed exceptions."""
        if response.is_success:
            if response.status_code == 204:
                return None
            return response.json()

        status = response.status_code
        try:
            body = response.json()
            error_msg = body.get("error", response.text)
        except (json.JSONDecodeError, ValueError):
            error_msg = response.text
        error_msg = str(error_msg)
        if self.api_key:
            error_msg = error_msg.replace(self.api_key, "[REDACTED]")

        if status in (401, 403):
            raise AuthenticationError(error_msg)
        if status == 404:
            raise NotFoundError("Resource", "unknown")
        if status == 400:
            hint = ""
            if "folder_id" in str(error_msg).lower() or "folder" in str(error_msg).lower():
                hint = " (Hint: Hevy API rejects folder_id in PUT payloads)"
            raise ValidationError(f"{error_msg}{hint}")
        if status == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(int(retry_after) if retry_after else None)
        if status >= 500:
            raise ServerError(status, error_msg)
        raise HevyError(f"HTTP {status}: {error_msg}", status_code=status)

    @retry(
        retry=retry_if_exception_type((RateLimitError, ServerError)),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Make an HTTP request with retry logic."""
        logger.debug("hevy_request", method=method, path=path)
        response = self._client.request(method, path, **kwargs)
        return self._handle_response(response)

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self._request("GET", path, params=params)

    def _post(self, path: str, json_data: dict[str, Any]) -> Any:
        return self._request("POST", path, json=json_data)

    def _put(self, path: str, json_data: dict[str, Any]) -> Any:
        return self._request("PUT", path, json=json_data)

    # ── Pagination ─────────────────────────────────────────────────────────

    def _paginate(
        self,
        path: str,
        items_key: str,
        page_size: int = 10,
        max_pages: int | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """Yield items across all pages."""
        page = 1
        while True:
            data = self._get(path, params={"page": page, "pageSize": page_size})
            items = data.get(items_key, [])
            yield from items

            page_count = data.get("page_count", 1)
            if page >= page_count:
                break
            if max_pages and page >= max_pages:
                break
            page += 1

    # ── Response helpers ────────────────────────────────────────────────────

    @staticmethod
    def _normalize_routine_response(data: dict[str, Any], routine_id: str) -> dict[str, Any]:
        """Normalize routine API response: Hevy may return routine as list or dict.

        Lesson learned: Hevy API inconsistently returns routine as a list or dict.
        Always check isinstance and take [0] if list.
        """
        from typing import cast

        routine_data: Any = data.get("routine", data)

        if isinstance(routine_data, list):
            if not routine_data:
                raise NotFoundError("Routine", routine_id)
            routine_data = routine_data[0]
            logger.debug("routine_response_was_list", routine_id=routine_id)

        return cast("dict[str, Any]", routine_data)

    def _sanitize_update_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Strip forbidden fields from update payload.

        CRITICAL: Hevy API returns 400 if folder_id is included in PUT payload.
        Also strips other read-only fields (id, created_at, updated_at) that
        may leak in when using GET response data directly as update input.
        """
        stripped = []
        for field in self.FORBIDDEN_UPDATE_FIELDS:
            if field in payload:
                stripped.append(field)
                del payload[field]

        if stripped:
            logger.info(
                "sanitized_update_payload",
                stripped_fields=stripped,
                title=payload.get("title"),
            )

        # Also strip read-only fields from nested exercises and sets
        for ex in payload.get("exercises", []):
            ex.pop("index", None)
            ex.pop("title", None)  # exercise title is read-only in update
            for s in ex.get("sets", []):
                s.pop("index", None)
                s.pop("rpe", None)  # rpe is read-only in routine sets

        return payload

    # ── Workouts ───────────────────────────────────────────────────────────

    def list_workouts(self, page: int = 1, page_size: int = 5) -> WorkoutList:
        """Get a paginated list of workouts."""
        data = self._get("/v1/workouts", params={"page": page, "pageSize": page_size})
        return WorkoutList.model_validate(data)

    def get_workout(self, workout_id: str) -> Workout:
        """Get a single workout by ID."""
        data = self._get(f"/v1/workouts/{workout_id}")
        return Workout.model_validate(data)

    def create_workout(self, workout: WorkoutInput) -> Workout:
        """Create a new workout."""
        payload = {"workout": workout.model_dump(exclude_none=True)}
        data = self._post("/v1/workouts", payload)
        return Workout.model_validate(data)

    def update_workout(self, workout_id: str, workout: WorkoutInput) -> Workout:
        """Update an existing workout."""
        payload = {"workout": workout.model_dump(exclude_none=True)}
        data = self._put(f"/v1/workouts/{workout_id}", payload)
        return Workout.model_validate(data)

    def count_workouts(self) -> int:
        """Get total number of workouts."""
        data = self._get("/v1/workouts/count")
        result = WorkoutCount.model_validate(data)
        return result.workout_count

    def list_workout_events(
        self, since: str | None = None, page: int = 1, page_size: int = 5
    ) -> dict[str, Any]:
        """Get workout events (updates/deletes) since a given date."""
        params: dict[str, Any] = {"page": page, "pageSize": page_size}
        if since:
            params["since"] = since
        result: dict[str, Any] = self._get("/v1/workouts/events", params=params)
        return result

    def iter_all_workouts(self, page_size: int = 10) -> Generator[dict[str, Any], None, None]:
        """Iterate over all workouts across pages."""
        yield from self._paginate("/v1/workouts", "workouts", page_size=page_size)

    # ── Routines ───────────────────────────────────────────────────────────

    def list_routines(self, page: int = 1, page_size: int = 5) -> RoutineList:
        """Get a paginated list of routines."""
        data = self._get("/v1/routines", params={"page": page, "pageSize": page_size})
        return RoutineList.model_validate(data)

    def get_routine(self, routine_id: str) -> Routine:
        """Get a single routine by ID.

        Handles the case where Hevy API may return routine as a list or dict.
        """
        logger.debug("getting_routine", routine_id=routine_id)
        data = self._get(f"/v1/routines/{routine_id}")
        routine_data = self._normalize_routine_response(data, routine_id)
        return Routine.model_validate(routine_data)

    def create_routine(self, routine: RoutineInput) -> Routine:
        """Create a new routine."""
        payload = {"routine": routine.model_dump(exclude_none=True)}
        data = self._post("/v1/routines", payload)
        return Routine.model_validate(data)

    def update_routine(self, routine_id: str, routine: RoutineUpdateInput) -> Routine:
        """Update an existing routine.

        CRITICAL: Never include folder_id in PUT payload - Hevy returns 400.
        The routine response may be a list or dict - normalize accordingly.
        """
        routine_dict = routine.model_dump(exclude_none=True)
        self._sanitize_update_payload(routine_dict)

        payload = {"routine": routine_dict}
        logger.debug(
            "updating_routine",
            routine_id=routine_id,
            title=routine_dict.get("title"),
            exercise_count=len(routine_dict.get("exercises", [])),
        )

        data = self._put(f"/v1/routines/{routine_id}", payload)
        routine_data = self._normalize_routine_response(data, routine_id)
        return Routine.model_validate(routine_data)

    def iter_all_routines(self, page_size: int = 10) -> Generator[dict[str, Any], None, None]:
        """Iterate over all routines across pages."""
        yield from self._paginate("/v1/routines", "routines", page_size=page_size)

    # ── Routine Folders ────────────────────────────────────────────────────

    def list_folders(self, page: int = 1, page_size: int = 5) -> RoutineFolderList:
        """Get a paginated list of routine folders."""
        data = self._get("/v1/routine_folders", params={"page": page, "pageSize": page_size})
        return RoutineFolderList.model_validate(data)

    def get_folder(self, folder_id: str) -> RoutineFolder:
        """Get a single folder by ID."""
        data = self._get(f"/v1/routine_folders/{folder_id}")
        return RoutineFolder.model_validate(data)

    def create_folder(self, title: str) -> RoutineFolder:
        """Create a new routine folder."""
        payload = {"routine_folder": {"title": title}}
        data = self._post("/v1/routine_folders", payload)
        return RoutineFolder.model_validate(data)

    # ── Exercise Templates ─────────────────────────────────────────────────

    def list_exercises(self, page: int = 1, page_size: int = 5) -> ExerciseTemplateList:
        """Get a paginated list of exercise templates."""
        data = self._get("/v1/exercise_templates", params={"page": page, "pageSize": page_size})
        return ExerciseTemplateList.model_validate(data)

    def get_exercise(self, exercise_id: str) -> ExerciseTemplate:
        """Get a single exercise template by ID."""
        data = self._get(f"/v1/exercise_templates/{exercise_id}")
        return ExerciseTemplate.model_validate(data)

    def create_exercise(self, exercise: CustomExerciseInput) -> dict[str, Any]:
        """Create a custom exercise template."""
        payload = {"exercise": exercise.model_dump(exclude_none=True)}
        result: dict[str, Any] = self._post("/v1/exercise_templates", payload)
        return result

    def get_exercise_history(
        self,
        exercise_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[ExerciseHistoryEntry]:
        """Get exercise history for a specific exercise template."""
        params: dict[str, Any] = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        data = self._get(f"/v1/exercise_history/{exercise_id}", params=params)
        entries = data.get("exercise_history", [])
        return [ExerciseHistoryEntry.model_validate(e) for e in entries]

    def iter_all_exercises(self, page_size: int = 100) -> Generator[dict[str, Any], None, None]:
        """Iterate over all exercise templates across pages."""
        yield from self._paginate(
            "/v1/exercise_templates", "exercise_templates", page_size=page_size
        )

    # ── Utility ────────────────────────────────────────────────────────────

    @staticmethod
    def load_json_file(path: str | Path) -> dict[str, Any]:
        """Load and parse a JSON file."""
        file_path = Path(path)
        if not file_path.exists():
            raise HevyError(f"File not found: {file_path}")
        with open(file_path) as f:
            result: dict[str, Any] = json.load(f)
            return result
