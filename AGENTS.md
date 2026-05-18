# AGENTS.md

## What this project is

A BDD-focused fork of [opencode](https://github.com/sst/opencode).
It extends opencode with new behaviors. Existing opencode behaviors are
**not** re-specified here — only net-new behavior introduced by this fork.

## Architecture hierarchy (strictly enforced)

```
1st class — features/*.feature        ← the spec; start here always
2nd class — features/steps/*_steps.py ← wiring; exists to serve features
3rd class — src/ow_agent_orchestration/ ← implementation; exists to serve steps
```

**The golden rule:** no step definition may exist without a feature that
calls it. No implementation code may exist without a step that calls it.
Work always flows top-down: feature → step → implementation.

## Directory layout

```
features/
  environment.py          # behave hooks and shared context
  <domain>/
    <behavior>.feature    # one file per distinct behavior
  steps/
    <domain>_steps.py     # step defs grouped by domain, not by class/module

src/
  ow_agent_orchestration/
    __init__.py
    <domain>/             # mirrors features/<domain>/ structure
```

## Stack

| Layer       | Tool                      |
|-------------|---------------------------|
| BDD runner  | behave                    |
| Language    | Python 3.12+              |
| Package/env | hatch                     |
| License     | MIT (copyright "opencode")|

## Conventions

- Feature files use plain Gherkin. Avoid custom DSL in steps — steps should
  read like English.
- One `<domain>_steps.py` per domain. Never one step file per feature file.
- `environment.py` owns fixture setup/teardown (`before_scenario`,
  `after_scenario`). Do not put setup logic in step files.
- `src/` is a proper importable package. It must be usable independently of
  behave (i.e., no behave imports inside `src/`).

## Documentation strategy

- Feature files **are** the primary documentation. Write them to be read
  by humans, not just executed by behave.
- `README.md` is intentionally thin — entry point only.
- This file (`AGENTS.md`) is the architectural memory for AI agents.
  Update it when the architecture changes, not when behaviors change.

## Running the suite

```bash
hatch run behave                     # all features
hatch run behave features/<domain>/  # one domain
```
