#!/bin/sh
# remove stuff from . to make a subset of a Prevent distro for use with Debian tests

set -x
set -e

rm -rf META-INF cgi-bin doc jars jre library xsl
mv bin oldbin
mkdir bin
mv oldbin/{cov-commit-defects,cov-emit,cov-install-gui,cov-internal-analyze-c,cov-query-db,license.dat} bin/
rm -rf oldbin

# EOF
