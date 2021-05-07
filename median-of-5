#!/usr/bin/perl -w
# run a program, discarding its output, but measuring its
# excution time; do this 5 times

# Originally written by Scott McPeak and contributed to the
# public domain.

use strict;
use Time::HiRes qw( gettimeofday );

sub usage {
  print(<<"EOF");
usage: $0 [options] program [args...]

options:
  -setup 'command': specify untimed command to run before program
  -iters n        : number of iterations to run (default: 5)
  -hide           : hide program console output
  -oneline        : only print a single output summary line

EOF
}


# -------------------- command line -------------------
# command to invoke before each timed test
my $setup = "";

# number of times to run the test
my $iters = 5;

# true if we will show the console output of the program
my $showOutput = 1;

# True to show just one line of output.
my $oneline = 0;

while (@ARGV && $ARGV[0] =~ m/^-/) {
  my $opt = shift @ARGV;

  if ($opt eq "-setup") {
    $setup = shift @ARGV;
  }
  elsif ($opt eq "-iters") {
    $iters = shift @ARGV;
  }
  elsif ($opt eq "-show") {
    $showOutput = 1;
  }
  elsif ($opt eq "-hide") {
    $showOutput = 0;
  }
  elsif ($opt eq "-oneline") {
    $showOutput = 0;
    $oneline = 1;
  }
  else {
    usage();
    die("unknown option: $opt\n");
  }
}

if (@ARGV == 0) {
  usage();
  die("must specify a program to run\n");
}


# ---------------------- iterations --------------------
# sequence of wallclock times in milliseconds (as floating-point)
my @results = ();

# run it $iters times
for (my $i = 1; $i <= $iters; $i++) {
  if ($setup ne "") {
    if (mysystem($setup) != 0) {
      die("setup command failed: $setup\n");
    }
  }

  # always sync the disks before timing
  mysystem("sync");

  # get time before running the child ($secs, $msecs)
  my @before = gettimeofday();

  # run it
  #
  if ($showOutput) {
    # Redirect input from /dev/null to avoid hanging if the program
    # tries to read stdin.
    #
    # It is unfortunate that I cannot easily do redirection w/o using
    # shell, since that means metacharacters in @ARGV are vulnerable.
    mysystem("@ARGV </dev/null");
  }
  else {
    mysystem("@ARGV </dev/null >/dev/null 2>&1");
  }

  my @after = gettimeofday();

  my $diff = ($after[0] - $before[0]) * 1000 +
             int(($after[1] - $before[1]) / 1000);

  if (!$oneline) {
    print("median-of-5 run $i: $diff ms\n");
  }
  push @results, ($diff);
}


if (!$oneline && $iters > 1) {
  # summarize all runs on one line at the end
  print("all   : @results\n");
}


# sort the results in increasing numeric order
@results = sort {$a <=> $b} @results;
#print("sorted: @results\n");

# Select middle, first quartile, and last quartile elements.
my $n = scalar(@results);
my $median = $results[int($n / 2)];
my $firstQuartile = $results[int($n / 4)];
my $lastQuartile = $results[int($n * 3 / 4)];

# Interquartile dispersion.
my $interquartile = $lastQuartile - $firstQuartile;

# mean average
my $sum = 0;
foreach my $r (@results) {
  $sum += $r;
}
my $mean = $sum / scalar(@results);   # yields floating-point

# variance
my $distsqsum = 0;
foreach my $r (@results) {
  $distsqsum += ($mean - $r) * ($mean - $r);
}
my $variance = $distsqsum / scalar(@results);

my $stddev = sqrt($variance);


if ($oneline) {
  printf("%10d +/- %4d ms: %s\n",
         $median,
         $interquartile,
         join(' ', @ARGV));
}

elsif ($iters > 1) {
  printf("median: %10d    ms\n", $median);
  printf("iquart: %10d    ms\n", $interquartile);
  printf("mean  : %13.2f ms\n", $mean);
  printf("stddev: %13.2f ms\n", $stddev);
}


exit(0);


# like system(), but bail on ctrl-C
sub mysystem {
  my $res = system(@_);
  if ($res == 2) {
    # ctrl-C
    kill(2, $$);
    die("should have died...");
  }
  return $res;
}


# EOF
