#!/usr/bin/perl -w
# Run a program and print its running time.
# Similar to 'log-runtime', but with greater precision.

use strict;
use Time::HiRes qw( gettimeofday );

if (@ARGV < 1) {
  print STDERR ("usage: $0 <command> [<args>...]\n");
  exit(2);
}

my ($startSeconds, $startMicroseconds) = gettimeofday();

my $code = system(@ARGV);

my ($endSeconds, $endMicroseconds) = gettimeofday();

my $elapsedSeconds = $endSeconds - $startSeconds;

my $elapsedMicroseconds = $endMicroseconds - $startMicroseconds;
if ($elapsedMicroseconds < 0) {
  $elapsedMicroseconds += 1000000;
  $elapsedSeconds--;
}

#printf("elapsed %d.%06d: @ARGV\n",
#  $elapsedSeconds,
#  $elapsedMicroseconds);

printf("time-command.pl: @ARGV: elapsed %d.%06d\n",
  $elapsedSeconds,
  $elapsedMicroseconds);

# Propagate the same exit status.
if ($code == 0) {
  exit(0);
}
elsif ($code >= 256) {
  exit($code >> 8);
}
else {
  #print STDERR ("Propagating signal $code\n");
  kill($code, $$);

  # Cygwin kill seems somewhat ineffective.
  print STDERR ("time-command: Child command died by signal $code\n");
  exit(2);
}


# EOF
