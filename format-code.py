#!/usr/bin/env python3
"""
Read some code on stdin and produce a formatted version on stdout.

Currently, there is just one formatting rule: making tables.

A table begins with a comment line of the form:

  // Columns: COL1 COL2 ... COLn

Each COLi is a column start descriptor with one of these forms:

  @M:RE
  RE

where M is a positive integer and RE is a Python regular expression.
If RE contains any spaces, they must be backslash-escaped.  Similarly,
the RE can begin with "\@" in order to evade the first form.

When provided, M is a 1-based column number specifying the minimum
start character column for its text column.

Successive lines are then parsed as table lines:

* If the line is blank, it is ignored, meaning it will appear in the
  output unmodified.

* Otherwise, if the line starts with less whitespace than the column
  header comment, that ends that table.  The line is then a candidate
  for starting a new table.

* Otherwise, if the line does not begin with text matching RE1 (the RE
  for COL1), possibly after some whitespace, it is ignored.

* Otherwise, starting at the point after RE1 matched, we search for RE2.
  If that is found, it marks the start of the second entry for this row.
  The first entry begins where RE1 matched, and continues up to the
  point RE2 matched, except with trailing whitespace removed.  After
  the RE2 match, we search for RE3 to find the start of the third entry,
  and so forth.

* Running out of lines in the input also terminates the table.

After parsing the table, we have a header line and a sequence of parsed
lines, some of which are "ignored", and the rest consist of a sequence
of "entry" strings.  Each table column width is then calculated,
starting with the first, as the smallest width that is greater than or
equal to the length of all of the entry strings in that column, and also
large enough to satisfy the @M constraint on the next column if there is
one.

Once column widths are calculated, first emit the header line
unmodified, then the ignored lines and table rows, with each table row
having its entries padded with trailing spaces out to its column width,
except for the last entry in each row.

Example input (input file with 4 lines):

  // Columns: \{ \S+ \S+ @30:\S+ \}
  { a, bronze, bar },
  some other line, will be "ignored"
  { eleven, nine, twenty },

Corresponding output:

  // Columns: \{ \S+ \S+ @30:\S+ \}
  { a,      bronze,          bar    },
  some other line, will be "ignored"
  { eleven, nine,            twenty },

"""

import argparse              # argparse
import os                    # os.getenv
import re                    # re.compile
import signal                # signal.signal
import sys                   # sys.argv, sys.stderr, sys.stdin
import traceback             # traceback.print_exc


# -------------- BEGIN: boilerplate -------------
# These are things I add at the start of every Python program to
# allow better error reporting.

# Positive if debug is enabled, with higher values enabling more printing.
debugLevel = 0
if (os.getenv("DEBUG")):
  debugLevel = int(os.getenv("DEBUG"))

def debugPrint(str):
  """Debug printout when DEBUG >= 2."""
  if debugLevel >= 2:
    print(str)

# Ctrl-C: interrupt the interpreter instead of raising an exception.
#signal.signal(signal.SIGINT, signal.SIG_DFL)

class Error(Exception):
  """A condition to be treated as an error."""
  pass

def die(message):
  """Throw a fatal Error with message."""
  raise Error(message)

def exceptionMessage(e):
  """Turn exception 'e' into a human-readable message."""
  t = type(e).__name__
  s = str(e)
  if s:
    return f"{t}: {s}"
  else:
    return f"{t}"

def call_main():
  """Call main() and catch exceptions."""
  try:
    main()

  except SystemExit as e:
    raise      # Let this one go, otherwise sys.exit gets "caught".

  except BaseException as e:
    print(f"{exceptionMessage(e)}", file=sys.stderr)
    if (debugLevel >= 1):
      traceback.print_exc(file=sys.stderr)
    sys.exit(2)
# --------------- END: boilerplate --------------


# True to enable various debug printouts.
debug = False


# RE to match a descriptor:
#   - optional "@M:"
#   - a sequence of non-space, non-backslash characters, mixed with
#     backslash-anything
#   - optional spaces
#                           1 2          34
descriptorRE = re.compile(r'(@([0-9]+):)?((?:[^\\ ]|\\.)+) *')

