#!/usr/bin/perl -w
# read lines from stdin and write them to stdout w/timestamps

use strict 'subs';

# Time::HiRes is in the standard perl distro as of 5.8
use Time::HiRes qw( gettimeofday );

# turn on autoflush (why isn't there just an explicit 'flush' function?)
$| = 1;

while (defined($line = <STDIN>)) {
  my ($secs, $usecs) = gettimeofday();
  printf("%d.%06d %s", $secs, $usecs, $line);
}

# EOF
