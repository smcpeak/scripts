#!/usr/bin/env python3
"""
This script is a hello-world Python template.
"""

import argparse              # argparse
import os                    # os.getenv
import signal                # signal.signal
import sys                   # sys.argv, sys.stderr
import time                  # time.sleep
import traceback             # traceback.print_exc


# -------------- BEGIN: boilerplate -------------
# These are things I add at the start of every Python program to
# allow better error reporting.

class Error(Exception):
  """A condition to be treated as an error."""
  pass

def die(message):
  """Throw a fatal Error with message."""
  raise Error(message)

# Ctrl-C: interrupt the interpreter instead of raising an exception.
signal.signal(signal.SIGINT, signal.SIG_DFL)

def call_main():
  """Call main() and catch exceptions."""
  try:
    main()

  except SystemExit as e:
    raise      # Let this one go, otherwise sys.exit gets "caught".

  except BaseException as e:
    print(f"{type(e).__name__}: {str(e)}", file=sys.stderr)
    if (os.getenv("DEBUG")):
      traceback.print_exc(file=sys.stderr)
    sys.exit(2)
# --------------- END: boilerplate --------------


# Some example code doing common, useful things in Python.
def main():
  # Print without an implicit newline.
  print("Hello, ", end="")

  # Ordinary printing with an implicit newline.
  print("world.")

  # Print with f-string interpolation.
  print(f"There are {len(sys.argv)} arguments:")

  # Iteration with a explicit index variable.
  for index, argument in enumerate(sys.argv):
    print(f"  [{index}]: {argument}")


  # Command line parsing with 'argparse'.
  parser = argparse.ArgumentParser()

  # Flag option (no argument).
  parser.add_argument("--die", action="store_true", help="Call die().")

  # Option with an integer argument.
  parser.add_argument("--sleep", metavar="N", type=int, help="Call sleep(N).")

  # Positional arguments.
  parser.add_argument("args", nargs="*", help="Positional arguments.")

  # Parse 'sys.argv'.
  opts = parser.parse_args()


  # f-string interpolation prints lists like:
  #   ['x', 'y', 'z']
  print(f"Positional arguments: {opts.args}.")

  # Conjuction in an 'if'.
  if opts.die and opts.sleep != None:
    die("You passed both --die and --sleep.")

  # Test the flag option.
  if opts.die:
    die("Calling die() due to --die.")

  # Test the option with argument.  Note that "if opts.sleep" would not
  # fire for "--sleep 0" because 0 is considered falsy.
  if opts.sleep != None:
    seconds = opts.sleep
    print(f"Sleeping for {seconds} seconds due to --sleep.")
    time.sleep(seconds)
    print("Done sleeping.")

call_main()


# EOF
