#!/bin/bash
set -e

# Folders to exclude from Docker builds
EXCLUDED_FOLDERS=("configs" "clap" "infrastructure" "scripts" ".github")

# Get manual override from first argument (optional)
MANUAL_FOLDER="$1"

# Manual override
if [ -n "$MANUAL_FOLDER" ]; then
  echo "folders=[\"$MANUAL_FOLDER\"]" >> "$GITHUB_OUTPUT"
  echo "Manual override: Building $MANUAL_FOLDER"
  exit 0
fi

# Get git root directory and cd to it
GIT_ROOT=$(git rev-parse --show-toplevel)
cd "$GIT_ROOT"
echo "Working from git root: $GIT_ROOT"

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

  # Combine both and find folders (not just Dockerfile changes)
  FOLDERS=$(echo -e "$CHANGED_FILES\n$COMMITTED_FILES" \
    | grep -v '^$' \
    | xargs -r dirname \
    | grep -v '^\.$' \
    | sort -u)
fi

# Filter out excluded folders AND verify Dockerfile exists
FILTERED_FOLDERS=""
for folder in $FOLDERS; do
  # Extract the base folder name (first part of path)
  BASE_FOLDER=$(echo "$folder" | cut -d'/' -f1)

  # Skip if it's "." or ".."
  if [ "$BASE_FOLDER" = "." ] || [ "$BASE_FOLDER" = ".." ]; then
    echo "Skipping invalid folder: $BASE_FOLDER"
    continue
  fi

  # Check if it's in the excluded list
  EXCLUDED=false
  for excluded in "${EXCLUDED_FOLDERS[@]}"; do
    if [ "$BASE_FOLDER" = "$excluded" ]; then
      EXCLUDED=true
      echo "Filtering out excluded folder: $folder"
      break
    fi
  done

  # Skip if excluded
  if [ "$EXCLUDED" = true ]; then
    continue
  fi

  # Check if Dockerfile exists in this folder
  if [ -f "$BASE_FOLDER/Dockerfile" ]; then
    echo "✓ Found Dockerfile in: $BASE_FOLDER"
    FILTERED_FOLDERS="$FILTERED_FOLDERS$BASE_FOLDER"$'\n'
  else
    echo "✗ No Dockerfile in: $BASE_FOLDER (skipping)"
  fi
done

# Remove trailing newline, deduplicate, and use filtered folders
FOLDERS=$(echo -n "$FILTERED_FOLDERS" | grep -v '^$' | sort -u || echo "")

# Convert to JSON array
if [ -z "$FOLDERS" ]; then
  JSON="[]"
else
  JSON=$(printf '%s\n' $FOLDERS | jq -R . | jq -s .)
fi

# Output results
if [ -n "$GITHUB_OUTPUT" ]; then
  echo "folders=$JSON" >> "$GITHUB_OUTPUT"
fi

echo "Detected folders: $JSON"

# For local testing, also print as newline-separated list
if [ -z "$GITHUB_OUTPUT" ]; then
  echo ""
  if [ -n "$FOLDERS" ]; then
    echo "Folders to build:"
    echo "$FOLDERS"
  else
    echo "No folders to build (all filtered or no Dockerfiles found)"
  fi
fi