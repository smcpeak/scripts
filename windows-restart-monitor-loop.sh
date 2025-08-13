#!/bin/sh
# Run `windows-restart-monitor.py` in a loop.

if [ "x$2" = "x" ]; then
  printf "usage: $0 <python program> <seconds between queries> <warn hours>\n"
  exit 2
fi

# This requires the python program as an argument because the python on
# the PATH is probably Cygwin Python, but the Python script to run
# requires Windows Python.
python="$1"

seconds="$2"
hours="$3"

monitor=$(cygpath -m $(which windows-restart-monitor.py))

while true; do
  #echo "$python" "$monitor" -warn "$hours"
  "$python" "$monitor" -warn "$hours"
  sleep "$seconds"
done

# EOF
