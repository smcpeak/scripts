#!/bin/sh
# Run tests in current directory.

set -e
set -x

for fn in *.in; do
  expected=$(echo $fn | sed 's/in$/out/')

  args=""
  argsfile=$(echo $fn | sed 's/in$/args/')
  if test -f $argsfile; then
    args=$(cat $argsfile)
    # t5.args has an argument with a space in it, so I need the quotes.
    tsv-to-html-table "$args" < $fn > tmp.actual
  else
    tsv-to-html-table < $fn > tmp.actual
  fi

  diff $expected tmp.actual
done

rm tmp.actual

# EOF
