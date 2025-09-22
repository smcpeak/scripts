#!/bin/sh
# For all files that are new according to `git`, chmod them based on
# their extension.

# This is meant for use on Cygwin where everthing is executable by
# default.

git ls-files --others --exclude-standard | \
  egrep -i '\.(h[hp]*|c[cp]*|ded|png)$' | \
  xargsn runecho chmod 644

# EOF
