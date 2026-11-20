# Standing rules (AI supervisor kit)

Project copy of the kit's `protocol/RULES.md`. These win over the kit.

## Owner

- Hobby project; the owner works on it in occasional sessions, sometimes months apart, from the desktop app. Claude writes the code (C#); the owner must understand every system through its design note before it is built.

## Money

- Claude subscription only. Never add an API key, never enable extra usage. Free tiers only for other AI, with billing off.
- Purchases, payments, subscriptions: never.

## Privacy

- No private data in this project: it's a simulation with made-up towns.
- The repo is **public**: no personal details about the owner in any file, commit or board.
- Cloud AI allowed for: all code and docs in this repo.

## Read-only sources

- `archive/` is frozen (the Python prototype at the tag `python-prototype`, and the September plan). Never write there.

## Protected files

- Never modify or stage in a runner task: `PROJECT.md`, `README.md`, `CLAUDE.md`, `docs/VISION.md`, `docs/KIT-RULES.md`, `kit.config.json`, `archive/` (also in `kit.config.json` → `protectedPaths`).

## Git

- Commit with a `Co-Authored-By` line. One branch + PR per piece of work; `main` stays working. **Never push without asking.** The owner merges PRs themselves.

## Accounts

- Never sign in, approve OAuth, accept terms, or handle passwords/keys for the owner. Ask.

## App

- No live app yet. The first one will be the map viewer (stage 1), on localhost only.
