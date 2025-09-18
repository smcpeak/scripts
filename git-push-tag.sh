#!/bin/sh
# Push a single tag.

if [ "x$1" = "x" ]; then
  echo "usage: $0 tagname"
  echo "Pushes <tagname> to the origin server."
  exit 2
fi

runecho git push origin tag "$1"

# EOF
