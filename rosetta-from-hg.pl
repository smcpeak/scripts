#!/usr/bin/perl -w
# convert from Mercurial ("Hg") to Rosetta

use strict 'subs';


# ------------------- command-line processing ------------------
sub usage {
  print(<<"EOF");
usage: $0 hg-repo rosetta-repo
EOF
}

if (@ARGV != 2) {
  usage();
  die("wrong number of arguments\n");
}

$hgRepo = $ARGV[0];
$rosettaRepo = $ARGV[1];

# normalize by removing any trailing '/'s
$hgRepo =~ s,/+$,,;
$rosettaRepo =~ s,/+$,,;


# ---------------------- sanity checking -----------------------
if (! -d "$hgRepo/.hg") {
  die("\"$hgRepo\" does not appear to be a Mercurial repository.  " .
      "It should have a subdirectory named \".hg\".\n");
}

if (-e $rosettaRepo) {
  die("\"$rosettaRepo\" already exists; it should not, because this " .
      "script will create it.\n");
}


# ---------------- get entire set of revisions -----------------
# map from revision number (e.g., 0, 1, 2, ...) to the revision
# hash (e.g., 2d08e5ffe52586991b23032730b7849f9aa4725e)
%revHashes = (-1 => "0000000000000000000000000000000000000000");

# map from revision number to primary parent
%revParent = ();

# map from revision number to merge parent, or -1 if none
$revMParent = ();

# look at all revisions
foreach my $line (hgCmdLines('log', '--template', "{rev} {node} {parents}\n")) {
  my ($rev, $hash, $p1r, $p1h, $p2r, $p2h) =
    ($line =~ m/^([0-9-]+) ([0-9a-f]+) (?:([0-9-]+):([0-9a-f]+)(?: ([0-9-]+):([0-9a-f]+))?)?$/);
    #            ^^^^^^^^^ ^^^^^^^^^^^    ^^^^^^^^^ ^^^^^^^^^^^    ^^^^^^^^^ ^^^^^^^^^^^
    #              $rev       $hash         $p1r       $p1h          $p2r       $p2h

  if (!defined($hash)) {
    die("malformed log line: $line\n");
  }
  $revHashes{$rev} = $hash;
  
  if (!defined($p1r)) {
    # special case: sole parent is numerically preceding
    # revision number (see cmdutil.py, look for "showparents")
    $p1r = $rev - 1;
  }
  $revParent{$rev} = $p1r;
  pretendUsed($p1h);

  if (!defined($p2r)) {
    $p2r = -1;
  }
  $revMParent{$rev} = $p2r;
  pretendUsed($p2h);
}


# make the main Rosetta directory
mkdirOrDie($rosettaRepo);
mkdirOrDie("$rosettaRepo/revs");


# ---------------- get individual revision info ----------------
# Currently, it is my intent that the final result is independent
# of the order in which the revisions are retrieved.  But I may
# want to make changes that will cause order dependence, and in
# any case it's nice to have the order be deterministic.
foreach my $r (sort {$a <=> $b} keys(%revHashes)) {
  eval {
    if ($r != -1) {
      getRevInfo($r);
    }
  };
  if ($@) {
    die("rev $r: $@");
  }
}

sub getRevInfo {
  my ($rev) = @_;
  print("getting revision $rev ...\n");

  # create Rosetta directory for this rev
  mkdirOrDie("$rosettaRepo/revs/$rev");

  # pull main info for the meta file
  my @info = hgCmdLines('log',
                        '--rev', $revHashes{$rev},
                        '--template', "{author}\n{date}\n{desc}\n");
  my $author = shift(@info);
  my $dates = shift(@info);      # UTC <space> TZ_secs
  my @comments = @info;

  # parse $dates
  my ($utc, $tz) = ($dates =~ m/^([0-9]+)\.([0-9-]+)$/);
  if (!defined($tz)) {
    die("malformed dates: $dates\n");
  }

  # get $parents
  my $parent = $revParent{$rev}; 
  my $mparent = $revMParent{$rev};
  
  # get file-level events relative to $parent
  my @events = getFileEvents($rev, $parent);

  # write the revinfo file
  open(OUT, ">$rosettaRepo/revs/$rev/revinfo");
  print OUT ("rev: $rev\n");
  if ($parent != -1) {
    print OUT ("parent: $parent\n");
  }
  if ($mparent != -1) {
    print OUT ("mparent: $mparent\n");
  }
  print OUT ("author: $author\n");
  print OUT ("date: $utc\n");
  print OUT ("tz: $tz\n");
  print OUT ("comments:\n");
  foreach my $c (@comments) {
    print OUT ("  $c\n");
  }
  print OUT ("events:\n");
  foreach my $e (@events) {
    print OUT ("  $e\n");
  }
  close(OUT) or die;
}


