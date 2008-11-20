#!/usr/bin/perl -w
# script to automate a number of Prevent result minimization tasks

use strict 'subs';

sub usage {
  print(<<"EOF");
usage: $0 <checker> <function-name-prefix> <task> [<task>...]

Runs each task in sequence.

<task> is one of:
  init           create the working directory
  test           test to see if difference of interest remains
  model-tunits   put set of tunits with events into required-commands.sh
  (more to document)
EOF
}

if (@ARGV < 3) {
  usage();
  exit(2);
}

#$SIG{INT} = \&handleSigInt;

$HOME = $ENV{"HOME"};
$deltadir = "$HOME/wrk/cplr/delta";
$delta = "$deltadir/bin/delta";
$topformflat = "$deltadir/bin/topformflat";

$checker = shift @ARGV;
$function = shift @ARGV;

diagnostic("checker: $checker");
diagnostic("function: $function");

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
  $dirWithDefect = $dirNewast;
}
else {
  diagnostic("old AST found it");
  $dirWithDefect = $dirOldast;
}


# ---------------------------- dispatch -------------------------
# main task dispatch loop
while (@ARGV) {
  $task = shift @ARGV;
  diagnostic("task: $task");

  # primitive tasks
  if ($task eq "clean") {
    clean();
  }
  elsif ($task eq "init") {
    init();
  }
  elsif ($task eq "test") {
    my $result = testDifference(0);
    print("testDifference: $result\n");
  }
  elsif ($task eq "test-all-chk") {
    my $result = testDifference(1);
    print("testDifference: $result\n");
  }
  elsif ($task eq "model-tunits") {
    modelTunits();
  }
  elsif ($task eq "model-tunits-radius1") {
    modelTunitsRadius(1);
  }
  elsif ($task eq "model-tunits-radius2") {
    modelTunitsRadius(2);
  }
  elsif ($task eq "model-tunits-radius3") {
    modelTunitsRadius(3);
  }
  elsif ($task eq "model-tunits-radius4") {
    modelTunitsRadius(4);
  }
  elsif ($task eq "model-tunits-radius5") {
    modelTunitsRadius(5);
  }
  elsif ($task eq "model-tunits-radius10") {
    modelTunitsRadius(10);
  }
  elsif ($task eq "all-tunits") {
    useAllTunits();
  }
  elsif ($task eq "min-req-tunits") {
    minimizeTunits("required-commands.sh");
  }
  elsif ($task eq "min-main-tunits") {
    minimizeTunits("compile-commands.sh");
  }
  elsif ($task eq "preprocess") {
    preprocess();
  }
  elsif ($task eq "strip-hashline") {
    stripHashline();
  }
  elsif ($task eq "flat0") {
    topformflat(0);
  }
  elsif ($task eq "flat1") {
    topformflat(1);
  }
  elsif ($task eq "flat2") {
    topformflat(2);
  }
  elsif ($task eq "flat3") {
    topformflat(3);
  }
  elsif ($task eq "flat4") {
    topformflat(4);
  }
  elsif ($task eq "min-pp-code") {
    minimizePPCode();
  }
  elsif ($task eq "bak-pp") {
    backupPPCode();
  }

  # combined procedures
  elsif ($task eq "expand-radius-inc") {
    expandRadiusIncrementally();
  }
  elsif ($task eq "init-tunits") {
    initAndGetTunits();
  }
  elsif ($task eq "pp-and-strip") {
    preprocessAndStrip();
  }
  elsif ($task eq "min-seq") {
    minimizeSequence();
  }

  # main end-to-end command
  elsif ($task eq "end-to-end") {
    endToEnd();
  }

  else {
    die("unknown task: $task\n");
  }
}

exit(0);


# ----------------------------- clean ---------------------------
sub clean {
  run("rm -rf $workdir");
}


# ------------------------------ init ---------------------------
sub init {
  if (-d $workdir) {
    die("directory already exists: $workdir\n");
  }

  # the 'minimize' subdirectory should already exist
  run("mkdir", $workdir);
  run("ln minimize/template/* $workdir");

  # get minimal set of files
  my @minimalFiles = $oldastFinds? getErrorFiles($dirOldast) :
                                   getErrorFiles($dirNewast);
  #diagnostic("minimal files: @minimalFiles");

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
  my ($allCheckers) = @_;

  my $script = testScriptName();

  # use pp sources if they exist
  my $settings = "";
  if (-d "$workdir/pp") {
    diagnostic("using pp");
    $settings .= " COMPILE_PP_SOURCES=1";
  }

  # possibly turn on all checkers
  if ($allCheckers) {
    $settings .= " ALLCHECKERS=1";
  }

  diagnostic("test script: $script");
  return 0==mysystem("cd $workdir && $settings NO_GCC_TEST=1 $script -v");
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
    my ($file) = ($line =~ m/^([^:]*):[0-9]+:/);
    if (defined($file)) {
      $seenFiles{$file} = 1;
    }
  }
  
  close(IN) or die("make: $!\n");
  
  return keys(%seenFiles);
}


