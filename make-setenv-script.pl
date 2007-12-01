#!/usr/bin/perl -w
# script to print the environment as a shell script that can
# be sourced to recreate that environment

use strict 'subs';

print(<<"EOF");
# script to re-create environment
# created by $0

EOF

# sorting the keys is useful because then I can diff environments
foreach $key (sort (keys (%ENV))) {
  # filter (comment) out certain variables that are frequently
  # changing and/or highly dependent on the current context
  if ($key eq "PWD" ||
      $key eq "_" ||
      $key eq "OLDPWD" ||
      $key eq "SHLVL") {
    print("#");
  }

  my $value = $ENV{$key};
  
  # escape any single-quotes in $value; note that backslash is
  # not a metacharacter in bourne shell single-quote strings,
  # so a different techniqe must be used
  $value =~ s/\'/\'"'"\'/g;

  print("export $key='$value'\n");
}

print("\n#EOF\n");


# EOF
