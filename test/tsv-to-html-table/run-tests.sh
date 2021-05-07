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
  fi

  tsv-to-html-table $args < $fn > tmp.actual
  diff $expected tmp.actual
done

rm tmp.actual

# EOF
