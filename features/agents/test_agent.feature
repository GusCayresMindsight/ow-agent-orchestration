Feature: Built-in Test agent
  As a developer using ow
  I want a "test" primary agent available out of the box
  So that I can write and debug BDD tests without risking accidental edits to source code

  ow ships a "test" agent by writing its definition into the ow-scoped
  opencode config directory before delegating to the bundled opencode binary.
  The agent is always overwritten on startup so its definition stays in sync
  with the installed ow version.

  Background:
    Given ow is installed

  Scenario: ow writes the test agent definition into the ow config directory
    When the user runs any ow command
    Then a "test.md" agent file exists under the ow opencode config agents directory

  Scenario: The test agent is configured as a primary agent
    When the user runs any ow command
    Then the test agent config declares mode "primary"

  Scenario: The test agent requires confirmation before editing files
    When the user runs any ow command
    Then the test agent config sets edit permission to "ask"

  Scenario: The test agent requires confirmation before running shell commands
    When the user runs any ow command
    Then the test agent config sets bash permission to "ask"

  Scenario: The test agent definition is refreshed on every ow invocation
    Given a stale "test.md" exists under the ow opencode config agents directory
    When the user runs any ow command
    Then the stale content is replaced with the current bundled agent definition
