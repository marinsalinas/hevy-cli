# Security Policy

## Supported versions

`hevy-cli` is pre-1.0 and only the latest minor release line receives security fixes. Once 1.0 ships, this table will be updated to track a broader support window.

| Version | Supported          |
|---------|--------------------|
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security problems.

Use one of the following private channels:

1. **Preferred:** [GitHub Security Advisory](https://github.com/marinsalinas/hevy-cli/security/advisories/new) — opens a private thread with the maintainers and lets us coordinate a fix and a CVE if warranted.
2. Email **marinssalinas@gmail.com** with subject line `[hevy-cli security]`.

Please include:

- A description of the issue and its impact.
- Steps to reproduce (a minimal example is ideal).
- The version of `hevy-cli` affected (output of `hevy --version`).
- Any suggested mitigation, if you have one.

## What to expect

- Acknowledgement within **72 hours**.
- A triage assessment (severity, scope, fix plan) within **7 days**.
- Fix released as a patch version; coordinated disclosure timeline agreed with the reporter.
- Credit in the advisory and changelog unless you request anonymity.

## Scope

In scope:

- The `hevy-cli` codebase in this repository.
- The packaging/publishing pipeline (`.github/workflows/release.yml`, PyPI artifact integrity).
- Handling of user-supplied API keys (storage, logging, masking, environment precedence).

Out of scope:

- Vulnerabilities in the upstream Hevy API itself — report those to Hevy.
- Issues in third-party dependencies — report upstream; we will bump the pin once a fix is available.
- Social-engineering attacks that do not involve a flaw in this codebase.

## Safe harbour

Good-faith research conducted within this scope will not result in legal action from the maintainer. Please give us reasonable time to address the issue before public disclosure.
