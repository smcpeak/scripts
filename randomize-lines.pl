#!/usr/bin/perl -w
# read stdin, write same lines in random order to stdout

use strict 'subs';

srand();

my @lines = <STDIN>;
my $numlines = @lines;

# loop invariant: lines[0..$i-1] are randomly ordered
for (my $i = 0; $i < $numlines; $i++) {
  # select random line in the unrandomized tail
  my $pick = $i + int(rand($numlines - $i));

  # swap lines[$i] and lines[$pick]
  my $tmp = $lines[$pick];
  $lines[$pick] = $lines[$i];
  $lines[$i] = $tmp;
  
  # no particular reason to wait on writing these out
  print($lines[$i]);
}


# EOF
