#!/usr/bin/env python3
"""
Report all lines that were added recently, are still in the repo, and
have the substring "TODO".  The notion of recency and the substring can
be configured with command line options.
"""

import subprocess
import re
from datetime import datetime, timedelta
from typing import Optional, Set, Iterator, Tuple
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


# A typical `git blame --date=short` output line looks like:
#
#   a1b2c3d4 (Alice Smith 2024-06-01  42)     int foo = 42;
#
# The regex matches these elements:
#
#                        + commit hash
#                        |       + author (group 1)
#                        |       |       + date as YYYY-MM-DD (group 2)
#                        |       |       |                     + line number
#                        V       V       V                     V     V line contents (group 3)
blame_re = re.compile(r'^[^ ]+ \((.+?)\s+(\d{4}-\d{2}-\d{2})\s+\d+\) (.*)$')

def blame_file(file: str, cutoff: datetime, substring: str) -> Iterator[Tuple[int, str]]:
  """
  Blame `file`, and yield (line_no, content) for lines that contain
  `substring` and were added since `cutoff`.
  """
  try:
    proc = subprocess.run(
      ["git", "blame", "--date=short", file],
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      encoding="utf-8",
      check=True
    )
  except subprocess.CalledProcessError:
    return

  for i, line in enumerate(proc.stdout.splitlines(), start=1):
    m = blame_re.match(line)
    if not m:
      continue
    author, date_str, content = m.groups()
    date = datetime.strptime(date_str, "%Y-%m-%d")
    if date >= cutoff and substring in content:
      yield i, content


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
  args = parser.parse_args()

  global verbose
  verbose = args.verbose

  cutoff: datetime = datetime.now() - timedelta(days=args.days)

  vbprint("Running 'git log' ...")
  files: Set[str] = find_candidate_files(args.days, args.substring)
  vbprint(f"Candidate files: {files!r}")

  if not files:
    print(f"No files with {args.substring!r} added in the last {args.days} days.")
    return

  for file in sorted(files):
    vbprint(f"Running `git blame` on {file!r} ...")
    for line_no, content in blame_file(file, cutoff, args.substring):
      print(f"{file}:{line_no}: {content.strip()}")


if __name__ == "__main__":
  main()
