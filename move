#!/bin/sh
# move a file (or set of files) to another directory; different
# from 'mv' in that this script will refuse to change a file's
# name -- it will only move it between directories
#
# the purpose is to prevent accidentally renaming files when I
# mistype the name of the intended destination directory
#
# tip: if you *do* accidentally rename, use 'history' to find
# out which file you renamed, and to recover its name
# 
# I think gnu 'mv' should have a command-line option that does
# what this script does.. 'mv' *does* behave similarly when the
# final argument ends in a '/' (slash), but that's not quite what
# I want..

if [ "$1" = "" ]; then
  echo "usage: $0 src [sources..] dest"
  exit 0
fi

# get last argument; be careful about arguments which contain spaces:
# e.g. if there are 3 arguments, $# will expand to 3, then this will
# be concatenated to become  last="${3}"  which then gets evaluated
# by this shell (need braces because $# might be > 9)
eval 'last="${'$#'}"'
                             
# my earlier method
#last=`eval 'echo "${'$#'}"'`

# debugging
#echo $last
#exit 0

# test to see if it's a directory
if [ -d "$last" ]; then
  # ok, just send all the arguments to 'mv' since nothing will be renamed
  exec mv "$@"
else
  # oops, mistyped destination, most likely
  echo "move: $last is not a directory"
  exit 1
fi

