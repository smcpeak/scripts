#!/usr/bin/env python3
"""
Read some code on stdin and produce a formatted C macro definition.

The input is a sequence of C/C++ lines of code.  The output is a macro
definition that has all lines except the last terminated with a
backslash, with the backslashes all arranged into a single column.

If there are existing backslashes at the ends of lines, they are
stripped first, so their initial presence is irrelevant.

Example input:

  #define mymacro(a,b,c)
    lines \
    of code that are
    ragged and maybe inconsistent about \
    existing backslashes

Corresponding output:

  #define mymacro(a,b,c)                \
    lines                               \
    of code that are                    \
    ragged and maybe inconsistent about \
    existing backslashes

"""

import argparse              # argparse
import os                    # os.getenv
import re                    # re.compile
import signal                # signal.signal
import sys                   # sys.argv, sys.stderr, sys.stdin
import traceback             # traceback.print_exc


# -------------- BEGIN: boilerplate -------------
# These are things I add at the start of every Python program to
# allow better error reporting.

# Positive if debug is enabled, with higher values enabling more printing.
debugLevel = 0
if (os.getenv("DEBUG")):
  debugLevel = int(os.getenv("DEBUG"))

def debugPrint(str):
  """Debug printout when DEBUG >= 2."""
  if debugLevel >= 2:
    print(str)

# Ctrl-C: interrupt the interpreter instead of raising an exception.
#signal.signal(signal.SIGINT, signal.SIG_DFL)

class Error(Exception):
  """A condition to be treated as an error."""
  pass

def die(message):
  """Throw a fatal Error with message."""
  raise Error(message)

def exceptionMessage(e):
  """Turn exception 'e' into a human-readable message."""
  t = type(e).__name__
  s = str(e)
  if s:
    return f"{t}: {s}"
  else:
    return f"{t}"

def call_main():
  """Call main() and catch exceptions."""
  try:
    main()

  except SystemExit as e:
    raise      # Let this one go, otherwise sys.exit gets "caught".

  except BaseException as e:
    print(f"{exceptionMessage(e)}", file=sys.stderr)
    if (debugLevel >= 1):
      traceback.print_exc(file=sys.stderr)
    sys.exit(2)
# --------------- END: boilerplate --------------


def main():
  # Parse command line.
  parser = argparse.ArgumentParser(
    description="Read in some C/C++ code, write it out with an "+
                "aligned column of trailing backslashes.")
  parser.add_argument("--strip", action="store_true",
    help="Just remove existing trailing backslashes.")
  opts = parser.parse_args()

  # All input lines.
  inputLines = sys.stdin.readlines()

  # Index of next input line to parse.
  inputLineIndex = 0

  # Lines after trimming backslashes.
  trimmedLines = []

  # Length of longest trimmed line.
  maxLength = 0

  # Parse lines.
  while inputLineIndex < len(inputLines):
    # Strip all trailing whitespace from each line.
    line = inputLines[inputLineIndex].rstrip("\r\n\t ")
    inputLineIndex += 1

    # If the line ends with a backslash, discard it too.
    if (line[-1:] == "\\"):
      line = line[:-1].rstrip(" \t")

    trimmedLines.append(line);

    if len(line) > maxLength:
      maxLength = len(line)

  # Emit them with backslashes in a single column.
  index = 0
  for line in trimmedLines:
    if opts.strip or index == len(trimmedLines)-1:
      # Strip mode, or last line.
      print(line)
    else:
      padding = ' ' * (maxLength - len(line))
      print(f"{line}{padding} \\")
    index += 1


call_main()


# EOF
