#!/usr/bin/env python3
"""
Insert a line into a text file at a given 1-based line number.

Usage:
  script.py FILE STRING LINE_NUMBER

Behavior:
  - Positive N: insert STRING as a new line at 1-based line N (push existing lines down).
  - Negative N: position relative to end:
      -1 -> append after the last line
      -2 -> insert right before the last line
      -3 -> before the second-to-last line
      ...
  - N = 0 is invalid and produces an error.

Notes:
  - The inserted line will end with the file's prevailing newline style
    (CRLF, LF, or CR) if detectable; otherwise LF is used.
  - If appending after a file whose last line lacks a trailing newline,
    a newline is added to separate the existing last line from the inserted line.
  - LINE_NUMBER outside the file's range is clamped:
      N > len(lines)+1 -> append at end
      N < -(len(lines)+1) -> insert at beginning
"""

from __future__ import annotations

import sys
from typing import List


def usage(prog: str) -> str:
  return f"Usage: {prog} FILE STRING LINE_NUMBER"


def detect_eol(lines: List[str]) -> str:
  # Prefer CRLF if present, then LF, then CR; default to LF.
  for line in lines:
    if line.endswith("\r\n"):
      return "\r\n"
  for line in lines:
    if line.endswith("\n"):
      return "\n"
  for line in lines:
    if line.endswith("\r"):
      return "\r"
  return "\n"


def clamp(value: int, low: int, high: int) -> int:
  return high if value > high else (low if value < low else value)


def compute_insert_index(n: int, line_count: int) -> int:
  if n == 0:
    raise ValueError("Line number 0 is invalid.")
  if n > 0:
    idx = n - 1
  else:
    # -1 => after last (index == line_count)
    # -2 => before last (index == line_count - 1), etc.
    idx = line_count + n + 1
  return clamp(idx, 0, line_count)


def prepare_insertion(text: str, eol: str) -> str:
  # Disallow embedded newlines to ensure a single logical line insert.
  if ("\n" in text) or ("\r" in text):
    raise ValueError("STRING must not contain newline characters.")
  return text + eol


def insert_line_into_lines(lines: List[str], text: str, n: int) -> List[str]:
  eol = detect_eol(lines)
  idx = compute_insert_index(n, len(lines))
  insertion = prepare_insertion(text, eol)

  # If appending and the current last line lacks a newline, add one to keep lines separate.
  if idx == len(lines) and len(lines) > 0 and not lines[-1].endswith(("\n", "\r")):
    lines = lines.copy()
    lines[-1] = lines[-1] + eol

  new_lines = lines[:idx] + [insertion] + lines[idx:]
  return new_lines


def main(argv: List[str]) -> int:
  if len(argv) != 4:
    print(usage(argv[0]), file=sys.stderr)
    return 2

  file_path = argv[1]
  text = argv[2]
  try:
    n = int(argv[3], 10)
  except ValueError:
    print("LINE_NUMBER must be an integer.", file=sys.stderr)
    return 2

  if n == 0:
    print("Line number 0 is invalid.", file=sys.stderr)
    return 2

  try:
    with open(file_path, "r", newline="") as f:
      contents = f.read()
  except FileNotFoundError:
    print(f"File not found: {file_path}", file=sys.stderr)
    return 2
  except OSError as e:
    print(f"Error reading file '{file_path}': {e}", file=sys.stderr)
    return 2

  # Split into lines preserving line endings if present.
  lines = contents.splitlines(keepends=True)

  try:
    new_lines = insert_line_into_lines(lines, text, n)
  except ValueError as e:
    print(str(e), file=sys.stderr)
    return 2

  try:
    with open(file_path, "w", newline="") as f:
      f.write("".join(new_lines))
  except OSError as e:
    print(f"Error writing file '{file_path}': {e}", file=sys.stderr)
    return 2

  return 0


if __name__ == "__main__":
  sys.exit(main(sys.argv))
