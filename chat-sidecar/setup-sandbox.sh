#!/bin/bash
# Setup the sandbox worktree for the chat sidecar
set -e

MAIN_REPO="/Users/palmer/Work/Dev/Vault"
SANDBOX_DIR="/Users/palmer/Work/Dev/.vault-sandbox"

echo "Setting up sandbox worktree..."

# Clean up existing worktree if present
if [ -d "$SANDBOX_DIR" ]; then
    echo "Removing existing sandbox..."
    cd "$MAIN_REPO"
    git worktree remove "$SANDBOX_DIR" --force 2>/dev/null || rm -rf "$SANDBOX_DIR"
fi

# Create fresh worktree from HEAD
cd "$MAIN_REPO"
git worktree add "$SANDBOX_DIR" HEAD --detach

# Symlink node_modules
ln -sf "$MAIN_REPO/node_modules" "$SANDBOX_DIR/node_modules"

# Verify
echo "Sandbox created at: $SANDBOX_DIR"
echo "Testing vite build..."
cd "$SANDBOX_DIR"
npx vite build --mode development > /dev/null 2>&1 && echo "Build OK!" || echo "Build FAILED"
