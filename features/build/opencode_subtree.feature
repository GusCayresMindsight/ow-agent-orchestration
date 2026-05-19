@behave
Feature: opencode bundled as a git subtree
  As a maintainer of ow
  I want the opencode source to live inside this repository as a git subtree
  So that I can apply ow-specific patches while still absorbing upstream releases

  The opencode source (https://github.com/sst/opencode) is incorporated under
  opencode/ using git subtree. Each upstream release is squash-merged as a
  single commit; ow-specific changes (such as the logo rebrand) are plain
  commits layered on top. Pulling a new upstream release:

    git subtree pull --prefix=opencode https://github.com/sst/opencode <tag> --squash

  resolves any conflicts with ow patches using standard git tooling, with no
  special tooling required beyond git itself.

  The binary is built from the local subtree source during CI, so no third-party
  binary download is required at release time.

  Scenario: opencode source is present in the repository without any external fetch
    Given the ow-agent-orchestration repository is checked out
    Then the directory opencode/packages/opencode/src/ exists
    And the file opencode/packages/opencode/package.json exists

  Scenario: the logo patch rewrites the "opencode" glyph to "ow"
    Given the ow-agent-orchestration repository is checked out
    Then opencode/packages/opencode/src/cli/logo.ts defines a logo with two halves named "left" and "right"
    And each half has exactly 4 rows
    And no row in either half is wider than 8 characters
    And opencode/packages/opencode/src/cli/ui.ts defines a wordmark that reads "ow"

  Scenario: the opencode git history records both the upstream incorporation and ow patches
    Given the git log of the opencode/ prefix
    Then the git history includes a commit that incorporated the upstream opencode source
    And the git history includes a commit that applies ow-specific changes

  Scenario: the release workflow builds the binary from the local subtree
    Given the release workflow at .github/workflows/release.yml
    Then it installs dependencies from opencode/
    And it runs the build script at opencode/packages/opencode/script/build.ts
    And it uploads the resulting opencode-linux-x64.tar.gz as a release asset
    And it does not download a pre-built binary from any external URL
