#! /bin/csh -f
# plot several files in gnuplot

if ( "$1" == "" ) then
  echo "usage: $0 list-of-files"
  exit
endif

foreach fn ( $* )
  how?

