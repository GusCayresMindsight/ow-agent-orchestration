@behave
Feature: Storage isolation from stock opencode
  As a developer with both ow and a personal opencode installation
  I want ow to store sessions, config, cache, and state in separate directories
  So that my ow workspace does not interfere with my regular opencode usage

  ow overrides the XDG base directory environment variables when it invokes
  the bundled opencode, redirecting all storage to paths scoped under
  ~/.local/share/ow/, ~/.config/ow/, ~/.cache/ow/, and ~/.local/state/ow/.
  Stock opencode continues to use its own directories unchanged.

  Scenario: ow redirects XDG_DATA_HOME so sessions are stored separately
    When the user runs ow
    Then opencode receives XDG_DATA_HOME pointing to an ow-specific directory

  Scenario: ow redirects XDG_CONFIG_HOME so config is stored separately
    When the user runs ow
    Then opencode receives XDG_CONFIG_HOME pointing to an ow-specific directory

  Scenario: ow redirects XDG_CACHE_HOME so the cache is stored separately
    When the user runs ow
    Then opencode receives XDG_CACHE_HOME pointing to an ow-specific directory

  Scenario: ow redirects XDG_STATE_HOME so state is stored separately
    When the user runs ow
    Then opencode receives XDG_STATE_HOME pointing to an ow-specific directory

  Scenario: ow does not use the stock opencode data directory
    When the user runs ow
    Then opencode does not receive XDG_DATA_HOME pointing to the system default
