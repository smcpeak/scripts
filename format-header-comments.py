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
import re                    # re.compile
import sys                   # sys.stdin
import traceback             # traceback.print_exc

from typing import Any, Match, Pattern, TextIO, Union
from boilerplate import *


def main() -> None:
  # Parse command line.
  parser = argparse.ArgumentParser(
    description="Read in a set of #includes, write it out with "+
                "aligned comments.")
  opts = parser.parse_args()

  # All input lines.
  inputLines: list[str] = sys.stdin.readlines()

  # Length of the longest code line, ignoring trailing whitespace and
  # comment.  The initial value is the minimum column number.
  longestLength: int = 40

  # For each input line, either a tuple of (code, comment) or a string
  # that is just the code (which could itself be a comment, if the input
  # line only has a comment).
  parsedLines: list[Union[tuple[str, str], str]] = []

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
      code: str = m.group(1)
      comment: str = m.group(3)

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


if __name__ == "__main__":
  call_main(main)


# EOF
