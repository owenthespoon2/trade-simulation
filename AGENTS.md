# Guide for any AI working on this project

This file is for **any AI assistant**, Claude or not (Codex, Gemini, Copilot, a local model...). Claude also reads [`CLAUDE.md`](CLAUDE.md); the rules are the same. Standing rules for unattended runs are in [`docs/KIT-RULES.md`](docs/KIT-RULES.md).

## Start here

1. Read [`PROJECT.md`](PROJECT.md) (the **NOW** section and **Next steps**).
2. Read the newest design note in [`docs/design/`](docs/design/).
3. The game is described in [`docs/VISION.md`](docs/VISION.md).
4. The foundation (engine, headless mode, data, layout) is planned and built in the sister repository [`evolution-sandbox`](https://github.com/owenthespoon2/evolution-sandbox) ([design note 0](https://github.com/owenthespoon2/evolution-sandbox/blob/main/docs/design/0-foundation.md)). It has its own `AGENTS.md`.

## Who does what

- **The AI writes all the code. The owner must understand it.** The owner is learning the logic and the maths and is new to git and GitHub.
- **Every system starts as a design note** in `docs/design/`: what it does, the maths, the logic, worked examples with real numbers. Explain it, put the owner's questions and answers into the note, and **don't build until the owner says it makes sense.** The note stays in step with the code.
- **One small step at a time;** show it, then ask before the next. Brainstorms go one topic at a time, with questions for the owner.
- Explain each git and GitHub step as you do it.

## The supervisor way of working: cheap helpers

The owner's projects use an **AI supervisor** pattern (Claude's version is the "AI supervisor kit"): **the main, most capable model plans, designs and talks with the owner; small, cheap helper agents do the legwork.**

- **Finding files, running tests, summarising logs:** send a helper on the **cheapest, fastest model** you have (for Claude: Haiku).
- **Web research:** send a helper on a **mid-tier model** (for Claude: Sonnet). Ask for sources and a list of what it couldn't verify. During planning, **check facts with research** rather than trusting memory.
- **Never** run helpers on the most expensive model. Hard design work and conversations with the owner stay with the main model.
- **If your tool has no helper agents,** do the same jobs yourself but keep them small: read only the files you need, and don't dump whole logs into the conversation.
- **Small, well-defined jobs** go on [`BOARD.md`](BOARD.md) for unattended runs: one task per session, following [`docs/KIT-RULES.md`](docs/KIT-RULES.md).

## Rules

- Simulation rules from day one: **money as whole numbers, only ever transferred**; a fixed update order; seeded randomness (same seed → same world); **headless first** (the simulation never depends on the graphics).
- `archive/` is frozen reference: read it, never edit or copy from it.
- Free tools only. **Never add API keys or enable paid services.**
- **British English** in docs and UI text.
- **No personal details anywhere:** the repository is public.

## Git

- One branch and one pull request per piece of work; `main` always works.
- Ask before pushing. The owner clicks **Merge** on GitHub, unless they ask the AI to do the whole flow (branch, commit, push, pull request, merge, pull).
- At the end of every working chat: update `PROJECT.md` (Last updated, NOW, Next steps, Decisions, Session log) and the README's **Latest update**.