# ----------------------- modelTunitsRadius ------------------------
# Populate 'compile-commands.sh' with compile commands for all
# transation units mentioned in the defect and model events, plus a
# given radius distance in the callgraph.

sub modelTunitsRadius {
  my ($radius) = @_;
  
  my @funcs = getDefectFunctions();
  
  diagnostic("defect functions:");
  foreach my $fn (@funcs) {
    diagnostic("  $fn");
  }

  my @files = radiusExpandFuncsToFiles($radius, @funcs);

  # throw away path information
  @files = map { $_ =~ s|.*/||; $_; } @files;

  diagnostic("expanded files at radius $radius:");
  foreach my $file (@files) {
    diagnostic("  $file");
  }

  # use those files to filter the set of translation units
  createFilteredTUnits("$workdir/all-compile-commands.sh",    # input
                       "$workdir/compile-commands.sh",        # output
                       @files);                               # filter
}

sub getDefectFunctions {
  # use cov-format-errors to get the functions
  open(IN, "make -f minimize/template/Makefile " .
           "emacs-format-error NEWAST=$newastFinds " .
                              "CHECKER=$checker FUNCTION=$function |")
    or die("cannot run make: $!\n");

  # map of found function names to 1
  my %seenFunctions = ();

  my $line;
  while (defined($line = <IN>)) {
    my ($fn) = ($line =~ m/^function: (.*)/);
    if (defined($fn)) {
      $seenFunctions{$fn} = 1;
    }
  }

  close(IN) or die("make: $!\n");

  return keys(%seenFunctions);
}

# expand @funcs by $radius callchain link, then map them to their
# containing file names
sub radiusExpandFuncsToFiles {
  my ($radius, @funcs) = @_;

  # set of original functions
  my %rootFuncs = ();
  foreach my $fn (@funcs) {
    $rootFuncs{$fn} = 1;
  }

  # get function number -> name map
  my @funcNumberToName = ();
  open(IN, "<$dirWithDefect/output/.cache/funcname.cache")
    or die("cannot read $dirWithDefect/output/.cache/funcname.cache\n");
  my $line;
  while (defined($line = <IN>)) {
    chomp($line);
    push @funcNumberToName, ($line);
  }
  close(IN) or die;

  while ($radius--) {
    # root+called functions
    my %expandedFuncs = %rootFuncs;

    # process callgraph
    open(IN, "<$dirWithDefect/output/.cache/callgraph.cache")
      or die("cannot read $dirWithDefect/output/.cache/callgraph.cache");
    while (defined($line = <IN>)) {
      my ($caller, $callee) = ($line =~
        m/^[0-9]+\|([0-9]+)\|[0-9]+\|([0-9]+)\|/);
        # ^^^^^^^   ^^^^^^   ^^^^^^   ^^^^^^   ...
        #  file     caller    line    callee   ...
      if (defined($callee)) {
        my $callerName = $funcNumberToName[$caller];
        my $calleeName = $funcNumberToName[$callee];
        if (defined($rootFuncs{$callerName})) {
          #diagnostic("expansion edge: $callerName -> $calleeName");
          $expandedFuncs{$calleeName} = 1;
        }
      }
    }
    close(IN) or die;

    # pile expanded back into root
    %rootFuncs = %expandedFuncs;
  }

  # read the filename cache
  my @fileNames = ();
  open(IN, "<$dirWithDefect/output/.cache/filename.cache")
    or die("cannot read $dirWithDefect/output/.cache/filename.cache");
  while (defined($line = <IN>)) {
    chomp($line);
    push @fileNames, ($line);
  }
  close(IN) or die;

  # files containing %rootFuncs
  my %rootFiles = ();

  # process callgraph again to get files
  open(IN, "<$dirWithDefect/output/.cache/callgraph.cache")
    or die("cannot read $dirWithDefect/output/.cache/callgraph.cache");
  while (defined($line = <IN>)) {
    my ($file, $caller) = ($line =~
      m/^([0-9]+)\|([0-9]+)\|/);
      #   ^^^^^^   ^^^^^^     ...
      #    file    caller     ...
    if (defined($caller)) {
      my $callerName = $funcNumberToName[$caller];
      if (defined($rootFuncs{$callerName})) {
        my $fname = $fileNames[$file];
        #diagnostic("func file: $callerName -> $fname");
        $rootFiles{$fname} = 1;
      }
    }
  }
  close(IN) or die;

  return keys(%rootFiles);
}


# ------------------ expandRadiusIncrementally ------------------
# Expand the tunits around the defect until we find it.

