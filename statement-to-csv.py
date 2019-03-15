#!/usr/bin/env python3
# Read text pasted from a financial statement, write CSV.

import re                    # re.compile
import sys                   # sys.argv, sys.stdin
import traceback             # traceback.print_exc


# -------------- prologue boilerplate -------------
# These are things I add at the start of every Python program to
# allow better error reporting.

class Error(Exception):
  """A condition to be treated as an error."""
  pass

# Throw a fatal error with message.
def die(message):
  raise Error(message)


# ------------------- program -------------------

# Return 'str' but with all commas removed.
def stripCommas(str):
  return re.sub(',', '', str)

regex = re.compile(
  "^([0-9][0-9])/([0-9][0-9]) " +    # 1,2: 2-digit date
  "(.*) " +                          # 3: description
  "([0-9.,-]+) " +                   # 4: amount
  "([0-9.,-]+)$"                     # 5: balance
)

assumedYear = 2018

def main():
  lineNumber = 0

  for line in sys.stdin:
    lineNumber += 1
    m = regex.match(line)
    if m:
      (month, day, desc, amt, balance) = m.groups()
      amt = stripCommas(amt)
      balance = stripCommas(balance)

      print("{}-{}-{},\"{}\",{},{}".format(
        assumedYear, month, day, desc, amt, balance))
    else:
      die("line {} malformed".format(lineNumber))

try:
  main()


# ------------- epilogue boilerplate -----------
# This is some stuff that I add at the end of all Python programs
# because otherwise errors are not handled well.

except Error as e:
  print("Error: "+e.args[0], file=sys.stderr)
  sys.exit(2)

except SystemExit as e:
  raise      # let this one go

except:
  print("Error: "+str(sys.exc_info()[1]), file=sys.stderr)
  #traceback.print_exc(file=sys.stderr)       # Enable for debugging.
  sys.exit(2)


# EOF
