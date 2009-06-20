#!/usr/bin/perl -w
# given a document with <span class="reqid">...</span> markers,
# add anchors above them for hyperlinking purposes

use strict;
              
my $line;
while (defined($line = <STDIN>)) {
  chomp($line);

  my ($before, $name, $after) =
    ($line =~ m,^(.*)<span class="reqid">(.*)</span>:(.*)$,);
  if (defined($after)) {
    $name = lc($name);
    print("$before<a name=\"reqid-$name\"></a>$after\n");
  }

  print($line . "\n");
}

# EOF
