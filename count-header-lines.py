#!/usr/bin/env python3
"""
This script measures the number of lines produced by the C++
preprocessor (`g++ -E`) when processing a sequence of header files.  For
each prefix of the list of provided header files, it computes the number
of lines of preprocessor output when those headers are included in that
order, thereby assessing the context-dependent incremental cost of each
header.
"""

import argparse
import subprocess
import sys
import re

from boilerplate import *
from typing import List, Tuple


def parse_args() -> argparse.Namespace:
  """
  Parse and return the command-line arguments.
  """
  parser = argparse.ArgumentParser(
    description=
      "Measure preprocessor output line counts for header file prefixes."
  )
  parser.add_argument(
    "--expand",
    action="store_true",
    help="Read the contents of the files to get the list of headers.")
  parser.add_argument(
    "-I",
    dest="includes",
    action="append",
    metavar="INCDIR",
    default=[],
    help="Add INCDIR to the include path.")
  parser.add_argument(
    "headers",
    metavar="header",
    type=str,
    nargs="+",
    help="List of header files to include.",
  )
  return parser.parse_args()


def generate_includes(headers: List[str]) -> str:
  """
  Return a string containing `#include "..."` directives for each header
  in the list.
  """
  return "".join(f'#include "{hdr}"\n' for hdr in headers)


def run_preprocessor(
  include_text: str,
  include_dirs: List[str]
) -> Tuple[int, int]:
  """
  Run `g++ -E -xc++ -` with the given include directives and return a
  tuple: (number of lines of output, number of lines containing the
  substring "template").
  """
  try:
    command: List[str] = ["g++", "-E", "-xc++", "-"];
    for dir in include_dirs:
      command.append(f"-I{dir}")

    proc = subprocess.run(
      command,
      input=include_text,
      text=True,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      check=True
    )
    lines = proc.stdout.splitlines()
    total_lines = len(lines)
    template_lines = sum(1 for line in lines if "template" in line)
    return total_lines, template_lines

  except subprocess.CalledProcessError as e:
    print("Error invoking g++ with input:", file=sys.stderr)
    print("-----------------------------", file=sys.stderr)
    print(include_text, file=sys.stderr)
    print("-----------------------------", file=sys.stderr)
    print("g++ stderr output:", file=sys.stderr)
    print(e.stderr, file=sys.stderr)
    raise


def measure_line_counts(
  headers: List[str],
  include_dirs: List[str]
) -> List[Tuple[str, int, int, int, int]]:
  """
  For each prefix of the header list, measure the number of lines of
  preprocessor output and number of lines containing "template".
  Return a list of (header name, added lines, total lines,
  added templates, total templates) tuples.
  """
  result: List[Tuple[str, int, int, int, int]] = []
  prev_total_lines = 0
  prev_total_templates = 0

  for i in range(1, len(headers) + 1):
    prefix = headers[:i]
    include_text = generate_includes(prefix)
    total_lines, total_templates = run_preprocessor(include_text, include_dirs)

    added_lines = total_lines - prev_total_lines
    added_templates = total_templates - prev_total_templates
    result.append((headers[i - 1],
                   added_lines, total_lines,
                   added_templates, total_templates))

    prev_total_lines = total_lines
    prev_total_templates = total_templates

  return result


include_re = re.compile("""
  ^\s*\#\s*include\s*           # "#include "
  ["<]                          # opening delimiter
  ([^">]+)                      # 1: file name
  [">]                          # closing delimiter
  .*$                           # ignored remainder of line
""", re.VERBOSE)


def expand_files(files: List[str]) -> List[str]:
  """
  Read each file in `files`, looking for #include lines.  Return the
  sequence of file names that were #included.
  """
  ret: List[str] = []

  for file_name in files:
    with open(file_name, "r") as file:
      for line in file:
        m = include_re.match(line)
        if m:
          target = m.group(1)
          debugPrint(f"Got {target} from {file_name}")
          ret.append(target)

  return ret


def print_report(
  measurements: List[Tuple[str, int, int, int, int]]
) -> None:
  """
  Print the formatted summary table of header file measurements.
  """
  # Compute width of "file name" column based on maximum `name` length.
  name_width = max(17, *(len(name) for name, *_ in measurements))

  name_header = f"{'file name':<{name_width}}"
  name_separa = "-" * name_width

  print(f"{name_header}   +lines  t.lines  +templates  t.templates")
  print(f"{name_separa}  -------  -------  ----------  -----------")
  for name, added, total, added_tpl, total_tpl in measurements:
    print(f"{name:<{name_width}}  {added:7}  {total:7}  {added_tpl:10}  {total_tpl:11}")


def main() -> None:
  args = parse_args()

  files = args.headers
  if args.expand:
    files = expand_files(files)

  measurements = measure_line_counts(files, args.includes)
  print_report(measurements)


if __name__ == "__main__":
  call_main(main)


# EOF
