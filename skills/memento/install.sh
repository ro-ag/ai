#!/bin/sh
# Memento skill installer — no clone needed. Installs runtime CLI + skill markdown
# for Claude Code, Codex, Copilot CLI, Gemini CLI (skill dirs). Cursor/Kimi/etc.:
# paste the AGENTS.md pointer snippet from README.md afterwards.
#
# Install:       curl -fsSL https://raw.githubusercontent.com/ro-ag/ai/main/skills/memento/install.sh | sh
# Private fork:  gh api repos/YOU/FORK/contents/skills/memento/install.sh -H "Accept: application/vnd.github.raw" | MEMENTO_REPO=YOU/FORK sh
#
# Env: MEMENTO_REPO (default ro-ag/ai), MEMENTO_BRANCH (default main),
#      GH_TOKEN (for curl against a private fork), MEMENTO_RULES_DIR (optional
#      config.json rules_dir for global promoted rules).
set -eu

REPO="${MEMENTO_REPO:-ro-ag/ai}"
BRANCH="${MEMENTO_BRANCH:-main}"
RAW="https://raw.githubusercontent.com/$REPO/$BRANCH/skills/memento"
DEST="$HOME/.agents/memento"

fetch() { # $1 = filename, $2 = destination path
    if [ -n "${GH_TOKEN:-}" ] && command -v curl >/dev/null 2>&1 &&
        curl -fsSL -H "Authorization: token $GH_TOKEN" "$RAW/$1" -o "$2" 2>/dev/null; then
        return 0
    fi
    if command -v curl >/dev/null 2>&1 && curl -fsSL "$RAW/$1" -o "$2" 2>/dev/null; then
        return 0
    fi
    if command -v gh >/dev/null 2>&1 &&
        gh api "repos/$REPO/contents/skills/memento/$1?ref=$BRANCH" \
            -H "Accept: application/vnd.github.raw" >"$2" 2>/dev/null; then
        return 0
    fi
    echo "memento install: cannot fetch $1 — check network; a private fork needs GH_TOKEN or the gh CLI logged in" >&2
    exit 1
}

mkdir -p "$DEST" "$HOME/.agents/skills/memento" "$HOME/.claude/skills/memento"
fetch memento.py "$DEST/memento.py"
for f in SKILL.md BOOTSTRAP.md; do
    fetch "$f" "$HOME/.agents/skills/memento/$f"
    cp "$HOME/.agents/skills/memento/$f" "$HOME/.claude/skills/memento/$f"
done
if [ -n "${MEMENTO_RULES_DIR:-}" ]; then
    printf '{"rules_dir": "%s"}\n' "$MEMENTO_RULES_DIR" >"$DEST/config.json"
fi

python3 "$DEST/memento.py" check >/dev/null
echo "memento installed."
echo "  CLI    : python3 ~/.agents/memento/memento.py check"
echo "  skills : ~/.claude/skills/memento (Claude), ~/.agents/skills/memento (Codex/Copilot/Gemini)"
echo "  Cursor/Kimi/opencode/...: paste the AGENTS.md pointer snippet — https://github.com/$REPO/tree/$BRANCH/skills/memento#per-tool-pickup"
