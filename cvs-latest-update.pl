#!/usr/bin/perl -w
# find the date of the latest CVS update, by looking in CVS/Entries
# for the latest date listed

if (! -f "CVS/Entries") {
  die("This script is mean to be run in a directory that has a CVS/Entries file.\n");
}
                                     
$verbose = 0;
if (@ARGV >= 1 && $ARGV[0] eq "-v") {
  $verbose = 1;
}

sub diagnostic {
  my ($msg) = @_;
  if ($verbose) {
    print($msg . "\n");
  }
}

open(IN, "<CVS/Entries") or die("cannot open CVS/Entries\n");
@lines = <IN>;
close(IN) or die;

# current latest date; start with a very old one so it will
# be quickly surpassed
$bestDate = "Tue Jan  1 00:00:00 1980";

# map month names to integers
%monthMap = (
  "Jan" => 1,
  "Feb" => 2,
  "Mar" => 3,
  "Apr" => 4,
  "May" => 5,
  "Jun" => 6,
  "Jul" => 7,
  "Aug" => 8,
  "Sep" => 9,
  "Oct" => 10,
  "Nov" => 11,
  "Dec" => 12
);

sub monthNameToInt {
  my ($name) = @_;

  my $ret = $monthMap{$name};
  if (defined($ret)) {
    return $ret;
  }
  else {
    die("unknown month: $name");
  }
}

for ($i = 0; $i < @lines; $i++) {
  #       01          2   3                        45
  # e.g. "/arraymap.h/1.3/Fri Oct 11 22:07:00 2002//"
  $line = $lines[$i];

  @fields = split("/", $line);
  $date = "";

  if ($fields[0] eq "D" && defined($fields[1])) {
    # directory; recursively find the latest date in it
    $date = `cd \"$fields[1]\"; $0`;
    chomp($date);
    
    diagnostic("recursive date for $fields[1]: $date");
  }
  elsif (@fields == 6) {
    $date = $fields[3];
  }

  if ($date =~ m/dummy/) {
    # this is a "dummy timestamp" used for just-added files, and
    # should therefore be ignored
    $date = "";
  }

  if ($date && datecmp($date, $bestDate) > 0) {
    $bestDate = $date;
  }
}

print("$bestDate\n");
exit(0);

# return:
#   <0    if $d1 < $d2
#   =0    if $d1 = $d2
#   >0    if $d1 > $d2
sub datecmp {
  my ($d1, $d2) = @_;

  #              0   1   2  3        4
  # $d1 is e.g. "Fri Oct 11 22:07:00 2002"

  diagnostic("datecmp(\"$d1\", \"$d2\")");

  my @d1fields = split(/ +/, $d1);
  my @d2fields = split(/ +/, $d2);

  my $ret = ($d1fields[4] - $d2fields[4]);
  if ($ret != 0) { return $ret; }

  $ret = (monthNameToInt($d1fields[1]) - monthNameToInt($d2fields[1]));
  if ($ret != 0) { return $ret; }

  $ret = ($d1fields[2] - $d2fields[2]);
  if ($ret != 0) { return $ret; }

  #                       0  1  2
  # $d1fields[3] is e.g. "22:07:00"

  my @t1fields = split(/:/, $d1fields[3]);
  my @t2fields = split(/:/, $d2fields[3]);

  for (my $j = 0; $j < 3; $j++) {
    $ret = ($t1fields[$j] - $t2fields[$j]);
    if ($ret != 0) { return $ret; }
  }

  return 0;
}


# EOF
