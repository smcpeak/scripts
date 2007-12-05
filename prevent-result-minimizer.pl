#!/usr/bin/perl -w
# script to automate a number of Prevent result minimization tasks

use strict 'subs';

sub usage {
  print(<<"EOF");
usage: $0 <checker> <function-name-prefix> <task>

<task> is one of:
  init           create the working directory
  test           test to see if difference of interest remains
  model-tunits   put set of tunits with events into required-commands.sh
EOF
}

if (@ARGV != 3) {
  usage();
  exit(2);
}

#$SIG{INT} = \&handleSigInt;

$HOME = $ENV{"HOME"};
$delta = "$HOME/wrk/cplr/delta/bin/delta";

$checker = $ARGV[0];
$function = $ARGV[1];
$task = $ARGV[2];

diagnostic("checker: $checker");
diagnostic("function: $function");
diagnostic("task: $task");

# the Makefile is sensitive to these
$ENV{"CHECKER"} = $checker;
$ENV{"FUNCTION"} = $function;

$workdir = "minimize/$checker-" . toSafeChars($function);
diagnostic("workdir: $workdir");


# ------------------------ check output dirs --------------------

# Confirm that one analysis finds the result and the other does not.

$dirNewast = "dir-newast";
$dirOldast = "dir-oldast";

$newastFinds = defectFound($dirNewast);
$oldastFinds = defectFound($dirOldast);

if ($newastFinds == $oldastFinds) {
  if ($newastFinds) {
    die("both analyses found the defect\n");
  }
  else {
    die("neither analysis found the defect\n");
  }
}

if ($newastFinds) {
  diagnostic("new AST found it");
}
else {
  diagnostic("old AST found it");
}


# ---------------------------- dispatch -------------------------
if ($task eq "init") {
  init();
}
elsif ($task eq "test") {
  my $result = testDifference();
  print("testDifference: $result\n");
}
elsif ($task eq "model-tunits") {
  modelTunits();
}
elsif ($task eq "preprocess") {
  preprocess();
}
elsif ($task eq "min-req-tunits") {
  minimizeTunits("required-commands.sh");
}
elsif ($task eq "min-main-tunits") {
  minimizeTunits("compile-commands.sh");
}
else {
  die("unknown task: $task\n");
}


# ------------------------------ init ---------------------------
sub init {
  # TEMPORARY
  run("rm", "-rf", $workdir);

  if (-d $workdir) {
    die("directory already exists: $workdir\n");
  }

  # the 'minimize' subdirectory should already exist
  run("mkdir", $workdir);
  run("ln minimize/template/* $workdir");

  # get minimal set of files
  my @minimalFiles = $oldastFinds? getErrorFiles($dirOldast) :
                                   getErrorFiles($dirNewast);
  diagnostic("minimal files: @minimalFiles");

  # throw away path information
  @minimalFiles = map { $_ =~ s|.*/||; $_; } @minimalFiles;
  diagnostic("minimal files: @minimalFiles");
  
  # use those files to filter the set of translation units
  createFilteredTUnits("$workdir/all-compile-commands.sh",    # input
                       "$workdir/required-commands.sh",       # output
                       @minimalFiles);                        # filter
                       
  run("touch $workdir/compile-commands.sh");
}

                   
# Given $dir, search for an <error> XML element for $checker and
# $function.  Then extract the set of file names mentioned by that
# report.
sub getErrorFiles {
  my ($dir) = @_;

  my $xmlFname = "$dir/output/$checker.errors.xml";
  open(IN, "<$xmlFname") or die("cannot read $xmlFname\n");

  diagnostic("parsing $xmlFname");

  # parsing state; see below for description of each
  my $state = 0;

  # file seen between <checker> and <function>
  my $fileAfterChecker = "";
  
  # map from seen file names to 1 (this is intended to act as a set)
  my %seenFiles = ();

  my $line;
  while (defined($line = <IN>)) {
    chomp($line);

    # state 0: outside an <error> of interest
    if ($state == 0) {
      if ($line =~ m|<error>|) {
        $state = 1;
      }
    }

    # state 1: inside an <error>, waiting to see <checker>
    elsif ($state == 1) {
      my ($c) = ($line =~ m|<checker>(.*)</checker>|);
      if (defined($c)) {
        if ($c eq $checker) {
          $state = 2;
        }
        else {
          $state = 0;     # wrong checker
        }
      }
    }

    # state 2: saw right <checker>, waiting to see <function>
    elsif ($state == 2) {
      my $f;

      # file in which defect occurs?
      ($f) = ($line =~ m|<file>(.*)</file>|);
      if (defined($f)) {
        $fileAfterChecker = $f;
      }

      # transition to next state?
      ($f) = ($line =~ m|<function>(.*)</function>|);
      if (defined($f)) {
        if ($f =~ m/^$function/) {
          $state = 3;

          # initialize the set of seen files
          if ($fileAfterChecker) {      # not set for defects associated directly with files
            %seenFiles = ($fileAfterChecker => 1);
          }
        }
        else {
          $state = 0;     # wrong function
        }
      }
    }

    # state 3: saw right function, collecting fnames
    elsif ($state == 3) {
      my ($f) = ($line =~ m|<file>(.*)</file>|);
      if (defined($f)) {
        $seenFiles{$f} = 1;
      }

      if ($line =~ m|</error>|) {
        # done with the error report of interest, bail out
        last;
      }
    }
    
    else {
      die("unknown state: $state");
    }
  }

  close(IN) or die;
  
  # collect the set of seen files
  my @ret = keys(%seenFiles);
  if (@ret == 0) {
    die("did not find $checker/$function in $xmlFname\n");
  }
  
  return @ret;
}

  
# write to $outputFile every line of $inputFile that contains a
# substring in @filterFileNames
sub createFilteredTUnits {
  my ($inputFile, $outputFile, @filterFileNames) = @_;
  
  open(IN, "<$inputFile") or die("cannot read $inputFile: $!\n");
  open(OUT, ">$outputFile") or die("cannot write $outputFile: $!\n");

  my $ct = 0;

  my $line;
  while (defined($line = <IN>)) {
    # loop over all filter names to see if $line should be admitted
    foreach my $n (@filterFileNames) {
      if ($line =~ m/$n/) {      # crude
        print OUT ($line);
        $ct++;
        last;
      }
    }
  }

  close(IN) or die;
  close(OUT) or die;
  
  diagnostic("wrote $ct lines to $outputFile");
  
  if ($ct == 0) {
    die("no translation units passed the filter!\n");
  }
}


