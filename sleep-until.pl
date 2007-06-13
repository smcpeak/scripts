#!/usr/bin/perl -w
# sleep until specified time

use strict 'subs';

if (@ARGV == 0) {
  print("usage: $0 HH:MM\n");
  exit(2);
}

$alarmTime = $ARGV[0];

($alarmHour, $alarmMin) =
  ($alarmTime =~ m/^(\d\d):(\d\d)$/);
if (!defined($alarmMin)) {
  die("malformed time: $alarmTime\n");
}
#print("alarmHour=$alarmHour, alarmMin=$alarmMin\n");

#  0    1    2     3     4    5     6     7     8
($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) =
  localtime(time);
pretendUsed($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst);

$diff = ($alarmHour - $hour) * 60 + ($alarmMin - $min);
if ($diff < 0) {
  $diff += 24 * 60;
}

$diffHours = int($diff / 60);
$diffMins = $diff % 60;

printf("sleeping for $diff minutes (%02d:%02d)\n", $diffHours, $diffMins);
sleep($diff * 60);
#print("done sleeping\n");

exit(0);

sub pretendUsed {
}

# EOF

