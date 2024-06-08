#!/usr/bin/env python3
"""Rewrite the input as lines centered with dashes.

Example input:

  some text
  // ---- text with dashes ----

Corresponding output:

  // ---------------------------- some text ----------------------------
  // ------------------------ text with dashes -------------------------
"""

import argparse              # argparse
import difflib               # difflib.unified_diff
import os                    # os.getenv
import re                    # re.compile
import signal                # signal.signal
import subprocess            # subprocess.run
import sys                   # sys.argv, sys.stderr
import time                  # time.sleep
import traceback             # traceback.print_exc

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

def main() -> None:
  existingRE = re.compile(r"^(\s*)(\S.*)$")

  for line in sys.stdin:
    line = line.rstrip("\n")
    if m := existingRE.match(line):
      prefix = m.group(1)
      text = m.group(2)
      text = text.strip(" -/")

      numDashes = 72 - len(prefix) - len(text) - len("//   ")
      if numDashes <= 0:
        print(line)

      else:
        numLeftDashes = numDashes // 2
        numRightDashes = numDashes - numLeftDashes

        leftDashes = "-" * numLeftDashes
        rightDashes = "-" * numRightDashes

        print(f"{prefix}// {leftDashes} {text} {rightDashes}")

    else:
      print(line)

call_main()


# EOF
