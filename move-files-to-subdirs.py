#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import sys
from typing import List, Match


def main() -> None:
  parser = argparse.ArgumentParser(
    description="Move files matching '([a-z]+)-(\\d+)-(\\d+)\\.([a-z]+)' into directories named by the second match group."
  )
  parser.add_argument(
    "-n", "--dry-run", action="store_true",
    help="Print the moves that would be made, but do not actually move any files."
  )
  parser.add_argument(
    "-v", "--verbose", action="store_true",
    help="Print every move that is made."
  )
  args = parser.parse_args()

  pattern: re.Pattern[str] = re.compile(r"^([a-z]+)-(\d+)-(\d+)\.([a-z]+)$")
  files: List[str] = os.listdir(".")

  for filename in files:
    match: Match[str] | None = pattern.match(filename)
    if not match:
      continue

    target_dir: str = match.group(2)
    source_path: str = os.path.join(".", filename)
    target_path: str = os.path.join(target_dir, filename)

    # Ensure destination directory exists
    if not os.path.exists(target_dir):
      if args.dry_run:
        print(f"Would create directory {target_dir}")
      else:
        os.mkdir(target_dir)

    if os.path.exists(target_path):
      print(f"Error: Target file already exists: {target_path}", file=sys.stderr)
      sys.exit(2)

    if args.dry_run:
      print(f"Would move {filename} -> {target_path}")
    else:
      shutil.move(source_path, target_path)
      if args.verbose:
        print(f"Moved {filename} -> {target_path}")


if __name__ == "__main__":
  main()
