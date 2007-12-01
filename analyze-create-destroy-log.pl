#!/usr/bin/perl -w
# track a sequence of create and destroy events to find leaks

use strict 'subs';

# set of in-use mem locations; all values are whatever followed the
# address on the creation line; keys begin with "x" so they will be
# uniformly treated as strings
%inuse = ();

$lineno = 0;

while (defined($line = <STDIN>)) {
  chomp($line);
  $lineno++;

  my ($addr, $info) = ($line =~ m/Created arena at 0(x[0-9a-f]+): (.*)$/);
  if (defined($addr)) {
    if (defined($inuse{$addr})) {
      die("$line: created existing arena: $addr\n");
    }
    $inuse{$addr} = $info;
  }

  ($addr) = ($line =~ m/Destroyed arena at 0(x[0-9a-f]+)/);
  if (defined($addr)) {
    if (!defined($inuse{$addr})) {
      die("$line: destroyed arena not created: $addr\n");
    }
    $inuse{$addr} = undef;
  }
}

foreach $k (sort(keys(%inuse))) {
  my $v = $inuse{$k};
  if (defined($v)) {     # why is this necessary?
    print("leaked: 0$k: $inuse{$k}\n");
  }
}

# EOF
