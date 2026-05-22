#!/usr/bin/env bash
# Run the full ai-synapse test suite.
# - pytest for Python unit tests under tests/
# - bash-driven smoke tests for shell entry points
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "==> pytest tests/"
python3 -m pytest tests/ -v

echo ""
echo "==> bash tests/test_version_bump_check.sh"
bash tests/test_version_bump_check.sh

echo ""
echo "==> bash tests/test_tag_dev.sh"
bash tests/test_tag_dev.sh

echo ""
echo "==> bash tests/test_lockfile_cli.sh"
bash tests/test_lockfile_cli.sh

echo ""
echo "==> bash tests/test_pins_cli.sh"
bash tests/test_pins_cli.sh

echo ""
echo "==> bash tests/test_doctor_cli.sh"
bash tests/test_doctor_cli.sh

echo ""
echo "==> bash tests/test_drift_cli.sh"
bash tests/test_drift_cli.sh

echo ""
echo "==> bash tests/test_install_force.sh"
bash tests/test_install_force.sh

echo ""
echo "==> bash tests/test_clerk_cli.sh"
bash tests/test_clerk_cli.sh

echo ""
echo "==> bash tests/test_clerk_auth_cli.sh"
bash tests/test_clerk_auth_cli.sh

echo ""
echo "==> bash tests/test_telemetry_cli.sh"
bash tests/test_telemetry_cli.sh

echo ""
echo "All test suites passed."
