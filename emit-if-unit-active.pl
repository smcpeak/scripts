#!/usr/bin/perl -w
# run a cov-commit command line if its translation unit is active

use strict 'subs';

sub usage {
  print(<<"EOF");
usage: $0 cov-emit <various args> file.cpp

The job of this script is to see if file.cpp is listed in either
units.txt or required-units.txt, both in the current directory.  If
so, then it runs its command line; otherwise it simply exits.

The text files list one file per line.  The line contents must exactly
match file.cpp for it to be considered a hit.

EOF
}

if (@ARGV == 0) {
  usage();
  exit(2);
}

$unit = $ARGV[@ARGV - 1];

if (fileContains("units.txt", $unit) ||
    fileContains("required-units.txt", $unit)) {
  exec(@ARGV);
  die("exec: $!\n");
}
else {
  exit(0);
}


sub fileContains {
  my ($fname, $unit) = @_;

  if (!open(IN, "<$fname")) {
    # missing file does not contain anything
    return 0;
  }

  my $line;
  while (defined($line = <IN>)) {
    chomp($line);
    if ($line eq $unit) {
      close(IN);
      return 1;
    }
  }
  
  close(IN);
  return 0;
}


# EOF
