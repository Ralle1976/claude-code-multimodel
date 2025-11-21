#!/usr/bin/env bash

#
# Upgrade Script: Switch to Circuit Breaker Versions
#
# This script upgrades the openai-cli and gemini-cli commands
# to use the improved versions with circuit breaker protection.
#

set -e

PLUGIN_DIR="/home/ralle/claude-code-multimodel/plugins/multi-provider-cli-chat"
COMMANDS_DIR="$HOME/.claude/commands"

echo "=== Multi-Provider CLI Chat - Circuit Breaker Upgrade ==="
echo ""

# Check if plugin directory exists
if [ ! -d "$PLUGIN_DIR" ]; then
  echo "❌ Plugin directory not found: $PLUGIN_DIR"
  exit 1
fi

# Check if improved versions exist
if [ ! -f "$PLUGIN_DIR/commands/openai-cli-improved.cjs" ]; then
  echo "❌ openai-cli-improved.cjs not found"
  exit 1
fi

if [ ! -f "$PLUGIN_DIR/commands/gemini-cli-improved.cjs" ]; then
  echo "❌ gemini-cli-improved.cjs not found"
  exit 1
fi

echo "✓ Found improved CLI versions"
echo ""

# Create backup directory
BACKUP_DIR="$PLUGIN_DIR/commands/backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "Created backup directory: $BACKUP_DIR"

# Backup original versions
if [ -f "$PLUGIN_DIR/commands/openai-cli.cjs" ]; then
  cp "$PLUGIN_DIR/commands/openai-cli.cjs" "$BACKUP_DIR/openai-cli.cjs"
  echo "✓ Backed up openai-cli.cjs"
fi

if [ -f "$PLUGIN_DIR/commands/gemini-cli.cjs" ]; then
  cp "$PLUGIN_DIR/commands/gemini-cli.cjs" "$BACKUP_DIR/gemini-cli.cjs"
  echo "✓ Backed up gemini-cli.cjs"
fi

echo ""

# Replace with improved versions
echo "Upgrading to circuit breaker versions..."
cp "$PLUGIN_DIR/commands/openai-cli-improved.cjs" "$PLUGIN_DIR/commands/openai-cli.cjs"
echo "✓ Upgraded openai-cli.cjs"

cp "$PLUGIN_DIR/commands/gemini-cli-improved.cjs" "$PLUGIN_DIR/commands/gemini-cli.cjs"
echo "✓ Upgraded gemini-cli.cjs"

echo ""

# Update symlinks in ~/.claude/commands/
if [ -L "$COMMANDS_DIR/openai-cli" ]; then
  echo "Updating openai-cli symlink..."
  rm "$COMMANDS_DIR/openai-cli"
  ln -s "$PLUGIN_DIR/commands/openai-cli.cjs" "$COMMANDS_DIR/openai-cli"
  echo "✓ Updated openai-cli symlink"
fi

if [ -L "$COMMANDS_DIR/gemini-cli" ]; then
  echo "Updating gemini-cli symlink..."
  rm "$COMMANDS_DIR/gemini-cli"
  ln -s "$PLUGIN_DIR/commands/gemini-cli.cjs" "$COMMANDS_DIR/gemini-cli"
  echo "✓ Updated gemini-cli symlink"
fi

echo ""
echo "=== Upgrade Complete ==="
echo ""
echo "New Features:"
echo "  • Circuit Breaker Protection (3 failures in 5 min → 10 min cooldown)"
echo "  • Server Error Detection (500, 502, 503, 504)"
echo "  • Timeout Handling (5 minute max)"
echo "  • Input Size Validation (10MB max)"
echo "  • State Persistence:"
echo "    - ~/.claude-openai-cli-state.json"
echo "    - ~/.claude-gemini-cli-state.json"
echo ""
echo "Backup Location: $BACKUP_DIR"
echo ""
echo "To test: Restart Claude Code and try /openai-cli or /gemini-cli"
echo ""
