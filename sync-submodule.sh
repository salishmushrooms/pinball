#!/bin/bash

# Sync submodule script for MNP data archive
# Handles automatic GitHub action updates to the submodule

echo "Syncing mnp-data-archive submodule..."

# Navigate to submodule directory
cd mnp-data-archive

# Reset any local changes and sync with remote
git fetch origin
git reset --hard origin/main

# Return to main repo
cd ..

# Update the main repo to point to the new submodule commit
git add mnp-data-archive
git status

echo ""
echo "✓ Submodule synced successfully!"
echo ""
echo "If you see changes to commit, run:"
echo "  git commit -m 'Update mnp-data-archive submodule'"
echo "  git push origin main"