# ------------------------ testDifference -----------------------

# return 1 if the current input passes the test, and 0 if not
sub testDifference {
  my $script = testScriptName();

  # use pp sources if they exist
  my $usepp = "";
  if (-d "$workdir/pp") {
    diagnostic("using pp");
    $usepp = "COMPILE_PP_SOURCES=1";
  }

  diagnostic("test script: $script");
  return 0==mysystem("cd $workdir && $usepp NO_GCC_TEST=1 $script -v");
}

# return the name of the script to use for testing purposes
sub testScriptName {
  if ($oldastFinds) {
    # new does not; we are working on a false negative
    return "./fn-test.sh";
  }
  else {
    # new finds the bug; we are working on a false positive
    return "./fp-test.sh";
  }
}


# ------------------------ model-tunits -------------------------

# Populate 'required-commands.sh' with the compile commands for
# all translation units mentioned by events in the defect.

sub modelTunits {
  # get set of files mentioned by events
  my @eventFiles = getEventFiles();
  
  # throw away path information
  @eventFiles = map { $_ =~ s|.*/||; $_; } @eventFiles;
  diagnostic("event files: @eventFiles");

  # use those files to filter the set of translation units
  createFilteredTUnits("$workdir/all-compile-commands.sh",    # input
                       "$workdir/required-commands.sh",       # output
                       @eventFiles);                          # filter
}
  

sub getEventFiles {
  # use cov-format-errors to get the events
  open(IN, "make -f minimize/template/Makefile " .
           "emacs-format-error NEWAST=$newastFinds " .
                              "CHECKER=$checker FUNCTION=$function |")
    or die("cannot run make: $!\n");

  # map of found file names to 1
  my %seenFiles = ();

  my $line;
  while (defined($line = <IN>)) {
    my ($file) = ($line =~ m/^(.*):[0-9]+:/);
    if (defined($file)) {
      $seenFiles{$file} = 1;
    }
  }
  
  close(IN) or die("make: $!\n");
  
  return keys(%seenFiles);
}


# ---------------------- minimize tunits ------------------------

# Minimize the set of needed translation units to repro the problem.

# Run delta to minimize $commandsFile such that the test passes.
# $commandsFile should be either "compile-commands.sh" or
# "required-commands.sh".
sub minimizeTunits {
  my ($commandsFile) = @_;

  my $script = testScriptName();

  run("cd $workdir && " .
      "NO_GCC_TEST=1 $delta -in_place -test=$script $commandsFile");
}


