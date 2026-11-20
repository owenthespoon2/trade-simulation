# Trade Simulation

A fantasy medieval trader game in a simulated world, written in **C# / .NET**. **Start at [`PROJECT.md`](PROJECT.md)** (NOW section); the game is described in [`docs/VISION.md`](docs/VISION.md). Work runs with the AI supervisor kit at `C:\Projects\ai-supervisor-kit`; standing rules in [`docs/KIT-RULES.md`](docs/KIT-RULES.md).

## Working with the owner (normal chats)

- **Claude writes the code; the owner must understand it.** Every system starts as a design note in `docs/design/` (maths, logic, worked examples with numbers). Explain it, answer questions in the note, and **don't build or move on until the owner says it makes sense.** The note stays in step with the code.
- One small step at a time; show it, then ask before the next. Explain git/GitHub steps as you do them.
- **Subagents always get a cheap model:** `haiku` for finding files, running tests and summaries; `sonnet` for web research. Never let a scout inherit Opus. See the kit's `protocol/MODEL-ROUTING.md`.
- Update `PROJECT.md` (and the README's "Latest update") at the end of every working chat.
- One branch + PR per piece of work. Never push without asking; the owner clicks Merge.
- The repo is **public**: no personal details anywhere.

## Lean routing (runner task sessions)

1. One `[ ]` task per session from `BOARD.md`: mark `[x]`, commit only task files + board, stop.
2. If the task names files, read them directly (whole sections, one call). Use the `scout` subagent only when files are unknown. Never grep the whole repo yourself.
3. Fewer, bigger turns: batch independent reads in one message, combine shell steps, never read the same file twice.
4. Edit only with Edit/Write (never sed/perl/heredoc).
5. Tests via the `tester` subagent once a C# project exists (`dotnet test <project> --filter <name>`). Until then check maths with one `node -e` call and pages by reading them back once.
6. Never background-and-wait on long jobs: leave them to the supervisor and say so in the receipt.
7. After 3 failed attempts: revert task files, mark `[!]` with one line why, stop.

## Guardrails

- Protected files (never modify or stage in a task): `PROJECT.md`, `README.md`, `CLAUDE.md`, `docs/VISION.md`, `docs/KIT-RULES.md`, `kit.config.json`, `archive/`.
- `archive/` is frozen reference: read it, never edit or copy from it.
- Simulation rules from day one: money as whole numbers and only ever transferred; fixed update order; seeded randomness (same seed → same world).
- Money: Claude subscription only; never add API keys or enable paid usage.
- British English in docs and UI text.
