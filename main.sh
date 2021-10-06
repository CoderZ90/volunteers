#!/bin/env bash

git config user.name $GITHUB_ACTOR
git config user.email "${GITHUB_ACTOR}@github.com"

set -eu

echo "Starting"

# Copy old images
git checkout gh-pages
mkdir tmp
cp -r images tmp

# Fetch updated data
git checkout main
python3 src/fetch.py

# Commit
git checkout gh-pages
cp -r tmp/* .
rm -r tmp

git add .
set +e  # Grep succeeds with nonzero exit codes to show results.

if git status | grep 'new file\|modified'
then
    set -e
    git commit -am "Update - $(date)"
    git remote set-url origin "https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git" # includes access token
    git push --force-with-lease origin gh-pages
else
    echo "No changes since last run"
fi

echo "Done"