# -------------------------- preprocess -------------------------

# Preprocess all of the translation units, putting their results
# into $workdir.  Also write a shell script that will compile all
# of them.

sub preprocess {
  mychdir($workdir);
  run("rm -rf pp ; mkdir pp");
  preprocessCmdFile("compile-commands.sh");
  preprocessCmdFile("required-commands.sh");
  mychdir("../..");
}

# Parse $cmdFile and use that to produce the preprocessed files
# and compilation commands.  Assumes the input is as produced by
# prevent/utilities/create-build-script.pl.
sub preprocessCmdFile {
  my ($cmdFile) = @_;

  open(IN, "<$cmdFile")
    or die("cannot read $cmdFile: $!\n");

  open(OUT, ">pp/commands.sh")
    or die("cannot write pp/commands.sh: $!\n");

  my $line;
  while (defined($line = <IN>)) {
    chomp($line);

    # grab the tunit name, and everything after the echo
    my ($tunit, $rest) = ($line =~ m/^echo ([^\&]+) \&\& (.*)/);
    if (!defined($rest)) {
      die("failed to extract tunit name from command line: $line\n");
    }
    
    # throw away the echo; it would appear in the pp'd output
    # if we left it in there
    $line = $rest;

    # C or C++?
    my $isCPP;
    if ($line =~ m/ \&\& g\+\+ /) {
      $isCPP = 1;
    }
    elsif ($line =~ m/ \&\& gcc /) {
      $isCPP = 0;
    }
    else {
      die("cannot determine language from command line: $line\n");
    }
    
    # use it to form the name of a preprocessed file
    my $ppName = makeUnique("pp",
                            getFileName($tunit) . ($isCPP? ".ii" : ".i"));

    # change -c to -E
    if (!( $line =~ s/ -c / -E / )) {
      die("failed to find -c in command line: $line\n");
    }

    # remove any output specification
    $line =~ s/ -o *[^ ]+//;

    # run the preprocessing command line, writing output to $ppName
    run("($line) >pp/$ppName");

    # append an appropriate command line to OUT (which is
    # in the pp/ directory, so the name does not have that)
    print OUT ("echo $ppName && " .
               ($isCPP? "g++ -c" : "gcc -c") . " -o /dev/null $ppName\n");
  }

  close(IN) or die;
  close(OUT) or die;
}


# -------------------------- subroutines ------------------------

# return true if $checker/$function is found in $dir
sub defectFound {
  my ($dir) = @_;

  my $code = mysystem("grep '<function>$function</function>' $dir/output/$checker.errors.xml " .
                      ">/dev/null 2>&1");
  if ($code == 0) {
    return 1;    # found
  }
  else {
    return 0;    # not found
  }
}


sub diagnostic {
  print(@_, "\n");
}

  
# map a string to only safe identifier characters
sub toSafeChars {
  my ($s) = @_;
  
  $s =~ s/[^a-zA-Z0-9_]/_/g;
  
  return $s;
}


# run a command, and die if it fails
sub run {
  my (@cmd) = @_;

  diagnostic("@cmd");
  my $code = mysystem(@cmd);
  if ($code != 0) {
    if ($code >= 256) {
      $code = $code >> 8;
      die("exited with code $code: @cmd\n");
    }
    else {
      die("died by signal $code: @cmd\n");
    }
  }
}


# like system, except bail if underlying command died by
# ctrl-c
sub mysystem {
  my (@cmd) = @_;

  my $code = system(@cmd);
  if ($code == 2) {
    die("interrupted\n");
  }
  return $code;
}


# chdir or die
sub mychdir {
  my ($d) = @_;
  
  chdir($d) or die("cannot chdir to $d: $!\n");
  print("chdir $d\n");
}


# return just the file name portion of a path
sub getFileName {
  my ($d) = @_;
  
  $d =~ s|.*/||;
  
  return $d;
}


# add stuff if necessary to "$dir/$fname" so it does not exist;
# return just the $fname portion
sub makeUnique {
  my ($dir, $fname) = @_;

  if (! -f "$dir/$fname") {
    return $fname;
  }

  my $i = 2;
  while (-f "$dir/$fname.$i" && $i < 100) {
    $i++;
  }

  if ($i == 100) {
    die("unable to find a uniqifying suffix: $dir/$fname\n");
  }
  
  return "$fname.$i";
}


#  # called when ctrl-c pressed; children already killed
#  sub handleSigInt {
#    die("ctrl-c pressed\n");
#  }


# EOF
