#!/bin/sh
# Run tests in current directory.

set -e
set -x

for fn in *.in; do
  expected=`echo $fn | sed 's/in$/out/'`

  # Test a file name specified on the command line.
  hex2bin $fn > tmp.bin
  bin2hex tmp.bin > tmp.out
  diff $expected tmp.out

  # Test with stdin.
  hex2bin < $fn > tmp.bin
  bin2hex tmp.bin > tmp.out
  diff $expected tmp.out
done

rm tmp.out tmp.bin

# EOF
