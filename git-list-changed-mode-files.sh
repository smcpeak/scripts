#!/bin/sh
# List files that are regarded as having changed only because of permissions.

# Written by ChatGPT.

git diff --diff-filter=M --name-status | awk '$1 == "M" {print $2}' | while read file; do
  if git diff "$file" | grep -q '^old mode'; then
    echo "$file"
  fi
done

# EOF
