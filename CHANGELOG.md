# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Pre-1.0 releases may include breaking changes in minor versions.

## [0.2.1](https://github.com/marinsalinas/hevy-cli/compare/v0.2.0...v0.2.1) (2026-04-24)


* release 0.2.1 ([#8](https://github.com/marinsalinas/hevy-cli/issues/8)) ([0b31fb8](https://github.com/marinsalinas/hevy-cli/commit/0b31fb84f993fd460c34ee15490dac0faa9217da))

## [Unreleased]

### Added

- This changelog.
- [`CONTRIBUTING.md`](CONTRIBUTING.md), [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md), [`SECURITY.md`](SECURITY.md) for open-source hygiene.
- GitHub issue templates (bug report, feature request) and pull request template under [`.github/`](.github/).
- [Dependabot](.github/dependabot.yml) configuration for weekly grouped updates of Python deps and GitHub Actions.
- `release-please` workflow at [`.github/workflows/release-please.yml`](.github/workflows/release-please.yml) with config/manifest, driving automated version bumps, CHANGELOG entries, tagging, GitHub Releases, and PyPI publishing via OIDC Trusted Publishing + Sigstore attestations.
- `conventional-pre-commit` hook enforcing Conventional Commits on commit messages.
- pre-commit.ci config block in [`.pre-commit-config.yaml`](.pre-commit-config.yaml) for hosted autofix + weekly autoupdate PRs.

### Changed

- Trimmed [`ARCHITECTURE.md`](ARCHITECTURE.md) to design decisions only; moved API coverage table to [`docs/usage.md`](docs/usage.md) and removed stale project-layout and phased-implementation sections.
- Bumped `__version__` in [`src/hevy_cli/__init__.py`](src/hevy_cli/__init__.py) from `0.1.0` to `0.2.0` to match `pyproject.toml`; added `x-release-please-version` anchor.
- Updated PyPI classifier from `Development Status :: 3 - Alpha` to `4 - Beta`; added `Operating System :: OS Independent`.
- Expanded [`.gitignore`](.gitignore) with `.env`, `.env.*`, `.envrc`, `config.toml`, `.DS_Store`, `.idea/`, `.vscode/`, `*.swp`.
- Raised `pytest-cov` `fail_under` from `60` to `70` (organic coverage currently `~75%`).
- README badges row now includes Codecov, pre-commit.ci, and Ruff; added Contributing and Changelog sections; toned down tagline.
- Consolidated the tag-triggered `release.yml` into the single `release-please.yml` workflow (one source of truth; no tag-vs-release race).

## [0.2.0] — 2026-04-05

### Added

- Folder filtering and search on `routines list`.
- UUID lookup support in `routines rename`.
- Webhooks documentation ([`docs/WEBHOOKS.md`](docs/WEBHOOKS.md)).
- Pre-commit hooks (ruff, mypy) and `Makefile` with `lint`, `format`, `typecheck`, `test`, `check` targets.

### Changed

- Applied Hevy API lessons from smart-coach process — refactored request/response handling for consistency.
- `RoutineExercise.rest_seconds` type changed from `str` to `int` to match API behaviour (fixes deserialization errors).

### Fixed

- Correct handling of API response wrapper in `update_routine`.
- Resolved mypy and ruff CI errors after tightening strict mode.

## [0.1.0] — 2026-04-04

### Added

- Initial project scaffold: `src/` layout, `pyproject.toml` with hatchling, uv-based workflow.
- `HevyClient` with API-key auth, `httpx` sync transport, tenacity-based retry on 429/5xx, page/pageSize pagination iterator.
- Typed error hierarchy: `HevyError`, `AuthenticationError`, `NotFoundError`, `ValidationError`, `RateLimitError`, `ServerError`.
- XDG-compliant config loading (TOML) with three-tier auth resolution: `--api-key` flag > `HEVY_API_KEY` env var > `config.toml`.
- Pydantic v2 models for workouts, routines, exercises, folders, and their nested types.
- Output formatters: JSON, YAML, and `rich` tables (auto-selected by TTY detection).
- Commands: `workouts {list, get, create, update, count, events}`, `routines {list, get, create, update}`, `folders {list, get, create}`, `exercises {list, get, create, history}`, `config {set, get, show, path}`.
- CI workflow (lint / typecheck / test matrix across 3.11-3.13 / build).
- Test suite with `pytest` + `respx` for mocked HTTP integration tests.

[Unreleased]: https://github.com/marinsalinas/hevy-cli/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/marinsalinas/hevy-cli/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/marinsalinas/hevy-cli/releases/tag/v0.1.0