# return a list of file-level events that transform $parent into $rev
sub getFileEvents {
  my ($rev, $parent) = @_;

  my @ret = ();
  
  # directory into which to place diffs, etc.
  my $rosettaRevDir = "$rosettaRepo/revs/$rev/";

  # get manifests for current and parent
  my %revManifest = getManifest($rev);
  my %parentManifest = getManifest($parent);

  # see what happened to files in %parentManifest
  foreach my $path (keys(%parentManifest)) {
    my ($parentFileHash, $parentMode) =
      split(' ', $parentManifest{$path});

    # NOTE: Mercurial does not have a notion of file rename in
    # its metadata; it simply has (history-preserving) copy and
    # remove.  Even though Rosetta does have direct support for
    # rename, I do *not* try to recover renames at this stage.
    # Instead, a post-process history refactorer can transform
    # remove/copy operations into renames.

    # deleted?
    if (!defined($revManifest{$path})) {
      push @ret, stringifyEvent('remove',
                                'path' => $path);
      next;
    }

    # get current info
    my ($revFileHash, $revMode) =
      split(' ', $revManifest{$path});
    
    # mode change?
    if ($parentMode ne $revMode) {
      push @ret, stringifyEvent('chmod-abs',
                                'path' => $path,
                                'mode' => $revMode);
    }
    
    # content change?
    if ($parentFileHash ne $revFileHash) {
      # look at the file-level history to see if the change
      # recorded there names a different parent than $rev
      
      # get file-level history
      my %fileHistory = getFileHistory($path);

      # get parent and revlink specifically for the version
      # of the file as it exists in $rev
      my ($revFileParent, $revFileLinkRev) =
        split(' ', $fileHistory{shortenHash($revFileHash)});

      # does the file DAG match the revision DAG?
      if (shortenHash($parentFileHash) eq $revFileParent) {
        # yes: this is the easy case where we just need to
        # show a content diff

        # write the diff to a file
        my $diffFname = getUniqueFname($rosettaRevDir,
                                       basename($path) . ".diff");
        hgCmdRedirect($rosettaRevDir . $diffFname,
          "diff", "-r", $revHashes{$parent},
                  "-r", $revHashes{$rev},
                  "$hgRepo/$path");

        # include a diff record
        push @ret, stringifyEvent('modified-diff',
                                  'path' => $path,
                                  'diff' => $diffFname);
      }
      else {
        # no: let's treat this as a reversion
        push @ret, stringifyEvent('revert',
                                  'path' => $path,
                                  'rev' => $revFileLinkRev);

        # just a sanity check
        if ($revFileLinkRev == $parent) {
          # if this was the case, then we should have already found
          # that the file-level DAG matched
          die("should not happen");
        }

        # we need to confirm that $revFileLinkRev is among
        # the ancestors of $rev
        if (!amongAncestors($revFileLinkRev, $rev)) {
          die("want to revert $path to rev $revFileLinkRev, but it is " .
              "not among the ancestors of rev $rev\n");
        }
      }
    }
  }

  # see what happened to files in %revManifest
  foreach my $path (keys(%revManifest)) {
    # anything also in %parentManifest has already been
    # handled by the loop above
    if (defined($parentManifest{$path})) {
      next;
    }

    # file info
    my ($revFileHash, $revMode) =
      split(' ', $revManifest{$path});
      
    # the file was either created from scratch or reverted
    
    # get file-level history info, similar to above
    my %fileHistory = getFileHistory($path);
    my ($revFileParent, $revFileLinkRev) =
      split(' ', $fileHistory{shortenHash($revFileHash)});
      
    if ($revFileParent eq "000000000000") {
      # created from scratch
      my $fname = getUniqueFname($rosettaRevDir,
                                 basename($path) . ".new");
      hgCmdRedirect($rosettaRevDir . $fname,
        "cat", "-r", $revHashes{$rev}, "$hgRepo/$path");
      push @ret, stringifyEvent('created',
                                'path' => $path,
                                'contents' => $fname,
                                'mode' => $revMode);
    }
    else {
      # reverted; similar to above
      push @ret, stringifyEvent('revert',
                                'path' => $path,
                                'rev' => $revFileLinkRev);

      if (!amongAncestors($revFileLinkRev, $rev)) {
        die("want to revert $path to rev $revFileLinkRev, but it is " .
            "not among the ancestors of rev $rev\n");
      }
    }
  }

  return @ret;
}


