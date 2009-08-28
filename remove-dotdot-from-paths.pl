#!/usr/bin/perl -w
# remove ".." in path names input one per line

use strict;

my $line;
while (defined($line = <STDIN>)) {
  $line =~ s/[\r\n]+$//;

  my @components = split(/\//, $line);

  my @output = ();

  foreach my $c (@components) {
    if ($c ne "..") {
      push @output, ($c);
    }
    else {
      if (scalar(@output) > 0) {
        pop @output;
      }
      else {
        die("\"..\" cannot be removed: $line\n");
      }
    }
  }

  print(join('/', @output) . "\n");
}

# EOF
