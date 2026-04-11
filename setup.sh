#!/bin/bash

# setup.sh - Codex Elixir Phoenix Installation Script
# This script injects the .codex framework into a target Phoenix project.

set -e

# --- Configuration ---
SOURCE_DIR=".codex"

# --- Functions ---
show_help() {
    echo "Usage: ./setup.sh <target_project_path>"
    echo ""
    echo "Arguments:"
    echo "  target_project_path    The absolute or relative path to your Phoenix project root."
    echo ""
    echo "Example:"
    echo "  ./setup.sh ~/projects/my_phoenix_app"
}

# --- Validation ---
TARGET_PATH=$1

if [ -z "$TARGET_PATH" ]; then
    show_help
    exit 1
fi

if [ ! -d "$TARGET_PATH" ]; then
    echo "Error: Target directory '$TARGET_PATH' does not exist."
    exit 1
fi

if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory '$SOURCE_DIR' not found. Please run this script from the root of the codex-elixir-phoenix distribution."
    exit 1
fi

# Resolve target path to absolute path
TARGET_ABS_PATH=$(cd "$TARGET_PATH" && pwd)

echo "🚀 Injecting Codex framework into: $TARGET_ABS_PATH"

# --- Implementation ---
# Copy .codex directory to target
# Using -r for recursive
# Note: Since tests/ is at the root of the distribution repo, NOT inside .codex/, 
# simply copying .codex/ naturally excludes tests/.
cp -r "$SOURCE_DIR" "$TARGET_ABS_PATH/"

echo "✅ Codex successfully injected into: $TARGET_ABS_PATH"
echo "💡 To begin, run: cd \"$TARGET_PATH\" && codex \$phx-intro"
