Feature: Built-in Test agent
  As a developer using ow
  I want a "test" primary agent available by default
  So that I can write and debug BDD tests without accidentally editing source code

  The "test" agent is defined in the opencode source alongside "build" and
  "plan". It cycles between them via Tab / Shift+Tab.

  Scenario: the test agent is listed as a primary agent
    When I list the available agents
    Then "test" is included in the list as a primary agent

  Scenario: the test agent requires confirmation before editing any file
    Given I have the "test" agent
    Then its edit permission is "ask"

  Scenario: the test agent requires confirmation before running any shell command
    Given I have the "test" agent
    Then its bash permission is "ask"

  Scenario: the test agent has a system prompt
    Given I have the "test" agent
    Then it has a non-empty system prompt
