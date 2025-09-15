#!/bin/sh
# Make a staged file executable.

if [ "x$1" = "x" ]; then
  echo "usage: $0 staged-file"
  echo "Makes <staged-file> executable in the index."
  exit 2
fi

runecho git update-index --chmod=+x "$1"

# EOF
