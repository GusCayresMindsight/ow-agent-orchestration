@behave
Feature: Installation via curl
  As a developer on Linux
  I want to install ow-agent-orchestration with a single command
  So that I can use it without interfering with any existing opencode installation

  The install script is distributed via GitHub Releases:
  https://github.com/GusCayresMindsight/ow-agent-orchestration/releases/latest/download/install

  Background:
    Given curl and bash are available on the system

  Scenario: The ow command becomes available after install
    Given the ow command is not installed
    When the user runs the install script
    Then the ow command is available at ~/.local/bin/ow

  Scenario: The install script does not expose opencode to the PATH
    When the user runs the install script
    Then the opencode command is not added to the PATH

  Scenario: The install does not affect an existing opencode installation
    Given the user has their own opencode installed at "/usr/local/bin/opencode"
    When the user runs the install script
    Then "/usr/local/bin/opencode" is unchanged

  Scenario: Install is idempotent
    Given the ow command is already installed
    When the user runs the install script again
    Then the command exits successfully
    And the ow command still works
