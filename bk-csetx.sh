#!/bin/sh

# Copyright (c) 2005 by BitMover, Inc.
# All rights reserved.
#
# The following Source Code ("Code") was produced by BitMover, Inc.
# The Code is provided for recipient's use with the following restrictions:
#   1) This entire legend must be reproduced in association with the
#      Code on all media and as a part of any software program developed
#      by the user, in whole or part;
#   2) Users may copy or modify the Code without charge;
#   3) Users shall not license or distribute the Code to anyone else
#      except BitMover.
#   4) This code is provided with no support from BitMover, Inc.; and,
#   5) This code is provided without any obligation of BitMover, Inc.
#      to assist in its use, correction, modification or enhancement.
#
# THIS CODE IS COPYRIGHTED BY BITMOVER, INC.
# THIS CODE IS PROVIDED "AS IS" WITHOUT EXPRESS OR IMPLIED WARRANTY OF
# ANY KIND.    BITMOVER, INC. MAKES NO REPRESENTATIONS ABOUT THE
# SUITABILITY OF THE CODE FOR ANY PURPOSE.    BITMOVER, INC. DISCLAIMS
# ALL WARRANTIES WITH REGARD TO THE CODE, INCLUDING ALL IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.  IN
# NO EVENT SHALL BITMOVER, INC. BE LIABLE FOR ANY SPECIAL, INDIRECT,
# INCIDENTAL, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING
# FROM USE OF THE CODE, REGARDLESS OF THE THEORY OF LIABILITY.
#
# BITMOVER, INC. SHALL NOT BE LIABLE FOR ANY INFRINGEMENT OF COPYRIGHTS,
# TRADE SECRETS, PATENTS OR OTHER INTELLECTUAL PROPERTY RIGHT BY THE CODE,
# OR ANY PART THEREOF, OR ANY USE THEREOF.
#
# rick@work.bitmover.com|src/csetx.sh|20060619015828|61848

# Copyright (c) 2005 BitMover

usage() {
	echo "Usage: csetx.sh <rev>"
	echo "Where <rev> is not a merge revision"
	exit 1
}
test "X$1" != X -a "X$2" = X || usage

cd `bk root` || {
	echo Must be in a repository
	usage
}
MERGE=`bk changes -r"$1" -d'$if(:MERGE:){MERGE\n}'`
test "X$MERGE" != "XMERGE" || {
	echo "Revision '$1' is a merge revision."
	usage
}
# Assume filesystem that has hardlinks
set -e
bk clone -lr"$1" . BitKeeper/tmp/EXCLUDE
cd BitKeeper/tmp/EXCLUDE
bk rset -hr+ | grep -v '^ChangeSet|' > BitKeeper/tmp/LIST
set +e
# parse file names with spaces
IFS='|'
# Current Name | Parent Name | Parent Rev | Name | Rev
cat BitKeeper/tmp/LIST | while read CNAME PARNAME PARREV NAME REV
do
	# assert CNAME = NAME
	test "X$CNAME" = "X$NAME" || {
		echo "Assert fail: rev name ($NAME) matches cur name ($CNAME)."
		exit 1
	}
	# If this is a create, delete the file.
	test "$PARREV" = "1.0" && {
		echo "Deleting file which was created: $CNAME"
		bk rm "$CNAME"
		touch BitKeeper/tmp/commit
		continue
	}

	# Check flags, if they are different, just warn them
	WANT=`bk prs -hnd:FLAGS: -r$PARREV "$CNAME"`
	GOT=`bk prs -hnd:FLAGS: -r$REV "$CNAME"`
	test "$WANT" = "$GOT" || {
		echo "Warning, not restoring flags change in $CNAME"
		echo "OLD: $WANT"
		echo "NEW: $GOT"
	}

	# Check mode
	WANT=`bk prs -hnd:RWXMODE: -r$PARREV "$CNAME"`
	GOT=`bk prs -hnd:RWXMODE: -r$REV "$CNAME"`
	test "$WANT" = "$GOT" || {
		bk chmod  $WANT "$CNAME"
		touch BitKeeper/tmp/commit
	}

	# Make sure we rename it properly
	test "$PARNAME" = "$CNAME" && continue

	bk mv "$CNAME" "$PARNAME"
	touch BitKeeper/tmp/commit

done
# This needs to be combined into the cset exclude changeset
test -f BitKeeper/tmp/commit && bk commit -y'cset exclude, part 2'

# Pull in the work
cd ../../..
bk pull BitKeeper/tmp/EXCLUDE && rm -rf BitKeeper/tmp/EXCLUDE
exit 0
