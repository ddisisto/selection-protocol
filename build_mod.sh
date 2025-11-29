#!/bin/bash
# Build and deploy Selection Protocol BepInEx plugin

set -e

GAME_DIR="$HOME/.steam/steam/steamapps/common/The Bibites"
PLUGIN_DIR="$GAME_DIR/BepInEx/plugins"
PROJECT_DIR="$(dirname "$0")/mod"

echo "=== Building Selection Protocol Plugin ==="
cd "$PROJECT_DIR"
dotnet build -c Release

echo ""
echo "=== Deploying to game ==="
cp bin/Release/netstandard2.1/SelectionProtocol.dll "$PLUGIN_DIR/"
echo "✅ Plugin deployed to: $PLUGIN_DIR/SelectionProtocol.dll"

echo ""
echo "=== Next steps ==="
echo "1. Restart The Bibites to load new plugin version"
echo "2. Check BepInEx log: cat \"$GAME_DIR/BepInEx/LogOutput.log\""
echo "3. Test endpoint: curl http://localhost:5001/health"
