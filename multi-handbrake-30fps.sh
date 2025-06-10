#!/bin/sh
# Run handbrake on multiple files.

for fn in "$@"; do
  echo "------ $fn ------"
  d=$(dirname "$fn")
  b=$(basename "$fn")

  # The script only works if the source file is the current directory.
  (cd "$d" && handbrake-30fps.sh "$b") || break
done

# EOF
