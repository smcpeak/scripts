#!/usr/bin/perl -w
# recursivediff.pl
# recursively diff two trees and generate a big patch file

# get my name without the path
$me = $0;
$me =~ s%.*/%%;

if ( @ARGV < 3 ) {
  print STDOUT <<EOF;
usage: $me oldtree newtree list-of-filenames
  oldtree: tree of original files
  newtree: tree of modified files
  list: filenames, relative to {new,old}tree

  Run this script from the parent directory of oldtree and newtree.
  newtree should be the original name of the tree, while oldtree
  should be some different name.  Diffs are sent to stdout.
  Reports about which files differ are sent to stderr.

  Example:
    ~/tmp% gunzip -c package.tar.gz | tar xf -
    ~/tmp% cp -R package orig-package
    [make changes to ~/tmp/package]
    ~/tmp% (cd package; find . -name '*.[ch]*' -print) > pkgfiles
    ~/tmp% $me orig-package package pkgfiles > allchanges.patch
    [then later, to use created patch]
    ~/foo% gunzip -c package.tar.gz | tar xf -
    ~/foo% patch < ~/tmp/allchanges.patch
EOF
  exit(0);
}

# parameters
($oldtree, $newtree, $listfile) = @ARGV;
$oldtree =~ s%/$%%;    	 # strip any trailing slash from directory names
$newtree =~ s%/$%%;


# open the list of sources
open(LIST, "<$listfile") or die("$me: can't open $listfile: $!\n");
while ($fn = <LIST>) {
  chomp($fn);

  # remove a leading "./" since find likes to put that but I don't
  # want it to show up in my patch files
  $fn =~ s%^\./%%;

  $oldfn = "$oldtree/$fn";
  $newfn = "$newtree/$fn";

  if (-d $oldfn && -d $newfn) {
    # they're both directories, probably found by "find . -name '*' -print";
    # just silently skip them
    next;
  }

  if (! -f $oldfn || ! -f $newfn) {
    print STDERR ("$me: $oldfn or $newfn doesn't exist (as -f)\n");
    next;
  }

  $cmd = "diff -c $oldfn $newfn";
  #print("$cmd\n");
  #next;

  $code = system($cmd);
  $status = $code >> 8;
  if ($status >= 2) {
    print STDERR ("$me: `$cmd' failed with exit code $status\n");
  }
  elsif ($status == 1) {
    print STDERR ("$me: $oldfn and $newfn are different\n");
  }
}
close(LIST) or die;

exit(0);
