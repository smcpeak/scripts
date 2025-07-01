#!/usr/bin/env python3
"""
Read a set of #includes on stdin and write it with appropriate directory
names prepended to the file names.

For example, when given:

  #include "something-in-smbase.h"     // foo
  #include "something-in-ast.h"        // bar
  #include "something-else.h"          // other

the output would be:

  #include "smbase/something-in-smbase.h"     // foo
  #include "ast/something-in-ast.h"        // bar
  #include "something-else.h"          // other

Note that this script does not align the comments.  See
format-header-comments.py for that capability.
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


filesInDir: dict[str, dict[str, bool]]


def get_map_of_subdir_to_files() -> dict[str, dict[str, bool]]:
  """Return a dictionary that maps each subdirectory of the current
  directory to the set of files in it, where each set is a dictionary
  from the name to True."""

  result: dict[str, dict[str, bool]] = {}

  for d in os.listdir("."):
    if os.path.isdir(d):
      files: dict[str, bool] = {}

      for f in os.listdir(d):
        if os.path.isfile(os.path.join(d, f)):
          files[f] = True

      result[d] = files

  return result


def main():
  # Parse command line.
  parser = argparse.ArgumentParser(
    description="Read in a set of #includes, write it out with "+
                "directory names added.")
  opts = parser.parse_args()

  # All input lines.
  inputLines = sys.stdin.readlines()

  # An #include line:
  #   1. Optional preceding whitespace.
  #   2. The file name.
  #   3. Optional trailing contents, such as a comment.
  includeLineRE = re.compile(R'^(\s*)#include "([^"]+)"(.*)$')

  # Files in subdirectories.
  subdir_to_files = get_map_of_subdir_to_files()

  # Parse lines.
  for line in inputLines:
    # Strip line endings.
    line = line.rstrip("\r\n")

    printed = False

    if m := includeLineRE.match(line):
      leading = m.group(1)
      fname = m.group(2)
      trailing = m.group(3)

      # If `fname` is in the map, insert its directory name.
      for d, files in subdir_to_files.items():
        if fname in files:
          print(f'{leading}#include "{d}/{fname}"{trailing}')
          printed = True
          break

    if not printed:
      # Print the original line.
      print(line)


if __name__ == "__main__":
  call_main()


# EOF
