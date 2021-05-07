#!/bin/sh
# Run tests in current directory.

set -e
set -x

for fn in *.in; do
  expected=`echo $fn | sed 's/in$/out/'`

  tsv-to-html-table < $fn > tmp.actual
  diff $expected tmp.actual
done

rm tmp.actual

# EOF
