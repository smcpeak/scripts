#!/usr/bin/perl -w
# use gnuplot to plot a CSV file

use strict 'subs';

sub usage {      
  print("$0 < file.csv | gnuplot -persist\n");
}

#  if (@ARGV == 0) {
#    usage();
#    exit(2);
#  }

# read the header line
$line = <STDIN>;
if (!defined($line)) {
  die("input is empty\n");
}
chomp($line);
@labels = split(',', $line);

if (@labels < 2) {
  die("the labels line should have at least two labels, one for X and one for the first Y\n");
}

# write the plot line
print("plot");
for ($col=1; $col < @labels; $col++) {
  if ($col > 1) {
    print(",");
  }
  print(" '-' with lines title '$labels[$col]'");
}
print("\n");

# read all the data into memory
while (defined($line = <STDIN>)) {
  chomp($line);
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
