#!/usr/bin/perl -w
# test xargs' ability to split long inputs into many command lines

use strict;

if (@ARGV > 0 && $ARGV[0] eq "-test") {
  # indicate that a process was invoked by writing a line
  # to stdout and exiting
  printf("$$: nargs=%d length=%d\n", scalar(@ARGV), length("@ARGV"));
  exit(0);
}

if (@ARGV != 2) {
  die("usage: $0 argstring nargs\n");
}

my $argstring = $ARGV[0];
my $nargs = $ARGV[1];

# file for recording number of process invocations
my $tmpfile = "/tmp/test-xargs.$$.tmp";

open(OUT, "| xargs $0 -test > $tmpfile") or die;

for (my $i=0; $i < $nargs; $i++) {
  print OUT ("$argstring\n");
}

close(OUT) or die;

system("cat $tmpfile");
unlink($tmpfile);

exit(0);

# EOF
