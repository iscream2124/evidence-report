#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SOURCE="$ROOT/skills/evidence-report"
INSTALL_CLI=false

if [[ "${1:-}" == "--cli" ]]; then
  INSTALL_CLI=true
elif [[ $# -gt 0 ]]; then
  echo "usage: ./install.sh [--cli]" >&2
  exit 2
fi

install_link() {
  local parent="$1"
  local target="$parent/evidence-report"
  mkdir -p "$parent"
  if [[ -e "$target" || -L "$target" ]]; then
    echo "skip existing: $target"
  else
    ln -s "$SKILL_SOURCE" "$target"
    echo "installed: $target"
  fi
}

install_link "$HOME/.agents/skills"
install_link "$HOME/.claude/skills"

if [[ "$INSTALL_CLI" == true ]]; then
  python3 -m pip install --user "$ROOT"
fi

echo "Evidence Report installed for Codex and Claude-compatible Agent Skills."
[[ "$INSTALL_CLI" == true ]] && echo "CLI installed: evidence-report"