# get manifest for $rev as a hash:
#   path -> "<filehash> <mode_octal>"
sub getManifest {
  my ($rev) = @_;

  my %ret = ();

  # --debug: add the filehash to the output
  # -v: add the mode to the output
  # (both of these options seem to me like bad UI design,
  # but they are the only documented methods of getting
  # this information from the 'manifest' command)
  foreach my $line (hgCmdLines('--debug', '-v', 'manifest',
                               $revHashes{$rev})) {
    # parse the manifest line
    #
    # note that 'mode' is rendered by 'manifest' in octal, but perl
    # will treat it as a string or as decimal (depending on unknown
    # heuristics); I will carry it through w/o interpreting, thereby
    # preserving the octal meaning
    my ($fileHash, $mode, $path) =
      ($line =~ m/^([0-9a-f0]+) ([0-7]+) (.*)$/);
    if (!defined($path)) {
      die("malformed manifest line: $line");
    }

    # insert results into return hash
    if (defined($ret{$path})) {
      die("manifest line repeats info for file: $path");
    }
    $ret{$path} = "$fileHash $mode";
  }

  return %ret;
}



# return history info for $path:
#   <short hash> -> "<parent short hash> <linkrev>"
#
# 'linkrev' is the numeric repository revision in which
# the given file contents were introduced
sub getFileHistory {
  my ($path) = @_;

  my %ret = ();

  eval {
    # This is the only way I know of to get the file-level history
    # information without writing a Python extension.
    my @lines = hgCmdLines("debugindex", "$hgRepo/.hg/store/data/${path}.i");

    # since it's a "debug" command, verify its output even more
    # carefully than I would otherwise
    my $first = shift(@lines);
    if ($first ne "   rev    offset  length   base linkrev nodeid       p1           p2") {
      die("unexpected first line from debugindex: $first\n");
    }

    foreach my $line (@lines) {
      my @fields = split(' ', $line);
      if (@fields != 8) {
        die("malformed debugindex line: $line\n");
      }

      my $linkrev = $fields[4];
      my $nodeid = $fields[5];
      my $p1 = $fields[6];

      $ret{$nodeid} = "$p1 $linkrev";
    }
  };
  if ($@) {
    die("getFileParents $path: $@");
  }

  return %ret;
}


# turn a long hash into a short hash
sub shortenHash {
  my ($h) = @_;
  
  my ($s) = ($h =~ m/^([0-9a-f]{12})/);
  if (!defined($s)) {
    die("malformed hash: $h\n");
  }
  
  return $s;
}


# see if $needle is among the ancestors of $child
#
# This algorithm by itself is linear.  Since it can be called a linear
# number of times, the total cost is quadratic.  However, it should
# only be called rarely, because we typically expect that the
# file-level DAG will match the revision-level DAG.
#
sub amongAncestors {
  my ($needle, $child) = @_;
  
  # basic DFS
  my @worklist = ($child);   # nodes not yet explored
  my %done = ();             # nodes whose parents have been added to worklist

  while (@worklist > 0) {
    my $node = shift(@worklist);

    # it is possible for a node to end up on the worklist
    # more than once; if so, we only need to look at its
    # children the first time
    if ($done{$node}) {
      next;
    }

    if ($node == $needle) {
      return 1;    # found it
    }

    my $p1 = $revParent{$node};
    my $p2 = $revMParent{$node};

    if ($p1 != -1 && !$done{p1}) {
      unshift @worklist, ($p1);
    }

    if ($p2 != -1 && !$done{p2}) {
      unshift @worklist, ($p2);
    }
    
    $done{$node} = 1;
  }
  
  return 0;
}


# ---------------------- Rosetta output ------------------------
# return a stringified form of an event record
sub stringifyEvent {
  my ($name, %attrs) = @_;

  my @ret = ("$name:");
  foreach my $k (keys(%attrs)) {
    push @ret, ("  $k: $attrs{$k}");
  }

  return @ret;
}


