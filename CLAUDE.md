# Trade Simulation

A hobby simulation of settlements and trade on a formula-made world, being rebuilt in TypeScript one small, understood piece at a time. **Start at [`PROJECT.md`](PROJECT.md)** (NOW section). Work is run with the AI supervisor kit at `C:\Projects\ai-supervisor-kit`; standing rules in [`docs/KIT-RULES.md`](docs/KIT-RULES.md).

## Working with the owner (normal chats)

- The owner is learning: explain git/GitHub steps and maths as you go. One small step, show it, ask before the next.
- Design and learning work ("Together" on the board) happens in normal chats, not the runner.
- Update `PROJECT.md` at the end of every working chat: Last updated, NOW, decisions, session log, roadmap.
- Each piece of work gets its own branch and PR. Never push without asking; the owner clicks Merge.
- The repo is **public**: no personal details anywhere.

## Lean routing (runner task sessions)

1. One `[ ]` task per session from `BOARD.md`: mark `[x]`, commit only task files + board, stop.
2. If the task names files, read them directly (whole sections, one call). Use the `scout` subagent only when files are unknown. Never grep the whole repo yourself.
3. Fewer, bigger turns: batch independent reads in one message, combine shell steps, never read the same file twice.
4. Edit only with Edit/Write (never sed/perl/heredoc).
5. No test suite yet. Check maths with one `node -e` call; check pages by reading them back once. Once `sim/` exists, tests via the `tester` subagent.
6. Never background-and-wait on long jobs: leave them to the supervisor and say so in the receipt.
7. After 3 failed attempts: revert task files, mark `[!]` with one line why, stop.

## Guardrails

- Protected files (never modify or stage in a task): `PROJECT.md`, `CLAUDE.md`, `docs/KIT-RULES.md`, `kit.config.json`, `archive/`.
- `archive/python-prototype/` is frozen reference: read it, never edit or copy from it.
- Money: Claude subscription only; never add API keys or enable paid usage.
- British English in docs and UI text.
