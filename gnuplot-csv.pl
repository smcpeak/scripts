#!/usr/bin/perl -w
# use gnuplot to plot a CSV file

use strict 'subs';

sub usage {
  print(<<"EOF");
$0 [options] < file.csv | gnuplot -persist

options:
  -points          Print points instead of lines
  -log             Use logscale for X and Y axes
  -no-legend       Turn off legend
  -xlabel <label>  Label X axis with <label>, overriding input
  -ylabel <label>  Label Y axis with <label>
  -title <title>   Set graph title
  -png <X> <Y>     Output as PNG file with size <X>x<Y>; use with -output
  -output <fname>  Write output to <fname>
EOF
}

my $style = "lines";
my $xlabel = undef;

# process command line arguments
while (@ARGV != 0) {
  my $opt = shift(@ARGV);

  if ($opt eq "-points") {
    $style = "points lt rgb \"black\"";
  }
  elsif ($opt eq "-log") {
    print("set logscale xy\n");
  }
  elsif ($opt eq "-no-legend") {
    print("set key off\n");
  }
  elsif ($opt eq "-xlabel") {
    $xlabel = shift(@ARGV);
  }
  elsif ($opt eq "-ylabel") {
    my $arg = shift(@ARGV);
    print("set ylabel '$arg'\n");
  }
  elsif ($opt eq "-title") {
    my $arg = shift(@ARGV);
    print("set title '$arg'\n");
  }
  elsif ($opt eq "-png") {
    my $x = shift(@ARGV);
    my $y = shift(@ARGV);
    print("set terminal png size $x,$y\n");
  }
  elsif ($opt eq "-output") {
    my $arg = shift(@ARGV);
    print("set output '$arg'\n");
  }
  else {
    usage();
    die("unknown option: $opt\n");
  }
}

# read the header line
$line = <STDIN>;
if (!defined($line)) {
  die("input is empty\n");
}

# CSV files often use CRLF line endings, so 'chomp' is inadequate.
$line =~ s/[\r\n]+$//;

@labels = split(',', $line);

if (@labels < 2) {
  die("the labels line should have at least two labels, one for X and one for the first Y\n");
}

if (!$xlabel) {
  # Use the first column header as the default X axis label.
  $xlabel = $labels[0]
}

# Write a line with the X axis label.
print("set xlabel '$xlabel'\n");

# write the plot line
print("plot");
for ($col=1; $col < @labels; $col++) {
  if ($col > 1) {
    print(",");
  }
  print(" '-' with $style title '$labels[$col]'");
}
print("\n");

# read all the data into memory
while (defined($line = <STDIN>)) {
  $line =~ s/[\r\n]+$//;
  push @data, $line;
}

# process each column
for ($col=1; $col < @labels; $col++) {
  foreach my $d (@data) {
    my @values = split(',', $d);
    print("$values[0] $values[$col]\n");
  }

  print("e\n");
}


# EOF
