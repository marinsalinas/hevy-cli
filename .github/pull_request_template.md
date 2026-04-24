<!--
Thanks for opening a pull request! A few notes:

- The PR title should follow Conventional Commits (e.g. `feat: add hevy stats command`, `fix: handle 401 on token rotation`). It will be the squash-merge message and feed the release bot.
- Keep PRs focused — one logical change per PR makes review and bisecting easier.
-->

## Summary

<!-- What does this change do, and why? Link the issue if there is one. -->

Closes #

## Type of change

<!-- Delete the ones that don't apply. -->

- Bug fix (`fix:`)
- New feature (`feat:`)
- Breaking change (`feat!:` / `BREAKING CHANGE:` trailer)
- Docs only (`docs:`)
- Refactor / internals (`refactor:`)
- CI / tooling (`ci:` / `chore:`)

## Checklist

- [ ] `make check` passes locally (lint + typecheck + test).
- [ ] Tests added or updated for behaviour changes; bug fixes include a regression test.
- [ ] `CHANGELOG.md` updated under `## [Unreleased]` if the change is user-visible.
- [ ] `docs/` updated if command surface, auth, or config changed.
- [ ] No API keys, workout IDs, or other personal data in the diff or in test fixtures.
- [ ] PR title follows Conventional Commits.
