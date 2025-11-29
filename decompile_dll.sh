#!/bin/bash
# Decompile BibitesAssembly.dll from Steam to local mod/decompiled directory
# This gives us readable C# source for exploring game state structures

set -e

# Add dotnet tools to PATH if not already there
export PATH="$PATH:$HOME/.dotnet/tools"

GAME_DIR="$HOME/.steam/steam/steamapps/common/The Bibites"
DLL_PATH="$GAME_DIR/The Bibites_Data/Managed/BibitesAssembly.dll"
OUTPUT_DIR="$(dirname "$0")/mod/decompiled"

echo "=== Decompiling BibitesAssembly.dll ==="

# Check if ilspycmd is available
if ! command -v ilspycmd &> /dev/null; then
    echo "❌ ilspycmd not found"
    echo ""
    echo "Install with:"
    echo "  dotnet tool install -g ilspycmd"
    echo ""
    echo "Then add to PATH (if not already):"
    echo "  export PATH=\"\$PATH:\$HOME/.dotnet/tools\""
    exit 1
fi

# Check if DLL exists
if [ ! -f "$DLL_PATH" ]; then
    echo "❌ BibitesAssembly.dll not found at: $DLL_PATH"
    echo ""
    echo "Expected game location:"
    echo "  $GAME_DIR"
    exit 1
fi

# Clean old decompiled code
if [ -d "$OUTPUT_DIR" ]; then
    echo "🧹 Removing old decompiled code..."
    rm -rf "$OUTPUT_DIR"
fi

# Decompile
echo "🔍 Decompiling to: $OUTPUT_DIR"
ilspycmd "$DLL_PATH" --nested-directories --project -o "$OUTPUT_DIR"

echo ""
echo "✅ Decompilation complete!"
echo ""
echo "=== Explore the code ==="
echo "Key locations:"
echo "  Pause/Speed:     mod/decompiled/ManagementScripts/TimeController.cs"
echo "  Selection:       mod/decompiled/ManagementScripts/UserControl.cs"
echo "  Organism data:   mod/decompiled/SimulationScripts/BibiteScripts/"
echo ""
echo "Search for keywords:"
echo "  grep -r 'keyword' mod/decompiled/"
