# Use hevy-cli with Claude Code

This package ships a [Claude Code skill](https://docs.claude.com/en/docs/claude-code) so Claude can query your Hevy data without writing one-off HTTP scripts.

## What you get

When you ask Claude something like *"summarise my workouts from this week"* or *"what's my bench press PR?"*, Claude:

1. Recognises the Hevy intent via the skill's description.
2. Loads `SKILL.md` from `~/.claude/skills/hevy/` into context.
3. Invokes `hevy <subcommand> --format json` via the Bash tool.
4. Parses the typed JSON response and answers in plain language.

Compared to letting Claude write `httpx` code from scratch, this saves roughly 2–3× tokens per Hevy-related request and removes the surface area where Claude can hallucinate auth headers, miss pagination, or misread error responses.

## One-time install

Prerequisites: `pip install hevy-cli`, then run `hevy auth login` to store the
API key in the operating system credential store (see [main
README](../README.md#configure)).

```bash
# From a clone of this repo
mkdir -p ~/.claude/skills
cp -r skills/hevy ~/.claude/skills/
```

That's it. There is no enable/disable command; Claude Code activates skills based on their YAML `description` field matching the user's prompt.

## Verify

In a Claude Code session, run:

```
> List my last 5 workouts as a brief summary.
```

Expected behaviour:

- Claude invokes `hevy workouts list --format json` via the Bash tool.
- Parses the JSON and responds with titles + dates only.

If Claude instead writes a Python script using `httpx` or `requests`, the skill is not activating. Common causes:

- Path mismatch — confirm `~/.claude/skills/hevy/SKILL.md` exists.
- Prompt too generic — make sure the prompt mentions Hevy or workout-specific terminology.
- Older Claude Code build — skills are a feature of newer releases.

## Customise

The skill is plain markdown. Edit any of these to taste:

- **`SKILL.md`** — top-level instructions, command reference, error patterns.
- **`SKILL.md` frontmatter `description`** — the trigger. Tighten if it activates too often, broaden if it activates too rarely.
- **`examples/*.md`** — recipes Claude reads on demand. Add your own (e.g. `examples/mesocycle_compare.md` for analyses you do regularly).

Changes apply on the next prompt — no reload step.

## Update on hevy-cli upgrades

The skill is versioned with the CLI. When you upgrade (`pip install -U hevy-cli`), pull the latest skill too:

```bash
# From a fresh clone or pull
cp -r skills/hevy ~/.claude/skills/
```

This keeps the command reference accurate against new subcommands or flag changes.

## Roadmap

- **MCP server** — same capability via the Model Context Protocol, working on Claude Desktop, Cursor, opencode, Continue, and other MCP clients without per-platform skill files. Planned for a future minor release.
- **Plugin marketplace listing** — once Claude Code's marketplace is open, this skill ships there for one-click install.

## Privacy and safety

The skill grants Claude **read-write access** to your Hevy account through the CLI. Specifically Claude can:

- Read all your workouts, routines, folders, and exercise templates.
- Create new workouts and routines (`hevy workouts create`, `hevy routines create`).
- Update existing workouts and routines.

It cannot delete data — Hevy's API does not expose `DELETE` endpoints for any resource.

The CLI never logs your API key. The skill explicitly tells Claude not to print it. If you want belt-and-suspenders, run Claude Code with a separate Hevy account or a read-only-style review before letting it run write commands.
