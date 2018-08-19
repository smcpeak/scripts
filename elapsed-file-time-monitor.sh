#!/bin/sh
# continually print the elapsed time since the latest file was created

# This is meant to be run in a directory that has files being created
# periodically, such as the directory with video capture files.  It
# continually prints the time difference between the latest timestamp in
# the current directory and the current time.

# Put a newline to separate from the prompt.
echo ""

# Run until Ctrl+C.
while true; do
  # Get name of last modified file.
  latestFname=$(/bin/ls --sort=time -r | tail -1)

  # Get the unix time of its "birth" time.
  latest=$(stat -c "%W" "$latestFname")

  # Get current time.
  cur=$(date +%s)

  # Elapsed time.
  s=$(expr $cur - $latest)

  # Convert to minutes.
  m=$(expr $s / 60)

  # Print it such that the output overwrites itself.
  printf "Elapsed: $m minutes    \r"

  # I only care about accuracy of one minute.
  sleep 60
done

# EOF
