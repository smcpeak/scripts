#!/usr/bin/env python3
"""
Report all lines that were added recently, are still in the repo, and
have the substring "TODO".  The notion of recency and the substring can
be configured with command line options.
"""

import subprocess
import re
from datetime import datetime, timedelta
from typing import List, Optional, Set, Iterator, Tuple
import argparse


# True to print extra info as we go.
verbose: bool = False


def vbprint(s: str) -> None:
  """Print `s` if `verbose`."""
  if verbose:
    print(s)


# RE to extract the file name from the file header.
diff_file_re = re.compile(r'^diff --git a/.* b/(.*)')

def find_candidate_files(days: int, substring: str) -> Set[str]:
  """
  Find files with the `substring` added or changed within the last
  `days` days.
  """
  proc = subprocess.run(
    ["git", "log", f"--since={days} days ago", "-p"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    encoding="utf-8",
    check=True
  )

  files_with_substring: Set[str] = set()
  current_file: Optional[str] = None

  for line in proc.stdout.splitlines():
    if line.startswith('diff --git'):
      m = diff_file_re.match(line)
      if m:
        current_file = m.group(1)

    # Filter for added lines.  This isn't perfect because if, say, a
    # line that literally contains "+++" is added, then the diff line
    # will be "++++", and hence wrongly excluded, but that's rare enough
    # that I won't worry about it.
    elif line.startswith('+') and not line.startswith('+++'):
      if substring in line and current_file:
        files_with_substring.add(current_file)

  return files_with_substring


# A typical `git blame --show-name --date=short` output line looks like:
#
#   a1b2c3d4 filename.cc (Alice Smith 2024-06-01  42)     int foo = 42;
#
# The reason for `--show-name` is, without that, the file name will
# appear if and only if git detects renames in the file's history, which
# makes the format inconsistent.  There is no way to disable that
# output, so instead we force it to always be present.
#
blame_re = re.compile(r"""
  ^\S+\s                     #    commit hash
  [^(]+\s                    #    filename, due to --show-name
  \(                         #    open paren beginning author and date
    [^)]*                    #    author
    (\d{4}-\d{2}-\d{2})\s+   # 1: date as YYYY-MM-DD
    \d+                      #    line number (right aligned)
  \)\s                       #    close paren ending author and date
  (.*)$                      # 2: line contents
""", re.VERBOSE)


def test_blame_re() -> None:
  m = blame_re.match("a1b2c3d4 filename.cc (Alice Smith 2024-06-01  42)     int foo = 42;")
  assert(m is not None)
  assert(m.group(1) == "2024-06-01")
  assert(m.group(2) == "    int foo = 42;")

test_blame_re()


def blame_file(file: str, cutoff: datetime, substring: str) -> Iterator[Tuple[str, str, int, str]]:
  """
  Blame `file`, and yield (date_added, file, line_no, content) for lines that
  contain `substring` and were added since `cutoff`.
  """
  try:
    proc = subprocess.run(
      ["git", "blame", "--show-name", "--date=short", file],
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      encoding="utf-8",
      check=True
    )
  except subprocess.CalledProcessError as e:
    vbprint(f"error running git blame: {e}")
    return

  for i, line in enumerate(proc.stdout.splitlines(), start=1):
    m = blame_re.match(line)
    if not m:
      vbprint(f"unrecognized blame output: {line!r}")
      continue
    date_str, content = m.groups()
    date = datetime.strptime(date_str, "%Y-%m-%d")
    if date >= cutoff and substring in content:
      yield date_str, file, i, content


def main() -> None:
  parser = argparse.ArgumentParser(
    description="Find lines with a substring added recently and still present, showing file and line number."
  )
  parser.add_argument(
    "--verbose",
    action="store_true",
    help="Enable verbose output"
  )
  parser.add_argument(
    "--days",
    type=int,
    default=30,
    help="Number of days to look back (default: 30)"
  )
  parser.add_argument(
    "--substring",
    type=str,
    default="TODO",
    help="Substring to search for (default: 'TODO')"
  )
  parser.add_argument(
    "--file",
    type=str,
    help="Name of single file to check"
  )
  args = parser.parse_args()

  global verbose
  verbose = args.verbose

  cutoff: datetime = datetime.now() - timedelta(days=args.days)
  vbprint(f"Cutoff: {cutoff}")

  files: Set[str] = set()
  if args.file:
    files = {args.file}
  else:
    vbprint("Running 'git log' ...")
    files = find_candidate_files(args.days, args.substring)
  vbprint(f"Candidate files: {files!r}")

  if not files:
    print(f"No files with {args.substring!r} added in the last {args.days} days.")
    return

  matching_lines: List[Tuple[str, str, int, str]] = []

  for file in sorted(files):
    vbprint(f"Running `git blame` on {file!r} ...")
    matching_lines.extend(blame_file(file, cutoff, args.substring))

  matching_lines.sort(reverse=True)
  for date_str, file, line_no, content in matching_lines:
    print(f"{date_str} {file}:{line_no}: {content.strip()}")


if __name__ == "__main__":
  main()
