Feature: ow entrypoint
  As a developer
  I want to run ow as I would run opencode
  So that I get the extended behaviors of ow-agent-orchestration with a familiar interface

  ow delegates to its bundled opencode. The user's own opencode installation,
  if present, is never invoked.

  Scenario: ow passes arguments through to opencode
    When the user runs "ow <subcommand> [args]"
    Then the bundled opencode receives the same subcommand and args

  Scenario: ow uses its bundled opencode, not the user's
    Given the user has their own opencode at "/usr/local/bin/opencode"
    When the user runs any ow command
    Then the bundled opencode is invoked, not the one at "/usr/local/bin/opencode"

  Scenario: ow propagates opencode's exit code
    When the bundled opencode exits with a non-zero code
    Then ow exits with the same code

  Scenario: ow passes stdout through from opencode
    When opencode writes to stdout
    Then ow's stdout contains the same output

  Scenario: ow passes stderr through from opencode
    When opencode writes to stderr
    Then ow's stderr contains the same output

  Scenario: ow passes stdin through to opencode
    When the user provides input on stdin
    Then opencode receives that input

  Scenario: ow forwards SIGINT to opencode
    Given opencode is running under ow
    When the user sends SIGINT
    Then opencode receives SIGINT

  Scenario: ow forwards SIGTERM to opencode
    Given opencode is running under ow
    When the user sends SIGTERM
    Then opencode receives SIGTERM

  Scenario: ow forwards SIGWINCH to opencode
    Given opencode is running under ow
    When the terminal is resized
    Then opencode receives SIGWINCH

  Scenario: ow --version shows ow's version and the bundled opencode version
    When the user runs "ow --version"
    Then the output includes the ow version
    And the output includes the bundled opencode version
