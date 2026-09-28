#!/bin/sh
# Copies the agent, the two commands and the skills into ~/.claude.
# Replaces only folders and files with our names; everything else there is left alone.
set -e
here=$(cd "$(dirname "$0")" && pwd)
claude_dir=${CLAUDE_DIR:-$HOME/.claude}

py=$(command -v python3 || command -v python || true)
if [ -z "$py" ] || ! "$py" -c "import sys; sys.exit(sys.version_info < (3, 11))"; then
    echo "Needs Python 3.11 or later on PATH." >&2
    exit 1
fi

for kind in agents commands skills; do
    mkdir -p "$claude_dir/$kind"
    for item in "$here/$kind"/*; do
        name=$(basename "$item")
        rm -rf "$claude_dir/$kind/$name"
        cp -R "$item" "$claude_dir/$kind/$name"
        echo "installed $kind/$name"
    done
done
echo "Done. Start a new Claude Code session to pick them up."
