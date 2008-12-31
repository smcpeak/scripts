#!/usr/bin/perl -w
# test xargs' ability to split long inputs into many command lines

use strict;

if (@ARGV > 0 && $ARGV[0] eq "-test") {
  # indicate that a process was invoked by writing a line
  # to stdout and exiting
  printf("$$: nargs=%d length=%d\n", scalar(@ARGV), length("@ARGV"));
  exit(0);
}

if (@ARGV != 3) {
  die("usage: $0 firstarg argstring nargs\n");
}

my $firstarg = $ARGV[0];
my $argstring = $ARGV[1];
my $nargs = $ARGV[2];

# file for recording number of process invocations
my $tmpfile = "/tmp/test-xargs.$$.tmp";

open(OUT, "| xargs $0 -test > $tmpfile") or die;

print OUT ("$firstarg\n");
for (my $i=0; $i < $nargs; $i++) {
  print OUT ("$argstring\n");
}

close(OUT) or die;

system("cat $tmpfile");
unlink($tmpfile);

exit(0);

# EOF
