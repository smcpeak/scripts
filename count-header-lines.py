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
    "headers",
    metavar="header",
    type=str,
    nargs="+",
    help="List of header files to include.",
  )
  return parser.parse_args()


def generate_includes(headers: List[str]) -> str:
  """
  Return a string containing `#include <...>` directives for each header
  in the list.
  """
  return "".join(f"#include <{hdr}>\n" for hdr in headers)


def run_preprocessor(include_text: str) -> int:
  """
  Run `g++ -E -xc++ -` with the given include directives and return the
  number of lines of output.
  """
  try:
    proc = subprocess.run(
      ["g++", "-E", "-xc++", "-"],
      input=include_text,
      text=True,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      check=True
    )
    return len(proc.stdout.splitlines())
  except subprocess.CalledProcessError as e:
    print("Error invoking g++ with input:", file=sys.stderr)
    print("-----------------------------", file=sys.stderr)
    print(include_text, file=sys.stderr)
    print("-----------------------------", file=sys.stderr)
    print("g++ stderr output:", file=sys.stderr)
    print(e.stderr, file=sys.stderr)
    raise


def measure_line_counts(headers: List[str]) -> List[Tuple[str, int, int]]:
  """
  For each prefix of the header list, measure the number of lines of
  preprocessor output.  Return a list of (header name, added lines,
  total lines) tuples.
  """
  result: List[Tuple[str, int, int]] = []
  previous_total = 0

  for i in range(1, len(headers) + 1):
    prefix = headers[:i]
    include_text = generate_includes(prefix)
    total_lines = run_preprocessor(include_text)
    added_lines = total_lines - previous_total
    result.append((headers[i - 1], added_lines, total_lines))
    previous_total = total_lines

  return result


def print_report(measurements: List[Tuple[str, int, int]]) -> None:
  """
  Print the formatted summary table of header file measurements.
  """
  print("file name          added lines  total lines")
  print("-----------------  -----------  -----------")
  for name, added, total in measurements:
    print(f"{name:<17}  {added:11}  {total:11}")


def main() -> None:
  args = parse_args()
  measurements = measure_line_counts(args.headers)
  print_report(measurements)


if __name__ == "__main__":
  call_main(main)


# EOF
