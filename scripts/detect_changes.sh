#!/bin/bash
set -e

# Get manual override from first argument (optional)
MANUAL_FOLDER="$1"

# Manual override
if [ -n "$MANUAL_FOLDER" ]; then
  echo "folders=[\"$MANUAL_FOLDER\"]" >> "$GITHUB_OUTPUT"
  echo "Manual override: Building $MANUAL_FOLDER"
  exit 0
fi

# First commit → build all folders with Dockerfile
if [ $(git rev-list --count HEAD) -eq 1 ]; then
  echo "First commit detected - building all Dockerfile folders"
  FOLDERS=$(find . -maxdepth 2 -name Dockerfile -exec dirname {} \; | sed 's|^\./||')
else
  # Use git status to detect changed files (uncommitted changes)
  echo "Detecting changes from git status and git diff..."
  CHANGED_FILES=$(git status --short | awk '{print $2}')

  # Also get committed changes from main branch
  COMMITTED_FILES=$(git diff --name-only origin/main...HEAD 2>/dev/null || echo "")

  # Combine both and find Dockerfile folders
  FOLDERS=$(echo -e "$CHANGED_FILES\n$COMMITTED_FILES" \
    | grep -E '(Dockerfile|/)' \
    | xargs -r dirname \
    | grep -v '^\.$' \
    | sort -u)
fi

# Convert to JSON array
JSON=$(printf '%s\n' $FOLDERS | jq -R . | jq -s .)

# Output results
if [ -n "$GITHUB_OUTPUT" ]; then
  echo "folders=$JSON" >> "$GITHUB_OUTPUT"
fi

echo "Detected folders: $JSON"

# For local testing, also print as newline-separated list
if [ -z "$GITHUB_OUTPUT" ]; then
  echo ""
  echo "Folders to build:"
  echo "$FOLDERS"
fi