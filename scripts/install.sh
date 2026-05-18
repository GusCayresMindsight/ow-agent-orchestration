#!/usr/bin/env bash
# install.sh — installs ow and its bundled opencode for the current user
#
# Overrideable environment variables (used by the test suite):
#   OW_PACKAGE           Python package to install (default: ow-agent-orchestration)
#   OW_OPENCODE_BASE_URL Base URL for opencode tarball downloads
#                        (default: https://github.com/anomalyco/opencode/releases/latest/download)

set -euo pipefail

OW_PACKAGE="${OW_PACKAGE:-ow-agent-orchestration}"
OW_OPENCODE_BASE_URL="${OW_OPENCODE_BASE_URL:-https://github.com/anomalyco/ow-agent-orchestration/releases/latest/download}"
INSTALL_BIN="${HOME}/.local/bin"
OPENCODE_DIR="${HOME}/.local/share/ow"
OPENCODE_BIN_DIR="${OPENCODE_DIR}/bin"

# ── Detect architecture ──────────────────────────────────────────────────────
ARCH=$(uname -m)
case "${ARCH}" in
    x86_64)  OC_ARCH="x64" ;;
    aarch64) OC_ARCH="arm64" ;;
    *)
        echo "error: unsupported architecture: ${ARCH}" >&2
        exit 1
        ;;
esac

OC_TARBALL="opencode-linux-${OC_ARCH}.tar.gz"

# ── 1. Bootstrap uv if not present ──────────────────────────────────────────
if ! command -v uv &>/dev/null; then
    echo "uv not found — installing..."
    curl -LsSf https://astral.sh/uv/install.sh | env HOME="${HOME}" sh
    export PATH="${INSTALL_BIN}:${PATH}"
fi

# ── 2. Install the ow Python package via uv ──────────────────────────────────
echo "Installing ow..."
uv tool install "${OW_PACKAGE}"

# ── 3. Download and unpack the bundled opencode binary ───────────────────────
mkdir -p "${OPENCODE_BIN_DIR}"

TEMP_TAR=$(mktemp -t opencode-XXXXXX.tar.gz)
TEMP_DIR=$(mktemp -d)
# shellcheck disable=SC2064
trap 'rm -rf "${TEMP_TAR}" "${TEMP_DIR}"' EXIT

echo "Downloading opencode (linux/${OC_ARCH})..."
curl -fsSL "${OW_OPENCODE_BASE_URL}/${OC_TARBALL}" -o "${TEMP_TAR}"
tar -xzf "${TEMP_TAR}" -C "${TEMP_DIR}"

OC_BIN=$(find "${TEMP_DIR}" -name "opencode" -type f | head -n1)
if [ -z "${OC_BIN}" ]; then
    echo "error: opencode binary not found inside ${OC_TARBALL}" >&2
    exit 1
fi

cp "${OC_BIN}" "${OPENCODE_BIN_DIR}/opencode"
chmod +x "${OPENCODE_BIN_DIR}/opencode"

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo "ow installed to ${INSTALL_BIN}/ow"
echo "opencode bundled at ${OPENCODE_BIN_DIR}/opencode"

if [[ ":${PATH}:" != *":${INSTALL_BIN}:"* ]]; then
    echo ""
    echo "Add ${INSTALL_BIN} to your PATH:"
    echo "  echo 'export PATH=\"\${HOME}/.local/bin:\${PATH}\"' >> ~/.bashrc"
fi
