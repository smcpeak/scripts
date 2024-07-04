#!/usr/bin/env python3
"""
Read a set of #includes on stdin and write it with aligned comments.

The input is something like:

  #include "foo.h" // foo
  #include "bar.h"   // bar

and the output would then be:

  #include "foo.h"           // foo
  #include "bar.h"           // bar

with all of the comments aligned to a column that is a multiple of 10.
"""

import argparse              # argparse
import os                    # os.getenv
import re                    # re.compile
import signal                # signal.signal
import sys                   # sys.argv, sys.stderr, sys.stdin
import traceback             # traceback.print_exc

from typing import Any, Match, Pattern, TextIO


# -------------- BEGIN: boilerplate -------------
# These are things I add at the start of every Python program to
# allow better error reporting.

# Positive if debug is enabled, with higher values enabling more printing.
debugLevel = 0
if debugEnvVal := os.getenv("DEBUG"):
  debugLevel = int(debugEnvVal)

def debugPrint(str: str) -> None:
  """Debug printout when DEBUG >= 2."""
  if debugLevel >= 2:
    print(str)

# Ctrl-C: interrupt the interpreter instead of raising an exception.
signal.signal(signal.SIGINT, signal.SIG_DFL)

class Error(Exception):
  """A condition to be treated as an error."""
  pass

def die(message: str) -> None:
  """Throw a fatal Error with message."""
  raise Error(message)

def exceptionMessage(e: BaseException) -> str:
  """Turn exception 'e' into a human-readable message."""
  t = type(e).__name__
  s = str(e)
  if s:
    return f"{t}: {s}"
  else:
    return f"{t}"

def call_main() -> None:
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
    description="Read in a set of #includes, write it out with "+
                "aligned comments.")
  opts = parser.parse_args()

  # All input lines.
  inputLines = sys.stdin.readlines()

  # Length of the longest code line, ignoring trailing whitespace and
  # comment.  The initial value is the minimum column number.
  longestLength = 40

  # For each input line, either a tuple of (code, comment) or a string
  # that is just the code (which could itself be a comment, if the input
  # line only has a comment).
  parsedLines = []

  # A line of code to format should have:
  #   1. Something that ends with non-whitespace.
  #   2. Possibly empty whitespace.
  #   3. A comment.
  codeLineRE = re.compile(R"^(.*\S)(\s*)(//.*)$")

  # Parse lines.
  for line in inputLines:
    # Strip all trailing whitespace from each line.
    line = line.rstrip("\r\n\t ")

    if m := codeLineRE.match(line):
      code = m.group(1)
      comment = m.group(3)

      # Add to the longest length, using +2 because (+1) we want at
      # least one space between the code and the comment, and (+1) to
      # counteract the -1 in the calculation of `codeWidth`.
      if len(code)+2 > longestLength:
        longestLength = len(code)+2

      parsedLines.append((code, comment))

    else:
      parsedLines.append(line)

  # Choose the starting column for comments.  We round up to the next
  # multiple of 10, then subtract 1 because (e.g.) column 40 has 39
  # characters preceding it.
  codeWidth = ((longestLength+9) // 10 * 10) - 1

  # Print them back out, aligning the comments.
  for parsedLine in parsedLines:
    if isinstance(parsedLine, str):
      print(parsedLine)
    else:
      (code, comment) = parsedLine
      padding = (codeWidth - len(code)) * " "
      print(f"{code}{padding}{comment}")


call_main()


# EOF
