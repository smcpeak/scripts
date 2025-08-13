# boilerplate.py
"""
Definitions to enhance error reporting in a Python program.

To use, first import all the symbols:

  from boilerplate import *

Then define `main` somewhere:

  main() -> None:
    ...

Finally, at the end, call it via `call_main`:

  if __name__ == "__main__":
    call_main(main)

Principally, this suppresses the stack trace on exceptions unless the
DEBUG envvar is set to a non-zero value.  Instead, it prints a single
line that includes the exception class name (since unfortunately some
exceptions rely on that to communicate the problem) and any text string
that accompanies it, falling back to the file:line where it was raised
if there is no text.

It also offers a few convenience functions for error reporting, such as
the `die` function.

Finally, it changes Ctrl+C so it terminates the script, similar to most
other programs, rather than raising an exception (which is often
ineffective at stopping the program).
"""

import os                    # getenv
import signal                # signal
import sys                   # argv, stderr, stdin, exc_info
import traceback             # print_exc

from typing import Callable, NoReturn


# Positive if debug is enabled, with higher values enabling more printing.
debugLevel: int = 0
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


def die(message: str) -> NoReturn:
  """Throw a fatal Error with message."""
  raise Error(message)


def exceptionMessage(e: BaseException) -> str:
  """Turn exception 'e' into a human-readable message."""

  t = type(e).__name__
  s = str(e)

  if s:
    return f"{t}: {s}"

  else:
    # If no extra info, try to get the location of the `raise`.  This is
    # needed for AssertionError, for example.
    _, _, exc_traceback = sys.exc_info()
    if exc_traceback:
      # Get the last frame.
      frame = traceback.extract_tb(exc_traceback)[-1]
      fname = os.path.basename(frame.filename)
      return f"{t} at {fname}:{frame.lineno}"

    else:
      # All we have is the exception class name.
      return f"{t}"


def call_main(main: Callable[[], None]) -> None:
  """Call `main()` and catch exceptions."""
  try:
    main()

  except SystemExit as e:
    raise      # Let this one go, otherwise sys.exit gets "caught".

  except BaseException as e:
    print(f"{exceptionMessage(e)}", file=sys.stderr)
    if (debugLevel >= 1):
      traceback.print_exc(file=sys.stderr)
    sys.exit(2)


# EOF
