#!/usr/bin/env bash
# @name: install
# @description: CLI entry point for installing and managing skill symlinks
# @audience: consumer
# @action: install
# @scope: synapse
set -euo pipefail

# Delegates to lib/common.sh, lib/commands-skills.sh, and lib/commands-manage.sh.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

source "$SCRIPT_DIR/lib/common.sh"
source "$SCRIPT_DIR/lib/commands-skills.sh"
source "$SCRIPT_DIR/lib/commands-manage.sh"

# Main
case "${1:-}" in
    install)        shift; cmd_install "$@" ;;
    agents)         cmd_install_agents ;;
    identity)       cmd_install_identity ;;
    codex)          shift; cmd_install_codex "$@" ;;
    codex-project)  shift; cmd_install_codex_project "$@" ;;
    gemini)         shift; cmd_install_gemini "$@" ;;
    list)           cmd_list ;;
    available)      cmd_available ;;
    clean)          cmd_clean ;;
    doctor)         cmd_doctor_symlinks ;;
    doctor-symlinks) cmd_doctor_symlinks ;;
    zip)            shift; cmd_zip "$@" ;;
    -h|--help|"")   usage ;;
    *)              echo "Unknown command: $1"; usage; exit 1 ;;
esac
