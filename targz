#! /bin/csh -f
# script to tar and gunzip a directory

if ( "$1" == "" ) then
  echo usage: $0 directory-name
  echo writes directory-name.tar.gz into current directory
  exit
endif

# I often screw up and put a trailing slash in the name
# (by using tcsh filename completion); this fixes it
set d = `echo $1 | sed 's#/$##'`

tar cvf - $d | gzip -c > $d.tar.gz
