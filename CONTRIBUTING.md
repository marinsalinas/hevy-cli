# Contributing

Thanks for your interest in `hevy-cli`. This document describes how to get a dev environment set up, what the project expects from a pull request, and how changes flow to a release.

If you are just reporting a bug or requesting a feature, open an issue — no setup required.

## Code of conduct

Participation in this project is governed by the [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before engaging.

## Development setup

Prerequisites:

- Python >= 3.11
- [`uv`](https://docs.astral.sh/uv/) (the project uses uv for dependency resolution, virtualenv management, and builds)
- `make` (optional, for the convenience targets)

One-time setup:

```bash
git clone https://github.com/marinsalinas/hevy-cli.git
cd hevy-cli
make dev       # equivalent to: uv sync --group dev && uv run pre-commit install
```

Run the CLI from a checkout:

```bash
uv run hevy --help
```

## Local quality gates

Before opening a pull request, the following must pass:

```bash
make check     # runs lint + typecheck + test
```

Or individually:

```bash
make lint       # ruff check + ruff format --check
make typecheck  # mypy --strict
make test       # pytest with coverage
make format     # auto-fix lint + format (only when you want to write)
```

Coverage has a floor enforced by `pytest-cov` (`fail_under` in [pyproject.toml](pyproject.toml)); new code should keep the floor from dropping.

Pre-commit hooks run the same linters on every commit. If you skipped `make dev`, run `uv run pre-commit install` so they fire automatically.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the design decisions behind the project (CLI framework choice, HTTP client, auth model, error hierarchy, testing strategy). If you are proposing a change that affects one of those choices, open an issue to discuss it first — the ARCHITECTURE document is the log where new decisions are recorded.

## Commit messages

This project follows the [Conventional Commits 1.0](https://www.conventionalcommits.org/en/v1.0.0/) specification. The release automation (see "Releases" below) parses commit messages to generate the changelog and decide version bumps, so consistency matters.

Common types:

- `feat:` — a new user-visible feature (minor bump)
- `fix:` — a bug fix (patch bump)
- `docs:` — documentation only
- `refactor:` — internal change, no behaviour change
- `test:` — adding or changing tests only
- `ci:` — CI / pre-commit config
- `chore:` — build config, dependency bumps

Breaking changes: append `!` (`feat!: drop Python 3.10 support`) or add a `BREAKING CHANGE:` trailer. Pre-1.0, breaking changes land as minor bumps.

## Pull requests

1. Fork, branch from `main`, keep the branch focused on one change.
2. Add or update tests for behaviour changes. Bug fixes should include a regression test.
3. Update [`CHANGELOG.md`](CHANGELOG.md) under `## [Unreleased]` if your change is user-visible.
4. Update `docs/` if you change command surface or auth/config behaviour.
5. Run `make check` locally.
6. Open the PR — GitHub Actions will re-run the same gates plus the 3.11 / 3.12 / 3.13 test matrix.
7. Keep the PR title in Conventional Commits format — it becomes the squash-merge message and feeds the release bot.

## Reporting security issues

Do **not** open public issues for suspected security vulnerabilities. See [SECURITY.md](SECURITY.md) for the private disclosure process.

## Releases

Releases are tag-driven. Tagging `vX.Y.Z` on `main` triggers [`release.yml`](.github/workflows/release.yml), which builds the sdist + wheel and publishes to PyPI via OIDC (no long-lived API token in the repo).

Maintainers: the version in [`pyproject.toml`](pyproject.toml) and [`src/hevy_cli/__init__.py`](src/hevy_cli/__init__.py) and the `CHANGELOG.md` heading are kept in sync by `release-please`; do not bump them by hand.

## Questions

Open a [GitHub Discussion](https://github.com/marinsalinas/hevy-cli/discussions) or an issue with the `question` label.
