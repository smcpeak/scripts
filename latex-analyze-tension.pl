#!/usr/bin/perl -w
# analyze a latex .log file produced with \tracingpages=1
# and report on the per-page tension/compression

if (@ARGV == 0) {
  print(<<"EOF");
usage: $0 file.log
EOF
  exit(0);
}
            
$inFname = $ARGV[0];
$bestLine = "";

open(IN, "<$inFname") or die("cannot read $inFname: $!\n");

#                                   ......12345678901234567890 1234567890
print("page tension    plus   minus              tension      0    compression\n" .
      "---- ------- ------- -------                 |---------|---------|\n");

while (defined($line = <IN>)) {
  my ($pageno) =
    ($line =~ m/\[(\d+)/);
  if (defined($pageno)) {
    # end of one page, beginning of next
    if ($bestLine) {
      my ($t, $g) =
        ($bestLine =~ m/^% t=([0-9.]+) .*g=([0-9.]+)/);
      if (!defined($g)) {
        die("malformed line: $bestLine\n");
      }

      my ($plus) = ($bestLine =~ m/plus ([0-9.]+)/);
      if (!defined($plus)) {
        $plus = "0";
      }

      my ($minus) = ($bestLine =~ m/minus ([0-9.]+)/);
      if (!defined($minus)) {
        $minus = "0";
      }

      my $tension = $g - $t;

      printf("%4d %7.1f %7.1f %7.1f ", $pageno, $tension, $plus, $minus);

      my $endptChar = "*";
      if ($tension >= 0) {
        if ($plus == 0) {
          $plus = 0.001;
        }
        my $scaled = int($tension / $plus * 10.0 + 0.5);
        if ($scaled > 26) {
          $scaled = 26;
          $endptChar = "<";
        }
        print(" " x (26 - $scaled) . $endptChar . "-" x $scaled);
      }
      else {
        if ($minus == 0) {
          $minus = 0.001;
        }
        my $scaled = int((-$tension) / $minus * 10.0 + 0.5);
        if ($scaled > 10) {
          $scaled = 10;
          $endptChar = ">";
        }
        print(" " x 26 . "-" x $scaled . $endptChar);
      }

      print("\n");
    }
    else {
      die("by page $pageno, never saw a \\tracingpages=1 line\n");
    }
    $bestLine = "";
    next;
  }

  if ($line =~ m/^% t=.*\#$/) {
    $bestLine = $line;
    next;
  }
}
close(IN) or die;

# EOF
