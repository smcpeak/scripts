#!/bin/sh
# interceptor script

# save the environment
printenv >env.txt

# save stdin (POST data)
cat >stdin.txt

# now run cov.cgi with that stuff
./cov.cgi.orig < stdin.txt > stdout.txt 2>stderr.txt
code=$?

# relay that output to apache
cat stdout.txt
cat stderr.txt 1>&2

exit $code

# EOF
