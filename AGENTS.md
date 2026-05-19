# AGENTS.md

## What this project is

A BDD-focused fork of [opencode](https://github.com/sst/opencode).
It extends opencode with new behaviors. Existing opencode behaviors are
**not** re-specified here — only net-new behavior introduced by this fork.

## Architecture hierarchy (strictly enforced)

All Gherkin specs live in a single shared root. Two BDD runners consume them:

```
1st class — features/**/*.feature         ← ALL specs (shared); start here always
2nd class — features/steps/*_steps.py          ← Python wiring; exists to serve features
            features/cucumber-tests/steps/*.ts ← TypeScript wiring; exists to serve features
3rd class — src/ow_agent_orchestration/        ← Python implementation; exists to serve Python steps
            opencode/packages/opencode/src/    ← TypeScript implementation; exists to serve TS steps
```

**The golden rule:** no step definition may exist without a feature that
calls it. No implementation code may exist without a step that calls it.
Work always flows top-down: feature → step → implementation.

## Directory layout

```
ow-agent-orchestration/
├── package.json              ← bun workspace root (covers opencode/* + features/cucumber-tests)
├── cucumber.json             ← cucumber-js config (run from repo root with: bun x cucumber-js)
├── features/                 ← ALL Gherkin feature files (shared spec root)
│   ├── environment.py        # behave hooks and shared context (required by behave)
│   ├── steps/                # Python step definitions (behave requires this name)
│   │   └── <domain>_steps.py
│   ├── cucumber-tests/       # TypeScript BDD infrastructure
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── support/
│   │   │   └── hooks.ts      # Effect runtime lifecycle (BeforeAll / AfterAll / Before)
│   │   └── steps/
│   │       └── <domain>_steps.ts
│   └── <domain>/
│       └── <behavior>.feature  # one file per distinct behavior
├── opencode/                 ← upstream subtree (unchanged except agent additions)
├── src/
│   └── ow_agent_orchestration/
│       └── <domain>/         # mirrors features/<domain>/ structure
└── pyproject.toml
```

## Stack

| Layer              | Tool                      |
|--------------------|---------------------------|
| Python BDD runner  | behave                    |
| TypeScript BDD runner | @cucumber/cucumber (bun) |
| Language (Python)  | Python 3.12+              |
| Language (TS)      | TypeScript / Bun          |
| Package/env        | hatch (Python), bun (TS)  |
| License            | MIT (copyright "opencode")|

## Conventions

- Feature files use plain Gherkin. Avoid custom DSL in steps — steps should
  read like English.
- One `<domain>_steps.py` (Python) or `<domain>_steps.ts` (TypeScript) per domain.
  Never one step file per feature file.
- `features/environment.py` owns Python fixture setup/teardown (`before_scenario`,
  `after_scenario`). Do not put setup logic in step files.
- `features/steps/` is behave's required name — it cannot be changed via configuration.
- `features/cucumber-tests/support/hooks.ts` owns TypeScript fixture setup/teardown
  (`BeforeAll`, `AfterAll`, `Before`). Do not put setup logic in step files.
- `src/` is a proper importable package. It must be usable independently of
  behave (i.e., no behave imports inside `src/`).
- TypeScript step files import directly from `opencode/packages/opencode/src/` via
  relative paths (`../../../opencode/…`) — no source introspection, no mocks.

## Documentation strategy

- Feature files **are** the primary documentation. Write them to be read
  by humans, not just executed by the BDD runner.
- `README.md` is intentionally thin — entry point only.
- This file (`AGENTS.md`) is the architectural memory for AI agents.
  Update it when the architecture changes, not when behaviors change.

## Running the suite

```bash
# Python BDD tests
hatch run behave                          # all features
hatch run behave features/<domain>/       # one domain

# TypeScript BDD tests
bun x cucumber-js                         # all TypeScript features (from repo root)
```
