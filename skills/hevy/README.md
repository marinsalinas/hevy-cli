# Hevy Claude Code Skill

A skill that teaches Claude Code (and other Anthropic-skill-compatible agents) how to query your Hevy workout data via the [`hevy-cli`](https://github.com/marinsalinas/hevy-cli) tool, instead of writing one-off HTTP scripts every time.

## What it does

When you ask Claude something like *"how many workouts did I do this week?"* or *"export my Push Day routine to a file"*, Claude detects the relevance via the skill's description, loads `SKILL.md` into context, and invokes the `hevy` CLI with proper flags. You get a typed answer back without Claude reinventing auth, pagination, or error handling each time.

Concrete benefits:

- **~2-3× fewer tokens** per Hevy-related request than letting Claude write standalone Python.
- **No more "Claude reinvents `httpx` calls"** — every interaction goes through the CLI's typed pydantic models.
- **Auth handling is centralised** — the CLI reads the key from the operating system credential store; Claude never asks you for it.
- **Errors are predictable** — the CLI's typed exception hierarchy (`AuthenticationError`, `NotFoundError`, `RateLimitError`) maps to user-facing messages in the skill.

## Prerequisites

- [Claude Code](https://docs.claude.com/en/docs/claude-code) installed and configured.
- `hevy-cli` installed and authenticated:
  ```bash
  pip install hevy-cli
  hevy auth login
  hevy --version                   # should print 0.3.0+ (Skill support added in 0.3.0)
  ```

## Install

The skill is a directory of markdown files. Copy it into your Claude Code skills directory:

```bash
# Linux / macOS / WSL
mkdir -p ~/.claude/skills
cp -r skills/hevy ~/.claude/skills/

# Verify Claude Code sees it
claude --help-skill hevy   # if your Claude Code build supports this; otherwise just trust the path
```

The skill activates automatically based on its `description` frontmatter — there is no enable/disable command. To deactivate, delete the directory.

## Verify it works

Open a Claude Code session and try:

```
> List my last 5 workouts as a brief summary.
```

Claude should:

1. Recognise the Hevy intent (skill activates).
2. Invoke `hevy workouts list --format json` via the Bash tool.
3. Parse the JSON and respond with titles + dates only — not dump the whole payload.

If Claude instead writes a Python script using `httpx` or `requests`, the skill is not loaded. Common causes:

- Wrong path — confirm `~/.claude/skills/hevy/SKILL.md` exists.
- Skill description not specific enough to trigger — re-read the description, ensure your prompt mentions Hevy / workouts / routines / training.
- Claude Code version too old — skills are a newer feature.

## Customise

The skill is plain markdown. Common edits:

- **Tighten the description trigger** if you find it activating on unrelated prompts.
- **Add domain examples** in `examples/` for analyses you do often (e.g. "compare current mesocycle to the previous one"). Reference them from `SKILL.md` so Claude knows to read them on demand.
- **Add anti-triggers** in the "Out of scope" section if Claude tries unsupported operations (e.g. workout deletion — Hevy's API doesn't expose it).

After editing, save the file. The next prompt picks up the change; no reload step.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Claude writes Python instead of using the CLI | Skill not loaded | Verify `~/.claude/skills/hevy/SKILL.md` exists |
| `hevy: command not found` in Claude's Bash output | CLI not installed or not on `PATH` | `pip install hevy-cli`; ensure your venv is active |
| `AuthenticationError: InvalidApiKey` | API key missing/wrong | `hevy auth status`, then `hevy auth login` |
| Claude dumps full JSON payload | Skill is loaded but Claude is being literal | Add a "summarise — never dump full payloads" note to your prompt |

## Roadmap

- **MCP server** (planned) — same capability exposed via the Model Context Protocol, working across Claude Desktop, Cursor, opencode, Continue, and other MCP clients without per-platform skill files.
- **Plugin marketplace listing** (planned) — once Claude Code's plugin marketplace is open, this skill ships there for one-click install.

See the [main repo issues](https://github.com/marinsalinas/hevy-cli/issues) to track progress.
