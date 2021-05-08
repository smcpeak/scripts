#!/usr/bin/env python3
# Written by Scott McPeak and contributed to the public domain.

"""check-doc-examples.py

Given a document that contains examples that are drawn from test files,
either as fragments or complete files, check that what is in the
document matches what is in the tests.

Within the document, examples are marked with BEGIN and END lines
that look like this:

  BEGIN example: "<filename>"
  END example

Then this script will expect to find that the contents of <filename>
match what is in the document between the markers.

The BEGIN marker line can indicate that what is in the document is only
a fragment of the complete file like this:

  BEGIN example: "<filename>" fragment=true

In that case, this script expects the test file to contain markers
like this:

  BEGIN: example fragment
  END: example fragment

and what is between those two must match what is in the document.

Additionally, the example in the document may be indented more than the
test file.  In that case, the "BEGIN example" line in the document must
have "indent=N" on the line, where N is the number of additional
spaces present in the document as compared to the test.

For the moment, this script assumes the document is HTML, so uses
HTML entity decoding before comparison.
"""

import difflib                         # context_diff
import html                            # unescape
import re                              # compile
import sys                             # argv, exit, stderr
import textwrap                        # dedent

programName = sys.argv[0]


# Number of errors encountered.
numErrors = 0


class Error(Exception):
  """A condition to be treated as an error."""
  pass


def diagnostic(msg):
  """Debug printout, normally disabled."""
  #print(msg)
  pass



def die(msg):
  """Print 'msg' as an error and stop."""

  print(textwrap.dedent(msg), file=sys.stderr);
  sys.exit(2)


def complain(msg):
  """Print 'msg' as an error, but keep going."""

  print("----------------------")
  print(textwrap.dedent(msg))
  print("")

  global numErrors
  numErrors += 1


def chomp(x):
  """Remove any trailing line terminator from 'x' and return that."""

  if x.endswith("\r\n"): return x[:-2]
  if x.endswith("\n") or x.endswith("\r"): return x[:-1]
  return x


def readFileLines(fname):
  """Read the lines of 'fname', returning them as a list."""

  with open(fname, "r") as fp:
    return fp.readlines()


# Recognize a string that is blank or entirely whitespace.
whitespacePattern = re.compile(r'^\s*$')