sub expandRadiusIncrementally {
  for (my $i = 1; $i <= 10; $i++) {
    modelTunitsRadius($i);
    if (testDifference(0)) {
      print("got it at radius $i");
      return 1;
    }

    if ($i == 5) {
      $i = 9;    # so after increment it will be 10
    }
  }
  
  return 0;
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
    #
    # the "|| exit" is important; I need this script to fail
    # when the preprocessed input is bad
    print OUT ("echo $ppName && " .
               ($isCPP? "g++ -c" : "gcc -c") . " -o /dev/null $ppName || exit\n");
  }

  close(IN) or die;
  close(OUT) or die;
}


# ------------------------- stripHashline -----------------------

# Remove the # lines from the pp input.

sub stripHashline {
  my $olddir = getcwd();

  mychdir("$workdir/pp");

  my @fnames = `ls *.i*`;
  foreach my $fn (@fnames) {
    chomp($fn);
    run("mv $fn $fn.prev && strip-hashline < $fn.prev > $fn && rm $fn.prev");
  }

  mychdir($olddir);
}


# -------------------------- topformflat ------------------------

# Remove newlines from the input so each line contains one top-level
# form (or, with increasing $level, smaller units of text per line).

sub topformflat {
  my ($level) = @_;

  my $olddir = getcwd();
  mychdir("$workdir/pp");

  my @fnames = `ls *.i*`;
  foreach my $fn (@fnames) {
    chomp($fn);
    run("mv $fn $fn.prev && $topformflat $level < $fn.prev > $fn && rm $fn.prev");
  }

  mychdir($olddir);
}


# ----------------------- minimizePPCode -----------------------

# Run delta to minimize the current pp code.

sub minimizePPCode {
  my $script = testScriptName();

  # use pp sources if they exist
  if (! -d "$workdir/pp") {
    die("directory does not exist: $workdir/pp\n");
  }

  # minimize the entire set of preprocessed files in pp
  # simultaneously!
  run("cd $workdir && " .
      "NO_GCC_TEST=1 COMPILE_PP_SOURCES=1 " .
        "$delta -in_place -test=$script pp/*.i*");
}


# ------------------------- backupPPCode ------------------------
# Copy the current pp code to pp-bak

sub backupPPCode {
  my $olddir = getcwd();
  mychdir("$workdir");

  run("rm -rf pp-bak");
  run("cp -a pp pp-bak");

  mychdir($olddir);
}


# ----------------------- initAndGetTuints ----------------------
# Go from scratch to minimized translation unit set.

sub initAndGetTunits {
  init();

  if (!testDifference(0)) {
    diagnostic("initial attempt with defect tunits fails");

    modelTunits();

    if (!testDifference(0)) {
      diagnostic("attempt with model tunits fails");

      if (!expandRadiusIncrementally()) {
        diagnostic("failed to do radius expansion");

        # will try with all the translation units
        useAllTunits();
      }

      minimizeTunits("compile-commands.sh");
    }
  }

  # the above code has already minimized compile-commands.sh, so now
  # do the same for required-commands.h
  minimizeTunits("required-commands.sh");

  # print how many tunits are in each file
  run("cd $workdir && wc -l required-commands.sh compile-commands.sh");
}


# -------------------------- useAllTunits -----------------------
# Put all translation units into compile-commands.sh

sub useAllTunits {
  run("cd $workdir && cp all-compile-commands.sh compile-commands.sh");
}


# ------------------------ preprocessAndStrip -------------------
# Preprocess, test, strip, test.

sub preprocessAndStrip {
  preprocess();
  if (!testDifference(0)) {
    die("preprocessing killed the result\n");
  }
  
  stripHashline();
  if (!testDifference(0)) {
    die("striping killed the result\n");
  }
}


# ----------------------- minimizeSequence ----------------------
# minimize at various levels

sub minimizeSequence {
  flatThenMin(0);
  flatThenMin(1);

  flatThenMin(0);
  flatThenMin(1);
  flatThenMin(2);

  flatThenMin(0);
  flatThenMin(1);
  flatThenMin(2);
  flatThenMin(3);

  flatThenMin(0);
  flatThenMin(1);
  flatThenMin(2);
  flatThenMin(3);
  flatThenMin(4);
  
  print("completed minimization at level 4\n");
  
  # print line counts
  run("cd $workdir/pp && wc -l *.ii");
}

sub flatThenMin {
  my ($level) = @_;

  diagnostic("flatThenMin($level)");

  topformflat($level);

  # this will die if minimization fails
  minimizePPCode();
}


# --------------------------- endToEnd --------------------------
# Run whole procedure, start to finish.

sub endToEnd {
  initAndGetTunits();
  preprocessAndStrip();
  minimizeSequence();
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


# current directory
sub getcwd {
  my $s = `pwd`;
  if ($? != 0) {
    die("pwd failed\n");
  }
  chomp($s);
  return $s;
}


#  # called when ctrl-c pressed; children already killed
#  sub handleSigInt {
#    die("ctrl-c pressed\n");
#  }


# EOF
