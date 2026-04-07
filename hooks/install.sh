#!/bin/bash
# Install Provenance Armor hook into Gemini CLI
#
# Usage: ./install.sh [project-dir]
#   project-dir: Path to your project (default: current directory)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ARMOR_ROOT="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="${1:-.}"
GEMINI_DIR="$PROJECT_DIR/.gemini"

echo "Provenance Armor — Gemini CLI Hook Installer"
echo "============================================="
echo ""
echo "  Armor root:  $ARMOR_ROOT"
echo "  Project dir: $(cd "$PROJECT_DIR" && pwd)"
echo ""

# Ensure .gemini directory exists
mkdir -p "$GEMINI_DIR"

# Check if settings.json already exists
SETTINGS="$GEMINI_DIR/settings.json"
if [ -f "$SETTINGS" ]; then
    echo "  Found existing $SETTINGS"
    echo "  Please manually add the hook configuration from:"
    echo "  $SCRIPT_DIR/settings.json"
    echo ""
    echo "  Add to your hooks.BeforeTool array:"
    echo '  {'
    echo '    "matcher": "shell|run_shell_command|write_file|delete_file|edit",'
    echo '    "hooks": [{'
    echo '      "name": "provenance-armor",'
    echo '      "type": "command",'
    echo "      \"command\": \"python3 $ARMOR_ROOT/hooks/provenance_armor_hook.py\","
    echo '      "timeout": 10000'
    echo '    }]'
    echo '  }'
else
    # Create settings.json with the hook
    cat > "$SETTINGS" << SETTINGSEOF
{
  "hooks": {
    "BeforeTool": [
      {
        "matcher": "shell|run_shell_command|write_file|delete_file|edit",
        "hooks": [
          {
            "name": "provenance-armor",
            "type": "command",
            "command": "python3 $ARMOR_ROOT/hooks/provenance_armor_hook.py",
            "timeout": 10000
          }
        ]
      }
    ]
  }
}
SETTINGSEOF
    echo "  Created $SETTINGS with Provenance Armor hook"
fi

echo ""
echo "Done. Provenance Armor will intercept tool calls in this project."
echo "Run 'gemini' in $PROJECT_DIR to test."