try:
  # Interpret the command line.
  if len(sys.argv) < 2:
    die(f"""\
      usage: {programName} <document to check>

      Checks the examples in the document to ensure they match files
      in this directory.""")

  documentName = sys.argv[1]

  # Read the document.
  documentLines = readFileLines(documentName)


  # Count of various occurrences.
  numExamples = 0

  # True if we are currently scanning the document to find an end marker.
  scanningForEnd = False

  # If 'scanningForEnd', details about the corresponding BEGIN.
  testFileName = None        # The <filename> in the marker.
  beginLineIndex = None      # Index in 'documentLines' of first example line.
  fragmentOnly = False       # True if "fragment=true".
  indentNumber = 0           # The N in "indent=N".
  exampleLines = []          # Example lines from the document.


  # Pattern for recognizing BEGIN markers.
  beginPattern = re.compile(r'BEGIN example: "([^"]+)"')

  # Recognize the "fragment" indicator.
  fragmentPattern = re.compile(r'fragment=true')

  # Recognize the "indent" indicator.
  indentPattern = re.compile(r'indent=([0-9]+)')

  # Pattern for END.
  endPattern = re.compile(r'END example')

  # Pattern for "BEGIN: example fragment", which appears inside tests.
  beginFragmentPattern = re.compile(r'BEGIN: example fragment')

  # Pattern for corresponding END.
  endFragmentPattern = re.compile(r'END: example fragment')


  # Scan the document for examples.
  for documentLineIndex, documentLine in enumerate(documentLines):
    documentLine = chomp(documentLine)

    if not scanningForEnd:
      m = beginPattern.search(documentLine)
      if m:
        numExamples += 1
        testFileName = m.group(1)
        beginLineIndex = documentLineIndex
        scanningForEnd = True
        fragmentOnly = True if fragmentPattern.search(documentLine) else False
        exampleLines = []

        indentNumber = 0
        im = indentPattern.search(documentLine)
        if im:
          indentNumber = int(im.group(1))

    else:
      m = endPattern.search(documentLine)
      if m:
        scanningForEnd = False
        endLineIndex = documentLineIndex
        if endLineIndex == beginLineIndex+1:
          complain(f"""\
            Line {endLineIndex+1} of {documentName} contains an END marker,
            but the immediately preceding line is a BEGIN marker.""")

          continue

        print(f'Line {beginLineIndex+2}: Checking "{testFileName}".')

        # Read the file referred to, which I call a "test" because that
        # is what I expect the examples are drawn from.
        testLines = []
        foundFragment = False
        withinFragment = not fragmentOnly
        for testLine in readFileLines(testFileName):
          testLine = chomp(testLine)

          if withinFragment:
            if fragmentOnly and endFragmentPattern.search(testLine):
              withinFragment = False
            else:
              testLines.append(testLine)

          else:
            if fragmentOnly:
              if beginFragmentPattern.search(testLine):
                if foundFragment:
                  complain(f"""\
                    Test file "{testFileName}" contains more than
                    one line with "BEGIN: example fragment".""")

                  # Here, we stop iterating over the lines of
                  # 'testFileName', but proceed with the rest of the
                  # checks, using the 'testLines' already accumulated.
                  break

                foundFragment = True
                withinFragment = True

        # Check that we found the end of the fragment if applicable.
        if fragmentOnly:
          if not foundFragment:
            complain(f"""\
              Line {beginLineIndex+1} of {documentName}:

                {documentLines[beginLineIndex]}

              refers to test file "{testFileName}" and
              indicates that only a fragment of the that file is used.
              However, the test does not contain any lines with the
              required "BEGIN: example fragment" text.""")
            continue

          if withinFragment:
            complain(f"""\
              Test file "{testFileName}" is missing the required
              "END: example fragment" line.""")
            continue

        # Check that it the right number of lines.
        if len(testLines) != len(exampleLines):
          if fragmentOnly:
            complain(f"""\
              Lines {beginLineIndex+2} to {endLineIndex} of {documentName},
              which is {len(exampleLines)} lines in total,
              contain an example referring to "{testFileName}",
              but its fragment has {len(testLines)} in it.""")
          else:
            complain(f"""\
              Lines {beginLineIndex+2} to {endLineIndex} of {documentName},
              which is {len(exampleLines)} lines in total,
              contain an example referring to "{testFileName}",
              but that file has {len(testLines)} in it.""")
          continue

        # The example has been collected in 'exampleLines', and the
        # corresponding test in 'testLines'.  Both lists have the same
        # number of elements and (ostensibly) matching indentation.
        # Compare for equality.
        if exampleLines != testLines:
          complain(f"""\
            Lines {beginLineIndex+2} to {endLineIndex} of {documentName}
            contain an example referring to "{testFileName}".  However,
            they are not equal, as shown in the following diff, where
            the "-" input is from {documentName}:""")

          difflines = difflib.unified_diff(exampleLines, testLines,
            lineterm="")
          atLeastOne = False
          for diffline in difflines:
            atLeastOne = True
            print(diffline)

          if not atLeastOne:
            raise Error("difflib did not find any differences!")

      else:
        # Accumulate lines of the example.

        # First, check for and remove indentation.
        if documentLine.startswith(" " * indentNumber):
          documentLine = documentLine[indentNumber:]

        elif whitespacePattern.match(documentLine):
          # Ignore blank and whitespace-only lines.
          pass

        else:
          complain(f"""\
            Line {beginLineIndex+1} of {documentName}:

              {documentLines[beginLineIndex]}

            indicates that the example is indented by {indentNumber} spaces.
            However, line {documentLineIndex+1}:

              "{documentLine}"

            does not contain enough indentation.""")

          # Despite the error, proceed to record the line so to minimize
          # further disruption to the comparison procedure
          pass

        # Decode HTML entities and record it.
        exampleLines.append(html.unescape(documentLine))

  if numErrors > 0:
    # Separate final summary from preceding errors.
    print("")

  print(textwrap.dedent(f"""\
    Finished checking.
    Found {numExamples} examples.
    There were {numErrors} errors."""))

  if numExamples == 0 or numErrors > 0:
    sys.exit(2)

except Error as e:
  print("Error: "+e.args[0], file=sys.stderr)
  sys.exit(2)

except IOError as e:
  if e.filename:
    print("Error: "+e.filename+": "+e.strerror, file=sys.stderr)
  else:
    print("Error: "+e.strerror, file=sys.stderr)
  sys.exit(2)




# EOF