# ------------------------ subroutines -------------------------
# return '@cmd' after prefixing proper 'hg' stuff to run it
sub hgCmd {
  my (@cmd) = @_;

  return ('hg', '-R', $hgRepo, @cmd);
}


# backtickLines(hgCmd(@_))
sub hgCmdLines {
  return backtickLines(hgCmd(@_));
}


sub hgCmdRedirect {
  my ($file, @cmd) = @_;

  runCmdRedirect($file, 'hg', '-R', $hgRepo, @cmd);
}


# mkdir or die
sub mkdirOrDie {
  my ($d) = @_;

  if (!mkdir($d)) {
    die("mkdir $d: $!\n");
  }
}


# run '@cmd', and return the list of resulting output lines,
# all of them having been chomped
sub backtickLines {
  my (@cmd) = @_;
            
  # fork (this sequence based on what is in the perlsec man page)
  my $pid = open(KID, "-|");
  if (!defined($pid)) {
    die("backtickLines: fork: $!\n");
  }
  
  if ($pid != 0) {
    # parent: read lines
    my @ret = ();

    # get first line and check for exec error
    my $line = <KID>;
    if (!defined($line)) {
      # no output
      goto finish;
    }
    chomp($line);
    my ($msg) = ($line =~ m/^rosetta-from-hg child exec error: (.*)$/);
    if (defined($msg)) {
      # obviously, it is possible for a program to legitimately
      # produce this string, but unlikely
      close(KID);
      die("@cmd: exec: $msg\n");
    }

    # get remaining lines
    @ret = ($line);
    while (defined($line = <KID>)) {
      chomp($line);
      push @ret, ($line);
    }

    # finish up
  finish:
    close(KID);
    eval {
      checkExitCode($?);
    };
    if ($@) {
      die("@cmd: $@");
    }

    return @ret;
  }

  else {
    # child: launch process
    if (!exec(@cmd)) {
      print("rosetta-from-hg child exec error: $!\n");
      exit(2);
    }
  }
}


# run @cmd, writing its standard output to $file
sub runCmdRedirect {
  my ($file, @cmd) = @_;
  
  # just use the shell, but be careful about metacharacters
  my $cmdline = "";
  foreach my $c (@cmd) {
    $cmdline .= shellQuote($c) . " ";
  }
  
  $cmdline .= "> " . shellQuote($file);
  
  run($cmdline);
}


# quote something for Bourne shell
sub shellQuote {
  my ($s) = @_;

  if ($s =~ m/^[a-zA-Z0-9_=+%:,.\/-]+$/) {
    # no metacharacters, so just use as-is (makes it easier to read if
    # we end up printing out the resulting command line)
    return $s;
  }

  $s =~ s/\'/\'"'"\'/g;      # ' -> '"'"'
  
  return "'$s'";
}


# run @cmd, die if it fails
sub run {
  my (@cmd) = @_;

  my $res = system(@cmd);
  
  eval {
    checkExitCode($res);
  };
  if ($@) {
    die("@cmd: $@");
  }
}


# check an exit code, die if nonzero
sub checkExitCode {
  my ($code) = @_;

  if ($code != 0) {
    my $sig = $code & 0xff;
    my $code = $code >> 8;
    die("failed with " .
        ($sig? "signal $sig" : "exit code $code") .
	"\n");
  }
}


# path -> final name component
sub basename {
  my ($path) = @_;
  
  my ($ret) = ($path =~ m,([^/]+)$,);
  if (!defined($ret)) {
    die("basename: bad path: $path\n");
  }
  
  return $ret;
}


# append a number to $base, if necessary, to make "${dir}${base}" unique
sub getUniqueFname {
  my ($dir, $base) = @_;

  if (! -e "${dir}${base}") {
    return $base;
  }

  my $n = 2;
  while (-e "${dir}${base}${n}") {
    $n++;
  }
  
  return $base;
}


# write @lines to $fname
sub writeFile {
  my ($fname, @lines) = @_;
  
  open(OUT, ">$fname") or die("cannot write $fname: $!\n");
  foreach my $line (@lines) {
    print OUT ("$line\n");
  }
  close(OUT) or die;
}


# silence warning about unused variable
sub pretendUsed {
}


# EOF
