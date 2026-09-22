#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SOURCE="$ROOT/skills/evidence-report"

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

echo "Evidence Report installed for Codex and Claude-compatible Agent Skills."
