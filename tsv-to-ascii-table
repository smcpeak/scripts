#!/usr/bin/env python3
# Written by Scott McPeak and placed into the public domain.

"""Convert TSV (tab separated value) on standard input into an ASCII
formatted table on standard output.

Given input like:

  name<tab>address<tab>pets
  doug<tab>19 park place<tab>2
  jim<tab>45 boardwalk avenue<tab>123

Produce output:

  name address             pets
  ---- ------------------- ----
  doug 19 park place          2
  jim  45 boardwalk avenue  123

That is:

  - The first line is treated as column titles.

  - Every column has a width equal to its largest element.

  - Values consisting entirely of numbers are right-aligned.
"""


import csv                   # reader
import html                  # escape
import re                    # compile
import sys                   # stdin

class Error(Exception):
  """A condition to be treated as an error."""
  pass


# Recognize numeric data.
numericPattern = re.compile(r"^[0-9][0-9.,]*$")


try:
  # Read the input into a list of lists.
  data = []
  numColumns = 0
  reader = csv.reader(sys.stdin, delimiter="\t")
  for row in reader:
    data.append(row)
    numColumns = max(numColumns, len(row))

  if len(data) == 0:
    # No input, no output.
    sys.exit(0)

  # Calculate column widths.
  columnWidths = [0] * numColumns
  for row in data:
    for i, cell in enumerate(row):
      columnWidths[i] = max(columnWidths[i], len(cell))

  # Print output table.
  for rowIdx, row in enumerate(data):
    # Print data in this row.
    for i, cell in enumerate(row):
      if i > 0:
        print(" ", end="")
      w = columnWidths[i]
      if numericPattern.match(cell):
        print(f"{cell: >{w}}", end="")
      else:
        print(f"{cell: <{w}}", end="")
    print("")

    if rowIdx == 0:
      # Print line below titles.
      for i in range(numColumns):
        if i > 0:
          print(" ", end="")
        dashes = "-" * columnWidths[i]
        print(f"{dashes}", end="")
      print("")

except Error as e:
  print("Error: "+e.args[0])
  sys.exit(2)

except IOError as e:
  if e.filename:
    print("Error: "+e.filename+": "+e.strerror)
  else:
    print("Error: "+e.strerror)
  sys.exit(2)


# EOF
