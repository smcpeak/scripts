#!/usr/bin/env python3
"""
This program converts blocks of C/C++ comments that use the single-line
"//" syntax into the block "/*...*/" syntax.  The program reads from
stdin and writes to stdout.

To recognize a block of comments, it looks for a maximal number of
consecutive lines (minimum of two) that all start with the same string
of whitespace, followed by "//".

For each block of comments, it does the following:

* Replace the first "//" with "/*", preserving the leading whitespace.

* Replace all intermediate "//" with two spaces (again preserving
  leading whitespace), unless the "//" is not followed by anything else
  on that line, in which case output a completely blank line (without
  any whitespace).

* For the last "//", if it is not followed by anything on that line,
  replace it with "*/" (preserving leading whitespace).  Otherwise,
  insert a new line below what was the last line, containing just "*/"
  indented by the same amount of whitespace as the elements of the
  block were.

Any text outside a comment block is copied unchanged to the ouptut.
Existing "/*...*/" comments are ignored (preserved unchanged).
"""

import re
import sys

from boilerplate import *
from typing import List, Tuple, Union


def get_lines() -> List[str]:
  """
  Read all lines from standard input and return them as a list of
  strings, discarding line endings.
  """
  return sys.stdin.read().splitlines()


def write_lines(lines: List[str]) -> None:
  """
  Write the given list of lines to standard output.
  """
  sys.stdout.write(''.join(line+'\n' for line in lines))


# A parsed line is either a pair of the leading whitespace and the text
# that followed the "//", or it is just the entire line for a line that
# does not match the comment line regex.
ParsedLine = Union[Tuple[str, str], str]


def parse_lines(input_lines: List[str]) -> List[ParsedLine]:
  """
  Parse all input lines depending on whether they are single-line
  comments.
  """

  comment_line_re = re.compile(r"""
    ^(\s*)                   # 1: leading whitespace
    //                       # comment start
    (.*)$                    # 2: text after comment start
  """, re.VERBOSE)

  output: List[ParsedLine] = []

  for line in input_lines:
    m = comment_line_re.match(line)
    if m:
      output.append((m.group(1), m.group(2)))
    else:
      output.append(line)

  return output


def has_leading_ws(parsed_line: ParsedLine, leading_ws: str) -> bool:
  """
  True if `parsed_line` is a tuple whose first element is `leading_ws`.
  """
  if isinstance(parsed_line, tuple):
    return parsed_line[0] == leading_ws
  else:
    return False


def process_lines(input_lines: List[str]) -> List[str]:
  """
  Process the input lines and return a new list of lines with the
  comment-block transformations applied.

  The algorithm finds maximal runs of consecutive lines (length >= 2)
  that all start with the identical leading-whitespace string followed
  by '//'. Each such run is converted according to the rules described
  in the script description above.
  """
  output_lines: List[str] = []
  block_start_index = 0
  num_input_lines = len(input_lines)

  # First parse all the lines.
  parsed_lines: List[ParsedLine] = parse_lines(input_lines)
  assert(len(parsed_lines) == num_input_lines)

  # Process the parsed lines.
  while block_start_index < num_input_lines:
    parsed_line = parsed_lines[block_start_index]

    if isinstance(parsed_line, tuple):
      leading_ws, after_text = parsed_line

      # Gather a maximal run of lines that have the same `leading_ws`.
      block_end_index = block_start_index
      while (block_end_index < num_input_lines and
             has_leading_ws(parsed_lines[block_end_index], leading_ws)):
        block_end_index += 1

      # Only treat this as a block if there are at least two consecutive
      # matching lines.
      if block_end_index - block_start_index >= 2:

        # Process every line in the block.
        for block_line_index in range(block_start_index, block_end_index):
          after_text = parsed_lines[block_line_index][1]

          # True if there was nothing after the slashes.
          empty_after: bool = (after_text == '')

          # First, middle, or last line?
          if block_line_index == block_start_index:
            # First line: replace '//' with '/*'.
            output_lines.append(f"{leading_ws}/*{after_text}")

          elif block_line_index < block_end_index - 1:
            # Middle line.
            if empty_after:
              # This was a line separating paragraphs.  Within the
              # /*...*/ syntax we are creating, such a line becomes
              # completely blank.
              output_lines.append('')

            else:
              # Replace '//' with two spaces.
              output_lines.append(f"{leading_ws}  {after_text}")

          else:
            # Last line.
            if empty_after:
              # Replace '//' with '*/'.
              output_lines.append(f"{leading_ws}*/")

            else:
              # First, replace '//' with two spaces.
              output_lines.append(f"{leading_ws}  {after_text}")

              # Then insert a new line with just "*/".
              output_lines.append(f"{leading_ws}*/")

        # Advance past the run.
        block_start_index = block_end_index

      else:
        # Isolated comment line: preserve as-is.
        output_lines.append(f"{leading_ws}//{after_text}")
        block_start_index += 1

    else:
      # Not a comment: preserve as-is.
      output_lines.append(parsed_line)
      block_start_index += 1

  return output_lines


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
  lines = example_input.splitlines()
  actual = process_lines(lines)
  expected = expected_output.splitlines()
  debugPrint(f"Lengths: actual={len(actual)} expected={len(expected)}")
  if debugLevel >= 2:
    write_lines(actual)
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