def parseColumnDescriptors(columnDescriptors):
  """
  Given a string consisting of a sequence of space-separated column
  descriptors, return a list of tuples with two elements:

    0: Mininum 1-based character column number to start
       this column, or None if there is no such constraint.

    1: Compiled RE that recognizes the start (or entirety) of
       entries in this column.
  """

  # TODO: Can I use a structured object?

  # Parsed descriptor objects.
  descriptors = []

  # Index of next character in 'columnDescriptors' to parse.
  index = 0

  while index < len(columnDescriptors):
    # Match the next descriptor.
    remainingText = columnDescriptors[index:]
    m = descriptorRE.match(remainingText)
    if m:
      try:
        colConstraint = m.group(2)
        regexp = m.group(3)

        parsedDescriptor = (
          None if colConstraint is None else int(colConstraint),
          re.compile(regexp)
        )
        descriptors.append(parsedDescriptor)
        index += len(m.group(0))

      except BaseException as e:
        die(f"while parsing descriptor \"{m.group(0)}\": " +
            f"{exceptionMessage(e)}")

    else:
      die(f"failed to parse as descriptor: \"{remainingText}\"")

  return descriptors


def testParseColumnDescriptors():
  """Unit tests for 'parseColumnDescriptors'."""

  def oneTest(input, expect):
    actual = parseColumnDescriptors(input)
    assert len(actual) == len(expect)
    i = 0
    while i < len(actual):
      assert actual[i][0] == expect[i][0]

      expectRE = re.compile(expect[i][1])
      if actual[i][1] != expectRE:
        print(f"input: {input}")
        print(f"i: {i}")
        print(f"actual: {actual[i][1]}")
        print(f"expect: {expectRE}")
      assert actual[i][1] == expectRE

      i += 1

  oneTest("", [])

  oneTest("a b c", [(None, "a"), (None, "b"), (None, "c")])

  oneTest("a @2:b @6::", [(None, "a"), (2, "b"), (6, ":")])

  oneTest("a\\ b \\@2:c", [(None, "a\\ b"), (None, "\\@2:c")])


def parseTableRow(rowText, columns):
  """
  Given the text of a row, 'rowText', and a sequence of parsed
  column descriptors, 'columns', yield a sequence of strings
  extracted from 'rowText' that will become table entries.

  Alternatively, if 'rowText' does not match the column descriptors,
  return None.
  """

  entries = []

  # First column is special.
  colStartRE = columns[0][1]
  firstEntryMatch = colStartRE.match(rowText)
  if firstEntryMatch:
    # Index of the previous match start.  (Initially 0.)
    prevStartIndex = firstEntryMatch.start(0)

    # Index of the end of the previous match.
    prevEndIndex = firstEntryMatch.end(0)

    # Look match successive column REs.
    for col in columns[1:]:
      colStartRE = col[1]
      entryMatch = colStartRE.search(rowText[prevEndIndex:])
      if entryMatch:
        # Index of start/end for this match.
        startIndex = prevEndIndex + entryMatch.start(0)
        endIndex   = prevEndIndex + entryMatch.end(0)

        # Pull out the previous entry text.
        entryText = rowText[prevStartIndex:startIndex].rstrip(" ")
        entries.append(entryText)

        # Prepare for the next entry.
        prevStartIndex = startIndex
        prevEndIndex   = endIndex

      else:
        # Did not match the RE.  All text from 'prevStartIndex'
        # is the final entry in this row.
        entryText = rowText[prevStartIndex:].rstrip(" ")
        entries.append(entryText)

        # Indicate we have consumed the line.
        prevStartIndex = len(rowText)

        break

    if prevStartIndex < len(rowText):
      # We ran out of column descriptors.  All remaining text is
      # the final entry.
      entryText = rowText[prevStartIndex:].rstrip(" ")
      entries.append(entryText)

    return entries

  else:
    # First RE does not match.
    return None


