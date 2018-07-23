#!/usr/bin/perl -w
# Convert HH:MM:SS form to seconds.

if (@ARGV != 1) {
  die("usage: $0 [HH:][MM:]SS\n");
}

my $hhmmss = $ARGV[0];

my @elts = split(/:/, $hhmmss);

my $ret = 0;
foreach my $e (@elts) {
  $ret = $ret*60 + $e;
}

print("$ret\n");

# EOF
