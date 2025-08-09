#!/usr/bin/env python3
"""
Convert consecutive single-line C/C++ '//' comment blocks into
'/* ... */' blocks.

Reads from stdin and writes to stdout.
"""

import sys

from boilerplate import *
from typing import List


def get_lines() -> List[str]:
  """
  Read all lines from standard input and return them as a list of strings,
  preserving line endings.
  """
  return sys.stdin.read().splitlines(keepends=True)


def write_lines(lines: List[str]) -> None:
  """
  Write the given list of lines to standard output.
  """
  sys.stdout.write(''.join(lines))


def is_comment_with_prefix(line: str) -> bool:
  """
  Return True if the line starts with some whitespace (possibly empty)
  followed immediately by '//' (no other characters between the whitespace
  and the slashes).
  """
  # find first non-whitespace
  idx = 0
  while idx < len(line) and line[idx].isspace() and line[idx] not in '\r\n':
    idx += 1
  # line may have newline characters after whitespace; ensure we don't index past end
  return idx + 1 < len(line) and line[idx:idx + 2] == '//'


def leading_whitespace_of_comment(line: str) -> str:
  """
  Given a line that satisfies is_comment_with_prefix(line), return the leading
  whitespace string (may be empty) that appears before the '//' on that line.
  """
  idx = 0
  while idx < len(line) and line[idx].isspace() and line[idx] not in '\r\n':
    idx += 1
  return line[:idx]


def process_lines(lines: List[str]) -> List[str]:
  """
  Process the input lines and return a new list of lines with the comment-block
  transformations applied.

  The algorithm finds maximal runs of consecutive lines (length >= 2) that all
  start with the identical leading-whitespace string followed by '//'. Each
  such run is converted according to the rules described in the prompt.
  """
  out: List[str] = []
  i = 0
  n = len(lines)

  while i < n:
    line = lines[i]
    # If this line starts with some ws then '//' consider possible block
    if is_comment_with_prefix(line):
      lead = leading_whitespace_of_comment(line)
      # attempt to gather maximal run that have same lead and start with '//'
      j = i
      while j < n and lines[j].startswith(lead) and lines[j][len(lead):].startswith('//'):
        j += 1
      run_len = j - i
      # Only treat as block if at least two consecutive matching lines
      if run_len >= 2:
        # process block from i..j-1
        for k in range(i, j):
          cur = lines[k]
          # rest_after_slashes includes everything after the two slashes, including any spaces and the line ending
          rest_after_slashes = cur[len(lead) + 2:]
          # Determine whether "not followed by anything else on that line"
          # i.e., after the '//' there is nothing except optional whitespace and newline
          rest_stripped = rest_after_slashes.strip('\r\n')
          if rest_stripped.strip() == '':
            # rest contains no non-space characters (only spaces and newline)
            empty_after = True
          else:
            empty_after = False

          # first line
          if k == i:
            # Replace first '//' with '/*' preserving leading whitespace and the rest exactly
            out.append(f"{lead}/*{rest_after_slashes}")
          # intermediate lines (not first and not last)
          elif k < j - 1:
            if empty_after:
              # produce a completely blank line (no whitespace)
              out.append('\n')
            else:
              # replace '//' with two spaces, preserving the rest
              out.append(f"{lead}  {rest_after_slashes}")
          else:
            # k == j-1 : last line of the run
            if empty_after:
              # replace '//' with '*/' preserving leading whitespace
              # ensure it ends with a newline
              if rest_after_slashes.endswith('\n') or rest_after_slashes.endswith('\r'):
                weird = rest_after_slashes[len(rest_after_slashes.rstrip('\r\n')):]
                out.append(f"{lead}*/{weird}")
              else:
                out.append(f"{lead}*/\n")
            else:
              # replace '//' with two spaces on the last line, then append a new line
              out.append(f"{lead}  {rest_after_slashes}")
              # add a separate closing '*/' line indented by the same leading whitespace
              out.append(f"{lead}*/\n")
        # advance past the run
        i = j
        continue
      # else: run length < 2 ; fallthrough and copy single line unchanged
    # default: copy line unchanged
    out.append(line)
    i += 1

  return out


example_input: str = """
Some text to preserve.

// A block
// of
// comments.
The commented entity.

  // Another
  // block.
  Another entity.

    // A
    // third
    // comment.
    //
    Third entity.

  // One line comments are unchanged.

  // Two line comments
  // are changed.

  // First comment para.
  //
  // Second comment para.  Separating lines become blank.
  //
  // Third para.
  Something.
"""

expected_output: str = """
Some text to preserve.

/* A block
   of
   comments.
*/
The commented entity.

  /* Another
     block.
  */
  Another entity.

    /* A
       third
       comment.
    */
    Third entity.

  // One line comments are unchanged.

  /* Two line comments
     are changed.
  */

  /* First comment para.

     Second comment para.  Separating lines become blank.

     Third para.
  */
  Something.
"""

def run_unit_test() -> None:
  """
  Simple unit test.
  """
  lines = example_input.splitlines(keepends=True)
  actual = process_lines(lines)
  expected = expected_output.splitlines(keepends=True)
  print(f"Lengths: actual={len(actual)} expected={len(expected)}")
  #write_lines(actual)
  assert(len(actual) == len(expected))
  i = 0
  while i < len(actual):
    if actual[i] != expected[i]:
      print(f"Line {i} differs:")
      print(f"  actual: {actual[i]}")
      print(f"  expect: {expected[i]}")
      sys.exit(2)
    i += 1
  assert(actual == expected)


def main() -> None:
  # Do this every time for simplicity.
  run_unit_test()

  lines = get_lines()
  transformed = process_lines(lines)
  write_lines(transformed)


if __name__ == '__main__':
  call_main(main)


# EOF