def emitTable(leadingWhitespace, rows, columns):
  """
  Format and emit 'rows' according to the 'columns' descriptors.

  'leadingWhitespace' is a string consisting entirely of whitespace to
  emit at the start of the line, and which is counted toward meeting the
  column number specifications in 'columns'.
  """

  if debug:
    print("emitTable:")
    print(f"  leadingWhitespace: \"{leadingWhitespace}\"")
    print("rows:")
    for r in rows:
      print(f"  {r}")
    print("columns:")
    for c in columns:
      print(f"  {c}")

  # Calculate the maximum width of each column.
  maxWidth = [0] * len(columns)
  for r in rows:
    if type(r) is list:
      colIndex = 0
      while colIndex < len(r):
        # We should not have more entries than we do column descriptors.
        assert colIndex < len(columns)

        entryText = r[colIndex]

        # Account for the width of 'entryText'.
        w = len(entryText)
        if w > maxWidth[colIndex]:
          maxWidth[colIndex] = w

        colIndex += 1

  if debug:
    print(f"maxWidth: {maxWidth}")

  # Apply the column start specifications from 'columns' by expanding
  # 'maxWidth' elements where needed.
  if True:
    # 1-based character column number for the first character of the
    # next data column.
    charColumn = len(leadingWhitespace)+1

    colIndex = 0
    while colIndex < len(maxWidth):
      assert colIndex < len(columns)
      colSpec = columns[colIndex]

      if colIndex == 0:
        # We don't apply any adjustments before the first data column.
        pass

      else:
        # We add a space between data columns.
        #
        # We do this even for colIndex==1 because we're really
        # accounting for the space that will be added after the previous
        # column as we try to predict where the current column (at
        # 'colIndex') will end up.
        charColumn += 1

        # Number of spaces we need to add to the previous column in order
        # to reach the minimum start character column.
        minStartCharColumn = colSpec[0]
        if minStartCharColumn is not None:
          delta = minStartCharColumn - (charColumn + maxWidth[colIndex-1])
          if delta > 0:
            maxWidth[colIndex-1] += delta

        # Account for the previous column.
        charColumn += maxWidth[colIndex-1]

      colIndex += 1

  if debug:
    print(f"maxWidth: {maxWidth}")

  # Render rows, taking 'maxWidth' into account for all but the last
  # data column in each row.
  for r in rows:
    if type(r) is list:
      print(leadingWhitespace, end="")

      # None of the row lists should be empty.
      assert len(r) >= 1

      colIndex = 0
      while colIndex < len(r) - 1:
        entryText = r[colIndex]

        # Add padding to the end of 'entryText'.
        paddingLen = maxWidth[colIndex] - len(entryText)
        assert paddingLen >= 0
        entryText += " " * paddingLen

        if colIndex > 0:
          # Space between columns.
          print(" ", end="")

        print(entryText, end="")

        colIndex += 1

      # The last entry is special because no padding is applied, and
      # we follow it with a newline.
      print(" ", end="")
      print(r[colIndex])

    else:
      # Print strings as they are, followed by a newline.
      print(r)


def main():
  testParseColumnDescriptors()

  # Line that begins a table.
  tableHeaderRE = re.compile(r'^(\s*)// Columns: (.*)$')

  # Table line, just pulling out the leading whitespace.
  tableLineRE = re.compile(r'(\s*)(.*)$')

  # All input lines.
  inputLines = sys.stdin.readlines()

  # Index of next input line to parse.
  inputLineIndex = 0

  # Scan for the start of a table.
  while inputLineIndex < len(inputLines):
    candidateHeaderLine = inputLines[inputLineIndex].rstrip("\r\n")
    inputLineIndex += 1

    if debug:
      print(f"candidateHeaderLine: {candidateHeaderLine}")

    headerMatch = tableHeaderRE.match(candidateHeaderLine)
    if headerMatch:
      headerLeadingWhitespace = headerMatch.group(1)
      columns = parseColumnDescriptors(headerMatch.group(2))

      if debug:
        print("found matching header:")
        print(f"  headerLeadingWhitespace: \"{headerLeadingWhitespace}\"")
        print(f"  columns:")
        for c in columns:
          print(f"    {c}")

      # The parsed table is a list where each entry is a string, meaning
      # a line that is "ignored" (passed through unchanged), or a list of
      # entry strings that will be arranged into columns.
      rows = []

      # Start by inserting the header as an ignored line.
      rows.append(candidateHeaderLine)

      # Parse the rows of the table.
      while inputLineIndex < len(inputLines):
        tableLine = inputLines[inputLineIndex].rstrip("\r\n")
        inputLineIndex += 1

        # Separate the leading whitespace, which should always succeed.
        lineMatch = tableLineRE.match(tableLine)
        assert lineMatch
        rowLeadingWhitespace = lineMatch.group(1)
        rowText = lineMatch.group(2)

        if len(rowLeadingWhitespace) < len(headerLeadingWhitespace):
          # End of table definition.  Put that line back so it can start a
          # new table.
          inputLineIndex -= 1
          break

        # Parse the entries of the line.
        entries = parseTableRow(rowText, columns)
        if entries is None:
          # Add the line as a string.
          rows.append(tableLine)
        else:
          rows.append(entries)

      # Format and emit the table.
      emitTable(headerLeadingWhitespace, rows, columns)

    else:
      # Not a recognized header, just emit the line unchanged.
      print(candidateHeaderLine)


call_main()


# EOF
